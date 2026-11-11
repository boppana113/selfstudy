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

Q: Trip history shows the driver's name and photo. Copy them onto the trip, or look them up?
A: Copy them when the trip is written. A trip is an immutable record, so the name at the time of the trip is the correct value and there's nothing to keep in sync. The cost is a few bytes per trip.
Why: Picture a receipt from March. It already stores the fare as charged then, not today's price. The driver who drove you was "Ana" with that photo; if she renames to "Ana M." in June, the March receipt showing "Ana" is accurate, not stale. So the usual denormalization cost, rewriting copies on every change, doesn't exist here. Keep driver_id too, to link to her current profile.
Flip: Data that should follow the source (a post's author name) stays normalized and is batch-fetched from a cache, one call per page, not one per row.

Q: Hot like counter at 50k likes/min, batched every 2 s: writes/s on the row before and after, and why does it matter?
A: 833 writes/s before, about 80% of a DynamoDB partition's ~1k/s limit, so a small spike throttles. After: one write of +1,666 every 2 s, 0.5 writes/s. The cost is a count up to 2 s stale.
Why: 50,000 ÷ 60 ≈ 833 likes a second, each one an update to the same row. On DynamoDB, a 1.2× viral spike crosses ~1,000 writes/s and users tapping like get errors. On Postgres, each update locks the row, so they queue and like latency climbs. The worker reads 2 seconds of likes (1,666) and applies them in one update: 0.5 writes/s, a 1,666× drop. Always finish with the limit the number is compared to.
Staff: The worker reads from Kafka or the likes table and commits only after the counter write, so a crash doesn't lose the batch.

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

Q: Given a list of access patterns, how do you pick keys and check every query is served?
A: Write each access pattern next to the exact query that serves it (table or GSI, key condition, sort direction, limit). Any pattern with no row is a missing index. The cost of each GSI is a second write per item and eventual consistency.
Why: Ride-sharing trips: "rider's trips, newest first" → base table PK=riderId, SK=timestamp#tripId, descending, limit 20. "Driver's trips, newest first" → GSI PK=driverId, same SK. "Trip detail by trip ID" → neither key answers it, so it needs its own path (a GSI on tripId or a separate item). Walking the list out loud is how you catch that third one.

Q: A driver opens trip history 1 s after a trip ends, and history is a DynamoDB GSI. What do they see?
A: Usually the trip, since GSI replication is typically sub-second, but it isn't guaranteed and GSIs have no strongly consistent reads. So show the just-finished trip from the trip-completion response, not by reading the index back.
Why: The trip write lands in the base table, then DynamoDB copies it to the GSI asynchronously. Most of the time that's milliseconds; under load it can lag. If the app ends the trip and immediately queries the GSI, the newest trip can be missing, and the driver thinks they weren't paid. The app already has the trip in the completion response, so it puts that at the top of the list.
Staff: Project only the list fields into the GSI to keep storage small; a throttled GSI throttles base-table writes too.

Q: Cassandra orders partitioned by restaurant_id; one chain gets 300k orders/day. What breaks, and what's the fix?
A: Partition size, not write rate: ~55 GB a year in one partition against Cassandra's ~100 MB guideline, so compaction and repair on those replicas fall over. Fix: partition key (restaurant_id, hour), about 6 MB per bucket.
Why: 300k × 365 ≈ 110M rows × ~500 B ≈ 55 GB. Writes are only ~3.5/s on average, so throughput is fine; the partition just never stops growing. Hourly buckets hold 300k ÷ 24 ≈ 12.5k rows, ~6 MB. "Last 50" reads the current hour's bucket (clustering created_at DESC, which is correct for newest-first) and steps back an hour if it's short.
Staff: Size buckets per tenant: small restaurants get daily buckets so you don't create thousands of near-empty partitions.

## 1:N and N:M relationships
Q: Users ↔ groups (N:M) in Postgres?
A: users, groups, and a memberships(user_id, group_id) table with a composite primary key and FKs to both, plus an index on group_id so "members of a group" is as fast as "groups of a user."
Why: Picture the two questions the app asks. "Which groups is user 42 in?" uses the primary key index on (user_id, group_id): fast. "Who's in group 7?" needs rows by group_id, and the composite key is sorted by user_id first, so without a second index that's a full scan of memberships. One `CREATE INDEX ON memberships(group_id)` fixes it. The FKs mean a deleted user can't leave orphan memberships behind.

Q: Users ↔ groups (N:M) in DynamoDB, both directions?
A: Adjacency list: one item per membership with PK=USER#u, SK=GROUP#g, plus a GSI that swaps PK and SK. Each direction is one query. A list attribute on the user only serves one direction and hits the 400 KB item limit.
Why: Picture storing group IDs as a list on the user item. "Groups for user 42" is one read. "Members of group 7" means scanning every user and checking their list: the whole table. And a user in 50,000 groups overflows the item. With one item per membership, "groups for 42" is `Query PK=USER#42`, and the GSI (PK=GROUP#g, SK=USER#u) makes "members of 7" `Query PK=GROUP#7`. Both are index reads.

Q: Can a DynamoDB GSI find students in a course if course IDs are stored as a list on each student item?
A: No. A GSI indexes top-level attributes only, not values inside a list. Store one item per enrollment (PK=STUDENT#s, SK=COURSE#c) and a GSI that flips them.
Why: The student item `{PK: STUDENT#s1, courses: [c4, c9]}` gives the GSI nothing to key on for c9. So "students in c9" would be a full-table scan. With an item per enrollment, the GSI has a COURSE#c9 key per row, and the query is one read. A 50k-student course as a list would also exceed the 400 KB item limit and make every enroll rewrite the same item.
Staff: A course with millions of students makes its GSI partition hot; shard the key (COURSE#c9#0–9).

## Foreign keys and constraints
Q: When do you give up foreign keys, and what replaces them?
A: When data is sharded or split across services, because the DB can't check a row on another shard, or when FK checks slow very hot writes. Replace them with three things: validate on write, propagate deletes as events (UserDeleted → anonymize the orders), and run a nightly reconciliation job for orphans. Integrity becomes eventual.
Why: Picture orders on shard 1 referencing a user on shard 3. Postgres on shard 1 can't look at shard 3, so the FK can't exist. Or orders live in the orders service's database and users in the users service's: different databases entirely. So the orders service checks the user exists via API before inserting. Deleting a user marks them deleted rather than cascading across services. A nightly job finds orders whose user is gone and flags them. The cost is that bad references can exist for a day.
Flip: Inside one database, keep the FKs. Dropping them for "performance" before you've measured a problem is giving up integrity for nothing.
Staff: Make the delete consumer idempotent, and alert when the reconciliation job finds orphans > 0, because that means event delivery broke.

Q: Orders and users split into separate services. A user deletes their account. What goes wrong, and what does the orders service do?
A: The orders become orphans: receipts show a blank name, and after a GDPR delete you still hold their data. The users service publishes UserDeleted via an outbox; the orders service anonymizes that user's orders, keeping amounts for accounting, rather than deleting them.
Why: The orders table keeps a plain user_id column; it just lost the constraint. Nothing deletes or fixes those rows on its own. When user 42 deletes their account, the users service writes a UserDeleted event in the same transaction (outbox), the orders service consumes it and strips name and address from 42's orders, and the tax records keep the totals. A nightly job catches any event that got lost.
