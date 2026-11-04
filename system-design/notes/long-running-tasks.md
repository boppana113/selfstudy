# Managing Long-Running Tasks

## Drill: 2026-11-01 (score 42%)
### Still weak
- ✅ (2026-11-03) Visibility timeout mechanics: thought the queue tracks which worker holds a job; it's a lease (message invisible for N s, reappears if not deleted/extended)
- ✅ (2026-11-03) Heartbeats = extending visibility timeout + writing last_heartbeat to jobs table; didn't name the consequence of timeout < job duration (duplicate processing, duplicate emails)
- Idempotency under at-least-once: partial completion (check each output / manifest), deterministic output keys, conditional status update gating notifications, ack last
- ✅ (2026-11-03) Misconception: thought the queue checks the DB before reassigning; SQS knows nothing about the jobs table
- SQS vs Kafka for jobs: no knowledge of Kafka offsets/partitions, head-of-line blocking, partition-capped parallelism
- 🟡 (2026-11-03: scaling metric fixed, alarm still wrong) Autoscaling: said raw queue depth; better is backlog per worker + age of oldest message
- ✅ (2026-11-03) Lambda 15-min limit vs 10-min jobs not considered
- Estimation: jumped to a number without math (fixed when prompted, Little's Law); poll-load math wrong (should be 1,667/30 ≈ 55 QPS)
- ✅ (2026-11-03, presigned upload) Missed in initial design: presigned upload to blob storage, how client learns completion
### Solid
- Async pattern: job id + DB row + queue + worker pool; why not in-request
- DLQ after max retries
- Polling as default for status, justified by tab-close / DB source of truth
### Interview-ready lines
- "The message goes invisible on receive; the worker extends the timeout as a heartbeat, and if it dies the message reappears for another worker."
- "Delivery is at-least-once, so I make each step idempotent: deterministic output keys, skip work already done, and a conditional status update that gates the notification."
- "Long independent jobs want per-message acks, so SQS. Kafka's offset-per-partition model gives head-of-line blocking and caps parallelism at the partition count."
- "Scale on backlog per worker; alarm on age of oldest message."
- "Arrival rate times duration: 3 per second times 600 seconds, about 1,700 workers."
- "I'd poll a status endpoint: about 50 QPS of key lookups, stateless, survives tab close. Email on completion; SSE only if we need live progress."
### Hold-in-mind questions
- A worker crashes after writing 3 of 5 outputs. Walk the timeline until the user has exactly one correct result and one notification.
- What goes wrong if visibility timeout < job duration, and what are the two fixes?
- Why is Kafka a poor fit for 20-minute jobs?
- What metric do you autoscale workers on, and what do you alarm on?
### Delivery
- Habit: conclusions without the reasoning ("you need roughly 2000 to 3000 workers"; one-sentence failure-mode answer). Show the math / walk the timeline out loud.
- Rewrite (Round 1): "This work takes 5 to 20 minutes and an HTTP request times out in about 30 seconds, so I'd make it async. The client gets a presigned URL and uploads straight to S3, then calls the API, which writes a job row as pending, drops the job ID on SQS, and returns the ID right away. Workers pull from the queue, transcode, and write outputs to S3 under the job ID, extending the visibility timeout as a heartbeat so if one dies the job reappears. When done, the worker marks the job completed; the client is polling a status endpoint and picks it up, and we email them in case they closed the tab."

## Drill: 2026-11-03 (score 50%)
### Questions
**R1 (Failure mode) 🟡**: A transcoding worker writes 3 of 5 renditions to S3, then crashes. Walk the timeline until the user has exactly one correct result and one notification.
- Follow-up: The first worker was only in a GC pause and finishes too. How do you get one set of files and one email?
- You said: The message becomes visible again, another worker redoes all five and marks the job completed. Follow-up: whoever finishes first updates the DB, and the other worker can't upload to S3.
- Strong answer: "The worker stops heartbeating, so the visibility timeout expires and the message reappears. Worker B picks it up, sees renditions one to three already exist under deterministic keys like outputs/{job_id}/720p, and only does four and five. Then it runs a conditional update, set completed where status is processing. If it gets one row back, it won and sends the email. If the original worker wakes up, S3 accepts its upload, but that's a harmless overwrite of the same key, and its status update hits zero rows, so it stays quiet. The message gets deleted last."

**R2 (Explain it) ✅**: What goes wrong when the visibility timeout is shorter than the job, and what are the two fixes?
- Follow-up: What actually happens to the message if you don't fix it, and what does a 30-minute fixed timeout cost you?
- You said: Fix 1 is heartbeating to extend the timeout. Fix 2 is setting the timeout to the expected duration plus a buffer. Without a fix, SQS makes the message visible and another worker takes it. The long timeout means slow detection of a dead worker.
- Strong answer: "The message reappears while the first worker is still running, so two workers transcode the same job: double compute, duplicate writes, and duplicate emails unless the status update gates it. If every attempt overruns, the receive count climbs until a healthy job lands in the DLQ. I'd keep a short lease, like five minutes, and heartbeat with ChangeMessageVisibility every 90 seconds or so. A long fixed timeout, like p99 plus 50%, is simpler, but a dead worker's job sits there for the whole timeout before anyone retries."

**R3 (Tradeoff duel) ❌**: The team already runs Kafka and wants the 20-minute transcode jobs on a Kafka topic instead of SQS. Agree?
- Follow-up: Ops overhead doesn't apply since Kafka already exists. Given that consumers commit an offset per partition, what goes wrong when one job takes 20 minutes and the ones behind it take 2?
- You said: Disagree, because SQS does the job without the overhead of running a cluster. Follow-up: didn't know.
- Strong answer: "I'd still use SQS. Kafka is a log: a consumer commits an offset meaning everything up to here is done, so if job 100 takes 20 minutes, I can't commit 101 to 110 even after they finish, and a crash replays all of them. Parallelism is capped at the partition count, so 2,400 concurrent jobs would need 2,400 partitions. A consumer that doesn't poll within max.poll.interval.ms gets kicked out and rebalanced, which causes duplicates. And there's no per-message retry or DLQ. SQS gives per-message leases and acks, and I scale by adding workers. Kafka is great for high-throughput event streams, not for a work queue of long jobs."

**R4 (Scale it up) 🟡**: What metric do you autoscale workers on, and what do you alarm on so you're paged before users notice?
- Follow-up: 10 of 50 workers are stuck and backlog per worker looks normal, but jobs wait an hour. What metric shows how long users are waiting?
- You said: Scale on queue depth per worker against a single threshold, and alarm when that spikes. Follow-up: total queue size over time.
- Strong answer: "I scale on backlog per worker, with separate scale-out and scale-in thresholds and a cooldown so it doesn't flap. On scale-in I protect busy workers or let them drain, since killing a 20-minute job wastes it. I page on age of the oldest message, tied to the SLA. That's the unluckiest user's wait, and it catches stuck workers and poison messages even when backlog looks fine. I'd also alarm on DLQ depth and stale heartbeats."

**R5 (Estimation) ❌**: 5 uploads per second at peak, 8-minute average transcode, one job per worker. How many workers at peak, and how many would you provision?
- Follow-up: The first five jobs take 8 minutes. Who picks up the five that arrive in second two?
- You said: 5 workers, provision 7. After the walkthrough: 5 × 60 × 8 = 2,400, plus 30–40% headroom, so over 3,000.
- Strong answer: "Little's Law: arrival rate times duration. 5 per second times 480 seconds is 2,400 jobs in flight, so 2,400 busy workers. With about 25% headroom for long jobs and spikes, around 3,000. That's expensive enough to make me look at GPU transcoding or spot instances, which is safe because retries are idempotent."

**R6 (Spot the flaw) ✅**: What's wrong with this design?
```
1. Client POSTs the raw video (up to 2 GB) to the API server
2. API server saves it to S3, inserts job row (pending), sends job ID to SQS
3. SQS triggers a Lambda function to transcode the video (jobs take 5–20 min)
4. Lambda receives the message, deletes it from SQS, then starts transcoding
5. Lambda writes outputs to S3 and marks the job completed
```
- Follow-up: With Fargate in place of Lambda but the same step 4, the worker crashes at minute 10. What happens to the job?
- You said: Use a presigned URL so the client uploads to S3 directly, then calls the API to start the job. Lambda times out at 15 minutes, so use ECS Fargate. Called steps 4 and 5 fine at first. Follow-up: don't delete; keep the message invisible with heartbeats so it reappears if the worker dies.
- Strong answer: "I see three problems. First, 2 GB through the API server ties up connections, so I'd hand out a presigned multipart URL and have the client call POST /jobs with the object key. Second, Lambda has a 15-minute hard limit, so 20-minute jobs fail every time; I'd use Fargate or EC2 workers polling SQS. Third, deleting on receive is at-most-once: a crash loses the job silently and it stays pending forever. I'd heartbeat, write outputs, do the conditional status update, and delete last. I'd also add a DLQ and a status endpoint plus email for completion."

### Still weak
- Gating the notification: thought S3 would block the second worker's upload. It won't; use a conditional status update (`WHERE status='processing'`, 1 row affected → send email), deterministic keys, skip finished renditions, delete last
- Kafka for jobs (2nd miss): offset commit per partition → head-of-line blocking, parallelism capped at partition count, `max.poll.interval.ms` rebalance → duplicates, no per-message retry/DLQ. Right conclusion, wrong reason ("ops overhead")
- Alarm metric: said total queue size; should be age of oldest message (tied to SLA). Also didn't mention scale-in hysteresis and draining or protecting in-flight 20-min jobs
- Estimation (2nd miss): dropped duration from Little's Law (said 5 workers for 5/s × 8 min). Fixed after the hint: 2,400 in flight, ~3,000 with headroom
- Didn't name the consequence before the fix: delete-on-receive = job silently lost; lease < duration = duplicate work and healthy jobs ending up in the DLQ
### Now solid
- Lease plus heartbeat, and the tradeoff of a long fixed timeout (slow failure detection)
- Presigned upload to S3; Lambda 15-min limit → Fargate/EC2 workers
- Scale on backlog per worker
### Interview-ready lines
- "Delivery is at-least-once, so I make the retry idempotent: deterministic output keys, skip renditions that already exist, and a conditional status update so only one worker wins and sends the email. I delete the message last."
- "Long, independent jobs want per-message acks and leases, so SQS. Kafka commits an offset per partition, which means one 20-minute job blocks the commits behind it, and parallelism is capped at the partition count."
- "I scale on backlog per worker, with separate scale-out and scale-in thresholds so it doesn't flap, and I page on age of the oldest message, because that's what users actually feel."
- "Arrival rate times duration: 5 per second times 480 seconds is 2,400 jobs in flight, so about 3,000 workers with headroom."
- "Deleting on receive makes it at-most-once, so a crash loses the job silently. I delete only after outputs and status are committed."
### Hold-in-mind questions
- Two workers both finish the same job. What exactly makes sure only one email goes out?
- Job #100 in a Kafka partition takes 20 min and #101–110 take 2 min. What happens to offsets, and what happens on a crash?
- 5 jobs/s, 8-minute average: how many workers, said in the order rate × seconds → number?
- What do you page on for a job queue, and why isn't queue size enough?
### Delivery
- Habit (RECURRING, 5th session across topics): the reasoning stays unsaid. You jump to the number or the fix and skip the setup or the consequence ("you need a minimum of five workers"; "I would look at the total queue size"; R2 went straight to fixes). Word choice: "enqueue/dequeue workers" → "scale out/in"; "liveness check" → "visibility timeout expires."
- Rewrite (Round 1): "Okay, the worker dies after three of five renditions. One: it stops heartbeating, so the visibility timeout expires and the message reappears. Two: worker B picks it up, sees renditions one to three already exist under the job's deterministic keys, and only does four and five. Three: it runs a conditional update, set completed where status is processing. It gets one row back, so it's the winner and it sends the email. If the original worker was just paused and wakes up, its update hits zero rows, so it stays quiet. Four: B deletes the message last. So one set of files and one email."
- Did well: honest "I don't know" instead of bluffing; R2 and R6 were concise and well structured

## Practice: 2026-11-03 (delivery only, ungraded)
Prompt: "A video takes 10 minutes to transcode. Why not do it inside the upload request?" Answered with the failure-mode frame over four tries.
### Delivery
- Better: consequence before the fix (timeout → false negative), narrated in steps ("first... then...").
- Still weak: the fix stopped at the presigned upload twice (upload and processing are separate problems); answered the worker side instead of the question asked (what the API returns, how the user learns it's done); "provision a job" → workers pull; "liveness check-in" → "extends the visibility timeout as a heartbeat".
- Rewrite: "If we transcode inside the upload request, it times out at the gateway after about 30 seconds. The work might still finish, so the user sees a failure that's actually a false negative, and when they retry, we transcode twice. So I'd make it async. The client uploads straight to S3 with a presigned URL, then calls POST /jobs. The API writes a job row as pending, puts the job ID on SQS, and returns the ID right away. A worker pulls the message, marks the job in progress, and extends the visibility timeout as a heartbeat while it transcodes. When it's done, it marks the job complete and deletes the message. The client polls a status endpoint with the job ID, and we email them in case they closed the tab."
