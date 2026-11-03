# Managing Long-Running Tasks

## Drill: 2026-11-01 (score 42%)
### Still weak
- Visibility timeout mechanics: thought the queue tracks which worker holds a job; it's a lease (message invisible for N s, reappears if not deleted/extended)
- Heartbeats = extending visibility timeout + writing last_heartbeat to jobs table; didn't name the consequence of timeout < job duration (duplicate processing, duplicate emails)
- Idempotency under at-least-once: partial completion (check each output / manifest), deterministic output keys, conditional status update gating notifications, ack last
- Misconception: thought the queue checks the DB before reassigning; SQS knows nothing about the jobs table
- SQS vs Kafka for jobs: no knowledge of Kafka offsets/partitions, head-of-line blocking, partition-capped parallelism
- Autoscaling: said raw queue depth; better is backlog per worker + age of oldest message
- Lambda 15-min limit vs 10-min jobs not considered
- Estimation: jumped to a number without math (fixed when prompted, Little's Law); poll-load math wrong (should be 1,667/30 ≈ 55 QPS)
- Missed in initial design: presigned upload to blob storage, how client learns completion
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
