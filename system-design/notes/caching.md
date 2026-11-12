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
- Threshold: cache past ~10k reads/s per Postgres box (said 100k)
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
