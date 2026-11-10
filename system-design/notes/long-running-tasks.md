# Managing Long-Running Tasks

## Drill: 2026-11-01 (score 42%)
### Still weak
- ✅ (2026-11-03) Visibility timeout mechanics: thought the queue tracks which worker holds a job; it's a lease (message invisible for N s, reappears if not deleted/extended)
- ✅ (2026-11-03) Heartbeats = extending visibility timeout + writing last_heartbeat to jobs table; didn't name the consequence of timeout < job duration (duplicate processing, duplicate emails)
- Idempotency under at-least-once: partial completion (check each output / manifest), deterministic output keys, conditional status update gating notifications, ack last
- ✅ (2026-11-03) Misconception: thought the queue checks the DB before reassigning; SQS knows nothing about the jobs table
- 🟡 (2026-11-04 LRT drill: HOL unprompted, replay + partition cap after follow-up; 2026-11-04, kafka drill: offset watermark/HOL + crash replay correct after hint; partition cap still not volunteered) SQS vs Kafka for jobs: no knowledge of Kafka offsets/partitions, head-of-line blocking, partition-capped parallelism
- 🟡 (2026-11-03: scaling metric fixed, alarm still wrong) Autoscaling: said raw queue depth; better is backlog per worker + age of oldest message
- ✅ (2026-11-03) Lambda 15-min limit vs 10-min jobs not considered
- ✅ (2026-11-09) Estimation: jumped to a number without math (fixed when prompted, Little's Law); poll-load math wrong (should be 1,667/30 ≈ 55 QPS)
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
- ✅ (2026-11-04: duration included unprompted) Estimation (2nd miss): dropped duration from Little's Law (said 5 workers for 5/s × 8 min). Fixed after the hint: 2,400 in flight, ~3,000 with headroom
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

## Drill: 2026-11-04 (score 50%; Below mid 0 · Mid 4 · Senior 0 · Staff 0)
Short drill: 4 rounds, one per hold-in-mind question.
### Questions
**R1 (Estimation) 🟦 Mid**: 5 transcode jobs per second at peak, 8-minute average, one job per worker. How many workers at peak, and how many would you provision?
- Follow-up: 5/s is already the peak, so what did the formula give before doubling, and what's the headroom for?
- You said: Little's Law, 5 × 8 × 60, then doubled for peak → 4,800. Follow-up: 2,400 before doubling, +50% → "3,200" (arithmetic slip; it's 3,600).
- Re-answer: Reasoning came through (assumption → formula → buffer reason → 3,600); still skipped saying 2,400 before adding the buffer.
- Strong answer: "Little's Law: 5 per second times 480 seconds is 2,400 jobs in flight, so 2,400 busy workers at peak. I'd add about 25% for long-tail jobs, retries and scale-up lag, so roughly 3,000. At that size I'd look at spot instances, which is safe because retries are idempotent."
- Staff adds: spot/GPU cost lever; choose p50 vs p95 duration in the formula based on the tail.

**R2 (Failure mode) 🟦 Mid**: A worker GC-pauses, its lease expires, and a second worker takes the same job. Both finish. What exactly makes sure only one email goes out?
- Follow-up: Both finish in the same millisecond and both read "processing". What DB operation makes only one win, and how does the winner know to send the email?
- You said: Timeline right; the loser checks the output and can't update the DB because it's already completed. Follow-up: an ACID transaction processes one at a time, the worker checks the in-progress → completed transition, and the winner sends the email.
- Strong answer: "One email is guaranteed by a conditional update: UPDATE jobs SET status='completed' WHERE id=? AND status='processing'. The database applies it atomically, so exactly one worker gets 1 row affected. That one sends the email, and the other gets 0 and exits. Read-then-write inside a transaction isn't enough at READ COMMITTED, because both can read 'processing'. Outputs use deterministic keys, so the duplicate upload is a harmless overwrite."
- Staff adds: commit-then-send gap (crash after commit = no email) → outbox row in the same transaction or a provider idempotency key on job_id.

**R3 (Tradeoff duel) 🟦 Mid**: Team wants transcode jobs on Kafka. Job 100 takes 20 min, 101–110 take 2 min. What happens to offsets, and on a crash at minute 15?
- Follow-up: On restart, is only job 100 reprocessed? And what does 2,400 concurrent jobs force on you?
- You said: Can't commit 101–110 until 100 finishes; on crash, job 100 is reprocessed; consumers for 101–110 sit idle; recommended SQS for mixed durations. Follow-up: 100–110 all get replayed; you need more partitions.
- Strong answer: "Kafka commits one offset per partition, so a 20-minute job blocks the commits behind it, and a crash replays everything after the last commit: 100 through 110. Each partition is read by exactly one consumer per group, so parallelism is capped at the partition count, and 2,400 concurrent jobs means about 2,400 partitions. A slow consumer also trips max.poll.interval.ms and causes a rebalance and duplicates. Long independent jobs want per-message leases and acks, so SQS."
- Staff adds: Kafka as intake log with a bridge to SQS/jobs table; KIP-932 share groups.

**R4 (Failure mode) 🟦 Mid**: 50 workers, 10 hung on a poison video, backlog per worker looks normal, jobs wait an hour. What pages you, and why isn't queue size enough?
- Follow-up: Why average rather than oldest? If hung workers keep heartbeating, does retries-per-job ever fire?
- You said: Average job wait time plus retries per job; queue size isn't enough because the other 40 still drain. Follow-up: switched to oldest-job wait; for heartbeating hung workers, watch processing time per worker.
- Strong answer: "I page on age of the oldest message, because that's the worst wait a user is feeling right now and maps to the SLA. An average hides the tail. Depth doesn't show throughput: 10 of 50 hung is 20% less capacity, so wait grows while depth per worker looks fine. To stop hung jobs from holding leases forever, I cap runtime at about 3× p99 and count a timeout as a failed attempt, so poison videos land in the DLQ, and I alarm on DLQ depth."
- Staff adds: progress-based heartbeats (frames done, not just alive); quarantine poison inputs.
### Gap to senior
- Gating the notification: single conditional UPDATE + rows affected = 1, not "ACID transaction" / read-then-write
- 🟡 (2026-11-09: partition cap volunteered, max.poll consequence named; mechanisms still vague, no decision-first) Kafka specifics: one consumer per partition per group; parallelism = partition count (~2,400); max.poll.interval.ms rebalance
- Paging: lead with age of oldest message + why (worst-case wait = SLA); max-runtime cap for hung-but-heartbeating workers
- ✅ (2026-11-09) Estimation: don't double an already-peak rate; say the intermediate number; do the headroom arithmetic out loud
### Staff stretch
- Outbox / email idempotency key for the commit-then-send gap
- Kafka intake log → bridge to queue; KIP-932 share groups
- Progress heartbeats; spot instances because retries are idempotent
### Interview-ready lines
- "Completion is a conditional update, set completed where status is processing. The worker that gets one row back sends the email."
- "Each partition has one consumer per group, so parallelism equals the partition count: 2,400 jobs means 2,400 partitions. That's why long jobs go on SQS."
- "I page on age of the oldest message, because that's the worst wait a user feels, and I cap job runtime so hung workers fail over to the DLQ."
- "5 per second times 480 seconds is 2,400 in flight, plus 25% headroom, so about 3,000."
### Delivery
- Habit: vague words where the specific mechanism belongs ("ACID transaction to ensure only one is processed", "add more partitions", "job wait time on average"). Structure improved: timelines narrated in order, method stated first in R1/R3.
- Rewrite (R2): "One email is guaranteed by a conditional update. Here's the timeline. Worker A pauses in GC, its lease expires, and the message reappears. Worker B picks it up and transcodes. Outputs go to deterministic keys, so if A wakes up and uploads too, it's just an overwrite. When each one finishes, it runs update jobs set completed where id is the job and status is processing. The database applies that atomically, so exactly one gets one row back. That worker sends the email, and the other gets zero rows and exits quietly. Then the message is deleted last."
- Did well: opened R1 and R3 with the method/conclusion; R1 re-answer used the whole frame.
- Frame reminders: on (re-answers: 1)

## Drill: 2026-11-09 (score 58%; Below mid 0 · Mid 5 · Senior 1 · Staff 0)
New scenario: report exports (~10-min PDF build, email a link).
### Questions
**R1 (Failure mode) 🟦 Mid**: Report export worker's lease expires mid-job, a second worker picks it up, both finish within the same second. Walk through what happens and what makes sure the user gets exactly one email.
- Follow-up: Both alive, both see the PDF exists. What exact DB operation decides who emails, and does the email go before or after it?
- You said: Reframed as worker A emails then crashes before the DB update → user sees a second email; fix = check output exists, skip the PDF, update DB. Follow-up: conditional update in-progress → complete, only one succeeds; email goes *before* the update; email service gets an idempotency key on job ID.
- Strong answer: "Both workers upload to the same deterministic key, so the second upload is a harmless overwrite. Then each runs update jobs set completed where id is the job and status is processing. The database applies that atomically, so exactly one gets one row back. That worker sends the email, keyed on job ID so its own retry can't double-send. The other gets zero rows and exits quietly. If the email went before the update, both would send and the update would protect nothing."
- Staff adds: commit-then-send gap → outbox row in the same transaction or sweeper for completed-but-not-notified.

**R2 (Scale it up) 🟦 Mid**: Team runs Kafka; export topic has 12 partitions; peak needs ~500 concurrent. What happens when you scale consumers up?
- Follow-up: At 500 partitions, each consumer on a 10-min export, max.poll.interval.ms default 5 min: what happens at minute 5? Can a spare consumer help a partition stuck on a poison export?
- You said: Partition cap unprompted: one consumer per partition → only 12 at a time. Fix: drain, repartition to 500, add spare consumers for poison jobs. Follow-up: past the poll interval Kafka reassigns the job; spares can't help "because they'll still fail"; move poison to a DLQ.
- Strong answer: "Consumers past 12 sit idle, because each partition has exactly one owner in a group, so exports queue behind 12 workers and wait times climb. Repartitioning to 500 doesn't fix it: a 10-minute job blows max.poll.interval, the consumer is kicked, the group rebalances, and the job replays from the last commit, forever. Spares can't help a stuck partition because they can't read it at all. Long independent jobs want per-message leases and acks, so I'd move this to SQS."
- Staff adds: if Kafka is mandatory, raise max.poll above p99 or pause/resume with a processing thread; Kafka intake → bridge to queue; KIP-932 share groups.

**R3 (Estimation) 🟩 Senior**: Export service on SQS, one PDF per worker. Peak 2 req/s, 10-min average. Workers at peak, and how many to provision?
- Follow-up: What is the 20% for, and what does 1,440 workers mean for the design or cost?
- You said: Little's Law, 2 × 600 = 1,200, +20% = 1,440. Follow-up: headroom for poison jobs; steady state → Fargate; spiky → switch to Lambda.
- Strong answer: "2 per second times 600 seconds is 1,200 in flight, so 1,200 busy workers at peak. I'd add about 20% for long-tail jobs, retries, and scale-up lag, so roughly 1,450. That's a big steady bill, so I'd run them on spot, which is safe because retries are idempotent. Not Lambda: a 10-minute average puts the p99 near the 15-minute cap, and default account concurrency is 1,000."
- Staff adds: size on p90 duration if the tail is fat; spot ~70% cheaper.

**R4 (Spot the flaw) 🟦 Mid**: What's wrong with this export pipeline ops config?
```
1. Autoscale workers on backlog per worker (target 1 msg/worker)
2. Page on-call when total queue depth > 5,000
3. Workers heartbeat every 60 s while building a PDF; no max runtime
4. maxReceiveCount = 5, then the message goes to the DLQ
5. Scale-in: terminate any worker when backlog per worker < 0.5
```
- Follow-up: 10 workers hang, depth sits at 300, some users waiting 40 min: does step 2 page? Step 5 kills a worker 9 min into a PDF: what happens to the job and the user?
- You said: Step 1 target too low (1.2); step 2 OK; step 3 needs a max runtime ~20 min; step 5 scale in below 1.2. Follow-up: step 2 won't page, switch to "long-running job on the queue"; scale in only idle workers. Re-answer on step 5 skipped by user.
- Strong answer: "Step 2 pages on depth, which says how much is waiting, not how long, so 10 hung workers and a 40-minute wait never fire it. I'd page on ApproximateAgeOfOldestMessage against the SLA. Step 3: a hung worker that keeps heartbeating holds its lease forever, so the receive count never climbs and step 4's DLQ never fires; a runtime cap around 2× p99 counts as a failed attempt. Step 5 kills busy workers: the lease expires, another worker starts over, the user waits 20 minutes instead of 10, and we wasted 9 minutes of compute. I'd use scale-in protection while busy, with separate scale-in and scale-out thresholds. Step 1 is fine."
- Staff adds: ECS task scale-in protection toggled by the worker; cooldown/hysteresis; alarm on DLQ depth.

**R5 (Explain it) 🟦 Mid**: In 60 s at the whiteboard: once an export worker has built the PDF, what are its steps to finish the job, in order, and why is each in that position?
- Follow-up: Where does deleting the SQS message go, and what does a worker do differently when its conditional update returns 0 rows?
- You said: S3 → conditional update in-progress → completed → notification with job ID as idempotency key. Follow-up: delete the SQS message last (queue owns the job until then); a 0-row worker still sends the notification.
- Strong answer: "Upload to a deterministic key like exports/{job_id}.pdf, so a duplicate is a harmless overwrite. Then set completed where status is processing. If I get one row back, I won, so I send the email keyed on job ID. If I get zero, someone else won and owns the email, so I stay quiet. I delete the message last, so a crash at any earlier step just lets it reappear and retry safely."
- Staff adds: crash between commit and email → outbox in the same transaction, or a sweeper.

**R6 (Tradeoff duel) 🟦 Mid**: "We already run Kafka with plenty of ops expertise. Why add SQS for exports?" Defend it in 45 s.
- Follow-up: They raise max.poll.interval.ms to 30 minutes. Is Kafka fine now?
- You said: Kafka suits jobs under 5 min; consumer times out before committing, job retries and fails, ends in a DLQ; SQS handles long jobs with Fargate or Lambda. Follow-up: messages come in too quickly, partitions can only handle so many, never drained in time.
- Strong answer: "I'd still use SQS. Kafka commits one offset per partition, so a 10-minute export blocks the commits behind it, and a crash replays all of them. Each partition has one consumer per group, so parallelism equals the partition count: 1,200 concurrent exports means 1,200 partitions. Raising max.poll fixes neither. SQS gives each job its own lease and ack, and I scale by adding workers. The cost is one more system to run; I'd use Kafka if these were short, ordered events."
- Staff adds: Kafka as intake log bridged to SQS; KIP-932 share groups. Kafka has no built-in DLQ.
### Gap to senior
- The 0-row worker sends no email; 1 row affected is the permission to send (backwards in R1 and R5). Update before email, never after
- Page on ApproximateAgeOfOldestMessage (3rd miss) and say why; runtime cap is what makes the DLQ fire for hung-but-heartbeating workers
- Kafka for jobs: lead with "I'd still use SQS," then precise mechanisms (1 consumer/partition → parallelism = partitions; per-partition offset → HOL + replay; max.poll → rebalance/replay loop, no built-in DLQ)
- Scale-in: state the consequence (wasted compute, user waits 2×), then protect busy workers
- Headroom = long tail + scale-up lag; no Lambda for ~10-min jobs (15-min cap vs p99, 1,000 default concurrency)
### Staff stretch
- Outbox / sweeper for the commit-then-send gap
- Spot instances because retries are idempotent; size on p90 for fat tails
- ECS scale-in protection + scale-in/out hysteresis
- Kafka intake → SQS bridge; KIP-932
### Now solid
- Little's Law estimation: no doubling, intermediate number said, headroom arithmetic right
- Partition cap volunteered unprompted
- Completion order: S3 → conditional update → email → delete message last
- Consequence before fix in R1 (user sees a second email)
### Interview-ready lines
- "One row back means I won, so I send the email. Zero means someone else did, so I stay quiet."
- "I page on age of the oldest message, because that's the longest any user is waiting. And I cap runtime so hung jobs end up in the DLQ."
- "I'd still use SQS: one consumer per partition caps parallelism, and per-partition offsets mean one slow job blocks the commits behind it."
- "Killing a busy worker wastes its compute and doubles the user's wait, so I protect busy workers on scale-in."
- "About 20% headroom for long-tail jobs and scale-up lag. A p99 near Lambda's 15-minute cap rules it out."
### Hold-in-mind questions
- Your conditional update returns 0 rows. What do you do, and why?
- What do you page on for a job queue, said bottom line first with the reason?
- "We already run Kafka." Defend SQS in three sentences, decision first.
- Scale-in fires while a worker is 9 minutes into a job. What happens, and the fix?
### Delivery
- Habit (2nd LRT drill in a row): vague words where the mechanism belongs ("change our metric to long-running job on the q", "partitions can only handle so many messages", "optimal cost savings"). R6 buried the bottom line.
- Rewrite (R6): "I'd still use SQS, for two reasons. First, Kafka commits one offset per partition, so if one export takes 10 minutes, I can't commit the jobs behind it even when they finish, and a crash replays all of them. Second, each partition has one consumer, so parallelism equals the partition count. 1,200 concurrent exports would need 1,200 partitions. SQS gives each job its own lease and ack, and I scale by adding workers. The cost is one more system to run. If these were short, ordered events, I'd use Kafka."
- Did well: R1 consequence before fix; R3 full estimation frame; R5 signposted steps.
- Frame reminders: on (re-answers: 1, skipped by user)
