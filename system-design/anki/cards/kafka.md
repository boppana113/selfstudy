# Kafka

## Partitions & consumer groups
Q: A topic has 6 partitions and one consumer group has 8 consumers. Who reads what?
A: Each partition goes to exactly one consumer in a group, so 6 consumers get one partition each and 2 sit idle. Parallelism inside a group is capped at the partition count.
Staff: Rebalances pause the group; cooperative-sticky assignment or static membership keeps deploys from stalling it.

Q: Same topic, 6 partitions, but 3 consumers in the group. How is work split?
A: Each consumer owns 2 partitions. One consumer can own many partitions, but a partition never has two consumers in the same group.

Q: A second consumer group subscribes to the same topic. Does it compete with the first group for messages?
A: No. Each group reads every partition independently and tracks its own offsets. That's the "stream" part: many readers, and replay by resetting offsets.

Q: Fraud, email, and analytics all read order events from one topic. Analytics wants to reprocess last week. How, without disturbing fraud?
A: Each team is its own consumer group with its own offsets. Analytics resets its group's offsets to last week's timestamp, as long as that's within retention. No new topic needed.
Staff: Tiered storage makes long retention cheap.

Q: What does a committed offset mean?
A: "This group has processed everything in this partition up to here." It's a single watermark per partition, not a per-message ack.

## Ordering & partition keys
Q: What ordering does Kafka guarantee?
A: Per partition only. Messages with the same key hash to the same partition, so they stay in order relative to each other. Across partitions there's no ordering at all.

Q: Who picks a message's partition, and how?
A: The producer's partitioner: hash(key) % numPartitions. With no key, the producer spreads messages across partitions, so you get no useful ordering.

Q: Uber driver location pings go into Kafka. What partition key, and why?
A: driver_id. It's high cardinality, so load spreads evenly, and I only need per-driver order, not order across drivers.
Staff: A log-compacted topic keyed by driver_id gives cheap "latest position" recovery for a new consumer.

Q: Why not partition the driver pings by city?
A: City is skewed: SF has tens of thousands of drivers and a small town has twenty, so one partition runs hot. One partition means one consumer, so adding consumers can't fix it. Matching should query a geo index fed from the stream instead.

Q: Why does adding partitions to a live keyed topic break ordering?
A: hash(key) % N changes, so most keys move to a new partition. During the switch, a key's older messages are still unread in the old partition while new ones land in another, read by a different consumer, so stale updates can overwrite fresh ones. Over-provision partitions up front, or migrate to a new topic.
Staff: Partitions aren't free (more leader elections and per-broker memory), so over-provisioning has a ceiling.

## Delivery semantics & idempotency
Q: A consumer uses enable.auto.commit=true and crashes mid-charge. What happens?
A: Auto-commit runs on a timer, so the offset may already be committed. The restart skips that message and the order is silently never charged. That's at-most-once.

Q: You commit only after the charge. The consumer charges, then crashes before committing. What happens, and what's the fix?
A: The next consumer re-reads from the last commit and charges the card again. That's at-least-once, the normal state for Kafka consumers. Make the consumer idempotent: pass order_id as the payment provider's idempotency key.
Staff: Write the result and a processed(order_id) row in one transaction (or an outbox), and run a reconciliation job against the provider.

Q: The consumer checks its own DB for the idempotency key, charges, then crashes before writing the row. What happens?
A: The replay finds no row and charges again: check-then-act races with the crash. Pass order_id as the payment provider's idempotency key so the provider drops the duplicate.

Q: Does Kafka's exactly-once (idempotent producer + transactions) prevent a duplicate charge to an external API?
A: No. It only covers Kafka-to-Kafka (read, process, write to another topic). Side effects outside Kafka need an idempotent consumer.

## Replication & durability
Q: RF=3, acks=1. The leader acks a write and dies before followers copy it. What happens?
A: The message is lost. The producer won't resend, because it already got a success ack.

Q: What does acks=all actually wait for?
A: The in-sync replicas (ISR), not all replicas. If the ISR has shrunk to just the leader, acks=all is no safer than acks=1.

Q: What setting stops acks=all from silently accepting writes with only one copy?
A: min.insync.replicas=2 (with RF 3). Below 2 in-sync replicas, the broker rejects writes with NotEnoughReplicas. That trades availability for durability: the producer sees errors instead of silent loss.

Q: What's the standard durable Kafka setup?
A: RF 3, acks=all, min.insync.replicas=2, idempotent producer, unclean leader election off. It survives one broker loss with no data loss and no write outage.
Staff: Rack-aware replicas across AZs; alert on under-replicated partitions; cross-region replication is async, so state the RPO.

Q: When is acks=1 a reasonable choice?
A: For loss-tolerant, last-write-wins data, like location pings that are replaced in 4 seconds. Not for orders or payments.

## Retries & DLQs
Q: A payment consumer retries a failing charge in a loop until it succeeds. What breaks?
A: Head-of-line blocking: every message behind it in the partition waits. If the loop runs past max.poll.interval.ms, the consumer is kicked from the group, and the next consumer hits the same message.

Q: How should a Kafka consumer handle a message that keeps failing?
A: Bounded retries with backoff, then publish it to a retry topic and finally a DLQ, commit, and move on. Treat a non-retryable error like a declined card as a business outcome, not a retry.

Q: After 10 failed retries, a consumer logs the error, commits, and moves on. What's wrong?
A: Silent loss: that message is never processed and nobody finds out. Send it to a DLQ with alerting before committing.

Q: A consumer sleeps a fixed 60 seconds between retries of a downstream API. What's the problem?
A: Retries stay synchronized and hit the API in waves while it's struggling. Use exponential backoff with jitter, and a circuit breaker during an outage.

## Kafka vs SQS
Q: Job 100 in a partition takes 20 minutes; 101–110 take 2 minutes and finish first. Can you commit offset 110? What if you crash now?
A: No. The commit is a watermark, and 100 isn't done. A crash replays 100 through 110.

Q: Why is Kafka a poor fit for a work queue of 20-minute jobs?
A: One slow job pins the commit watermark, and a crash replays everything after it. Parallelism is capped at the partition count. Processing past max.poll.interval.ms triggers a rebalance and duplicate work. There's no per-message retry or DLQ. SQS gives per-message leases and acks.
Staff: Newer Kafka versions add share groups (KIP-932) with per-message acks; or Kafka carries only dispatch while a jobs table holds state.

Q: Three teams need the same events. How would you do that with SQS, and what can't you do?
A: SNS fanning out to one SQS queue per team. Messages are deleted once acked, so no team can replay history.

Q: When is Kafka the right choice over SQS?
A: High-throughput event streams where several consumer groups each need the full history, ordering per key, and replay.

## Sizing
Q: 1M drivers each send a ping every 4 seconds, and a consumer handles 5k msg/s. How many partitions?
A: 1M / 4 = 250k msg/s average. 250k / 5k = 50 consumers minimum, and partitions must be at least the consumer count. Size for peak (2–3× average) and growth, around 150 partitions, because adding partitions later breaks key ordering.
