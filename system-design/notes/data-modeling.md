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

## Drill: 2026-11-10 (score 25%; Below mid 3 · Mid 3 · Senior 0 · Staff 0)
### Questions
**R1 (scenario) 🟦 Mid**: Ride-sharing trip history on DynamoDB: rider sees own trips newest first, driver sees own trips newest first. How do you pick keys and check both queries are served?
- Follow-up: What does the driver GSI cost, and what does a driver see opening history 1 s after a trip ends?
- You said: Base PK=riderId, SK=timestamp#tripId; GSI PK=driverId, same SK. After the follow-up: GSI is a second copy, double writes and storage; the trip won't be there yet.
- Re-answer: skipped by user.
- Strong answer: Base table keyed by rider, GSI keyed by driver, both sorted by timestamp plus trip ID so ties don't collide. I check by listing each access pattern against a query: rider history is a query on PK=riderId descending with a limit and a cursor; driver history is the same shape on the GSI; trip detail by trip ID isn't served by either, so it needs its own path. The GSI costs a second write per trip and is eventually consistent, usually sub-second but not guaranteed and with no strongly consistent reads, so I show the just-finished trip from the completion response.
- Staff adds: project only the list fields into the GSI; GSI throttling throttles base-table writes.

**R2 (tradeoff duel) 🟦 Mid**: Trip history shows driver name and photo: copy onto every trip (A) or store driver ID and look up (B)?
- Follow-up: 20 trips with 20 drivers: what does B cost per page? Is there an argument that copying is correct, not just faster?
- You said: B, source of truth in Postgres. Follow-up: 20 reads per page; B is correct because the driver ID could change and history needs strong consistency.
- Strong answer: I'd copy the driver's name and photo URL onto the trip when it's written. A trip is an immutable record, like a receipt that already stores the fare at the time, so the old value is the right one and there's nothing to keep in sync. I'd keep driver_id too, to link to the current profile. For data that should stay current, like a post author's name, I'd normalize and batch-fetch in one call (IN query or BatchGetItem) behind a cache, not 20 reads.
- Staff adds: rule: denormalize facts fixed at event time (snapshots); normalize data that should follow the source.

**R3 (spot the flaw) ⬜ Below mid**: Cassandra orders_by_restaurant, PK restaurant_id, clustering created_at DESC, order_id; 5M orders/day; one chain restaurant_id (2,000 locations) gets 300k/day.
- Follow-up: Where do the chain's writes go, and what does that partition look like after a year?
- You said: Said DESC should be ASC (wrong). After the hint: all writes go to one partition, ~110M rows a year.
- Re-answer: skipped by user.
- Strong answer: The chain puts 300k orders a day into one partition, about 55 GB a year at ~500 B a row, against Cassandra's ~100 MB guideline. Reading "last 50" stays one seek, but compaction and repair on those replicas fall over and neighbors slow down. Write rate isn't the issue (3.5/s average); size is. I'd make the partition key (restaurant_id, hour), about 12.5k rows or 6 MB each, and read the current bucket, stepping back if short. DESC is correct for "latest N".
- Staff adds: bucket size per tenant (small restaurants on daily buckets, big ones hourly).

**R4 (explain it) ⬜ Below mid**: Course platform on DynamoDB, students ↔ courses N:M, both directions one query.
- Follow-up: One item per student with a list, or one item per enrollment? Can a GSI find students if course IDs sit inside a list?
- You said: Record per student holding its courses, plus a GSI on course ID. Follow-up: "No idea, skip."
- Strong answer: One item per enrollment: PK=STUDENT#s, SK=COURSE#c, with the course title copied on. A GSI flips PK and SK, so "students in course c" is one query on the GSI and "courses for s" is one query on the base table, both paged. A list on one item can't be indexed by a GSI, hits the 400 KB limit for a 50k-student course, and makes every enrollment rewrite the same item.
- Staff adds: shard a huge course's GSI key (COURSE#c#0–9).

**R5 (failure mode) ⬜ Below mid**: Monolith split; orders and users in separate DBs; orders.user_id FK gone. A user deletes their account: what goes wrong, what instead?
- Follow-up: Orders keep user_id without the constraint; after deletion what do they point at, how does orders find out?
- You said: Thought orders would be merged into the users table; then: they point at nothing; not sure what else.
- Strong answer: Nothing stops orphans now, so the receipt page shows a blank name or errors, and after a GDPR delete we still hold the user's data. The app does the FK's job: validate the user on order create, the users service publishes UserDeleted via an outbox and the orders service anonymizes that user's orders (keeping amounts for accounting), and a nightly reconciliation job finds orders with unknown user_ids. The cost is that integrity becomes eventual, so I keep FKs inside each service's DB.
- Staff adds: idempotent consumer; alert on orphan count > 0 (means event delivery broke).

**R6 (estimation) 🟦 Mid**: Celebrity post at 50k likes/min, worker flushes every 2 s: writes/s on the counter row before and after, and why it matters?
- Follow-up: How many writes carry the 1,666 likes, so how many writes/s vs DynamoDB's ~1k/s per-partition limit?
- You said: 833 likes/s; 1,666 per 2 s; not sure why it matters. Follow-up: one write every 2 s vs 833.
- Strong answer: Unbatched that's 833 writes/s on one row, about 80% of a DynamoDB partition's ~1k/s limit, so a 1.2× spike throttles likes; on Postgres it's row-lock queueing. Batching makes it one write of +1,666 every 2 s, 0.5 writes/s. The cost is a count up to 2 s stale. The worker reads from Kafka or the likes table and commits after the counter write, so a crash doesn't lose likes.
- Staff adds: the likes table rebuilds the counter.

### Gap to senior
- Hot growing partition → bucket by time, (id, day/hour) (2nd miss).
- N:M in NoSQL = one item per edge + flipped GSI; lists can't be indexed (2nd miss).
- No FK across services → validate on write + UserDeleted event (anonymize) + nightly reconciliation (2nd miss).
- Say why a number matters: compare to a limit (833/s vs ~1k/s per partition).
- Snapshot data (receipts, name at trip time) is free to denormalize: nothing to sync.
- Name the cost unprompted (GSI = double write + eventual consistency).

### Staff stretch
- GSI projection; GSI throttling back-pressures base table.
- Per-tenant bucket size; shard a huge GSI key.
- Idempotent delete consumer; alert on orphans > 0.

### Interview-ready lines
- "One key that grows without bound means I bucket it: restaurant_id plus hour keeps each partition around 6 MB instead of 55 GB a year."
- "One item per enrollment, PK student, SK course, and a GSI flips them, so each direction is one query and no item grows without bound."
- "Without the FK, the app validates on write, consumes UserDeleted to anonymize, and runs a nightly orphan check. Integrity becomes eventual."
- "833 writes a second on one row is 80% of a partition's limit, so batching to 0.5 a second buys headroom for the cost of a 2-second-stale count."
- "A trip is an immutable record, so I copy the driver's name onto it. The old value is the right value."
- "The cost of the GSI is a double write and eventual consistency, so I show a just-finished trip from the write response."

### Delivery
- Habit: "I'm not sure" with no reasoning: R3 ("I'm not familiar with Cassandra internals"), R4 ("I have no idea. Let's skip this."), R5 twice, R6 ("I'm not sure why that number matters"). Also R1/R2 named the pick without a because or cost (recurring, 8th session).
- Rewrite (R5): "Once the FK is gone, nothing stops orders from pointing at a deleted user. So the receipt page shows a blank name, and if this was a GDPR delete, we're still holding their data. I'd have the users service publish a UserDeleted event, and the orders service anonymizes that user's orders, keeping the amounts for accounting. A nightly job catches anything the events missed. The cost is that integrity becomes eventual, so I keep real FKs inside each service's database."
- Did well: R6 opened with the estimation frame word for word; R1 opened with the keys.
- Frame reminders: on (re-answers: 2, both skipped by user)
