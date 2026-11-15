# Caching

## Pretest: 2026-11-12 (score 31%; Below mid 3 · Mid 5 · Senior 0 · Staff 0)
Started while data-modeling was still in progress (25%), by the user's choice.
### Questions
**Q1 🟦 Mid**: Product page at 50,000 reads/s on Postgres. How would you add a cache: what's the read path, and what happens when a price changes?
- You said: 50k is under Postgres's ~100k/s so no cache needed until more; cache product link/ID/price in Redis; invalidate and update on price change.
- Strong answer: "One Postgres box handles roughly 10k simple reads a second, so at 50k I need a cache. Cache-aside: read `product:{id}` from Redis; on a miss, read Postgres and set it with a 10-minute TTL. On a price change I write the database first, then delete the key, so the next read refills it with the new price. Deleting avoids two writers racing to leave a stale value, and the TTL bounds any missed delete."

**Q2 ⬜ Below mid**: Cache-aside vs write-through: how does each work, and when would you pick write-through?
- You said: in cache-aside the database updates the cache on an interval (backwards); write-through updates both; write-through for pricing, cache-aside for feeds.
- Strong answer: "In cache-aside the app owns the cache: reads check the cache, and on a miss the app reads the database and fills the cache; writes go to the database and delete the key. In write-through every write goes to the cache and the database together, so the cache is always warm and current. Write-through costs slower writes and caching data nobody reads, so I'd pick it when reads must see writes immediately and data is read soon after it's written."

**Q3 🟦 Mid**: Redis at 25 GB fills up. How does it decide what to evict, and LRU or LFU for a catalog with a few hundred always-popular items?
- You said: LRU evicts the earliest-inserted (wrong: that's FIFO); LFU for a persistent hot set (right pick).
- Strong answer: "Redis evicts once it hits maxmemory, using maxmemory-policy like allkeys-lru or allkeys-lfu. LRU throws out whatever was least recently read; LFU throws out whatever is read least often. For a stable hot set I'd use LFU, because a one-off scan of old products can push popular items out of LRU but not out of LFU."

**Q4 ⬜ Below mid**: Flash sale; a hot product's key expires at noon and 20,000 requests arrive that second. What happens, how do you prevent it?
- You said: all 20k hit the DB and slow it down (right); fix: LRU so hot items stay cached (wrong: the key expired on TTL, eviction is irrelevant).
- Strong answer: "All 20,000 miss at once and hit the database together, so product pages time out right as the sale opens. I'd coalesce requests: the first miss takes a short lock and rebuilds the key while the rest wait or get the stale value. I'd jitter TTLs so hot keys don't expire together, and pre-warm or refresh hot keys before a scheduled sale."

**Q5 🟦 Mid**: Fraud features from Redis take 2 ms. Add an in-process cache in each of 50 app servers: gain and cost?
- You said: fewer network calls; 50 copies become a consistency nightmare vs the source of truth.
- Strong answer: "In-process is about a microsecond instead of 2 ms, and it takes load off Redis. The cost is 50 copies that can each be stale, plus memory on every box. I'd keep the TTL short, say 10 seconds, so staleness is bounded, and only cache features that change slowly."

**Q6 ⬜ Below mid**: One celebrity's profile key gets 500k reads/s on a shard that tops out at ~100k. What do you do?
- You said: add Redis nodes: 500k / 70k at 70% load ≈ 8 nodes (math clean, mechanism wrong: one key → one shard).
- Strong answer: "One key always hashes to one shard, so more nodes don't help. I'd split the key into eight copies with suffixes and have readers pick one at random, about 62k each. Or serve it from read replicas, or an in-process cache with a few seconds' TTL. The cost is that a write has to update every copy, which is fine for a profile that rarely changes."

**Q7 🟦 Mid**: A bot requests nonexistent product IDs at 10k/s; the cache doesn't help. Why, and what would you do?
- You said: they're in neither cache nor DB; cache zero-row results so lookups fail fast.
- Strong answer: "Nothing gets cached for an ID that doesn't exist, so every request goes straight to Postgres: 10k/s of junk. I'd cache 'not found' with a short TTL, but random IDs can fill the cache with junk, so I'd put a Bloom filter of real IDs in front, which answers 'definitely not here' without touching the DB, and rate-limit the client."

**Q8 🟦 Mid**: Name a case where you'd deliberately not cache even though reads are heavy.
- You said: authorization lookups for JWTs; a stale cached permission lets a user bypass a rule (good reason, muddled example: JWTs are validated locally, there's no lookup).
- Strong answer: "Inventory at checkout: a stale count oversells, so I read the source of truth at commit time. Also when the hit rate is low, like one-off keys, or the data is write-heavy so I'd be invalidating constantly, or the database already handles the load. Each one is a cost I'd name instead of caching by default."

### Gap to mid
- Cache-aside: the app fills the cache on a miss and deletes on write; the DB never touches the cache
- Stampede on TTL expiry: request coalescing + jittered TTLs (eviction policy is irrelevant)
- Hot key: one key → one shard, so split/replicate the key; more shards don't help

### Gap to senior
- ✅ Threshold: cache past ~10k reads/s per Postgres box (said 100k)
- Read path with key + TTL; write = DB first, then delete key
- LRU = least recently read (not oldest insert); Redis maxmemory-policy
- In-process: µs vs 2 ms, bounded staleness via short TTL
- Penetration: short negative TTL + Bloom filter + rate limit
- Write-through cost: slower writes + caching unread data

### Hold-in-mind questions
- A hot key's TTL expires and 20,000 requests miss at once. What exactly stops them all hitting the database?
- One key gets 500k reads/s on a shard that handles 100k. Why don't more shards help, and what does?
- On a price update, do you update the cache or delete the key, and does the DB or the cache go first? What race does each choice open?

### Delivery
- Habit: fix doesn't act on what broke (Q4 "use LRU" for a TTL expiry; Q6 "add Redis nodes" for one key). Check: does this fix touch the thing that failed?
- Rewrite (Q6): "One key always hashes to one shard, so adding nodes doesn't help; all 500k reads still land on the same box. I'd copy the key instead: split it into eight copies with suffixes, readers pick one at random, and that's about 62k per copy, under the 70% line. The cost is a write has to update all eight. For a celebrity profile that changes rarely, I'd also put a local cache with a few seconds' TTL on each app server."
- Did well: Q6 estimation followed the frame exactly (assumption → formula → rounded number).

## Drill: 2026-11-15 (score 58%; Below mid 1 · Mid 3 · Senior 2 · Staff 0)
### Questions
**R1 (failure mode) 🟦 Mid**: Flash sale; a hot product's key expires at noon and 20,000 requests miss in that second. What exactly stops all 20,000 hitting the database?
- Follow-up: The lock holder crashes mid-rebuild or its DB query hangs 5 s. What happens to the 19,999, and how do you make them not wait at all?
- You said: request coalescing, one request takes a lock and refills, the rest read the cache; cost = waiters pay the first request's latency. Follow-up: waiters stall; fail fast with a short timeout + backpressure.
- Re-answer: skipped by user.
- Strong answer: "Twenty thousand misses at once would saturate Postgres, around 10k/s, and product pages time out right at launch. The first miss takes a lock with an expiry, SET NX PX 3000, so a crashed holder can't block everyone, and rebuilds the key. Meanwhile everyone else gets the stale value: I keep a soft expiry inside the value and a longer hard TTL, so nobody waits. Since the sale is scheduled, I'd pre-warm the key before noon and jitter TTLs."
- Staff adds: per-process singleflight so 50 servers send 50 rebuilds, not 20k; alert on DB QPS spikes on misses.

**R2 (scenario) 🟩 Senior**: Celebrity profile key at 500k reads/s on a shard that tops out at ~100k. Why don't more shards help, and what instead?
- Follow-up: How does a reader find one of the 8 copies, and what makes them land on 8 different shards?
- You said: sharding splits the keyspace, one key still lands on one box; 8 copies → 62.5k each, under 70%; cost = writes hit every copy. Follow-up: key + random suffix, client picks one at random (didn't answer the different-shards half).
- Strong answer: "One key lives on one shard, so I'd make eight copies with fixed suffixes 0 to 7 and readers pick one at random: about 62k per copy. Each suffixed key hashes separately, so I'd check their slots don't collide, and avoid hash tags, which force every copy into one slot. The cost is a write updates all eight, fine for a profile that rarely changes. I'd also put a few-second in-process cache on each app server."
- Staff adds: in-process cache absorbs most of it; detect hot keys automatically; non-atomic fan-out write means brief mixed versions.

**R3 (tradeoff duel) 🟦 Mid**: A price changes. Update the cache or delete the key, and DB or cache first? Pick one and defend it.
- Follow-up: Walk through a read arriving between your delete and your DB write. What ends up in the cache, and for how long?
- You said: delete key, then update DB (while reasoning "DB is source of truth first"); delete because next read gets a fresher TTL; flip to cache-first for trading. Follow-up: traced the race correctly and flipped to DB then delete.
- Strong answer: "Write the database first, then delete the key. Delete rather than update, because two concurrent writers updating the cache can land out of order and leave the old price until TTL; a delete is idempotent, and the next read refills from Postgres. Delete-first is worse: a reader in the gap refills the old price for the full TTL. A tiny window remains where a slow reader sets an old value after my delete, so the TTL bounds it, and I'd drive deletes off CDC if staleness is costly."
- Staff adds: delayed double delete; CDC (Debezium on the WAL) so deletes are never missed; for must-be-fresh data, write-through with a version check, never cache-first.

**R4 (spot the flaw) ⬜ Below mid**: What's wrong with this design?
```
Product service, 40k reads/s, Postgres behind Redis
- Redis: maxmemory 25 GB, maxmemory-policy noeviction
- Read: GET product:{id}; on miss read Postgres, SET with no TTL
- Write: UPDATE Postgres, then DEL product:{id}
- Nightly analytics job reads every product (5M items) through this same cache
```
- Follow-up: What happens with noeviction when the job pushes Redis to 25 GB?
- You said: no TTL means Redis going down stampedes Postgres; analytics job misses uncached products, so read from DB; fix = 5-min TTL + job reads DB. Follow-up: "Redis goes down."
- Strong answer: "Three problems. noeviction means once the job fills 25 GB, Redis rejects every new SET, so misses go to Postgres forever, the hit rate falls, and past 10k/s pages time out; I'd use allkeys-lfu. No TTL means one missed delete leaves a wrong price forever, so a 10-minute TTL bounds it. And the job's 5M cold reads fill the cache through the miss path, so I'd point it at a read replica."
- Staff adds: alert on used_memory vs maxmemory and hit rate; state the ambiguous assumption ("the job uses the normal read path") out loud.
- Note: user's reading (job does raw GETs, no fill) was a fair interpretation of the wording; under it, the missing-data point holds.

**R5 (estimation) 🟩 Senior**: 40k reads/s, Postgres ~10k, 95% hit rate: what does Postgres see? At what hit rate does it tip, and what drops the hit rate that far?
- Follow-up: What realistically drops 95% to 75%, and what hit rate do you alarm on?
- You said: 2k/s; 95% tips at 200k req/s; tips at 75%. Follow-up: new products added; alarm on traffic > 140k (70% of 200k) or hit rate < 90%.
- Strong answer: "Misses are 5% of 40k, so 2k a second on Postgres. It caps around 10k, so a 75% hit rate tips it; I'd alarm at 90% and on Postgres QPS directly. What actually drops a hit rate that far is a cold cache after a Redis failover, a bulk invalidation, memory pressure evicting the hot set, or a key-format change on deploy, so I'd keep a warm replica and pre-warm before cutting traffic."
- Staff adds: ramp traffic gradually onto a cold cache; pre-warm from LFU stats or access logs.

**R6 (scale it up) 🟦 Mid**: Product page goes global at 1M reads/s, mostly anonymous. What breaks first and which caching layer do you add?
- Follow-up: Shoppers in Tokyo, London, Ohio see the same page. What serves them without reaching your servers, and what's the catch on a price change?
- You said: 10 Redis replicas at 100%, 15 for ~66%; cost = writes to every replica. Follow-up: CDN for static content; price changes propagate to origin and replicas (answer cut off).
- Strong answer: "Anonymous shoppers see the same page, so the first layer is a CDN caching the rendered page or product JSON at the edge. At a 95% edge hit rate, origin sees 50k instead of 1M, and Tokyo gets it in 20 ms instead of 150. The catch is the edge holds the old price for its TTL, so I'd keep the TTL short, say 60 s, purge by surrogate key on a price change, and always re-read the price from the source of truth at checkout."
- Staff adds: cache the page shell at the edge and fetch price separately; stale-while-revalidate headers; Redis replication is async and Redis does it, so the cost is replica lag, not app writes; shard for memory, replicate for read throughput.

### Gap to senior
- Bare "Redis goes down" or "use LRU": name the actual mechanism before the fix (noeviction rejects writes; no TTL = missed delete is permanent)
- Lock for coalescing needs an expiry (SET NX PX); serve stale via soft expiry so nobody waits
- Order: DB first then delete; delete beats update because of racing writers, not TTL freshness; say "for the full TTL"
- Global anonymous reads → CDN first (edge TTL + purge on price change, checkout reads truth), not more Redis
- Hit rate craters from cold cache, bulk invalidation, eviction of the hot set, key-format change; not slow catalog growth
- Hot key copies: fixed suffixes, reader picks randomly; check slots don't collide, no hash tags

### Staff stretch
- CDC-driven deletes / delayed double delete; write-through with version check for must-be-fresh data
- Per-process singleflight; in-process cache in front of hot keys
- Alert on Postgres QPS, Redis used_memory vs maxmemory, and hit rate
- Warm replicas + pre-warm + traffic ramp for cold caches

### Interview-ready lines
- "noeviction means once memory fills, Redis rejects every new write, so misses go to Postgres forever; I'd use allkeys-lfu."
- "The coalescing lock has a 3-second expiry so a crashed holder can't block everyone, and the rest get the stale value meanwhile."
- "Database first, then delete: deleting means two racing writers can't leave an old price in the cache."
- "Anonymous global traffic goes to a CDN first; 95% at the edge turns 1M into 50k at origin, with a short TTL plus purge on price changes."
- "What actually craters a hit rate is a cold cache after failover or a mass invalidation, so I'd keep a warm replica and pre-warm before cutting traffic."
- "Eight copies with fixed suffixes, readers pick one at random; I'd check the copies land on different slots."

### Delivery
- Habit: fix doesn't touch what broke (2nd session in a row): R4 "set a TTL" to protect against "Redis goes down"; pretest Q4 "use LRU" for a TTL expiry. Also skipped what the user sees in R1 and R4.
- Rewrite (R3): "I'd write the database first, then delete the key. Database first because it's the source of truth; if I deleted first, a read in the gap would refill the old price and serve it for the full ten-minute TTL. And delete rather than update, because two writers updating the cache can land out of order and leave the old price stuck. The next read just refills from Postgres. The TTL bounds the one tiny race that's left."
- Did well: numbers drove decisions without prompting (R2 62.5k under 70%; R5 alarm at 140k = 70% of 200k).
- Frame reminders: on (re-answers: 1, skipped by user)
