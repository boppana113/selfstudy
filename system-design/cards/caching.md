# Caching

## Patterns
Q: How does cache-aside work, read and write?
A: The app owns the cache. Read: check cache, on a miss read the DB and set the key with a TTL. Write: update the DB, then delete the key. The DB never touches the cache.
Why: Picture GET product 42. The app asks Redis for `product:42`: miss. It reads Postgres, gets $20, sets `product:42` with a 10-minute TTL, and returns. The next 10,000 reads hit Redis. The price changes to $25: the app writes Postgres, deletes `product:42`, and the next read refills it with $25.

Q: Cache-aside vs write-through: when do you pick write-through, and what does it cost?
A: Write-through writes the cache and DB together on every write, so the cache is always warm and current. Pick it when reads must see writes immediately and data is read soon after writing; the cost is slower writes and caching data nobody reads.
Why: A user updates their profile and reloads. With cache-aside, the delete-then-refill works, but the first read after a write pays a miss. With write-through, the write puts the new profile in Redis and Postgres in one step, so the reload is a hit. But a bulk import of 1M rarely viewed products also lands in Redis, wasting memory.
Flip: Write-behind (cache now, DB asynchronously) for very write-heavy data that can tolerate losing the last few seconds if the cache dies.

## Invalidation
Q: A price changes. Update the cache or delete the key, and DB or cache first?
A: Write the DB first, then delete the key. Deleting avoids racing writers leaving a stale value; the TTL bounds any delete that gets lost.
Why: Two price updates race: A sets $25, B sets $30. If each overwrites the cache, A's slower cache write can land last, so the DB says $30 and the cache says $25 until TTL. If each deletes instead, the worst case is an extra miss that reads $30 from the DB. Cache first is worse: a reader can refill the old DB value between your cache delete and your DB write.
Staff: A tiny race remains (a slow reader sets the old row after your delete); bound it with the TTL, a delayed second delete, or CDC-driven deletes.

Q: Your cache keys have no TTL, and writes do DB-then-delete. What's the risk?
A: Any missed delete leaves the wrong value forever. A TTL (say 10 minutes) bounds how long a missed delete can last, and lets cold keys age out.
Why: The app updates Postgres to $25, then crashes before `DEL product:42`. With no TTL, Redis serves $20 until someone notices, maybe days. With a 10-minute TTL, the worst case is 10 minutes of $20.

## Eviction
Q: LRU vs LFU, and which for a catalog with a few hundred always-popular items?
A: LRU evicts the least recently read key; LFU evicts the least often read. LFU for a stable hot set, because a one-off scan can't push popular items out.
Why: A nightly job reads 1M old products once each. Under LRU, each of those is now "recently read," so the 300 bestsellers get evicted and morning traffic misses. Under LFU, the bestsellers have thousands of hits and the scanned items have 1, so the scanned items go first. In Redis, set `maxmemory` and `maxmemory-policy allkeys-lfu`.
Flip: LRU when popularity shifts fast (news, trending), since LFU keeps yesterday's hits too long.

Q: Redis is set to maxmemory-policy noeviction and hits maxmemory. What happens?
A: Redis keeps serving reads but rejects every write with an OOM error, so no new key can be cached. Use allkeys-lfu (or allkeys-lru) for a cache.
Why: A nightly job fills 25 GB with 5M cold products through the miss path. Next morning a new product goes hot: every request misses, the SET fails, so every request hits Postgres. The hit rate keeps falling, and past ~10k/s on Postgres product pages time out. Nothing recovers, because nothing is ever evicted.
Staff: Alert on used_memory vs maxmemory and on hit rate; keep batch jobs on a read replica, not the cache.

## Failure modes
Q: A hot key's TTL expires and 20,000 requests miss in the same second. What stops them all hitting the DB?
A: Request coalescing: the first miss takes a short lock and rebuilds the key, and the rest wait or get the stale value. Plus jittered TTLs so hot keys don't expire together.
Why: Noon, flash sale, `product:42` expires. Without coalescing, 20,000 queries hit Postgres at once, and product pages time out right as the sale opens. With it, request 1 sets `lock:product:42` (SET NX, 5 s), reads Postgres once, and refills. Requests 2–20,000 see the lock, wait 50 ms, and read the fresh key. One DB query instead of 20,000.
Staff: Serve stale while one worker refreshes (stale-while-revalidate); pre-warm keys before a scheduled sale.

Q: Does the eviction policy matter for a stampede when a key expires?
A: No. The key expired on its TTL; LRU vs LFU only decides what's dropped when memory is full. The fix is coalescing and jittered TTLs.
Why: Picture Redis at 40% memory. Nothing is being evicted at all. `product:42` disappears at 12:00:00 because its 10-minute TTL ran out. Switching to LFU changes nothing here; every request still misses at 12:00:00.

Q: One key gets 500k reads/s on a Redis shard that handles 100k. Why don't more shards help?
A: One key always hashes to one shard, so all 500k still land on the same box. Copy the key instead.
Why: You go from 4 shards to 8. `celeb:123` hashes to slot 5,021, which lives on shard 3 both before and after. Shard 3 still gets 500k/s and the other seven idle. Sharding spreads *different* keys; it can't split one key.

Q: How do you serve a hot key at 500k reads/s?
A: Split it into N copies (`celeb:123#1`–`#8`) and have readers pick one at random, or serve it from read replicas, or add an in-process cache with a few seconds' TTL. The cost: writes must update every copy.
Why: 8 copies spread across shards means 500k / 8 ≈ 62k each, under a 70% line on 100k boxes. The profile changes maybe once a day, so writing 8 keys is cheap. With a 2 s in-process cache on 200 app servers, Redis sees at most 200 reads per 2 s for that key, almost nothing.
Staff: Detect hot keys automatically (client-side counters, `redis-cli --hotkeys`) and split only those.

Q: A bot requests nonexistent IDs at 10k/s and the cache doesn't help. Why, and what fixes it?
A: Nothing gets cached for a missing ID, so every request reaches the DB. Cache "not found" with a short TTL, and put a Bloom filter of real IDs in front; rate-limit the client.
Why: `product:99999999` isn't in Redis or Postgres, so every request is a miss and a DB query: 10k/s of junk. Caching the miss for 60 s helps only if IDs repeat; a bot using random IDs fills Redis with junk entries instead. A Bloom filter of the 5M real IDs (a few MB) answers "definitely not here" in microseconds, so those requests never reach Redis or Postgres.

Q: In request coalescing, why does the rebuild lock need an expiry?
A: If the lock holder crashes mid-rebuild, a lock with no expiry blocks every waiter until they time out. Use SET lock:key NX PX 3000 so it frees itself.
Why: Request 1 takes `lock:product:42` and its server dies. Without an expiry, 19,999 requests wait on a refill that never comes, and every product page times out. With a 3 s expiry, the lock frees at 3 s, request 2 takes it, and the key is rebuilt.

Q: How do you make coalescing waiters not wait at all?
A: Serve stale: store a soft expiry inside the value and set a longer hard TTL. The first request past the soft expiry refreshes in the background, and everyone else gets the old value right away.
Why: `product:42` has a soft expiry of 12:00 and a hard TTL of 12:05. At 12:00:01, request 1 sees it's soft-expired, takes the lock, and re-reads Postgres. Requests 2–20,000 get the 11:50 value instantly. The price is a few seconds old, nobody waits, and Postgres sees one query.
Flip: Don't serve stale where staleness costs money (inventory at checkout); read the source of truth there.

Q: 40k reads/s, Postgres caps near 10k. At what hit rate does Postgres tip, and what drops a hit rate that far?
A: Misses reach Postgres: 40k × 25% = 10k, so it tips at 75%. Big drops come from a cold cache (Redis failover or restart), bulk invalidation, the hot set being evicted, or a key-format change on deploy.
Why: At 95%, misses are 5% × 40k = 2k/s. Redis fails over to an empty node: the hit rate is 0%, all 40k/s hit Postgres, and pages time out within seconds. Slow catalog growth only moves the hit rate a point or two.
Staff: Alarm at a 90% hit rate and on Postgres QPS directly.

Q: How do you keep a cache warm through failures and deploys?
A: A Redis replica with automatic failover (promoted already warm), RDB/AOF persistence for restarts, pre-warming the top keys before cutting traffic, and overwriting rather than mass-deleting on bulk updates.
Why: The primary dies. Sentinel promotes the replica, which already holds every key, so the hit rate stays at ~95%. For a brand-new cluster, load the top 100k keys from access logs first, then ramp traffic 10% → 50% → 100% so Postgres never sees 40k misses a second.

Q: You split a hot key into 8 copies. How do readers find one, and how do you keep the copies on different shards?
A: Fixed suffixes #0–#7; each reader picks a random number 0–7. Each suffixed key hashes on its own, so check the slots don't collide, and never use hash tags ({key}#n), which force every copy into one slot.
Why: `celeb:123#0`…`#7` hash to 8 slots. With 4 shards, two copies on one shard is likely, so that shard gets 125k/s and tips. Pick suffixes whose slots map to different shards. Writing `{celeb:123}#0` instead puts all 8 in the same slot, so you're back to 500k on one box.

## Where to cache
Q: Redis feature lookups take 2 ms. What does an in-process cache on 50 app servers gain and cost?
A: About 1 µs per lookup instead of 2 ms, and less load on Redis. The cost: 50 copies that can each be stale, and memory on every box. Keep the TTL short (~10 s) so staleness is bounded.
Why: A fraud check does 20 feature lookups: 40 ms from Redis, ~20 µs in-process. But a user's "orders in the last hour" changes on each order, and each of 50 boxes holds its own copy, so a box can score with a count up to 10 s old. Fine for slow-moving features like account age; bad for velocity counts.

Q: A product page goes global at 1M reads/s, mostly anonymous. Which layer do you add first, and what's the catch?
A: A CDN caching the page or product JSON at the edge; 95% edge hits turns 1M into 50k at origin. The catch: the edge serves the old price for its TTL, so keep the TTL short (~60 s), purge on price change, and re-read price at checkout.
Why: A shopper in Tokyo gets the page from a Tokyo edge in 20 ms instead of 150 ms from Ohio. The price drops from $25 to $20: without a purge, Tokyo shows $25 for up to 60 s. With a surrogate-key purge, every edge drops the page in seconds, and checkout charges the price from Postgres anyway.
Flip: Logged-in, personalized pages don't cache at the edge whole; cache the shared shell and fetch the personal parts.

## When not to cache
Q: Name cases where you'd not cache even with heavy reads.
A: Stale data does damage (inventory at checkout, account balance), low hit rate (one-off keys), write-heavy data (constant invalidation), or the DB already handles the load.
Why: Checkout: the cache says 3 seats left, the DB says 0, and you oversell, so read the source of truth at commit. Search with unique queries: 95% misses, so you pay a Redis hop for nothing. A counter updated 1,000 times a second: every write invalidates, so the hit rate is near zero.
Staff: Cache the browse path, re-check against the DB at commit.
