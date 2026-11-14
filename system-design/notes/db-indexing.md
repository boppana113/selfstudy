# Database Indexing

## Pretest: 2026-11-14 (score 19%; Below mid 5 · Mid 3 · Senior 0 · Staff 0)
### Questions
**Q1 🟦 Mid**: What is a database index, and what does it cost you to add one?
- You said: A data structure (e.g. B-tree) that speeds reads by locating rows; costs slower writes since it must be updated.
- Strong answer: An index is a separate sorted structure, usually a B-tree, that maps column values to row locations. A lookup reads 3–4 pages instead of scanning every row, so on 10M rows it's milliseconds instead of a multi-GB scan. The cost is that every insert, update and delete also has to update each index, and each index takes disk and buffer-cache memory. So I index the hot query patterns, not every column.

**Q2 ⏭️ Below mid**: For a write-heavy system (metrics, logs), how does an LSM tree handle a write, and what does it give up vs a B-tree?
- You said: Didn't know what an LSM tree is.
- Strong answer: An LSM tree appends the write to a log and puts it in an in-memory sorted table (the memtable). When the memtable fills, it's flushed to disk as an immutable sorted file (an SSTable), and background compaction merges SSTables. Every write is a sequential append, so write throughput is very high; Cassandra and RocksDB work this way. The cost is reads: a key might live in the memtable or any of several SSTables, so bloom filters are used to skip files that definitely don't have it, and compaction burns CPU and disk I/O. B-trees update pages in place, so writes are random I/O but reads follow one path. LSM for write-heavy, B-tree for read-heavy OLTP.

**Q3 ⬜ Below mid**: Composite index on (user_id, created_at): does column order matter, and does it help a query on created_at alone?
- You said: Indexing on created_at wouldn't help much; use a stored procedure to find recent orders.
- Strong answer: Order matters. The index is sorted by user_id first, then by created_at within each user, like a phone book sorted by last name then first name. "User X's orders from the last 30 days, newest first" jumps straight to user X and walks a range that's already sorted, with no sort step. A query on created_at alone can't use it, because of the leftmost-prefix rule: the timestamps are scattered across every user, so you need a separate index on created_at. A stored procedure doesn't change how the data is read.

**Q4 ⏭️ Below mid**: "Restaurants within 2 km": why doesn't a B-tree on (lat, lng) work, and what would you use?
- You said: Not sure.
- Strong answer: A B-tree is one-dimensional. It can narrow to a latitude band, but within that band longitudes are scattered, so you scan a strip that wraps the whole globe. I'd use a geospatial index. Geohash encodes 2D into a string where nearby points share a prefix, so a normal prefix range works; you query your cell plus its 8 neighbors to handle edges. Quadtrees split dense regions further, and R-trees index bounding boxes. In practice that's PostGIS with a GiST index, or Redis GEO (GEOSEARCH) for hot reads.

**Q5 🟦 Mid**: `LIKE '%wireless headphones%'` is slow even with an index on description. Why, and what would you use?
- You said: The tree parses strings on every row; the index only looks at the first characters. Didn't know the better system.
- Strong answer: A B-tree on description is sorted from the first character. A leading wildcard means the match can start anywhere, so the index is useless and Postgres does a full table scan, which takes seconds at 10M products. The fix is an inverted index: map each word to the list of product IDs that contain it, then intersect the lists for "wireless" and "headphones". That's Postgres tsvector with a GIN index, or Elasticsearch if you need ranking, typo tolerance and stemming, kept in sync via CDC and eventually consistent.

**Q6 🟦 Mid**: Ten indexes on a busy orders table: insert latency is up and disk is filling. What's going on, and how do you decide what to keep?
- You said: Indexes are stored on disk and accumulate; keep indexes only for high-demand queries, let others full-scan.
- Strong answer: Every insert writes the row plus all ten indexes, so 11 writes instead of 1, most of them random page writes. That's why latency climbed. The indexes also compete for buffer-cache memory, which pushes hot data out. I'd decide from stats rather than guesses: anything with zero scans in pg_stat_user_indexes gets dropped. Any index that's a leftmost prefix of another, like (user_id) next to (user_id, created_at), is redundant. Keep the ones that serve hot queries or enforce uniqueness.

**Q7 ⬜ Below mid**: SELECT order_id, total WHERE user_id = X, with an index on user_id. How can it be even faster without a new table or cache?
- You said: Add another index on total and search using two indexes.
- Strong answer: Make it a covering index by putting the selected columns in the index, for example (user_id) INCLUDE (order_id, total). The database then does an index-only scan and never visits the table, which saves one random read per row: 200 heap fetches for a user with 200 orders. The cost is a bigger index and a bit more write work. A second index on total doesn't help, because the query still has to go back to the table.

**Q8 ⬜ Below mid**: A hash index is O(1); why do databases default to B-trees? When would you want hash?
- You said: Hash uses O(n) memory vs B-tree O(log n); use hash if the DB is small.
- Strong answer: Both use O(n) space. A B-tree wins because its keys are sorted, so it handles ranges (created_at > X), ORDER BY, prefix LIKE 'abc%' and leftmost prefixes of composite indexes. A hash index only does exact equality. And with high fanout a B-tree is only 3–4 page reads, so O(1) vs O(log n) barely matters. I'd use hash when every lookup is an exact match on a key, like session ID → session; that's why key-value stores such as Redis and DynamoDB partition keys are hash-based.

### Gap to mid
- LSM tree basics: memtable → SSTable flush → compaction; write-optimized
- Composite index = sorted by first column then second; leftmost-prefix rule
- Covering index → index-only scan (no table lookup)
- Geospatial: why 1D B-tree fails; geohash / quadtree / R-tree
- Hash index = equality only, no ranges/sort (space is O(n) for both)

### Gap to senior
- Put numbers on it: 3–4 page reads vs full scan; 10 indexes = 11 writes per insert
- Bloom filters fix LSM read amplification; compaction cost
- Inverted index (term → doc IDs); Postgres GIN vs Elasticsearch
- Prune indexes from usage stats (idx_scan = 0, redundant leftmost prefixes)
- Geohash edge problem → query cell + 8 neighbors

### Hold-in-mind questions
- Why does an LSM tree make writes faster, and what do bloom filters fix on the read side?
- Given an index on (user_id, created_at), which queries can use it and which can't?
- How does geohash let a 1D index answer a 2D "nearby" query, and what's the edge problem?

### Delivery
- Habit (RECURRING, same root as the "reasoning stays unsaid" / "vague words" habits in earlier sessions): guesses stated as facts, with no mechanism ("hash-index will eat at the memory", "the tree needs to perform string parsing on every row"). When unsure, reason out loud: "I think the issue is…, because…".
- Rewrite (Q3): "Yes, order matters. A composite index is sorted by user ID first, then by created-at within each user, kind of like a phone book sorted by last name and then first name. So 'user X's last 30 days, newest first' is perfect for it: jump to user X and read a range that's already in order, with no sort. But a query on created-at alone can't use it. Those timestamps are scattered across every user, so it's a full scan, and I'd add a separate index on created-at if that query is hot."
- Did well: clean, quick "I don't know"s instead of rambling, and Q1 opened with the definition.
