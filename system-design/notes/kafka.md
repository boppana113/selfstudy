# kafka

## Drill: 2026-11-04 (score 42%; Below mid 1 · Mid 5 · Senior 0 · Staff 0)
### Questions
**R1 (Explain it) ⬜ Below mid**: Explain on a whiteboard, in about 60 seconds, how a Kafka topic gets from a producer to a group of consumers. Cover partitions, offsets, consumer groups, and the ordering you get.
- Follow-up: 3 consumers and 6 partitions: how is work divided, and what happens if the group grows to 7 or 8 consumers? What ordering guarantee do you get?
- You said: Producer → key → partition (the log) → consumer group processes → commits offset. Follow-up: "one or more consumers per partition"; adding consumers rebalances to cover more; ordering is "in the order events come in to the topic."
- Strong answer: "The producer hashes the key to pick a partition, and each partition is an append-only log. Within a consumer group, each partition goes to exactly one consumer, though one consumer can own several. So with 6 partitions and 3 consumers, each gets 2; add a 7th and 8th and those two sit idle, because parallelism is capped at the partition count. Consumers commit an offset per partition, which is how far they've processed. Ordering is per partition only: same key, same partition, so in order; across partitions there's no ordering. Other consumer groups read the same log independently with their own offsets."
- Staff adds: watch consumer lag per partition as the scaling signal; rebalances pause consumption, so use cooperative-sticky assignment or static membership to keep deploys from stalling the group.

**R2 (Scenario) 🟦 Mid**: Uber driver phones send a location update every 4 seconds into Kafka. What partition key, and why?
- Follow-up: The matching team wants to partition by city so one consumer sees all of SF. What goes wrong?
- You said: driver_id, so a driver's events stay in order. Follow-up: one consumer owns a whole city, a backlog builds, and if it fails messages go unprocessed.
- Strong answer: "driver_id. It's high cardinality, so load spreads evenly, and I only need per-driver ordering. City is badly skewed: SF has tens of thousands of drivers and a small town has twenty, so one partition runs hot, and since a partition has one consumer, adding consumers doesn't help. A consumer failure isn't the issue, since rebalancing reassigns the partition. Matching shouldn't read Kafka by city; a consumer writes latest positions into a geo index like Redis GEO or H3 cells, and matching queries that. Location pings are last-write-wins, so delivery semantics can be relaxed."
- Staff adds: a log-compacted topic keyed by driver_id gives cheap "latest position" recovery for a new consumer; at global scale, run regional clusters so a driver's pings never cross regions.

**R3 (Spot the flaw) 🟦 Mid**: What's wrong with this payment consumer?
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
- Staff adds: write the charge result and a processed(order_id) row in one transaction (or an outbox), run a reconciliation job against the provider, alert on DLQ depth and consumer lag, and treat a declined card as a business outcome, not a retry.

**R4 (Tradeoff duel) 🟦 Mid**: The team runs Kafka and wants 20-minute transcode jobs on a topic instead of SQS. Job 100 takes 20 min, and 101–110 take 2 min each. Agree? What happens to offsets?
- Follow-up: 101–110 finish while 100 is at minute 15. Can you commit offset 110? If it crashes then, which jobs rerun?
- You said: Disagree; SQS with visibility-timeout heartbeats and a DB status update fits. Follow-up: can't commit 110 because 100 isn't done; a crash reprocesses 100–110.
- Strong answer: "I'd keep SQS. A Kafka commit is a per-partition watermark meaning everything up to here is done, so one 20-minute job pins it, and a crash replays everything after it. Parallelism is capped at the partition count, so thousands of concurrent jobs means thousands of partitions. A job processed inline past max.poll.interval.ms gets the consumer kicked from the group, which rebalances and duplicates work. And there's no per-message retry or DLQ. SQS gives per-message leases and acks, so I scale by adding workers. Kafka is for high-throughput streams with replay and many consumer groups."
- Staff adds: if the org insists on one system, newer Kafka versions add share groups (KIP-932) with per-message acks, or Kafka can carry only the dispatch while a jobs table holds state; weigh that against running a second system.

**R5 (Failure mode) 🟦 Mid**: RF=3, producer acks=1. The leader for partition 4 acks a write and dies before followers copy it. What happens, and what would you change?
- Follow-up: With acks=all, if both followers fall out of the ISR and only the leader is left, are you still protected? What setting closes that gap?
- You said: The message is lost; the producer could resend; make the leader wait for replicas before acking. Follow-up: acks=all won't protect "because it only syncs new messages"; find a way to catch up replicas.
- Strong answer: "The message is gone, and the producer won't resend because it already got a success ack. acks=all waits for the in-sync replicas, not all replicas, so if the ISR shrinks to just the leader, it's no better than acks=1. The fix is min.insync.replicas=2 with RF 3: if fewer than two replicas are in sync, the broker rejects writes with NotEnoughReplicas, trading availability for durability. Keep unclean leader election off so an out-of-sync follower can't become leader and drop acked data. With an idempotent producer, retries don't create duplicates. acks=1 is fine for loss-tolerant data like location pings."
- Staff adds: rack awareness puts replicas in different AZs; alert on under-replicated partitions; acks=all costs a replication round trip in latency; cross-region replication (e.g. MirrorMaker) is async, so state the RPO.

**R6 (Estimation) 🟦 Mid**: 1M active drivers, an update every 4 s, one consumer handles 5k msg/s. Minimum partitions, and what would you provision?
- Follow-up: Drivers double next year, so you want 130 partitions. What goes wrong increasing partitions on a live topic keyed by driver_id?
- You said: 250k msg/s ÷ 5k = 50 consumers, +30% for failures = 65, partitions = consumers = 65. Follow-up: existing hash assignments could create hot partitions.
- Strong answer: "1M over 4 seconds is 250k messages a second on average, maybe 2–3× at peak. At 5k per consumer that's 50 consumers minimum, and partitions have to be at least the consumer count. I'd provision around 150 partitions for peak and growth, because adding partitions later changes hash mod N, which moves most drivers to new partitions. During the switch, a driver's old updates are still in the old partition while new ones land elsewhere, so per-driver ordering breaks and a stale position can overwrite a fresh one. If I had to grow, I'd migrate to a new topic, or rely on sequence numbers so consumers drop stale updates."
- Staff adds: partitions aren't free (more leader elections on broker failure, more files and memory per broker), so over-provisioning has a ceiling; plan the migration as a new topic with dual-write and a consumer cutover once the old one drains.
### Gap to senior
- Below mid: consumer group assignment was backwards (thought several consumers share a partition); extra consumers beyond the partition count sit idle
- Below mid: ordering scope, said topic-wide; it's per partition (per key)
- Durability: didn't know ISR, min.insync.replicas=2, unclean leader election; thought the producer would resend after an ack
- Delivery semantics: no consequences stated (auto-commit → silent loss; commit-after → double charge); missed retry topic/DLQ for poison messages
- Repartitioning: thought the issue is hot partitions; really, key remapping breaks per-key ordering → over-provision partitions
- Hot partitions: framed the city key as a failure risk; the real issue is skew that adding consumers can't fix
- Kafka for long jobs: got the offset watermark only after the hint; didn't volunteer the partition cap or max.poll.interval.ms rebalance
- Estimation: average only, not peak
### Staff stretch
- Consumer lag as the scaling signal; cooperative-sticky / static membership to avoid stop-the-world rebalances
- Outbox or same-transaction processed table, plus reconciliation against the payment provider
- Rack-aware replicas across AZs, under-replicated-partition alerts, cross-region RPO
- Partition count has a cost ceiling; migrate via a new topic with dual-write and cutover
- Log compaction for latest-state topics
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

## Drill: 2026-11-05 (partial, 2 of 6 rounds; not scored; Below mid 0 · Mid 1 · Senior 1 · Staff 0)
### Questions
**R1 (Explain it) 🟦 Mid**: 6 partitions, one consumer group with 8 consumers. Who reads what, and what ordering guarantee does each consumer get?
- Follow-up: "order created" and "order paid" for the same order get processed out of order. How, and how do you prevent it?
- You said: Each partition gets one consumer, so 6 work and 2 sit idle; consumer commits a sequential "commit ID". Follow-up: the events landed on different partitions; key by order so they share one.
- Strong answer: "Each partition goes to exactly one consumer in the group, so with 6 partitions and 8 consumers, two sit idle. One consumer can own several partitions, so if some die, a rebalance hands their partitions to the rest. Ordering is per partition only, with none across partitions, so I key by order_id and all of an order's events stay in sequence. The committed offset is a per-partition watermark: everything up to here is done."
- Staff adds: consumer lag per partition as the scaling signal; cooperative-sticky or static membership so rebalances don't stall deploys.

**R2 (Failure mode) 🟩 Senior**: acks=all, RF 3, both followers drop out of the ISR. A write is acked. Is it safe, and what would you change?
- Follow-up: with min.insync.replicas=2 and only the leader in sync, what does the producer see, and what are you giving up?
- You said: Not safe: only the leader has it, and if it crashes the producer never knows the write is gone. Set min.insync.replicas=2 so the broker rejects writes. Follow-up: producer's writes are rejected; "sacrificing throughput."
- Strong answer: "acks=all only waits for the in-sync replicas, so if the ISR shrinks to the leader, an acked write lives on one box, and if that box dies the write is gone with the producer believing it succeeded. I'd set min.insync.replicas=2 with RF 3, so the broker rejects writes with NotEnoughReplicas instead of losing them. The cost is write availability, not throughput: producers see errors until a follower catches up. I'd keep unclean leader election off so an out-of-sync follower can't become leader."
- Staff adds: rack-aware replicas across AZs, alert on under-replicated partitions; acks=1 is fine for loss-tolerant data like location pings.
### Gap to senior
- Say ordering scope unprompted: "per partition only, none across partitions, so I key by order_id"
- Use "offset" (not "commit ID"); it's a watermark, not a per-message ack
- Name the min.insync.replicas cost precisely: availability (writes fail), not throughput
### Resume
- ✅ Finished 2026-11-06 (R3–R6 below; full drill scored there).
### Delivery
- Habit: R1 bottom line first, then drifted into commit details nobody asked about; stop once the question is answered.
- Improved: R2 consequence before fix, unprompted: "If the leader replica crashes, then the producer has no knowledge that the message is gone."
- Frame reminders: on (re-answers: 0)

## Drill: 2026-11-06 (score 58%; Below mid 1 · Mid 3 · Senior 2 · Staff 0)
Completes the 11-05 partial drill: R1–R2 are in the entry above and counted in this score.
### Questions
**R3 (Failure mode) 🟩 Senior**: Your payment consumer commits only after the charge succeeds. It charges the card, then crashes before committing. What happens, and what does the customer see?
- Follow-up: The consumer checks your payment DB for the key, doesn't find it, charges, and crashes before writing the row. What stops the second charge?
- You said: Bottom line first: the customer gets charged twice; the partition is reassigned and the new consumer re-processes. Fix: idempotency key checked in the payment DB. Follow-up: reasoned that the payment provider keeps the key record, so it's not on our system.
- Strong answer: "Commit-after gives at-least-once. The partition is reassigned, the new consumer resumes from the last committed offset, and the charge replays, so the customer is charged twice. A check in my own DB races: charge, crash, row never written. So I pass order_id as the provider's idempotency key and the provider drops the duplicate. Kafka's exactly-once doesn't help, because it only covers Kafka-to-Kafka."
- Staff adds: reconciliation job against the provider; outbox or same-transaction processed row for our own records.

**R4 (Scale it up) 🟦 Mid**: The orders topic is keyed by order_id with 12 partitions, and traffic is about to triple. Someone proposes bumping it to 36 partitions on the live topic. What breaks?
- Follow-up: The default partitioner is hash(key) mod partition count. Where does order 123's next event land, and what if its "created" event is already in partition 5?
- You said: First: orders still go to the original 12 because the hashing stays the same (backwards); fix is a new topic with 36 partitions. Follow-up: events come out of order; fix is more compute per partition.
- Re-answer: Reasoning came through (key mod N → orders move partitions → out of order → new topic, drain old); missed what the user sees.
- Strong answer: "The partitioner is hash of the key mod the partition count, so going from 12 to 36 remaps most keys. Order 123's 'created' is still in partition 5 while 'paid' lands in partition 20, read by a different consumer, so 'paid' can be processed first and the payment is rejected or the order shows paid before it exists. I'd size partitions for growth up front. If I outgrow them, I'd make each consumer faster first (batching, a thread pool keyed by order_id), and otherwise migrate to a new topic and cut over once the old one drains."
- Staff adds: dual-write then cutover; partitions cost broker memory, files, and leader elections, so over-provisioning has a ceiling.

**R5 (Spot the flaw) 🟦 Mid**: What's wrong with this shipping-label consumer?
```
topic: shipments   (12 partitions, key = order_id)
consumer group: label-service, 20 consumers
  for each message:
      call the carrier API to create a label
      on error: sleep 60s and retry, up to 10 times
      after 10 failures: log the error, commit, move on
```
- Follow-up: One label keeps failing, so the consumer spends ~10 minutes in its retry loop. What happens to the other orders on that partition, and what does Kafka do to a consumer that hasn't polled in 10 minutes?
- You said: Fixed sleep synchronizes retries into a stampede on the carrier; use exponential backoff with jitter; after 10 failures return an error to the user (no user in an async consumer). Follow-up: the partition backs up; guessed Kafka assumes the consumer failed and restarts it, so it loops.
- Strong answer: "Three problems. The retry loop blocks the partition for ten minutes, so labels stop for every order behind it, and past max.poll.interval.ms, five minutes by default, the consumer is kicked, the partition moves, and the next consumer hits the same poison message. Log-and-commit silently drops the order: no label, and nobody knows. So I'd do two or three quick retries with jittered backoff, then a retry topic and a DLQ with alerting, and commit so the partition keeps moving. And 20 consumers on 12 partitions means 8 sit idle."
- Staff adds: alert on DLQ depth and per-partition lag; circuit breaker on the carrier API so an outage pauses consumption instead of flooding the DLQ; a DLQ replay tool.

**R6 (Tradeoff duel) ⬜ Below mid**: Order events need to reach fraud checks, the email service, and analytics, which sometimes reprocesses last week. Kafka or SQS?
- Follow-up: How does analytics rewind to last week without disturbing fraud's position, and what does Kafka cost you here?
- You said: Kafka, because it supports replay and SQS doesn't. Follow-up: analytics creates a new topic, replays onto it, and is its only consumer; cost is a new topic per team.
- Strong answer: "Kafka. Each team is its own consumer group reading the same log with its own offsets, so fraud, email, and analytics never affect each other, and a fourth team is just a new group. Analytics replays by resetting its group's offsets to last week's timestamp, as long as that's within retention, so I'd set retention to at least two weeks. SQS deletes a message once it's acked, so I'd need SNS fanning out to three queues and still couldn't replay. The cost is running Kafka, sizing partitions, and building retries and DLQs myself; for the email service alone, SQS would be simpler."
- Staff adds: tiered storage for long retention; schema registry so three teams can evolve the event format safely.
### Gap to senior
- Below mid: fan-out is one consumer group per team on the same log, each with its own offsets; replay = reset that group's offsets to a timestamp within retention. No new topic.
- Partitioner is hash(key) mod N: changing N remaps keys (they don't stay put), so per-key ordering breaks; size up front, new topic + drain to grow
- Poison message: long retry blocks the partition, and past max.poll.interval.ms the partition bounces between consumers; bounded retries → retry topic → DLQ; log-and-commit is silent loss
- Spot consumers > partitions unprompted (3rd miss): extras sit idle
- Idempotency lives at the provider (order_id as key); a local check-then-charge races
- Say what the user sees before the fix (R4, R5)
### Staff stretch
- Exactly-once covers Kafka-to-Kafka only; reconciliation against the provider
- Circuit breaker on downstream API; DLQ depth + per-partition lag alerts; DLQ replay tool
- Partition count ceiling; dual-write migration
- Tiered storage for long retention; schema registry for multi-team topics
### Interview-ready lines
- "Each team is its own consumer group with its own offsets, so analytics can rewind to last week without touching fraud."
- "The partitioner is hash of the key mod N, so changing N remaps keys and breaks per-key ordering. I size for growth up front."
- "A long retry loop blocks the partition and gets the consumer kicked, so I do a few retries, then a retry topic and a DLQ, and commit."
- "Twenty consumers on twelve partitions means eight are idle."
- "I pass order_id as the provider's idempotency key, because a check in my own DB races with a crash."
### Hold-in-mind questions
- Three teams read the same order events and one wants to replay last week. How, in Kafka, without a new topic?
- What does log-and-commit after N failures do to that message?
### Delivery
- Habit (RECURRING): consequence stops at the system view; user impact skipped. Consequence-before-fix order held all session. R4 first answer: consequence rested on a wrong mechanism ("still only go to the original 12"), then the fix; R5: "which can lead to a backlog" instead of "labels stop for every order on that partition."
- Rewrite (R6): "I'd use Kafka, because three teams need the same events and one needs replay. Each team is its own consumer group, so they read the same log with separate offsets and never step on each other. When analytics wants last week, it resets its group's offsets to that timestamp, as long as it's within retention, so I'd keep two weeks. SQS deletes a message once it's consumed, so I'd need SNS fanning out to three queues and still couldn't replay. The cost is running Kafka and building retries and a DLQ myself."
- Did well: R3 opened with the consequence unprompted ("the customer gets charged twice"), the miss from 11-04; used the unsure frame twice ("I don't know the exact mechanism, but I'd assume…").
- Frame reminders: off (re-answers: 1)
