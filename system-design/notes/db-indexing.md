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

## Drill: 2026-11-22 (score 42%; Below mid 1 · Mid 5 · Senior 0 · Staff 0)
### Questions
**R1 (explain it) 🟦 Mid**: 1M devices writing metrics. Walk through what an LSM tree does with a single write, and what bloom filters fix on reads.
- Follow-up: Where does an SSTable live, memory or disk, and why are writes cheap vs a B-tree?
- You said: WAL → memtables → immutable → "bulk write to Cassandra"; reads check several places, bloom filters rule out tables (put them on memtables). Follow-up: SSTables on disk; B-tree inserts "expensive".
- Strong answer: Every write is a sequential append to the commit log plus an insert into the in-memory memtable. When the memtable fills it's flushed as an immutable sorted SSTable on disk, and that IS Cassandra's storage: there's no separate DB behind it. B-trees update pages in place, so each write is a random disk write and sometimes a page split. The cost lands on reads: a key can be in the memtable or any SSTable, so a per-SSTable bloom filter answers "definitely not" or "maybe" from RAM, and compaction merges files to keep the count low.
- Staff adds: read/write/space amplification; leveled (reads) vs size-tiered (writes) compaction; tombstones slow reads until compacted.

**R2 (scenario) 🟦 Mid**: Order history with a composite index on (user_id, created_at). One query it serves perfectly, one it can't help, and what you'd do about the second.
- Follow-up: Ops dashboard wants every order in the last hour across all users. Can this index help?
- You said: Serves one user's orders in a date range; can't help "price above threshold" → covering index. Follow-up: no, user_id is sorted first so it grabs every page. No fix given.
- Strong answer: It serves "user X's orders, newest first": seek to user X, read a pre-sorted range. It can't serve "all orders in the last hour", because of the leftmost-prefix rule: timestamps are scattered across every user. I'd add a separate created_at index, at the cost of one more write per insert. user_id alone still uses it; a price filter within one user still uses it for the user and filters rows; covering helps SELECT columns, not WHERE filters.
- Staff adds: the created_at index is right-edge hot on inserts; at high write rates feed the dashboard via CDC to a time-series store.

**R3 (tradeoff duel) 🟦 Mid**: "Restaurants near me": why can't a B-tree on lat/lng handle it, then pick geohash or quadtree and defend it.
- Follow-up: User at a cell edge, best restaurant 50 m away in the next cell. What goes wrong and the fix?
- You said: 1D index vs 2D data, "merge and filter in memory"; geohash because widely used in production, quadtree splits naively. Follow-up: "I'm not sure", knew neighbors are findable.
- Re-say: skipped (given the four beats, declined to say it).
- Strong answer: A (lat, lng) B-tree narrows latitude, then scans a strip around the whole globe. I'd pick geohash because it makes "nearby" a prefix range query on an ordinary index or Redis. Cells are fixed-size, so points across an edge share no prefix: query my cell plus its 8 neighbors and filter by real distance. If density varied wildly, I'd switch to a quadtree, which splits only dense cells.
- Staff adds: PostGIS GiST or Redis GEOSEARCH in practice; static restaurants vs drivers moving every 4 s (cheap geohash updates win).

**R4 (spot the flaw) 🟦 Mid**: Product catalog, 10M rows, heavy inserts. What's wrong?
```
INDEX (seller_id)
INDEX (seller_id, created_at)
HASH INDEX (price)          -- for "price between $20 and $50"
B-TREE INDEX (description)  -- for LIKE '%wireless headphones%'
INDEX (title), INDEX (price, seller_id), INDEX (created_at, title) ...
```
- Follow-up: Anything wrong with the first two lines?
- You said: hash → B-tree for ranges; description → inverted index; last three slow inserts. Follow-up: first two look reasonable (missed the redundancy).
- Strong answer: Three problems. Hash can't do a range, so B-tree. A leading wildcard can't seek a B-tree, so it's a full scan of 10M rows; use tsvector + GIN or Elasticsearch. Too many indexes: (seller_id) is a leftmost prefix of (seller_id, created_at), so drop it, and drop anything with idx_scan = 0; 9 indexes = 10 writes per insert.
- Staff adds: Elasticsearch fed by CDC is eventually consistent (fine for a catalog); confirm what (created_at, title) serves before dropping.

**R5 (estimation) ⬜ Below mid**: SELECT order_id, total WHERE user_id = X, index on user_id, 500 scattered orders. How many page reads, and how to cut it without a table or cache?
- Follow-up: After the index finds the 500 entries, where do order_id and total come from?
- You said: "page size of 20" → 25 pages; fix by sorting or sharding. Follow-up: extra reads to get order ID; switch to a composite including order ID.
- Re-say: ✗ "scattered rows → ~500 pages; fix: sort users so they line up (clustering)." Missing "which means" (~50 ms uncached) and the cheap fix (covering index).
- Strong answer: The index finds user X's entries in 3–4 pages plus a leaf or two, but the rows are scattered, so it's ~500 random heap reads, roughly 50 ms if uncached. Make it covering: (user_id) INCLUDE (order_id, total) → index-only scan, under 10 pages. Cost: bigger index, a bit more write work. Sharding spreads load but each query still does 500 reads.
- Staff adds: clustering by key (InnoDB primary key (user_id, order_id)) puts a user's rows on adjacent pages; Postgres index-only scans need the visibility map current (vacuum).

**R6 (failure mode) 🟦 Mid**: 500M-row orders table, heavy writes. A teammate runs a plain CREATE INDEX in production at noon. What happens, and how should they have done it?
- Follow-up: What happens to inserts during the build, and what does a customer at checkout see?
- You said: Writes slow from per-insert index overhead; asked the goal. Follow-up: DB can't process writes during the build, checkout fails. No fix.
- Re-say: ✓ lock blocks writes → inserts queue, checkout times out → CONCURRENTLY → slower build (invalid index only if it fails).
- Strong answer: A plain CREATE INDEX takes a lock that blocks writes (reads still work) for the whole build, tens of minutes on 500M rows. Inserts queue, connections pile up, checkout times out. Use CREATE INDEX CONCURRENTLY: no write lock, but slower (two passes), not in a transaction, and a failed build leaves an INVALID index to drop and retry. MySQL: online DDL or gh-ost.
- Staff adds: migrations with lock_timeout (e.g. 5s) so a blocked DDL fails fast; off-peak; watch replica lag from the WAL burst.

### Gap to senior
- Covering index + page math: scattered rows = 1 random read each (500 rows ≈ 500 reads ≈ 50 ms uncached); INCLUDE selected columns → index-only scan, <10 reads; not sharding (missed in pretest AND drill)
- Finish with the fix + cost: R2 (created_at index), R3 (8 neighbors), R6 (CONCURRENTLY) all stopped at the problem
- Leftmost prefix both ways: (a,b) serves a and a+b, never b; (a) beside (a,b) is redundant
- LSM is the storage engine (not a layer in front of the DB); sequential append vs B-tree random in-place page writes; bloom filters per SSTable, "definitely not / maybe"
- Geohash: shared prefix → range query; cell + 8 neighbors for edges; quadtree when density is uneven
- Online index builds: plain CREATE INDEX blocks writes; CONCURRENTLY doesn't, slower and may leave INVALID index
### Staff stretch
- Leveled vs size-tiered compaction, tombstones
- Clustered storage by key (InnoDB PK), visibility map for index-only scans
- PostGIS GiST vs Redis GEOSEARCH; moving vs static points
- lock_timeout on migrations, replica lag from index builds
- CDC lag for Elasticsearch search
### Interview-ready lines
- "The rows are scattered, so that's one random read per row, about 500. A covering index makes it an index-only scan: under 10."
- "…so the fix is ___, and the cost is ___."
- "(user_id, created_at) serves user, or user plus time, but never time alone: leftmost prefix. That also makes a standalone (user_id) index redundant."
- "LSM writes are sequential appends to a log and a memtable; B-trees do random in-place page writes. Bloom filters let reads skip SSTables that definitely don't have the key."
- "Geohash turns 'nearby' into a prefix range query; I search my cell plus its 8 neighbors to handle edges."
- "Never a plain CREATE INDEX on a hot table. Use CONCURRENTLY: slower, but writes keep flowing."
### Delivery
- Habit: stopping at the problem without the fix ("I'm not sure what the fix is"; R6 ended at "the database isn't processing new writes"). Shift from earlier sessions: consequence now comes through, the fix drops.
- Rewrite (R6): "A plain CREATE INDEX locks the table against writes for the whole build, and on 500 million rows that's tens of minutes. So inserts queue up, connections pile up behind them, and a customer at checkout gets a timeout. The fix is CREATE INDEX CONCURRENTLY, which builds without blocking writes. The cost is that it's slower, and if it fails you're left with an invalid index to drop and retry."
- Did well: signposted R4 flaw by flaw; bottom line first in R2/R3.
- Frame reminders: on
- Re-say: 1/3, 1 skipped (fix + cost beat; "which means" in estimation)
