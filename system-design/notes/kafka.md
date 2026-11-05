# kafka

## Drill: 2026-11-04 (score 42%)
### Questions
**R1 (Explain it) ❌**: Explain on a whiteboard, in about 60 seconds, how a Kafka topic gets from a producer to a group of consumers. Cover partitions, offsets, consumer groups, and the ordering you get.
- Follow-up: 3 consumers and 6 partitions: how is work divided, and what happens if the group grows to 7 or 8 consumers? What ordering guarantee do you get?
- You said: Producer → key → partition (the log) → consumer group processes → commits offset. Follow-up: "one or more consumers per partition"; adding consumers rebalances to cover more; ordering is "in the order events come in to the topic."
- Strong answer: "The producer hashes the key to pick a partition, and each partition is an append-only log. Within a consumer group, each partition goes to exactly one consumer, though one consumer can own several. So with 6 partitions and 3 consumers, each gets 2; add a 7th and 8th and those two sit idle, because parallelism is capped at the partition count. Consumers commit an offset per partition, which is how far they've processed. Ordering is per partition only: same key, same partition, so in order; across partitions there's no ordering. Other consumer groups read the same log independently with their own offsets."

**R2 (Scenario) 🟡**: Uber driver phones send a location update every 4 seconds into Kafka. What partition key, and why?
- Follow-up: The matching team wants to partition by city so one consumer sees all of SF. What goes wrong?
- You said: driver_id, so a driver's events stay in order. Follow-up: one consumer owns a whole city, a backlog builds, and if it fails messages go unprocessed.
- Strong answer: "driver_id. It's high cardinality, so load spreads evenly, and I only need per-driver ordering. City is badly skewed: SF has tens of thousands of drivers and a small town has twenty, so one partition runs hot, and since a partition has one consumer, adding consumers doesn't help. A consumer failure isn't the issue, since rebalancing reassigns the partition. Matching shouldn't read Kafka by city; a consumer writes latest positions into a geo index like Redis GEO or H3 cells, and matching queries that. Location pings are last-write-wins, so delivery semantics can be relaxed."

**R3 (Spot the flaw) 🟡**: What's wrong with this payment consumer?
```
topic: orders   (12 partitions, key = order_id)
consumer group: payment-service
  enable.auto.commit = true   (commits every 5s)
  for each message:
      charge the card via the payment provider
      if the charge call fails: retry in a loop until it succeeds
```
- Follow-up: You commit only after the charge succeeds. The consumer charges, then crashes before committing. What happens, and what does the customer see?
- You said: Auto-commit commits before processing, so commit after the charge; the retry loop retries forever. Follow-up: use an idempotency key so the customer is charged once.
- Re-answer: Reasoning didn't come through. Both steps were fixes ("commit after processing", "check the idempotency key"); never said "the customer is charged twice."
- Strong answer: "Auto-commit runs on a timer, so a crash after the commit but mid-charge skips the message and the order is silently never charged: at-most-once. Committing after processing makes it at-least-once: crash before commit, the message replays, and the customer is charged twice. So I'd make the consumer idempotent with order_id as the provider's idempotency key; Kafka's exactly-once only covers Kafka-to-Kafka, not an external API. The infinite retry loop blocks the whole partition and, past max.poll.interval.ms, gets the consumer kicked from the group, so I'd do bounded retries with backoff, then a retry topic and a DLQ."

**R4 (Tradeoff duel) 🟡**: The team runs Kafka and wants 20-minute transcode jobs on a topic instead of SQS. Job 100 takes 20 min, and 101–110 take 2 min each. Agree? What happens to offsets?
- Follow-up: 101–110 finish while 100 is at minute 15. Can you commit offset 110? If it crashes then, which jobs rerun?
- You said: Disagree; SQS with visibility-timeout heartbeats and a DB status update fits. Follow-up: can't commit 110 because 100 isn't done; a crash reprocesses 100–110.
- Strong answer: "I'd keep SQS. A Kafka commit is a per-partition watermark meaning everything up to here is done, so one 20-minute job pins it, and a crash replays everything after it. Parallelism is capped at the partition count, so thousands of concurrent jobs means thousands of partitions. A job processed inline past max.poll.interval.ms gets the consumer kicked from the group, which rebalances and duplicates work. And there's no per-message retry or DLQ. SQS gives per-message leases and acks, so I scale by adding workers. Kafka is for high-throughput streams with replay and many consumer groups."

**R5 (Failure mode) 🟡**: RF=3, producer acks=1. The leader for partition 4 acks a write and dies before followers copy it. What happens, and what would you change?
- Follow-up: With acks=all, if both followers fall out of the ISR and only the leader is left, are you still protected? What setting closes that gap?
- You said: The message is lost; the producer could resend; make the leader wait for replicas before acking. Follow-up: acks=all won't protect "because it only syncs new messages"; find a way to catch up replicas.
- Strong answer: "The message is gone, and the producer won't resend because it already got a success ack. acks=all waits for the in-sync replicas, not all replicas, so if the ISR shrinks to just the leader, it's no better than acks=1. The fix is min.insync.replicas=2 with RF 3: if fewer than two replicas are in sync, the broker rejects writes with NotEnoughReplicas, trading availability for durability. Keep unclean leader election off so an out-of-sync follower can't become leader and drop acked data. With an idempotent producer, retries don't create duplicates. acks=1 is fine for loss-tolerant data like location pings."

**R6 (Estimation) 🟡**: 1M active drivers, an update every 4 s, one consumer handles 5k msg/s. Minimum partitions, and what would you provision?
- Follow-up: Drivers double next year, so you want 130 partitions. What goes wrong increasing partitions on a live topic keyed by driver_id?
- You said: 250k msg/s ÷ 5k = 50 consumers, +30% for failures = 65, partitions = consumers = 65. Follow-up: existing hash assignments could create hot partitions.
- Strong answer: "1M over 4 seconds is 250k messages a second on average, maybe 2–3× at peak. At 5k per consumer that's 50 consumers minimum, and partitions have to be at least the consumer count. I'd provision around 150 partitions for peak and growth, because adding partitions later changes hash mod N, which moves most drivers to new partitions. During the switch, a driver's old updates are still in the old partition while new ones land elsewhere, so per-driver ordering breaks and a stale position can overwrite a fresh one. If I had to grow, I'd migrate to a new topic, or rely on sequence numbers so consumers drop stale updates."
### Still weak
- Consumer group assignment was backwards (thought several consumers share a partition); extra consumers beyond the partition count sit idle
- Ordering scope: said topic-wide; it's per partition (per key)
- Hot partitions: framed the city key as a failure risk; the real issue is skew that adding consumers can't fix
- Delivery semantics: no consequences stated (auto-commit → silent loss; commit-after → double charge); missed retry topic/DLQ for poison messages
- Durability: didn't know ISR, min.insync.replicas=2, unclean leader election; thought the producer would resend after an ack
- Repartitioning: thought the issue is hot partitions; really, key remapping breaks per-key ordering → over-provision partitions
- Estimation: average only, not peak
### Interview-ready lines
- "Within a group, each partition has exactly one consumer, so parallelism tops out at the partition count, and extra consumers sit idle."
- "Ordering is per partition, so I key by the entity whose events must stay in order."
- "City-level keys create hot partitions that adding consumers can't fix, because one partition means one consumer."
- "Kafka is at-least-once: I commit after processing and make the consumer idempotent with order_id as the payment provider's idempotency key."
- "Bounded retries, then a retry topic and a DLQ, so one poison message can't block the partition."
- "RF 3, acks=all, min.insync.replicas 2: an acked write survives a broker loss, and the producer gets errors instead of silent loss."
- "Adding partitions remaps keys and breaks per-key ordering, so I size partitions for peak and growth up front."
### Hold-in-mind questions
- 6 partitions, 8 consumers in one group: who reads what?
- acks=all, but the ISR has shrunk to the leader alone: is an acked write safe? What setting fixes it?
- A consumer charges a card, then crashes before committing. Say it in order: what happens, what the customer sees, the fix.
- Why does adding partitions to a keyed topic break ordering, and how do you avoid it?
### Delivery
- Habit (RECURRING, 6th session): fix before consequence. R3: "I would fix it by having the producer make an idempotency key"; the re-answer was still two fixes, never "the customer is charged twice." R5: "I would look for a way to catch up the replicas" (a hedge where a setting or reasoning belonged).
- Rewrite (R3): "There are three problems. First, auto-commit runs on a timer, so the offset can commit before the charge finishes. If the consumer crashes then, the restart skips that message and the order is never charged, silently. If I commit after charging instead, a crash before the commit replays the message and the customer gets charged twice. So I'd commit after processing and pass order_id as the payment provider's idempotency key. Third, the retry loop: one card that keeps failing blocks everything behind it in the partition, so I'd do a few retries with backoff, then send it to a retry topic and a DLQ, and move on."
- Did well: R4 follow-up and R6 were concise, mechanism first, consequence included; R6 used the estimation frame unprompted.
- Frame reminders: on (re-answers: 1)
