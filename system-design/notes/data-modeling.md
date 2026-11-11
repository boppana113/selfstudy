# Data Modeling

## Pretest: 2026-11-10 (score 38%; Below mid 3 · Mid 4 · Senior 1 · Staff 0)
### Questions
**Q1 ⬜ Below mid**: Social app backend: when Postgres, when DynamoDB/Cassandra? What drives it?
- You said: Postgres when you need schema validation on write; NoSQL for flexible schema (schema-on-read), so the feed schema can evolve.
- Strong answer: I start from the access patterns. If I need joins, multi-row transactions, or ad-hoc queries, like payments or a user's settings, I'd use Postgres, and one box handles more than people expect. I'd pick DynamoDB or Cassandra when access is simple key lookups or range reads by a known key, and the write volume or data size outgrows one box. What I give up is joins, flexible queries, and cross-item transactions, so I have to design the tables around the queries up front. Schema flexibility is a minor factor, since Postgres has JSONB.

**Q2 🟦 Mid**: Store author username/avatar on every post, or only in users and look up? What do you give up?
- You said: Keep in users table; post holds a reference.
- Strong answer: I'd normalize by default: the post stores author_id, and I join or batch-fetch users. The cost is an extra lookup on every feed read, which a user cache removes. Denormalizing makes the read one hop, but changing a username means rewriting every post that user ever made, and copies can go stale. I'd denormalize only fields that rarely change and are read in bulk, and accept that a renamed user shows the old name for a while.

**Q3 🟩 Senior**: Chat messages in Cassandra/DynamoDB, query "latest 50 in a conversation": partition key and sort key?
- You said: Partition key = thread ID; sort key = timestamp + message ID.
- Strong answer: Partition key is the conversation ID, because then the whole conversation lives in one partition and "latest 50" is a single read. Sort key is timestamp plus message ID, so messages come back in order and two messages with the same timestamp don't collide. I query descending with a limit of 50 and page with the last sort key as a cursor.

**Q4 ⬜ Below mid**: A group chat has millions of messages in one conversation. What goes wrong, how do you fix it?
- You said: Simultaneous messages; fix by making the partition key thread ID + message ID, timestamp as sort key.
- Strong answer: One conversation is one partition, so it becomes hot and keeps growing. Every write hits one node, the per-partition throughput cap (around 1,000 writes/s in DynamoDB) throttles sends, and in Cassandra a partition past ~100 MB slows reads and compaction. I'd bucket by time: the partition key is (conversation_id, day or week), and the sort key stays timestamp + message ID. "Latest 50" reads the current bucket and steps back a bucket if needed. Adding message ID to the partition key would make every message its own partition, so a range read wouldn't work anymore.

**Q5 🟦 Mid**: Users in many groups (N:M): model in Postgres, then DynamoDB.
- You said: Users table plus a table mapping user ID → group ID with a foreign key; join. In DynamoDB, a list of group IDs on the user item if small.
- Strong answer: In Postgres: users, groups, and a memberships table (user_id, group_id) with a composite primary key and foreign keys to both, plus an index on group_id so both directions are fast. In DynamoDB I'd use an adjacency list: items with PK=USER#u, SK=GROUP#g, and a GSI that flips them, so "groups for a user" and "members of a group" are each one query. A list on the user item only answers one direction, and it hits the 400 KB item limit for big users.

**Q6 ⏭️ Didn't know**: When would you deliberately give up foreign keys and constraints, and what do you do instead?
- You said: Not sure.
- Strong answer: Once data is sharded or split across services, the database can't check a reference to a row on another shard or in another service's database. FKs also slow very hot writes and make big deletes and migrations painful. So the application takes over the job: validate on write, soft-delete instead of cascades, and run a periodic reconciliation job to find and clean orphans. The cost is that integrity becomes eventual, so I keep FKs inside one database wherever I can.

**Q7 🟦 Mid**: Like count on a celebrity post (50k likes/min): COUNT(*) or a stored counter? Problems?
- You said: Count on view; worried about simultaneous updates throttling; then suggested recomputing every few seconds.
- Strong answer: I'd store a counter on the post, because COUNT(*) scans the likes table on every view, and the post is viewed far more often than it's liked. But 50k increments a minute on one row is lock contention on a hot row. So I'd write likes to the likes table or a queue and have a worker fold them into the counter in batches every few seconds, or shard the counter into N sub-counters and sum them. Users see a count a few seconds stale, which is fine. The likes table stays the source of truth for "did I like this" and for rebuilding the counter.

**Q8 🟦 Mid**: "People you may know" (friends of friends): graph DB or existing store?
- You said: Graph DB, since it tracks relationships and hops; relational needs table scans; NoSQL doesn't support linkage.
- Strong answer: For two hops I'd keep it in the existing store. A friendships table indexed on user_id makes friends-of-friends a self-join that uses the index, not a full scan. Most companies compute PYMK offline in a batch job and store the results per user, so the online path is a key lookup. A graph database pays off when queries go many hops deep or are ad hoc, like fraud rings. The cost is a second database to run and keep in sync with the source of truth.

### Gap to mid
- Pick a database by access pattern, scale, and transactions, not by schema flexibility.
- Hot partition fix: bucket by time, not by message ID (that breaks range reads).
- When to give up FKs: data sharded or split across services → validate in the app and reconcile.
- COUNT(*) is a read cost (it scans); a counter is a write cost (one hot row). Don't mix them up.

### Gap to senior
- Name the cost of each choice: joins vs denormalized update fan-out, staleness.
- N:M in NoSQL: adjacency list + inverted GSI, so both directions are served.
- Specific limits: DynamoDB ~1k writes/s per partition and 400 KB per item; Cassandra partitions under ~100 MB.
- Hot counter: batch the increments or shard the counter; accept a few seconds of staleness.
- A new database (graph) costs operations and syncing; precompute offline first.

### Hold-in-mind questions
- Given a list of access patterns, how do you pick the partition key and sort key, and how do you check every query is served?
- When is denormalizing worth it, and how do you keep the copies in sync?
- How do you model N:M in a key-value or wide-column store so both directions are one query?

### Delivery
- Habit (RECURRING, 7th+ session across topics): naming a choice and stopping before its cost. Q2: "every post does not need to contain the information of the username and profile picture, just a reference"; Q1 and Q8 didn't say what the pick gives up either. Q7 hedged its best idea ("Perhaps a better way would be…").
- Rewrite (Q2): "I'd normalize: the post just stores author_id, and the feed batch-fetches users, usually from a cache. I'd pick this because usernames and avatars change, and if I copied them onto every post, one rename means rewriting thousands of rows. The cost is an extra lookup on every feed read. If that lookup became the bottleneck, I'd copy over only the fields that rarely change, and accept that they might be stale for a while."
- Did well: Q3 opened with the answer, and Q5 kept the two halves (Postgres, then DynamoDB) clearly separate.
