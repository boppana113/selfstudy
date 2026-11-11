# Kafka

## Partitions & consumer groups
Q: A topic has 6 partitions and one consumer group has 8 consumers. Who reads what?
A: 6 consumers get one partition each and 2 sit idle. Parallelism inside a group is capped at the partition count.
Why: Picture the group coordinator handing out partitions like keys to rooms: 6 keys, 8 people. Each partition can have only one reader per group, because the group commits one offset per partition and two readers would fight over it. So consumers 7 and 8 get nothing. Adding consumers beyond 6 changes nothing; adding partitions is what adds parallelism.
Staff: Rebalances pause the group; cooperative-sticky assignment or static membership keeps deploys from stalling it.

Q: Same topic, 6 partitions, but 3 consumers in the group. How is work split?
A: Each consumer owns 2 partitions. One consumer can own many partitions, but a partition never has two consumers in the same group.
Why: Same room-key picture: 6 keys, 3 people, so each gets 2. Consumer A polls partitions 0 and 1 in turn and commits an offset for each separately. If consumer C dies, the group rebalances and A and B get 3 each. Throughput per consumer is the limit here, not the partition count.

Q: A second consumer group subscribes to the same topic. Does it compete with the first group for messages?
A: No. Each group reads every partition independently with its own offsets. That's what makes Kafka a log, not a queue: many readers, and replay by resetting offsets.
Why: Picture the topic as a file on disk. Group "fraud" has a bookmark at line 1,000 in partition 0; group "email" has its own bookmark at line 950. Each reads at its own pace, and reading doesn't delete anything. In SQS the message is gone once one consumer acks it. In Kafka, 10 groups can each read the whole topic.

Q: Fraud, email, and analytics all read order events from one topic. Analytics wants to reprocess last week. How, without disturbing fraud?
A: Analytics resets its own consumer group's offsets to last week's timestamp. No new topic, and fraud's offsets are untouched.
Why: Each group's bookmark is independent. Analytics stops its consumers, runs `kafka-consumer-groups --reset-offsets --to-datetime 2026-11-03T00:00` on its group, and restarts. Its consumers re-read 7 days of events. Fraud's bookmark never moved. The only requirement is that retention is at least 7 days, or the data is already gone.
Staff: Tiered storage makes long retention cheap.

Q: What does a committed offset mean?
A: "This group has processed everything in this partition up to here." One watermark per partition, not a per-message ack.
Why: Picture messages 100–110 in a partition. The consumer finishes 101–110 but 100 is still running. It can't commit 110, because a commit says everything before it is done, and 100 isn't. If it commits 110 and crashes, 100 is skipped forever. If it waits and crashes, 100–110 all replay. That one-number design is why Kafka works for ordered streams and poorly for a job queue.

## Ordering & partition keys
Q: What ordering does Kafka guarantee?
A: Per partition only. Same key → same partition → in order. Across partitions, none.
Why: Picture driver 42's pings: all keyed by driver_id, all in partition 3, read by one consumer in order, so "position at 10:00:04" always lands after "position at 10:00:00." Driver 43 is in partition 5 with a different consumer, which might be slower, so 43's 10:00:00 ping can be processed after 42's 10:00:04. That's fine, because no one needs ordering across drivers.

Q: Who picks a message's partition, and how?
A: The producer's partitioner: hash(key) % numPartitions. With no key, messages are spread across partitions, so you get no useful ordering.
Why: The producer takes "driver-42," hashes it, takes mod 12, and gets partition 3. Every ping from driver-42 hits the same math and the same partition. With no key, the producer round-robins or sticks to a partition per batch, so driver-42's pings scatter across all 12 and arrive at consumers in any order.

Q: Uber driver location pings go into Kafka. What partition key, and why?
A: driver_id, because it's high cardinality (spreads load evenly) and per-driver order is the only order anyone needs.
Why: 1M drivers hash across 150 partitions, so each gets ~6,700 drivers and roughly equal load. Within a partition, each driver's pings stay in order, so the consumer never writes a stale position over a fresh one. Nothing downstream needs driver A's ping before driver B's, so cross-partition order isn't missed.
Staff: A log-compacted topic keyed by driver_id gives cheap "latest position" recovery for a new consumer.

Q: Why not partition the driver pings by city?
A: City is skewed, so one partition runs hot, and a hot partition can only have one consumer.
Why: Picture SF with 30,000 drivers and a small town with 20, both as keys. SF's partition gets 7,500 msg/s; the town's gets 5. One consumer owns the SF partition and can do 5k/s, so it falls behind, and adding consumers can't help because a partition has one reader per group. Matching by city should query a geo index fed from the stream, not depend on partition layout.

Q: Why does adding partitions to a live keyed topic break ordering?
A: hash(key) % N changes, so most keys move to a new partition. During the switch, a key's old messages are still unread in the old partition while new ones land in another.
Why: Picture going from 12 to 16 partitions. driver-42 was in partition 3 (hash % 12); now it's partition 9 (hash % 16). Its 10:00:00 ping sits unread in partition 3 behind a backlog, and its 10:00:04 ping is in partition 9, read immediately. Consumer B writes the 10:00:04 position; consumer A then writes 10:00:00 over it. Stale wins. Over-provision partitions up front, or migrate to a new topic and switch producers over.
Staff: Partitions aren't free (more leader elections and per-broker memory), so over-provisioning has a ceiling.

## Delivery semantics & idempotency
Q: A consumer uses enable.auto.commit=true and crashes mid-charge. What happens?
A: The offset may already be committed, so the restart skips the message and the order is silently never charged. That's at-most-once.
Why: Walk the timeline. Poll returns order 500 at 10:00:00.0. Auto-commit fires on its 5-second timer at 10:00:00.2 and commits 501. The charge call runs at 10:00:00.5 and the process dies at 10:00:01. The replacement consumer starts at 501. Order 500 is in the "shipped" pipeline with no payment, and nothing alerts because, from Kafka's view, it was processed.

Q: You commit only after the charge. The consumer charges, then crashes before committing. What happens, and what's the fix?
A: The next consumer re-reads from the last commit and charges again: at-least-once. Make the consumer idempotent by passing order_id as the payment provider's idempotency key.
Why: Timeline: charge for order 500 succeeds at 10:00:00.5, crash at 10:00:00.6 before the commit at 10:00:01. The new consumer polls from 500 and calls the provider again. Without the key, the customer sees two charges and a support ticket. With order_id as the idempotency key, the provider says "already charged, here's the original result," the consumer commits, and the customer sees one charge.
Staff: Write the result and a processed(order_id) row in one transaction (or an outbox), and run a reconciliation job against the provider.

Q: The consumer checks its own DB for the idempotency key, charges, then crashes before writing the row. What happens?
A: The replay finds no row and charges again. Check-then-act in your own DB races with the crash; put the key at the provider instead.
Why: Timeline: check DB for order 500, no row. Call provider, charge succeeds. Crash before `INSERT processed (500)`. Replay: check DB, still no row, charge again. The gap between the external call and your write is where the duplicate hides, and you can't make them one transaction. The provider sees both calls, so it's the one place that can dedupe.

Q: Does Kafka's exactly-once (idempotent producer + transactions) prevent a duplicate charge to an external API?
A: No. It covers Kafka-to-Kafka only (read, process, write to another topic). Side effects outside Kafka need an idempotent consumer.
Why: Kafka transactions make "consume from topic A, produce to topic B, commit offset" atomic, because Kafka controls all three. A Stripe call isn't inside that transaction. If the consumer charges and the transaction aborts, Kafka rolls back the offset and the produce, but Stripe already took the money, and the replay charges again.

## Replication & durability
Q: RF=3, acks=1. The leader acks a write and dies before followers copy it. What happens?
A: The message is lost, and the producer won't resend because it already got a success.
Why: Timeline: producer sends, leader writes to its log and replies OK at 10:00:00.1. The producer moves on. Leader's disk dies at 10:00:00.2, before followers fetched the message. A follower is elected leader with a log that ends one message earlier. That message exists nowhere. The producer's retry logic never fires because, from its view, nothing failed.

Q: What does acks=all actually wait for?
A: The in-sync replicas (ISR), not all replicas. If the ISR has shrunk to just the leader, acks=all is no safer than acks=1.
Why: RF=3, but one follower is down and another is lagging, so the ISR is just the leader. acks=all waits for every ISR member, which is one broker. The leader acks, dies, and the message is gone, same as acks=1. The setting only means "all the replicas that are currently keeping up," which can be one.

Q: What setting stops acks=all from silently accepting writes with only one copy?
A: min.insync.replicas=2 (with RF 3). Below 2 in-sync replicas, the broker rejects writes. The cost is availability: the producer sees errors instead of silent loss.
Why: Same scenario, ISR shrunk to the leader. With min.insync.replicas=2, the leader refuses the write with NotEnoughReplicas. The producer retries or fails loudly. Orders queue up and someone gets paged, but no acked message is ever on only one disk. That's the trade: a visible outage instead of an invisible loss.
Flip: For pings or metrics where loss is fine, leave it at 1 and keep writing.

Q: What's the standard durable Kafka setup?
A: RF 3, acks=all, min.insync.replicas=2, idempotent producer, unclean leader election off. It survives one broker loss with no data loss and no write outage.
Why: Walk one broker dying. RF 3 means two copies remain. min.insync=2 means every acked write was on at least two, so a surviving copy has everything. acks=all meant the producer waited for those two. Unclean election off means a lagging replica can never become leader and drop acked data. The idempotent producer means the retry after the failover doesn't duplicate. Two brokers dying at once would halt writes (ISR < 2), which is the right failure.
Staff: Rack-aware replicas across AZs; alert on under-replicated partitions; cross-region replication is async, so state the RPO.

Q: When is acks=1 a reasonable choice?
A: For loss-tolerant, last-write-wins data like location pings that get replaced in 4 seconds. Not for orders or payments.
Why: Picture losing driver 42's 10:00:00 ping. At 10:00:04 the next one arrives and the map is correct again; nobody noticed. acks=1 bought lower latency and higher throughput for that. Now picture losing order 500: the customer paid, no one ships it, and nothing replaces it. The cost of loss decides the setting.

## Retries & DLQs
Q: A payment consumer retries a failing charge in a loop until it succeeds. What breaks?
A: Head-of-line blocking: every message behind it in the partition waits. Past max.poll.interval.ms, the consumer is kicked out and the next one hits the same message.
Why: Order 500 has an expired card. The consumer retries every second, forever. Orders 501–900 sit in the same partition behind it, unprocessed; those customers wait. At 5 minutes the consumer hasn't polled, so the broker assumes it's dead and rebalances. The new owner starts at 500 again. The partition is stuck until someone intervenes.

Q: How should a Kafka consumer handle a message that keeps failing?
A: Bounded retries with backoff, then a retry topic, then a DLQ with alerting. Commit and move on. A non-retryable error like a declined card is a business outcome, not a retry.
Why: Order 500 fails. Try 3 times with backoff (1 s, 4 s, 16 s): a transient provider blip recovers. Still failing: publish to orders-retry, commit 500, move to 501, so the partition flows. A separate consumer reads the retry topic later. Still failing after that: orders-dlq, which pages someone. A declined card is different: that's not a failure to process; the order's answer is "declined," so write that and commit.

Q: After 10 failed retries, a consumer logs the error, commits, and moves on. What's wrong?
A: Silent loss: the message is never processed and nobody finds out. Send it to a DLQ with alerting before committing.
Why: Picture order 500 failing 10 times at 3 a.m. The log line scrolls past. The offset moves on. The customer paid, the order is "pending" forever, and the first signal is a support email a week later. With a DLQ, the message lands somewhere durable, DLQ depth > 0 pages on-call, and someone replays it after fixing the cause.

Q: A consumer sleeps a fixed 60 seconds between retries of a downstream API. What's the problem?
A: Retries stay synchronized and hit the API in waves while it's still struggling. Use exponential backoff with jitter, plus a circuit breaker during an outage.
Why: The API blips at 10:00:00. All 50 consumers fail at once and sleep 60 s. At 10:01:00 all 50 retry in the same second: the API, barely recovered, gets a spike and fails again. 10:02:00, same thing. With backoff and jitter, the retries spread over 30–90 s and ramp down, so the API sees a trickle. A breaker stops calls entirely once failures cross a threshold.

## Kafka vs SQS
Q: Job 100 in a partition takes 20 minutes; 101–110 take 2 minutes and finish first. Can you commit offset 110? What if you crash now?
A: No. The commit is a watermark, and 100 isn't done. A crash replays 100 through 110.
Why: Committing 110 would say "everything through 110 is done." If you then crash at minute 15, job 100 is lost: the new consumer starts at 111. So you hold the commit at 100. Now a crash at minute 15 restarts at 100, and 101–110 run a second time even though they finished. Either way, ten 2-minute jobs are hostage to one slow one.

Q: Why is Kafka a poor fit for a work queue of 20-minute jobs?
A: One slow job pins the commit watermark and a crash replays everything after it; parallelism is capped at partitions; long processing trips max.poll.interval.ms; and there's no per-message retry or DLQ. SQS gives each job its own lease and ack.
Why: Picture 500 export jobs an hour. In Kafka: 20 partitions means at most 20 run at once. A 20-minute job holds its partition's offset, so the 9 finished jobs behind it replay if anything restarts. At minute 5 the consumer hasn't polled, so the group rebalances and the job starts over. A failing job has nowhere to go but a retry topic you build yourself. In SQS: 500 workers each take a message, extend their own lease, ack when done, and a failure goes to the DLQ after 3 tries.
Staff: Newer Kafka versions add share groups (KIP-932) with per-message acks; or Kafka carries only dispatch while a jobs table holds state.

Q: Three teams need the same events. How would you do that with SQS, and what can't you do?
A: SNS fanning out to one SQS queue per team. Messages are deleted once acked, so no team can replay history.
Why: The producer publishes to an SNS topic, which copies each event into fraud-queue, email-queue, and analytics-queue. Each team consumes and deletes its own copy. Now analytics wants last week again: the messages were deleted the moment they were acked. There's no bookmark to rewind. In Kafka the data is still on disk and the group resets its offset.

Q: When is Kafka the right choice over SQS?
A: High-throughput event streams where several consumer groups each need the full history, ordering per key, and replay.
Why: Picture clickstream events at 500k/s read by fraud, recommendations, and a data warehouse loader, with the warehouse re-loading yesterday after a bug. Kafka: one topic, three groups, each with its own bookmark, replay is an offset reset, per-user order is free from the key. SQS would need SNS fan-out into three queues, can't replay, and has no ordering on a high-throughput standard queue.
Flip: For a job queue of independent long tasks, SQS; the per-message lease and DLQ are what you need.

## Sizing
Q: 1M drivers each send a ping every 4 seconds, and a consumer handles 5k msg/s. How many partitions?
A: 250k msg/s average needs 50 consumers minimum, so at least 50 partitions. Size for peak and growth, around 150, because adding partitions later breaks key ordering.
Why: 1M / 4 s = 250k msg/s. 250k / 5k per consumer = 50 consumers, and each needs its own partition, so 50 is the floor. Rush hour is 2–3× average, so 100–150 consumers at peak, and partitions must already exist for them. Adding partitions later remaps keys and scrambles per-driver order, so pick 150 up front.
