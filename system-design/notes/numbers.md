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
- Know single-box limits cold: Postgres ~10k+ TPS and several TB; Redis ~100k+ ops/s; WebSocket box ~100k conns
- Sharding is for write throughput and storage; reads scale with replicas or caches
- Memory ~100 ns; in-DC round trip ~0.5 ms
### Gap to senior
- Answer "does it fit on one box?" with a yes or no plus the capacity number
- Peak = 2–3× average, with a reason
- Finish the conversion the question asked for (per day → per year), then say what it decides
- Fix the right layer: CDN for static, collapse calls or add a region for dynamic
- Estimation examples need the threshold number that flips the decision
### Hold-in-mind questions
- At what write rate and data size does one Postgres box stop being enough, and what do you try before sharding?
- 50k reads/s on a hot set: how many Redis nodes vs Postgres replicas, and what protects the DB when the cache dies?
- Name two estimates that commonly flip a design decision, with the threshold for each.
### Delivery
- Habit: numbers and choices without their reason (recurring: also in delivery-framework, ml-delivery-framework, and the 11-05 speak log). Q3: "I'd plan for 50% more, which makes 9,000" with no reason; Q6 picked replicas without saying what one Redis node handles.
- Rewrite (Q2): "No, I wouldn't shard yet. One Postgres box handles roughly ten thousand simple writes a second and several terabytes, so five thousand writes and two terabytes fits with about 2x headroom. Sharding has a real cost: cross-shard queries, no easy transactions, and painful resharding. So I'd scale the box up, add read replicas for read load, and pick a shard key now, so when we approach the limits, splitting is a plan and not a fire drill."
