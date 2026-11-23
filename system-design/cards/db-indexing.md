# Database Indexing

## B-tree vs LSM-tree
Q: How does an LSM tree handle a write, and why is that fast?
A: Append to a log and insert into an in-memory sorted memtable. When it fills, flush it as an immutable sorted SSTable, and background compaction merges SSTables. Every write is sequential, so throughput is high; the cost is slower reads and compaction I/O.
Why: A metrics service takes 200k points/s. A B-tree would update a page somewhere on disk for each point, which is random I/O. The LSM tree buffers 64 MB in RAM, then writes it as one sorted file in a single sequential pass. Cassandra and RocksDB work this way.
Flip: B-tree for read-heavy OLTP (orders, users), since each read follows one path instead of checking several files.

Q: What do bloom filters fix in an LSM tree?
A: Read amplification. A key could live in the memtable or any SSTable, and a per-SSTable bloom filter answers "definitely not here" in memory, so the read skips that file.
Why: Read `sensor:42`. It isn't in the memtable, and there are 10 SSTables on disk. Without filters, that's up to 10 disk reads. With them, 9 filters say "no" from RAM and you read only the one file that might have it. A false positive costs one wasted read, and a filter never says "no" for a key that's present.

Q: Is an LSM tree a write buffer in front of Cassandra?
A: No. It is Cassandra's storage engine: the SSTables on disk are the database, with nothing behind them. Writes are cheap because they're a sequential log append plus a memtable insert, not a random in-place page write like a B-tree.
Why: Write `sensor:42 = 71.3`. It's appended to the commit log (sequential) and inserted into the memtable in RAM; done. Later, the 64 MB memtable flushes as one new SSTable in one pass. A B-tree would have found the leaf page for that key somewhere on disk and rewritten it, maybe splitting it.

## Hash, composite and covering indexes
Q: Index on (user_id, created_at). Does it help a query on created_at alone?
A: No. It's sorted by user_id first, so timestamps are scattered across every user (the leftmost-prefix rule). Add a separate created_at index if that query is hot.
Why: Phone book sorted by last name, then first name. "All Smiths named Ann" is fast. "Everyone named Ann" means reading the whole book. In the same way, "orders in the last hour" across all users can't seek, so it full-scans.

Q: Why put user_id before created_at for "user X's orders in the last 30 days, newest first"?
A: Equality column first, then range/sort column. The query seeks to user X and reads an already-sorted range with no sort step.
Why: User 7 has 2,000 orders. The index jumps to the user_id=7 block, where entries are already ordered by created_at, and reads the last 30 days backward: maybe 40 entries. Reversed as (created_at, user_id), it would scan 30 days of every user's orders and filter out everyone except user 7.

Q: SELECT order_id, total WHERE user_id = X is fast with an index on user_id. How do you make it faster without a cache?
A: A covering index, e.g. (user_id) INCLUDE (order_id, total). It enables an index-only scan with no table lookups; the cost is a bigger index and more write work.
Why: User X has 200 orders. With a plain user_id index, Postgres finds 200 row pointers and then does 200 random reads into the table to get total. With the covering index, total is already in the index entries, so there are 0 table reads. A second index on total wouldn't help, since the query still has to visit the table.

Q: A hash index is O(1). Why do databases default to B-trees?
A: A hash index only does exact equality. A B-tree keeps keys sorted, so it handles ranges, ORDER BY, prefix LIKE and composite leftmost prefixes, and at 3–4 page reads its log n barely costs more. Both use O(n) space.
Why: `created_at > now() - 1h` on a hash index means hashing every possible timestamp, which is impossible, so it full-scans. A B-tree on 100M rows with fanout ~500 is 3 levels deep, so a lookup is 3 page reads vs 1. That small gap buys you range queries.
Flip: Hash when every access is an exact key match, like session ID → session. Key-value stores (Redis, DynamoDB partition key) are hash-based.

Q: Index on user_id; user X has 500 orders scattered across the table. Roughly how many page reads for SELECT order_id, total?
A: About 500. The index walk is 3–4 pages plus a leaf or two, but each scattered row is its own random heap read. A covering index (INCLUDE order_id, total) makes it an index-only scan: under 10 reads.
Why: The index hands back 500 row pointers. Rows were inserted over two years, so each lives on a different page: 500 random reads, ~50 ms if uncached. Rows-per-page doesn't help when the rows aren't next to each other. Sharding spreads load, but each query still does 500 reads.
Staff: Clustering by key (InnoDB primary key (user_id, order_id)) puts one user's rows on adjacent pages, so even full-row fetches are a few pages.

Q: Does a covering index speed up a WHERE filter like "user X's orders over $100"?
A: No. Covering (INCLUDE) adds columns you SELECT, so the query skips the table lookup. To speed a filter, the column must be in the key: (user_id, price).
Why: With (user_id) INCLUDE (price), the DB seeks to user X and checks price on each of their 500 entries, with no table reads but still all 500 entries. With (user_id, price), it seeks to user X, price 100, and reads only the matching range.

## Geospatial
Q: Why doesn't a B-tree on (lat, lng) work for "restaurants within 2 km"?
A: A B-tree is one-dimensional. It narrows latitude, but within that band longitudes are scattered, so you scan a strip around the whole globe. Use a geospatial index (geohash, quadtree, R-tree).
Why: You're at lat 37.77. A 2 km box is lat 37.75–37.79, a strip that circles the Earth and contains every restaurant in Lisbon, Athens and Seoul at that latitude. The lng filter then throws away 99.9% of what you read.

Q: How does geohash let a normal index answer a "nearby" query, and what's the catch?
A: It encodes lat/lng into a string where nearby points share a prefix, so "nearby" becomes a prefix range query on an ordinary B-tree. The catch: two points across a cell boundary can have different prefixes, so you query your cell plus its 8 neighbors.
Why: Your geohash is `9q8yyk`. Restaurants in that ~1 km cell all start with `9q8yyk`, so it's one range scan. A place 50 m away across the edge is `9q8yys`, a different prefix, and you'd miss it without the neighbors. Redis GEOSEARCH and PostGIS handle this for you.
Staff: Quadtrees adapt cell size to density (Manhattan splits deep, Nevada stays coarse); geohash cells are fixed-size.

Q: Geohash or quadtree for "restaurants near me"?
A: Geohash: "nearby" becomes a prefix range query on an ordinary B-tree or Redis, with no special structure. Cost: cells are fixed-size, so a Manhattan cell holds thousands and a desert cell holds none.
Why: 9 cell lookups (yours plus 8 neighbors) on a plain index, then filter by real distance. A quadtree would split Manhattan down to small cells holding ~100 each, but you have to build and rebalance that tree.
Flip: Quadtree when density is very uneven and points rarely move, so you need bounded results per cell.

## Inverted indexes
Q: Why is `LIKE '%wireless headphones%'` slow even with an index on description, and what fixes it?
A: The B-tree is sorted from the first character, so a leading wildcard can't seek, and it's a full table scan. Use an inverted index (word → product IDs): Postgres tsvector + GIN, or Elasticsearch for ranking, typos and stemming.
Why: 10M products. LIKE reads every description, which takes seconds. The inverted index looks up "wireless" (80k IDs) and "headphones" (30k IDs) and intersects them to get 12k matches in milliseconds. Elasticsearch is kept in sync by CDC from the DB, so new products show up a second or so late.

## Cost of indexes on writes
Q: A table has 10 indexes and insert latency is creeping up. Why, and how do you prune?
A: Each insert writes the row plus all 10 indexes, 11 writes instead of 1, mostly random pages. Prune from stats: drop indexes with zero scans (pg_stat_user_indexes.idx_scan) and indexes that are a leftmost prefix of another.
Why: (user_id) and (user_id, created_at) both exist. Every query using the first can use the second, so the first is pure write cost. An index added for a one-off report shows idx_scan = 0 after a month, so drop it. Each drop removes one random write per insert and frees buffer-cache memory for hot data.

Q: A teammate runs a plain CREATE INDEX on a 500M-row orders table at noon. What happens?
A: It locks the table against writes for the whole build, tens of minutes, so inserts queue and checkout times out. Use CREATE INDEX CONCURRENTLY: no write lock, but slower, can't run in a transaction, and a failed build leaves an INVALID index to drop.
Why: The build reads all 500M rows. Each new order's INSERT waits on the lock, connections pile up until the pool is exhausted, and customers see checkout spin and then error. CONCURRENTLY does two passes while writes keep flowing.
Staff: Set lock_timeout (e.g. 5s) on migrations so a blocked DDL fails fast instead of queueing everyone behind it; MySQL uses online DDL or gh-ost.
