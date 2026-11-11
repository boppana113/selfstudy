# Data Modeling

## Relational vs document vs wide-column vs key-value vs graph
Q: Postgres or DynamoDB/Cassandra: what actually drives the choice?
A: Access patterns and scale. Joins, multi-row transactions, or ad-hoc queries → Postgres. Key lookups or range reads by a known key, at volume past one box → DynamoDB/Cassandra, and you give up joins, flexible queries, and cross-item transactions.
Why: Picture a payments table. "Show me all refunds over $100 last month, joined to the customer" is an ad-hoc query with a join: Postgres does it with an index; DynamoDB would need a table designed for exactly that question. Now picture chat messages at 20k writes/s and 1 TB/day: Postgres hits its write and storage ceiling, and the only query is "messages in conversation X," so a wide-column store partitioned by conversation_id fits. Schema flexibility barely matters, since Postgres has JSONB.
Flip: Default to Postgres and name the number that would make you switch: writes past ~10k/s or storage past several TB.

Q: "People you may know" (friends of friends): add a graph DB?
A: Usually no. Two hops is an indexed self-join on a friendships table, and PYMK is precomputed offline per user, so the online read is a key lookup. The cost of a graph DB is a second database to run and keep in sync.
Why: Picture user 42 with 300 friends. `SELECT friend_id FROM friendships WHERE user_id IN (42's friends)` is 300 index seeks, a few ms, not a scan. And nobody runs that on page load: a nightly batch job computes the top 20 suggestions per user and writes them to a table, so the feed reads one row. A graph database pays off when queries go 4+ hops or are ad hoc, like finding fraud rings.
Flip: Deep or ad-hoc traversals (fraud rings, supply-chain dependencies) are where a graph DB earns its ops cost.

## Normalization vs denormalization
Q: Store author name/avatar on every post, or look them up?
A: Normalize: the post stores author_id, and the feed batch-fetches users from a cache. The cost is one extra lookup per feed read.
Why: Picture a user with 3,000 posts changing their name. If the name is copied onto every post, that's 3,000 row rewrites, and until they finish, some posts show the old name. With a reference, it's one row. Reads pay instead: a feed of 20 posts needs 20 authors, but that's one batched cache call, ~1 ms.
Flip: Copy fields that almost never change onto a very hot read path, and accept that they'll sometimes be stale.
Staff: Sync denormalized copies with an async job driven by CDC or events, and accept a window of staleness.

Q: Like count on a hot post: COUNT(*) or a stored counter?
A: A stored counter, because COUNT(*) scans the likes table on every view. The cost is a hot row under 50k increments a minute, so batch the increments or shard the counter.
Why: Picture a celebrity post viewed 1M times an hour. COUNT(*) walks every like row on every view: millions of rows, millions of times. A counter column makes the view a single read. But now 50k likes a minute each try to lock the same row: contention. So likes go to the likes table or a queue, and a worker adds them to the counter every few seconds in one update, or the counter is split into 10 rows that are summed on read. Users see a count a few seconds old, which nobody notices.
Staff: The likes table stays the source of truth, so the counter can be rebuilt if it drifts.

## Partition key / primary key choice
Q: Chat messages in DynamoDB/Cassandra, "latest 50 in a conversation": keys?
A: Partition key = conversation_id, so the conversation is one partition and one read. Sort key = timestamp + message_id, for ordering and to break ties.
Why: Walk the query. The app asks for conversation 42's latest 50. With conversation_id as the partition key, all of 42's messages are on one node, stored in sort-key order, so the database reads the last 50 entries in one request and returns them newest first. Two messages sent in the same millisecond share a timestamp; the message_id suffix keeps them distinct and ordered. Paging is "give me 50 before this sort key."

Q: One group chat has millions of messages. What breaks, and what's the fix?
A: One hot, ever-growing partition: writes hit one node and get throttled, and reads slow as it grows. Fix: bucket by time, partition key = (conversation_id, day or week), and read back across buckets.
Why: Picture a 100k-member group sending 2k messages a second. All of them land on the one node that owns that partition. DynamoDB caps a partition at ~1k writes/s, so sends get throttled and users see "message failed." Cassandra lets it grow, but past ~100 MB the partition slows reads and compaction. With (conversation_id, 2026-11-10) as the key, each day is its own partition on its own node, and "latest 50" reads today's bucket, then yesterday's if needed.
Staff: Putting message_id in the partition key breaks the range read: every message becomes its own partition.

Q: DynamoDB per-partition and per-item limits?
A: ~1,000 writes/s (WCU) and ~3,000 reads/s (RCU) per partition; 400 KB max item size.
Why: These are the numbers that tell you a key design is in trouble. A chat at 2k sends/s into one conversation is 2× the write cap: throttling. A user item holding a list of 50,000 group IDs at ~10 bytes each is 500 KB: over the item limit, the write is rejected. When you hear "one hot key" or "a list that grows forever," check these two numbers.

## 1:N and N:M relationships
Q: Users ↔ groups (N:M) in Postgres?
A: users, groups, and a memberships(user_id, group_id) table with a composite primary key and FKs to both, plus an index on group_id so "members of a group" is as fast as "groups of a user."
Why: Picture the two questions the app asks. "Which groups is user 42 in?" uses the primary key index on (user_id, group_id): fast. "Who's in group 7?" needs rows by group_id, and the composite key is sorted by user_id first, so without a second index that's a full scan of memberships. One `CREATE INDEX ON memberships(group_id)` fixes it. The FKs mean a deleted user can't leave orphan memberships behind.

Q: Users ↔ groups (N:M) in DynamoDB, both directions?
A: Adjacency list: one item per membership with PK=USER#u, SK=GROUP#g, plus a GSI that swaps PK and SK. Each direction is one query. A list attribute on the user only serves one direction and hits the 400 KB item limit.
Why: Picture storing group IDs as a list on the user item. "Groups for user 42" is one read. "Members of group 7" means scanning every user and checking their list: the whole table. And a user in 50,000 groups overflows the item. With one item per membership, "groups for 42" is `Query PK=USER#42`, and the GSI (PK=GROUP#g, SK=USER#u) makes "members of 7" `Query PK=GROUP#7`. Both are index reads.

## Foreign keys and constraints
Q: When do you give up foreign keys, and what replaces them?
A: When data is sharded or split across services, because the DB can't check a row on another shard, or when FK checks slow very hot writes. Replace them with validation in the app, soft deletes instead of cascades, and a reconciliation job that finds orphans. Integrity becomes eventual.
Why: Picture orders on shard 1 referencing a user on shard 3. Postgres on shard 1 can't look at shard 3, so the FK can't exist. Or orders live in the orders service's database and users in the users service's: different databases entirely. So the orders service checks the user exists via API before inserting. Deleting a user marks them deleted rather than cascading across services. A nightly job finds orders whose user is gone and flags them. The cost is that bad references can exist for a day.
Flip: Inside one database, keep the FKs. Dropping them for "performance" before you've measured a problem is giving up integrity for nothing.
