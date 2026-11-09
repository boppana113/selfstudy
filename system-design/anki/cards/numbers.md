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

## Latency ladder
Q: Rough latencies: memory, SSD, in-DC round trip, cross-region round trip?
A: Memory ~100 ns, SSD ~100 µs, in-DC round trip ~0.5 ms, cross-region 50–150 ms (US East to Europe ~80–100 ms).

Q: EU users, servers in US East, 4 sequential API calls per page. Cost and fix?
A: ~80–100 ms per round trip, so 300–400 ms before anything renders. A CDN only helps static assets. Collapse the calls into one (backend-for-frontend), then add an EU region if it's still too slow.

## QPS from DAU
Q: 100M DAU × 5 posts/day. Average and peak write QPS?
A: 500M/day ÷ ~100k seconds ≈ 5k/s average. Plan for 2–3× at peak (evening spike), so 10–15k/s, which is near one primary's write limit.

## Storage estimation
Q: 500M posts/day, 1 KB text each, 1 in 10 has a 2 MB photo. Storage per year, and where does it live?
A: Photos: 50M × 2 MB = 100 TB/day ≈ 36 PB/year, vs under 200 TB/year of text. Photos go in blob storage behind a CDN; the DB holds text and a photo pointer.

## When scale doesn't require sharding
Q: When is a back-of-envelope estimate worth doing in an interview?
A: Only when the number can flip a decision. Example: 50k reads/s is past one Postgres box, so add a cache; 500/s isn't. Say the number, then say what it decided.
