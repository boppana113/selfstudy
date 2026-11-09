# Numbers to Know

## Single-box capacity
Q: 5k writes/s and 2 TB total. Shard Postgres on day one?
A: No. One well-tuned Postgres box handles roughly 10k+ simple writes a second and several TB, so it fits with headroom. Scale up, add read replicas, and pick a shard key now so splitting later is a plan.
Staff: Sharding costs cross-shard queries, transactions, and resharding. Set alerts at ~70% of write and disk limits so the split starts before it's urgent.

Q: What does sharding solve that replicas don't?
A: Write throughput and storage limits. Reads scale with replicas or a cache; writes and data size need sharding.

Q: 50k reads/s on a small hot set. Redis or Postgres replicas, and how many?
A: Redis. One node does 100k+ ops/s, so one primary plus a failover replica covers it. Replicas would take 5–6 Postgres boxes at ~10k reads/s each and add replication lag.
Staff: Protect against a cold cache with request coalescing and a DB sized to survive a few minutes without the cache.

Q: How big can one cloud server get (memory, cores)?
A: A standard large instance is ~128 vCPUs and 512 GiB RAM. Memory-optimized goes to 4 TB, and the biggest metal boxes hit 24 TB of RAM. Many datasets that sound "big" fit in one box's memory.

Q: How much storage can one server hold?
A: Up to ~60 TB of local SSD on storage-optimized instances, and ~336 TB of HDD on dense-storage ones. Object storage (S3) is effectively unlimited, at petabyte scale.

Q: The old rule "shard at 100 GB": still true?
A: No, it's outdated. Modern boxes hold TBs on disk and in memory, so shard on measured write throughput or storage limits, not a fixed size.

Q: One Postgres/MySQL instance: rough limits for writes, reads, and storage?
A: ~10–20k simple writes/s, more reads when the working set is in memory, and comfortably several TB (tens of TB with care). Shard when writes or storage pass that, not before.

Q: One Redis node: throughput, latency, and memory?
A: ~100k+ ops/s (more with pipelining), sub-millisecond latency, and memory up to hundreds of GB. The usual limit is memory, then single-threaded CPU on hot keys.

Q: One app server: plain HTTP requests vs WebSocket connections?
A: ~1–10k requests/s for typical handlers (depends on CPU work per request). Mostly-idle WebSocket connections: ~100k+ per box, so the limit is memory and file descriptors, not CPU.

Q: One Kafka broker: throughput and end-to-end latency?
A: Hundreds of MB/s, which is up to ~1M small messages/s. End-to-end latency is single-digit ms. Retention of days to weeks and TBs per broker is normal.

Q: Network bandwidth inside a data center, and what does it mean in bytes?
A: ~25 Gbps is common for standard instances, and 50–100+ Gbps on high-performance ones. Divide by 8: 25 Gbps ≈ 3 GB/s, 10 Gbps ≈ 1.25 GB/s.

## Latency ladder
Q: Rough latencies: memory, SSD, in-DC round trip, cross-region round trip?
A: Memory ~100 ns, SSD ~100 µs, in-DC round trip ~0.5 ms, cross-region 50–150 ms (US East to Europe ~80–100 ms).

Q: EU users, servers in US East, 4 sequential API calls per page. Cost and fix?
A: ~80–100 ms per round trip, so 300–400 ms before anything renders. A CDN only helps static assets. Collapse the calls into one (backend-for-frontend), then add an EU region if it's still too slow.

Q: HDD random seek vs SSD random read?
A: HDD ~10 ms, SSD ~100 µs (NVMe can be ~20 µs). About 100× apart, which is why random-access workloads live on SSD.

Q: Round trip within one AZ vs between AZs in the same region?
A: Within an AZ, under 1 ms. Across AZs, ~1–2 ms. Cheap enough for synchronous replication across AZs; cross-region (50–150 ms) usually isn't.

Q: Time to read 1 MB sequentially from memory, SSD, and HDD?
A: Memory ~10–50 µs, SSD ~0.2–1 ms, HDD ~5–20 ms.

Q: Indexed lookup latency in Postgres vs a Redis GET, measured from the app?
A: Postgres ~1–5 ms (index in memory, plus the network hop). Redis under 1 ms. A cache saves milliseconds per call and offloads the DB.

## QPS from DAU
Q: 100M DAU × 5 posts/day. Average and peak write QPS?
A: 500M/day ÷ ~100k seconds ≈ 5k/s average. Plan for 2–3× at peak (evening spike), so 10–15k/s, which is near one primary's write limit.

Q: Seconds in a day, a month, and a year (round numbers)?
A: Day 86,400 ≈ 100k. Month ≈ 2.5M. Year ≈ 30M (31.5M exact).

Q: Quick conversion: 1M requests/day is how many per second?
A: ~12/s (1M ÷ 86,400). So 1B/day ≈ 12k/s, and 100M/day ≈ 1.2k/s.

## Storage estimation
Q: 500M posts/day, 1 KB text each, 1 in 10 has a 2 MB photo. Storage per year, and where does it live?
A: Photos: 50M × 2 MB = 100 TB/day ≈ 36 PB/year, vs under 200 TB/year of text. Photos go in blob storage behind a CDN; the DB holds text and a photo pointer.

Q: Typical object sizes to assume: a text post, a metadata row, a photo, a minute of video?
A: Text post or row ~1 KB (ballpark 100 B–1 KB). Compressed photo ~200 KB–2 MB. Video ~5–50 MB per minute depending on resolution (1080p ≈ 50–100 MB/min).

Q: Powers of ten for storage: KB → PB?
A: KB 10³, MB 10⁶, GB 10⁹, TB 10¹², PB 10¹⁵. 1M × 1 KB = 1 GB; 1B × 1 KB = 1 TB; 1B × 1 MB = 1 PB.

## When scale doesn't require sharding
Q: When is a back-of-envelope estimate worth doing in an interview?
A: Only when the number can flip a decision. Example: 50k reads/s is past one Postgres box, so add a cache; 500/s isn't. Say the number, then say what it decided.
