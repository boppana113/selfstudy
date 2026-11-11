# Data Modeling

## Relational vs document vs wide-column vs key-value vs graph
Q: Postgres or DynamoDB/Cassandra: what actually drives the choice?
A: Access patterns and scale. Joins, multi-row transactions, or ad-hoc queries → Postgres. Simple key lookups or range reads by a known key at write volume or size past one box → DynamoDB/Cassandra, giving up joins, flexible queries, and cross-item transactions.
Staff: Schema flexibility is a weak reason, since Postgres has JSONB. Default to Postgres and say what would make you switch.

Q: "People you may know" (friends of friends): add a graph DB?
A: Usually no. Two hops is an indexed self-join on a friendships table, and PYMK is typically precomputed offline per user, so the online read is a key lookup. A graph DB pays off for deep or ad-hoc traversals (fraud rings), at the cost of a second database to run and sync.

## Normalization vs denormalization
Q: Store author name/avatar on every post, or look them up?
A: Normalize by default (post stores author_id; batch-fetch users from a cache). Denormalizing saves a read hop, but a rename means rewriting every post the user made, and copies go stale. Denormalize only fields that rarely change and are read in bulk.
Staff: Sync denormalized copies with an async job driven by CDC or events, and accept a window of staleness.

Q: Like count on a hot post: COUNT(*) or a stored counter?
A: A stored counter. COUNT(*) scans the likes table on every view. But 50k increments/min on one row is lock contention, so batch increments through a queue or worker every few seconds, or shard the counter into N rows and sum them. Users see a count a few seconds stale.
Staff: The likes table stays the source of truth, so the counter can be rebuilt if it drifts.

## Partition key / primary key choice
Q: Chat messages in DynamoDB/Cassandra, "latest 50 in a conversation": keys?
A: Partition key = conversation_id, so the conversation is one partition and one read. Sort key = timestamp + message_id, for ordering and to break ties. Query descending, limit 50, and page with the last sort key.

Q: One group chat has millions of messages. What breaks, and what's the fix?
A: One hot, ever-growing partition: writes hit one node and get throttled (DynamoDB ~1k writes/s per partition), and Cassandra slows past ~100 MB per partition. Fix: bucket by time, partition key = (conversation_id, day/week), and read back across buckets.
Staff: Putting message_id in the partition key breaks the range read: every message becomes its own partition.

Q: DynamoDB per-partition and per-item limits?
A: ~1,000 writes/s (WCU) and ~3,000 reads/s (RCU) per partition; 400 KB max item size.

## 1:N and N:M relationships
Q: Users ↔ groups (N:M) in Postgres?
A: users, groups, and a memberships(user_id, group_id) table with a composite primary key and FKs to both, plus an index on group_id so "members of a group" is as fast as "groups of a user."

Q: Users ↔ groups (N:M) in DynamoDB, both directions?
A: Adjacency list: items with PK=USER#u, SK=GROUP#g, plus a GSI that swaps PK and SK. "Groups for a user" and "members of a group" are each one query. A list attribute on the user item only serves one direction and hits the 400 KB item limit.

## Foreign keys and constraints
Q: When do you give up foreign keys, and what replaces them?
A: When data is sharded or split across services (the DB can't check a row on another shard or in another service), or FK checks slow very hot writes. Replace them with validation in the app on write, soft deletes instead of cascades, and a periodic reconciliation job that finds orphans. Integrity becomes eventual.
