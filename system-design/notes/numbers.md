# Numbers to Know / Estimation

## Pretest: 2026-11-08 (score 44%; Below mid 2 · Mid 5 · Senior 1 · Staff 0)
### Questions
**Q1 🟦 Mid**: Rough latency for a memory read vs an SSD read, and a network round trip inside one data center vs across regions?
- You said: SSD ~microseconds, in-DC "probably milliseconds", cross-region 50 ms. Skipped memory.
- Strong answer: "Memory is about 100 nanoseconds, an SSD read about 100 microseconds, so a thousand times slower. A round trip inside a data center is about half a millisecond, and cross-region is 50 to 150 milliseconds depending on distance. So one cross-region hop costs as much as a hundred in-DC calls, which is why I keep chatty calls inside one region."

**Q2 ⬜ Below mid**: A team wants to shard Postgres on day one: 5k writes/s peak, 2 TB total. What do you tell them? (Nudge: assume even spread, no hot rows.)
- You said: Asked what the heaviest writes are; said sharding is for large-scale reads; never said whether one box handles it.
- Strong answer: "Don't shard yet. A single well-tuned Postgres box handles roughly 10k+ simple writes a second and several terabytes on one disk, so 5k writes and 2 TB fits with headroom. Sharding costs cross-shard queries, transactions, and resharding pain, so I'd vertically scale, add read replicas for reads, and pick a shard key now so we can split later when we're near the limits."
- Note: sharding solves write throughput and storage limits; reads are scaled with replicas or a cache.

**Q3 🟦 Mid**: 100M DAU, 5 posts a day each. Average write QPS, and what do you plan for at peak?
- You said: 500M/day ÷ 86,400 ≈ 5,787 → ~6k/s; plan for 50% more → 9k/s.
- Strong answer: "500 million posts a day. A day is about 100k seconds, so that's about 5,000 writes a second on average. Traffic peaks in the evening at 2 to 3 times average, so I'd plan for 10 to 15k a second. That's around the limit of one database primary, so it tells me to think about write scaling."

**Q4 🟦 Mid**: Each post is ~1 KB of text; 1 in 10 has a 2 MB photo. Storage per year, and does it change where you store things?
- You said: 450 GB/day of text, 100 TB/day of photos, photos ~99.5% of bytes, start with S3 as cheapest.
- Strong answer: "Photos dominate. 50 million photos a day at 2 MB is 100 TB a day, about 36 petabytes a year, versus under 200 TB a year of text. So photos go in blob storage like S3 behind a CDN, and the database only holds the text and a pointer to the photo. The database stays small enough to fit on a few boxes, and the real cost line is blob storage and egress."

**Q5 🟩 Senior**: 10M concurrent WebSocket users. How many servers to hold the connections, and what limits a single box?
- You said: ~100k per box → 100 servers, provision 150 for failures; memory is the limit.
- Strong answer: "About 100k connections per box, so 100 servers, and I'd run about 150 for failover and uneven stickiness. Each box is limited by memory per connection and file descriptors, not CPU. When a box dies, 100k clients reconnect at once, so they need jittered backoff or they knock over the next box."

**Q6 ⬜ Below mid**: Profile reads at 50k/s on a small hot set. Read replicas or Redis, and how many Redis nodes?
- You said: Replicas, so Postgres is safe if Redis goes down and causes a stampede. No node count.
- Follow-up asked: "Doesn't a hot replica warrant more replicas?" Answer: replicas spread reads, but at ~10k simple reads/s each you'd need 5–6, and they lag.
- Strong answer: "Redis. A small hot set is exactly what caches are for, and one Redis node does 100k+ ops a second, so one primary plus a replica for failover covers 50k with room to spare. Replicas would take 5 or 6 Postgres boxes for the same load and add replication lag. To guard against a stampede if Redis dies, I'd use request coalescing and keep the database sized to survive a cold cache for a few minutes."

**Q7 🟦 Mid**: Users in Europe, servers only in US East, 4 sequential backend calls per page. Latency from distance, and what do you do?
- You said: 50 ms per round trip × 4 = 200 ms; use a CDN to cache static content near Europe.
- Strong answer: "US East to Europe is about 80 to 100 ms per round trip, so four sequential calls is 300 to 400 ms of pure distance before anything renders. A CDN only helps static assets; these are API calls. First I'd collapse the four calls into one with a backend-for-frontend, which cuts it to one round trip. If that's still too slow, I'd add an EU region, which raises data residency and replication questions."

**Q8 🟦 Mid**: When is back-of-envelope estimation worth doing vs skipping? Example where it changed your design?
- You said: Only when the number affects the design; concurrent reads decide whether to add a cache.
- Strong answer: "Only when the number could flip a decision. I skip it for things that obviously fit on one box. For example, if reads are 50k a second, that's past what one Postgres box serves, so I add a cache. If it's 500 a second, I don't. Same for storage: 36 petabytes of photos means blob storage, not the database. I say the number, then say what it decided."

### Gap to mid
- ✅ (2026-11-09, Postgres writes/Redis) Know single-box limits cold: Postgres ~10k+ TPS and several TB; Redis ~100k+ ops/s; WebSocket box ~100k conns
- 🟡 (2026-11-09: reads ✅, storage half still missed in R1) Sharding is for write throughput and storage; reads scale with replicas or caches
- Memory ~100 ns; in-DC round trip ~0.5 ms
### Gap to senior
- ✅ (2026-11-09 R4) Answer "does it fit on one box?" with a yes or no plus the capacity number
- Peak = 2–3× average, with a reason
- Finish the conversion the question asked for (per day → per year), then say what it decides
- ✅ (2026-11-09 R5) Fix the right layer: CDN for static, collapse calls or add a region for dynamic
- Estimation examples need the threshold number that flips the decision
### Hold-in-mind questions
- At what write rate and data size does one Postgres box stop being enough, and what do you try before sharding?
- 50k reads/s on a hot set: how many Redis nodes vs Postgres replicas, and what protects the DB when the cache dies?
- Name two estimates that commonly flip a design decision, with the threshold for each.
### Delivery
- Habit: numbers and choices without their reason (recurring: also in delivery-framework, ml-delivery-framework, and the 11-05 speak log). Q3: "I'd plan for 50% more, which makes 9,000" with no reason; Q6 picked replicas without saying what one Redis node handles.
- Rewrite (Q2): "No, I wouldn't shard yet. One Postgres box handles roughly ten thousand simple writes a second and several terabytes, so five thousand writes and two terabytes fits with about 2x headroom. Sharding has a real cost: cross-shard queries, no easy transactions, and painful resharding. So I'd scale the box up, add read replicas for read load, and pick a shard key now, so when we approach the limits, splitting is a plan and not a fire drill."

## Drill: 2026-11-09 (score 67%; Below mid 0 · Mid 4 · Senior 2 · Staff 0)
### Questions
**R1 (Scenario) 🟦 Mid**: Orders DB: 3,000 writes/s peak, 1.5 TB, growing 50%/year. An engineer wants to shard Postgres now. What do you tell them, and at roughly what point does sharding become necessary?
- Follow-up: You only checked writes. Does storage push you to shard sooner, and what do you do over those three years so it isn't a fire drill?
- You said: Not enough write traffic; sharding matters past ~10k writes/s; at 50%/year that's ~3 years out. Follow-up: didn't know what data volume has to do with sharding; set an alarm on traffic and plan the shard; sharding is expensive (migration).
- Re-answer: skipped by user.
- Strong answer: "Not yet. One Postgres box takes about 10k writes a second and several terabytes. We're at 3k and 1.5 TB; at 50% a year we hit the write limit in about 3 years, while storage only reaches about 5 TB, so writes are the binding limit. I'd alert at 70% of each, archive old orders to cold storage, and pick the shard key now so the split is a plan. Read replicas don't help, since they only offload reads."
- Staff adds: native monthly partitioning first; Citus/Vitess so resharding isn't hand-built.

**R2 (Tradeoff duel) 🟦 Mid**: Product page: 80k reads/s at peak, ~5 GB hot set. Postgres read replicas or Redis? How many boxes?
- Follow-up: 80k on a ~100k box is 80%. One node enough, how many would you run? If Redis dies, what hits Postgres and what does the user see?
- You said: Redis, because there's a hot set and it does ~100k reads/s sub-ms. Follow-up: 70% is safer, so two nodes; if Redis dies, users see millisecond-slower responses from Postgres.
- Strong answer: "Redis. A 5 GB hot set fits in memory and one node does about 100k ops a second, but 80k is too close, so two shards at ~40k each, each with a failover replica: four nodes. Replicas would take 8 or more Postgres boxes at ~10k reads each, with lag. If the cache drops, 80k reads land on a DB sized for 10k: it saturates, queries time out, and users see errors, so failover replicas plus request coalescing are part of the design."
- Staff adds: in-process LRU for hottest SKUs; TTL + invalidation on update; hot-key watch.

**R3 (Estimation) 🟦 Mid**: Chat app: 50M DAU × 40 messages/day × 500 bytes. Peak write rate, storage per year, and what each tells you about the design?
- Follow-up: You applied 2× peak to storage (730 TB). Does peak belong in yearly storage, and what does the right figure mean for Postgres?
- You said: 2B/day, 1 TB/day; doubled for peak; 730 TB/year; 20 MB/s; 40k writes/s → 4 boxes at 10k. Follow-up: storage uses average → 365 TB/year; peak only for rates. Never said what 365 TB means.
- Strong answer: "2 billion messages a day is about 20k writes a second, 40k at an evening peak of 2×, which is past one primary, so about 6 shards at 70%. Storage decides it though: 1 TB a day is 365 TB a year, about 100× one box. So a wide-column store like Cassandra partitioned by conversation ID, with old messages tiered to S3."
- Staff adds: RF=3 → ~1.1 PB raw/year; large group chats as hot partitions.

**R4 (Spot the flaw) 🟩 Senior**: URL shortener capacity plan, what's wrong?
```
Writes: 100M new links/month → 100M / 30 days / 86,400 ≈ 40 writes/s
Reads:  100:1 read/write → 4,000 reads/s
Storage: 500 bytes/link × 100M/month × 12 × 5 years = 3 TB
Plan:   Shard Postgres across 4 nodes from day one to handle the read load.
        Put a CDN in front of the redirect API to cut cross-region latency.
```
- Follow-up: What instead for 4,000 reads/s; does 3 TB change it; anything wrong with the CDN line?
- You said: Sharding is for writes, and 40/s is far under 10k. Follow-up: 4k reads is under ~10k/box; 3 TB on a ~5 TB box is under 60%; CDN line wrong because CDNs are for static data, and a 301 lets the browser cache the redirect.
- Strong answer: "Don't shard. 40 writes a second is nothing, 4,000 reads is about 40% of one box, and 3 TB over five years fits. One Postgres primary with a failover replica. Short links never change, so redirects are effectively static: I'd cache them at the CDN, with 302s and a short TTL if we need click counts."
- Note: the CDN line was a bad planted flaw. Redirects are cacheable at the edge; the real choice is 301 (cheap, lose analytics) vs 302 (keep counts).
- Staff adds: say what changes the plan (10× link creation; click analytics writes at read volume).

**R5 (Failure mode) 🟩 Senior**: App servers in US East; recommendations service moved to EU West; 6 sequential calls per page. What happens and what does the user see?
- Follow-up: They can't move back for a month. What do you change, and how does 480–600 ms compare to before?
- You said: 80–100 ms per round trip × 6 = 480–600 ms, user sees a delayed response; fix: co-locate. Follow-up: bundle the 6 calls into one, so 80–100 ms.
- Strong answer: "Those 6 calls went from about 3 ms in-region to about 500 ms cross-region, 200× worse, so every page loads half a second slower, and any 200 ms upstream timeout starts dropping recommendations. Short term, batch them into one call or parallelize, cache recommendations in US East since they tolerate staleness, and lazy-load the widget. Then move the service back next to its callers."
- Staff adds: egress cost; EU outage becomes a US outage; latency SLO alert + migration checklist covering callers.

**R6 (Explain it) 🟦 Mid**: In 45 s: two estimates that commonly flip a design decision, with the threshold for each.
- Follow-up: 10k or 100k writes per box? At 500 reads/s, would you add Redis, and what reads/s number makes you add a cache?
- You said: Cache vs replica: under 100k reads/s use Redis, above that use replicas with cache nodes; shard above 100k writes/s. Follow-up: meant 10k; would add Redis at 500 reads/s for sub-ms latency.
- Strong answer: "Reads: one Postgres box serves about 10k a second, so past that, or for a hot set, I add a cache; past 100k I shard the cache. Writes and storage: one primary takes about 10k writes a second and several terabytes, so past either I shard. Below them, one box. At 500 reads a second I skip the cache unless the latency budget is really tight."
- Staff adds: blob bytes → object storage; ~100k connections per box sizes WebSocket fleets.
### Gap to senior
- Finish with what the number decides (R1 storage, R3 365 TB ≈ 100× one box, R6)
- Storage is the second sharding trigger: several TB per box, checked alongside 10k writes/s
- Cache threshold: past ~10k reads/s or a hot set → cache; past ~100k → shard Redis (not replicas); replicas for moderate/uncacheable reads
- Cache death overloads the DB (not "a few ms slower"): failover replica per Redis primary + request coalescing
- Size at ~70% (6 shards not 4), give the reason for 2× peak, never apply peak to stored totals
### Staff stretch
- Table partitioning / Citus before hand-built sharding
- Replication factor in raw storage (365 TB → ~1.1 PB)
- Cross-region dependency couples outages; hot keys / hot partitions
### Interview-ready lines
- "365 TB a year is about 100 times one box, so storage, not writes, is what forces the sharding."
- "Sharding is for write throughput or storage: past about 10k writes a second or several terabytes, not before."
- "Past about 10k reads a second I add a cache; past 100k I shard the cache, not add replicas."
- "If the cache drops, 80k reads flatten Postgres, so I run a failover replica for each primary and coalesce misses."
- "40k at an evening peak, at 70% per box, is 6 shards."
### Hold-in-mind questions
- 365 TB/year of messages: what does that number decide, said in one sentence?
- What are the two triggers for sharding, with the number for each?
- At what read rate do you add a cache, and what do you do past 100k reads/s?
- Redis dies under 80k reads/s. What happens to Postgres and the user, and what prevents it?
### Delivery
- Habit: stopping before the "so what": the number lands, the "…which means ___ for the design" clause doesn't (R1, R3, R6). Related to the recurring "numbers without reasons" habit (2× peak with no reason in R3).
- Rewrite (R3): "Fifty million users times 40 messages is 2 billion a day. Over about 100k seconds that's 20k writes a second on average, and chat peaks in the evening at about twice that, so 40k. That's already past one Postgres primary. But storage is what decides it. 2 billion times 500 bytes is a terabyte a day, 365 terabytes a year, about a hundred times what one box holds. So I'd use a wide-column store like Cassandra, partitioned by conversation ID, and tier old messages to S3."
- Did well: bottom line first in nearly every round; R4 and R5 tight, full frame.
- Frame reminders: on (re-answers: 1, skipped by user)
