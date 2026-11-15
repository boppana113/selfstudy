# Numbers to Know

## Single-box capacity
Q: 5k writes/s and 2 TB total. Shard Postgres on day one?
A: No. One well-tuned Postgres box handles ~10k+ simple writes/s and several TB, so this fits with headroom. Scale up, add read replicas, and pick a shard key now so splitting later is a plan.
Why: 5k/s is half of one box's write ceiling, and 2 TB is a fraction of what a box holds. Sharding now means every query that crosses users becomes a scatter-gather, transactions across shards stop working, and you run a resharding tool before you need one. Picking the shard key (user_id) today costs nothing and means the split is a migration, not a redesign.
Staff: Sharding costs cross-shard queries, transactions, and resharding. Set alerts at ~70% of write and disk limits so the split starts before it's urgent.

Q: What does sharding solve that replicas don't?
A: Write throughput and storage limits. Reads scale with replicas or a cache; writes and data size need sharding.
Why: Picture adding 5 replicas to a primary at 12k writes/s. Every replica has to apply all 12k writes too, so the primary is still over its limit and the replicas lag. Picture 8 TB on a box that holds 5: each replica holds 8 TB too. Sharding splits the 12k writes into 3 × 4k and the 8 TB into 3 × 2.7 TB, which is what each box can take.

Q: 50k reads/s on a small hot set. Redis or Postgres replicas, and how many?
A: Redis. One node does 100k+ ops/s, so one primary plus a failover replica covers it. Replicas would take 5–6 Postgres boxes at ~10k reads/s each and add lag.
Why: 50k / 10k per Postgres replica = 5 boxes, plus the primary, each a full copy of the database to serve a few hot keys. 50k on one Redis node is 50% utilization. "Small hot set" is the tell: it fits in memory, so the cache hits almost always. And a Postgres replica is seconds behind; Redis is what you just wrote.
Staff: Protect against a cold cache with request coalescing and a DB sized to survive a few minutes without the cache.

Q: How big can one cloud server get (memory, cores)?
A: A standard large instance is ~128 vCPUs and 512 GiB RAM. Memory-optimized goes to 4 TB, and the biggest metal boxes hit 24 TB of RAM.
Why: Picture a "big" dataset: 100M users × 1 KB = 100 GB. That fits in a mid-size box's RAM with room to spare, so the whole working set can be in memory before you need to think about distributing it. The reflex to shard at 100 GB comes from a time when boxes had 16 GB.

Q: How much storage can one server hold?
A: Up to ~60 TB of local SSD on storage-optimized instances, and ~336 TB of HDD on dense-storage ones. Object storage (S3) is effectively unlimited.
Why: Picture 1 TB/day of chat messages. That's 365 TB/year, which is past one box's SSD, and backups and restores of a 60 TB database are already painful. So that number says "shard" or "tier old data to S3." 10 GB/day is 3.6 TB/year, and one box holds that for years.

Q: The old rule "shard at 100 GB": still true?
A: No, it's outdated. Modern boxes hold TBs on disk and in memory, so shard on measured write throughput or storage limits, not a fixed size.
Why: Picture a 500 GB Postgres on a box with 1 TB of RAM: the whole thing is in memory, queries are fast, and nothing is strained. Sharding it would add cross-shard joins and a resharding tool for no benefit. The real triggers are a primary near 10k writes/s or a disk approaching several TB.

Q: One Postgres/MySQL instance: rough limits for writes, reads, and storage?
A: ~10–20k simple writes/s, more reads when the working set is in memory, and comfortably several TB. Shard when writes or storage pass that, not before.
Why: Writes are bounded by WAL fsync and lock contention on one primary. Reads are bounded by CPU and whether the index is in memory; an in-memory indexed read is ~1 ms and a box can do tens of thousands. Storage is bounded by disk and by how long a backup or replica rebuild takes. When an interviewer gives you 3k writes/s, that's "one box, 30% full."

Q: One Redis node: throughput, latency, and memory?
A: ~100k+ ops/s (more with pipelining), sub-millisecond latency, memory up to hundreds of GB. The usual limit is memory, then single-threaded CPU on hot keys.
Why: Redis is single-threaded for commands, so one core processes everything, but each GET is a hash lookup in memory, so 100k/s is easy. Picture a 5 GB hot set at 80k reads/s: memory is fine, CPU is at 80%, so shard to two nodes. Picture 200 GB at 20k/s: CPU is fine, memory is the limit, so shard for capacity.

Q: One app server: plain HTTP requests vs WebSocket connections?
A: ~1–10k requests/s for typical handlers. Mostly-idle WebSocket connections: ~100k+ per box, limited by memory and file descriptors, not CPU.
Why: A request does work: parse, auth, a DB call, serialize. 1–10k/s depending on how much. An idle connection does nothing: it's a socket and some buffers, tens of KB. So 10M users means ~100 connection boxes and, separately, enough API boxes for their request rate.

Q: One Kafka broker: throughput and end-to-end latency?
A: Hundreds of MB/s, up to ~1M small messages/s. End-to-end latency single-digit ms. Retention of days to weeks and TBs per broker is normal.
Why: Kafka appends to a log sequentially and serves reads from the page cache, so it's disk-bandwidth bound, not seek bound. 250k pings/s × 200 bytes = 50 MB/s, a fraction of one broker. That's why "do we need more Kafka" is usually a question about the consumers, not the broker.

Q: Network bandwidth inside a data center, and what does it mean in bytes?
A: ~25 Gbps is common for standard instances, 50–100+ Gbps on high-performance ones. Divide by 8: 25 Gbps ≈ 3 GB/s, 10 Gbps ≈ 1.25 GB/s.
Why: Picture serving 2 MB photos at 1k/s: 2 GB/s, which is 16 Gbps, close to a standard box's 25. That number says "CDN" or "more boxes." Picture 500 B messages at 50k/s: 25 MB/s, nothing. Bandwidth matters for blobs and video, rarely for API traffic.

Q: What are the two triggers for sharding a database, with numbers?
A: Write throughput past ~10k writes/s on one primary, or data past several TB per box. Check both every time; reads alone never justify sharding.
Why: Picture the chat example: 1 TB/day. Writes are 50M × 40 / 100k s = 20k/s, past one box. Storage is 365 TB/year, far past one box. Both say shard. Picture the orders DB: 3k writes/s and 1.5 TB. Neither says shard. Reads at 50k/s with neither: cache or replicas, not shards.

Q: Orders DB at 3k writes/s and 1.5 TB, growing 50%/year. When must you shard, and what do you do meanwhile?
A: Writes hit ~10k in ~3 years; storage only reaches ~5 TB. Alert at 70% of each, archive old orders, scale up, and pick the shard key now.
Why: 3k → 4.5k → 6.75k → 10.1k: year 3 is the wall. Storage: 1.5 → 2.25 → 3.4 → 5 TB, still fine on one box. So the write ceiling is the trigger, in about 3 years. Alerting at 7k writes/s gives a year of warning. Archiving orders older than 2 years to cold storage buys storage time. Picking user_id as the shard key today means the year-3 migration is a planned split.
Staff: Native table partitioning by month first; Citus/Vitess so resharding isn't hand-built.

Q: 80k reads/s on a 5 GB hot set. How many Redis nodes?
A: Two shards at ~40k each, each with a failover replica: four nodes. One node at 80k is 80%, too hot.
Why: One node does ~100k/s. 80k is 80% utilization, which means a small spike or a failover takes it over. Two shards put each at 40%. Each shard needs a replica, or a node failure sends 40k reads/s to a Postgres sized for 10k. Postgres replicas instead: 8+ boxes at 10k each, each with a full copy of the DB.

Q: Redis dies under 80k reads/s. What happens?
A: 80k reads land on a Postgres sized for ~10k, so it saturates: queries queue, time out, and users see errors. Prevent it with a failover replica per Redis primary and request coalescing on misses.
Why: 10:00:00 Redis primary dies. 10:00:01 every cache miss goes to Postgres: 80k/s on a box that does 10k. Connections pile up, queries wait, the API times out, the whole site is down, not just slow. With a replica, failover takes ~10 s. With coalescing, 1,000 requests for the same key become one DB query while the cache refills.

Q: At what read rate do you add a cache, and what do you do past ~100k reads/s?
A: Past ~10k reads/s (one Postgres box), or for a small hot set, add a cache. Past ~100k, shard Redis, not add DB replicas.
Why: At 500 reads/s Postgres doesn't notice; a cache adds a system to run for nothing, unless latency is the point. At 10k the primary is busy and a cache takes 90% off. At 100k one Redis node is full, and DB replicas at 10k each would be 10 boxes, so Redis Cluster with 2–3 shards is the move.

## Latency ladder
Q: Rough latencies: memory, SSD, in-DC round trip, cross-region round trip?
A: Memory ~100 ns, SSD ~100 µs, in-DC round trip ~0.5 ms, cross-region 50–150 ms.
Why: Each step is ~1,000× the last, which is the thing to remember. A cache hit in memory is invisible. An SSD read is a thousand times slower but still under a millisecond. A call to another service in the same DC is another 5×. A call across the ocean is 100–200× that again. So one cross-region call costs more than a thousand SSD reads.

Q: EU users, servers in US East, 4 sequential API calls per page. Cost and fix?
A: ~80–100 ms per round trip, so 300–400 ms before anything renders. Collapse the calls into one (backend-for-frontend), then add an EU region if it's still too slow.
Why: Walk the page load. Call 1: 90 ms. Waits for it, call 2: 90 ms. Calls 3 and 4: 180 ms more. 360 ms of pure network before the first byte of content. A CDN caches images, not these API responses. A BFF endpoint does all four in the US DC (4 × 0.5 ms) and returns once: 90 ms total. An EU region makes it 4 × 5 ms, but costs a second deployment.

Q: HDD random seek vs SSD random read?
A: HDD ~10 ms, SSD ~100 µs (NVMe ~20 µs). ~100× apart, which is why random-access workloads live on SSD.
Why: An HDD physically moves a head: 10 ms. A database index lookup that touches 5 pages is 50 ms on HDD and 0.5 ms on SSD. At 1k lookups/s, an HDD can do 100. That's why "put the database on SSD" is a 100× win for random reads, and HDD is only for sequential streaming or cold storage.

Q: Round trip within one AZ vs between AZs in the same region?
A: Within an AZ, under 1 ms. Across AZs, ~1–2 ms. Cheap enough for synchronous replication across AZs; cross-region (50–150 ms) usually isn't.
Why: Picture a write that waits for a replica ack. Across AZs: +1–2 ms per write, so 10k writes/s is still fine, and you survive a data center fire. Cross-region: +80 ms per write, so every write is 80 ms slower and throughput per connection drops 50×. That's why cross-region replication is async and you state the RPO.

Q: Time to read 1 MB sequentially from memory, SSD, and HDD?
A: Memory ~10–50 µs, SSD ~0.2–1 ms, HDD ~5–20 ms.
Why: Sequential is bandwidth, not seeks: memory at ~20+ GB/s, SSD at 1–5 GB/s, HDD at ~100 MB/s. A 2 MB photo off SSD is ~1 ms; a 100 MB video minute is ~50 ms. That's why blob serving is network-bound, not disk-bound, once it's on SSD.

Q: Indexed lookup latency in Postgres vs a Redis GET, measured from the app?
A: Postgres ~1–5 ms (index in memory plus the network hop). Redis under 1 ms. A cache saves milliseconds per call and offloads the DB.
Why: Both include the ~0.5 ms in-DC round trip. Postgres then parses the query, walks a B-tree, checks visibility, returns: 1–5 ms. Redis does a hash lookup: ~0.1 ms. The latency win per call is small; the real win is that 90% of reads never touch the database, which is what keeps it under 10k/s.

Q: A service moves from your region to another (US East → EU West). 6 sequential calls per page: before vs after?
A: In-DC 6 × 0.5 ms ≈ 3 ms; cross-region 6 × 80–100 ms ≈ 500 ms, ~200× worse. Batch or parallelize the calls, cache locally, lazy-load, then co-locate.
Why: Each call waits for the previous one. Before: 3 ms, invisible. After: half a second of blank page on every load, which users notice and which hurts conversion. Batching: one call, 90 ms. Parallel: all 6 at once, 90 ms. Caching the ones that rarely change: fewer calls. Moving the service back: 3 ms again.

Q: Does a CDN help a URL shortener's redirect API?
A: Yes: a short code's target never changes, so redirects cache at the edge. 301 lets browsers and the CDN cache it (cheap, but you lose click counts); 302 with a short TTL keeps analytics.
Why: Picture a viral link: 100k hits/s, all for one code, all needing the same answer. With a 301, the first hit per edge location reaches your server; the rest are served from the edge, and browsers never ask again. Your API sees nearly nothing. The cost: you can't count clicks you never see. A 302 with a 60 s TTL caches at the edge but not in browsers, and edge logs give you counts.

## QPS from DAU
Q: 100M DAU × 5 posts/day. Average and peak write QPS?
A: 500M/day ÷ ~100k seconds ≈ 5k/s average. Plan 2–3× at peak, so 10–15k/s, which is near one primary's write limit.
Why: 100M × 5 = 500M posts/day. A day is ~86,400 s, round to 100k: 5k/s. Traffic isn't flat: evenings in the biggest time zone run 2–3× the average, so peak is 10–15k/s. That lands right at one Postgres box's ceiling, so the number decided something: plan the shard key now.

Q: Seconds in a day, a month, and a year (round numbers)?
A: Day 86,400 ≈ 100k. Month ≈ 2.5M. Year ≈ 30M (31.5M exact).
Why: 60 × 60 × 24 = 86,400; rounding to 100k makes division easy and errs 15% high, which is fine. Month = 30 × 86,400 ≈ 2.6M. Year = 365 × 86,400 ≈ 31.5M. "1M/day ≈ 12/s" and "100M/month ≈ 40/s" come straight from these.

Q: Quick conversion: 1M requests/day is how many per second?
A: ~12/s (1M ÷ 86,400). So 1B/day ≈ 12k/s, and 100M/day ≈ 1.2k/s.
Why: Memorize 1M/day = 12/s and scale by powers of ten. 10M/day = 120/s, 100M/day = 1.2k/s, 1B/day = 12k/s. Anything under 100M/day is under 1.2k/s and no single box cares. 1B/day is where one Postgres primary starts to be the question.

Q: When sizing shards for 40k writes/s peak at ~10k per box, how many shards?
A: About 6, not 4: size at ~70% utilization. And say why peak is 2–3× average (the evening spike).
Why: 40k / 10k = 4 boxes at 100%. A box at 100% has no room for a hot shard, a failover, or growth, and p99 climbs well before 100%. 40k / 7k per box ≈ 6. The 40k came from ~15k average × 2.5 for the evening spike, so say that too, so the interviewer knows you didn't pick 40k at random.

## Storage estimation
Q: Does the peak multiplier apply to yearly storage?
A: No. Peak applies to rates (QPS, bandwidth); stored totals use the average. 1 TB/day average is 365 TB/year.
Why: Peak is "how fast at the worst moment." Storage is "how much, in total, after a year," and the evening spike and the 3 a.m. lull average out over the year. Multiplying 365 TB by 2.5 would size disks for 900 TB that will never exist.

Q: Chat: 50M DAU × 40 msgs × 500 B. What does the storage number decide?
A: 1 TB/day = 365 TB/year, ~100× what one Postgres box comfortably holds, so storage, not writes, forces sharding: a wide-column store partitioned by conversation_id, old messages tiered to S3.
Why: 50M × 40 × 500 B = 1 TB/day. Writes are 2B/day ≈ 20k/s, past one box too, but 365 TB/year is the bigger problem: no single box, and backups of multi-TB databases already take hours. Cassandra partitioned by conversation_id spreads it over many nodes and makes "load this conversation" one partition read. Messages older than a year go to S3 at a fraction of the cost.
Staff: RF=3 makes it ~1.1 PB raw per year.

Q: 500M posts/day, 1 KB text each, 1 in 10 has a 2 MB photo. Storage per year, and where does it live?
A: Photos: 50M × 2 MB = 100 TB/day ≈ 36 PB/year, vs under 200 TB/year of text. Photos go in blob storage behind a CDN; the DB holds text and a pointer.
Why: Text: 500M × 1 KB = 500 GB/day ≈ 180 TB/year. Photos: 50M × 2 MB = 100 TB/day ≈ 36 PB/year, 200× the text. Nothing database-shaped holds 36 PB; S3 does, at ~$20/TB/month. The database stores `photo_url`, and the CDN serves the bytes so your servers never touch them.

Q: Typical object sizes to assume: a text post, a metadata row, a photo, a minute of video?
A: Text post or row ~1 KB. Compressed photo ~200 KB–2 MB. Video ~5–50 MB per minute (1080p ≈ 50–100 MB/min).
Why: A row is a few ints, a timestamp, and some text: hundreds of bytes, call it 1 KB to be safe. A phone photo is 2–4 MB raw, 200 KB–2 MB after compression. Video is 1,000× a photo per minute. So one video upload equals a million posts in storage, which is why media always goes to blob storage.

Q: Powers of ten for storage: KB → PB?
A: KB 10³, MB 10⁶, GB 10⁹, TB 10¹², PB 10¹⁵. 1M × 1 KB = 1 GB; 1B × 1 KB = 1 TB; 1B × 1 MB = 1 PB.
Why: The two anchors are "a billion 1 KB rows is a terabyte" and "a billion 1 MB photos is a petabyte." Everything else is scaling those. 100M users × 1 KB = 100 GB (one box's RAM). 500M × 2 MB = 1 PB (blob storage).

## When scale doesn't require sharding
Q: When is a back-of-envelope estimate worth doing in an interview?
A: Only when the number can flip a decision. Say the number, then say what it decided.
Why: 50k reads/s is past one Postgres box, so "add a cache" follows from it. 500 reads/s fits anything, so computing it buys nothing. The test before doing the math: "if this comes out 10× higher or lower, does my design change?" If no, skip it and say so.
