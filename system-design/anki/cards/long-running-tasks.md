# Long-Running Tasks

## Async worker pattern
Q: Why not transcode a video inside the upload request?
A: The gateway times out at about 30 seconds. The work might still finish, so the user sees a false failure, and their retry transcodes twice. Make it async: return a job ID right away.

Q: Walk through the async job pattern for a video upload.
A: The client uploads straight to S3 with a presigned URL, then calls POST /jobs. The API writes a pending job row, puts the job ID on SQS, and returns the ID. Workers pull, heartbeat, transcode, mark the job complete, and delete the message. The client polls a status endpoint, and we email on completion.

Q: Why can't 20-minute jobs run on Lambda?
A: Lambda has a 15-minute hard limit, so they fail every time. Use Fargate or EC2 workers polling SQS.

Q: Polling vs SSE for job status?
A: Poll a status endpoint by default: cheap key lookups, stateless, and it survives tab close. Email on completion. Use SSE only if you need live progress.

## Visibility timeouts & heartbeats
Q: What goes wrong when the visibility timeout is shorter than the job?
A: The message reappears while the first worker is still running, so two workers do the same job: double compute and duplicate emails. If every attempt overruns, the receive count climbs until a healthy job lands in the DLQ.

Q: What are the two fixes for a visibility timeout shorter than the job, and their tradeoff?
A: (1) A short lease, about 5 minutes, extended by heartbeat (ChangeMessageVisibility every ~90 s). (2) A long fixed timeout, like p99 plus 50%. The fixed one is simpler, but a dead worker's job sits for the whole timeout before a retry.

Q: A worker deletes the SQS message on receive, then crashes. What happens?
A: It's at-most-once: the job is lost silently and stays pending forever. Delete only after outputs and status are committed.

## Idempotency & retries
Q: A worker writes 3 of 5 renditions, then crashes. Walk the timeline to one correct result and one email.
A: The heartbeat stops, the timeout expires, and the message reappears. Worker B sees renditions 1–3 under deterministic keys and only does 4 and 5. It runs a conditional update (set completed where status='processing'); one row back means it won, so it sends the email. Delete the message last.

Q: Two workers both finish the same job. What makes sure only one email goes out?
A: A conditional status update: UPDATE ... SET status='completed' WHERE status='processing'. Only the worker that gets 1 row affected sends the email. S3 won't block the second upload; it's a harmless overwrite of the same key.

Q: Your conditional "set completed where status='processing'" returns 0 rows. Do you send the email?
A: No. Zero rows means another worker already finished and owns the notification, so you exit quietly. One row affected is the permission to send.

Q: After building the output, in what order does a worker finish the job?
A: Upload to a deterministic key, then the conditional status update, then the email (only if 1 row, keyed on job_id), then delete the queue message last. Email before the update would let both workers send; deleting earlier would lose the job on a crash.

Q: Why isn't "read the status, then write completed, inside a transaction" enough to send exactly one email?
A: At the default READ COMMITTED isolation both workers can read 'processing' and both write, so both send. Use one atomic conditional UPDATE ... WHERE status='processing' and act only on 1 row affected.
Staff: Close the commit-then-send gap with an outbox row in the same transaction or an idempotency key (job_id) on the email provider.

## SQS vs Kafka for jobs
Q: "We already run Kafka with plenty of ops expertise. Why add SQS for long export jobs?"
A: I'd still use SQS. Kafka commits one offset per partition, so a slow job blocks the commits behind it and a crash replays them, and parallelism is capped at the partition count. SQS gives each job its own lease and ack; the cost is one more system, and I'd use Kafka for short, ordered events.

Q: A Kafka consumer takes 10-minute jobs with the default max.poll.interval.ms (5 min). What happens?
A: At minute 5 the consumer is kicked from the group, the group rebalances, and the job replays from the last committed offset, which trips the limit again, so it loops forever. Kafka has no built-in DLQ; you'd have to build a retry topic.

Q: A Kafka partition is stuck on a poison job. Can a spare consumer in the group help?
A: No. Each partition has exactly one owner per group, so consumers beyond the partition count sit idle and can't read the stuck partition at all.

Q: Kafka partition: job 100 takes 20 min, 101–110 take 2 min. What happens to offsets, and on a crash at minute 15?
A: The offset can't advance past 100, so 101–110 stay uncommitted even when done. A crash replays everything after the last commit: 100 through 110.

Q: Why does Kafka cap parallelism for a job queue?
A: Each partition is read by exactly one consumer per group, so max concurrency equals the partition count. 2,400 concurrent jobs would need about 2,400 partitions.
Staff: A consumer that doesn't poll within max.poll.interval.ms (default 5 min) is kicked from the group, triggering a rebalance and duplicates.

## Scaling & alerting
Q: Scale-in terminates a worker 9 minutes into a 10-minute job. What happens, and the fix?
A: It stops heartbeating, the lease expires, and another worker starts from scratch: the user waits about 20 minutes instead of 10 and 9 minutes of compute is wasted. Turn on scale-in protection while busy and only terminate idle workers.
Staff: ECS task scale-in protection toggled by the worker, plus separate scale-in/scale-out thresholds with a cooldown.

Q: 10-minute average export jobs: why not run them on Lambda?
A: Durations are right-skewed, so the p99 is often 2–3× the mean, near or past Lambda's 15-minute hard cap. Default account concurrency is also 1,000, below a 1,200+ worker peak.

Q: What is p99 job duration, and how do you get it?
A: 99% of jobs finish faster than it. Log started_at/completed_at and read p99 from CloudWatch/Datadog or percentile_cont(0.99); with no data, assume about 2× the mean out loud. Size limits (timeouts, runtime caps) on the tail, not the average.

Q: You add 20% headroom to a Little's Law worker count. What is it for?
A: Jobs in the long tail above the average, retries, and lag while autoscaling catches up, not doubling an already-peak rate.
Staff: Run the pool on spot instances, safe because retries are idempotent.

Q: What do you autoscale job workers on?
A: Backlog per worker, with separate scale-out and scale-in thresholds and a cooldown so it doesn't flap. On scale-in, protect busy workers or let them drain.

Q: What do you page on for a job queue, and why isn't queue size enough?
A: Age of the oldest message, tied to the SLA. It's the unluckiest user's wait, and it catches stuck workers and poison messages even when the backlog looks normal. Also alarm on DLQ depth and stale heartbeats.

Q: 5 jobs per second, 8-minute average duration. How many workers?
A: Little's Law: rate × duration. 5/s × 480 s = 2,400 jobs in flight, so 2,400 busy workers, about 3,000 with headroom.

Q: Workers hang on a poison video but keep heartbeating. How do you stop them holding leases forever?
A: Cap job runtime (e.g. 3× p99); a timeout counts as a failed attempt so the job ends up in the DLQ. Alarm on runtime > p99 and DLQ depth.
Staff: Heartbeat with progress (frames done), not just liveness, so a stuck process with a live heartbeat thread is caught.

Q: Why page on age of the oldest message instead of average wait?
A: The average hides the tail because healthy workers pull it down; the oldest message is the worst wait a user feels right now and maps to the SLA.
