# Long-Running Tasks

## Async worker pattern
Q: Why not transcode a video inside the upload request?
A: The gateway times out at ~30 s, so the user sees a failure for work that's still running, and their retry transcodes it twice. Make it async: return a job ID right away.
Why: Walk the request. The upload lands at 10:00:00, transcoding starts and takes 10 minutes. At 10:00:30 the gateway closes the connection and the app shows "upload failed." The worker keeps going, unaware. The user taps retry at 10:00:35: a second transcode of the same video, and at 10:10 two copies and two emails. With a job ID, the response returns in 50 ms and the app polls status.

Q: Walk through the async job pattern for a video upload.
A: Client uploads straight to S3 with a presigned URL, then POSTs /jobs. The API writes a pending job row, enqueues the job ID, and returns it. Workers pull, heartbeat, transcode, mark complete, delete the message. The client polls status; email on completion.
Why: Each piece removes a failure. Presigned upload keeps 2 GB of video off your API servers. The job row exists before the queue message, so a lost message can be found and re-enqueued. The heartbeat keeps the lease alive so a second worker doesn't start the same job. Marking complete before deleting the message means a crash at the end replays harmlessly instead of losing the job. Polling is a cheap key lookup and survives the user closing the tab.

Q: Why can't 20-minute jobs run on Lambda?
A: Lambda has a 15-minute hard limit, so they fail every time. Use Fargate or EC2 workers polling SQS.
Why: Picture the job at minute 15: Lambda kills the process mid-transcode, the message goes back to the queue, the next Lambda starts over and dies at minute 15 again. Three tries later it's in the DLQ with nothing done. Fargate tasks run as long as they need; a 20-minute job is just a 20-minute job.
Flip: Jobs with a p99 well under 15 minutes (thumbnails, PDF renders) are fine on Lambda, and it scales to zero.

Q: Polling vs SSE for job status?
A: Poll by default: cheap key lookups, stateless, survives tab close. Email on completion. SSE only for live progress.
Why: Picture 10,000 users each with a job. Polling every 5 s is 2k reads/s on a status table or Redis, trivial, and any API server can answer. SSE holds 10,000 connections open on specific servers, needs a way to push updates to the right one, and drops when the user closes the laptop. For a 10-minute job, most users leave and come back, so the email is what they actually use.

## Visibility timeouts & heartbeats
Q: What goes wrong when the visibility timeout is shorter than the job?
A: The message reappears while the first worker is still running, so two workers do the same job: double compute and duplicate emails. If every attempt overruns, the receive count climbs until a healthy job hits the DLQ.
Why: Timeout 30 s, job 10 minutes. Worker A receives at 10:00:00. At 10:00:30 the message is visible again; worker B takes it. At 10:01:00 worker C. By 10:03 the receive count is past maxReceiveCount (say 5) and SQS moves the message to the DLQ, while A, B, C, D, and E are all still transcoding the same video. The user gets five emails and the job is flagged as failed.

Q: What are the two fixes for a visibility timeout shorter than the job, and their tradeoff?
A: A short lease (~5 min) extended by heartbeat, or a long fixed timeout (p99 + 50%). Fixed is simpler, but a dead worker's job sits for the whole timeout before a retry.
Why: Heartbeat: worker A calls ChangeMessageVisibility every 90 s. If A dies, the lease lapses within 5 minutes and B picks it up. Fixed 30-minute timeout: no heartbeat code, but if A dies at minute 1, the message is invisible until minute 30, so the user waits 40 minutes for a 10-minute job. With heartbeats, they wait ~15.
Flip: Fixed timeout is fine when jobs are short and uniform (p99 2 min, timeout 3 min); the stuck window is small.

Q: A worker deletes the SQS message on receive, then crashes. What happens?
A: At-most-once: the job is lost silently and stays pending forever. Delete only after outputs and status are committed.
Why: Timeline: receive at 10:00:00, delete at 10:00:01, crash at 10:03. The queue has no record. The job row says "processing" forever. No retry, no DLQ, no alarm, because nothing failed from the queue's view. The user polls status and sees "processing" for days.

## Idempotency & retries
Q: A worker writes 3 of 5 renditions, then crashes. Walk the timeline to one correct result and one email.
A: Heartbeat stops, lease expires, message reappears. Worker B sees renditions 1–3 at their deterministic keys and does only 4 and 5. It runs a conditional update to completed; 1 row means it won, so it emails. Delete the message last.
Why: Outputs are at `videos/{job_id}/720p.mp4` etc., so B can check what exists. B uploads 4 and 5 (or re-uploads all 5; same keys, harmless overwrite). Then `UPDATE jobs SET status='completed' WHERE id=? AND status='processing'` returns 1 row, since A never got there. B sends the email, then deletes the message. If A had somehow finished too, its update would return 0 rows and it would send nothing.

Q: Two workers both finish the same job. What makes sure only one email goes out?
A: A conditional status update: `UPDATE ... SET status='completed' WHERE status='processing'`. Only the worker that gets 1 row affected sends the email.
Why: Both A and B upload (same S3 keys, harmless). A runs the update first: 1 row, status is now completed, A sends the email. B runs the same statement a second later: the WHERE finds no row with status='processing', 0 rows affected, B sends nothing. The database serializes the two updates on the row, so there's no window where both see 1.

Q: Your conditional "set completed where status='processing'" returns 0 rows. Do you send the email?
A: No. Zero rows means another worker already finished and owns the notification. One row affected is the permission to send.
Why: Picture B getting 0 rows. The only way that happens is A already set completed (or the job was cancelled). If B emails anyway, the user gets two. So the rule is: the row count is the vote, and only the winner acts. B deletes its message copy and exits.

Q: After building the output, in what order does a worker finish the job?
A: Upload to a deterministic key, then the conditional status update, then the email (only if 1 row), then delete the queue message last.
Why: Each order change breaks something. Email before the update: both workers can email, because neither has lost the vote yet. Update before upload: status says done but the file isn't there, and a second worker skips it. Delete the message before the update: a crash in between loses the job with no retry. Upload → update → email → delete means every crash point either replays safely or has already finished.

Q: Why isn't "read the status, then write completed, inside a transaction" enough to send exactly one email?
A: At READ COMMITTED both workers can read 'processing' and both write, so both send. Use one atomic conditional UPDATE and act only on 1 row affected.
Why: Timeline at the default isolation. A begins, reads 'processing'. B begins, reads 'processing'. A writes completed, commits, emails. B writes completed (no conflict, it's just an update), commits, emails. The read and the write were separate statements, so the check wasn't atomic. `UPDATE ... WHERE status='processing'` makes the check and the write one statement, and the row lock makes B's version see A's result.
Staff: Close the commit-then-send gap with an outbox row in the same transaction or an idempotency key (job_id) on the email provider.

## SQS vs Kafka for jobs
Q: "We already run Kafka with plenty of ops expertise. Why add SQS for long export jobs?"
A: Still SQS, because Kafka commits one offset per partition, so a slow job blocks commits behind it and a crash replays them, and parallelism is capped at partitions. The cost is one more system to run.
Why: Picture 500 export jobs an hour, some 20 minutes long. Kafka with 20 partitions: 20 at a time, and when one 20-minute job sits at offset 100, the 2-minute jobs at 101–110 can't be committed, so a restart redoes them. SQS: 500 workers each lease a message, extend it while working, ack it when done, and a bad one goes to the DLQ after 3 tries. Kafka stays for the short, ordered events it's good at.

Q: A Kafka consumer takes 10-minute jobs with the default max.poll.interval.ms (5 min). What happens?
A: At minute 5 the consumer is kicked out, the group rebalances, and the job replays from the last commit, trips the limit again, and loops forever. Kafka has no built-in DLQ.
Why: Timeline: poll at 10:00, start the job. 10:05: no poll in 5 minutes, broker evicts the consumer. The partition is reassigned, the new owner polls from the same offset, starts the same job. 10:10: evicted. Every 5 minutes, forever, with 5 minutes of wasted compute each time, and the job never finishes. Raising the interval to 30 min helps but means a dead consumer isn't noticed for 30 min.

Q: A Kafka partition is stuck on a poison job. Can a spare consumer in the group help?
A: No. Each partition has exactly one owner per group, so spare consumers sit idle and can't read the stuck partition.
Why: Partition 3 is stuck on job 100. Consumers 7 and 8 are idle because there are only 6 partitions. They can't take job 101 from partition 3, because that would mean two readers on one partition, which Kafka's group protocol forbids. The jobs behind 100 wait until 100 is dealt with.

Q: Kafka partition: job 100 takes 20 min, 101–110 take 2 min. What happens to offsets, and on a crash at minute 15?
A: The offset can't advance past 100, so 101–110 stay uncommitted even when done. A crash at minute 15 replays 100 through 110.
Why: 101–110 finish by minute 4. The consumer holds the commit at 100 because committing 110 would mark 100 done. Crash at minute 15: the new consumer starts at 100 (15 minutes wasted) and runs 101–110 again (20 minutes of duplicate work, and duplicate side effects unless they're idempotent).

Q: Why does Kafka cap parallelism for a job queue?
A: Each partition is read by one consumer per group, so max concurrency is the partition count. 2,400 concurrent jobs would need ~2,400 partitions.
Why: Little's Law says 5 jobs/s × 480 s = 2,400 jobs in flight. In SQS, that's 2,400 workers each holding one message. In Kafka, 2,400 simultaneous jobs means 2,400 partitions, each with a leader election, replicas, and per-broker memory, for what is really a queue. That's a sign the tool doesn't fit.
Staff: A consumer that doesn't poll within max.poll.interval.ms (default 5 min) is kicked from the group, triggering a rebalance and duplicates.

## Scaling & alerting
Q: Scale-in terminates a worker 9 minutes into a 10-minute job. What happens, and the fix?
A: The lease expires and another worker starts over, so the user waits ~20 minutes instead of 10 and 9 minutes of compute is wasted. Turn on scale-in protection while busy and only terminate idle workers.
Why: Backlog drops, autoscaling picks a worker to kill. It's at minute 9 of a transcode. Heartbeats stop, the lease lapses after 5 minutes, worker B starts from scratch at minute 14, finishes at minute 24. The user's 10-minute job took 24. With protection, the worker marks itself busy at job start and clears it at the end, so the autoscaler only kills workers that are idle.
Staff: ECS task scale-in protection toggled by the worker, plus separate scale-in/scale-out thresholds with a cooldown.

Q: 10-minute average export jobs: why not run them on Lambda?
A: Durations are right-skewed, so p99 is often 2–3× the mean, near or past Lambda's 15-minute cap. Default concurrency is also 1,000, below a 1,200+ worker peak.
Why: "10-minute average" hides the tail. Picture the distribution: most jobs 6–8 minutes, some 20, a few 40 (big accounts). The 40-minute ones die at 15 every time, retry, die, DLQ. And at peak, 5 jobs/s × 600 s = 3,000 in flight, so 2,000 jobs are throttled waiting for a Lambda slot.

Q: What is p99 job duration, and how do you get it?
A: 99% of jobs finish faster than it. Log started_at/completed_at and read p99 from your metrics tool or percentile_cont(0.99); with no data, assume ~2× the mean out loud. Size timeouts and caps on the tail, not the average.
Why: Picture setting the runtime cap at the 10-minute average. Half of all jobs are killed. At p99 (say 25 minutes), 1 in 100 is killed, and those are likely the genuinely stuck ones. The number comes from real data: `SELECT percentile_cont(0.99) WITHIN GROUP (ORDER BY completed_at - started_at)`. In an interview, say "I'd assume p99 is around 2× the mean until I measure it."

Q: You add 20% headroom to a Little's Law worker count. What is it for?
A: The long tail above the average, retries, and autoscaling lag. Not a second peak multiplier if the rate was already peak.
Why: 2,400 workers covers 5 jobs/s at exactly 8 minutes each. Real jobs: some take 20, so they hold workers longer than the average predicts. Some fail and run twice. And when the rate ticks up, new workers take 2 minutes to start. 20% (480 workers) absorbs those. If the 5/s was already the peak rate, don't double it again.
Staff: Run the pool on spot instances, safe because retries are idempotent.

Q: What do you autoscale job workers on?
A: Backlog per worker, with separate scale-out and scale-in thresholds and a cooldown. On scale-in, protect busy workers.
Why: Picture scaling on CPU: a worker waiting on an S3 download is at 5% CPU but busy, so the autoscaler kills it. Backlog per worker says "200 messages, 50 workers, 4 each," which is the wait time in units of jobs. Scale out at >2 per worker, scale in at <0.5, with a 5-minute cooldown so a burst doesn't cause add-remove-add flapping.

Q: What do you page on for a job queue, and why isn't queue size enough?
A: Age of the oldest message, tied to the SLA. Queue size tells you how much is waiting, not how long. Also alarm on DLQ depth and stale heartbeats.
Why: Picture 10 of 50 workers hung on a poison video. The other 40 keep up, so queue size looks normal: 100 messages. But the jobs on the 10 hung workers are invisible to the queue and the ones behind them wait. Age of oldest message climbs past 30 minutes: that's the unluckiest user's wait right now, and it maps straight to "we promised 15 minutes."

Q: 5 jobs per second, 8-minute average duration. How many workers?
A: Little's Law: rate × duration. 5/s × 480 s = 2,400 jobs in flight, so 2,400 busy workers, ~3,000 with headroom.
Why: Picture the system in steady state. Every second, 5 jobs start and 5 finish. Each one is in the system for 480 seconds. So at any instant, 5 × 480 = 2,400 are running. If you have 2,000 workers, 400 jobs are always waiting and the queue grows without bound. 3,000 gives 20% for the tail and retries.

Q: Workers hang on a poison video but keep heartbeating. How do you stop them holding leases forever?
A: Cap job runtime at ~3× p99; a timeout counts as a failed attempt, so the job ends up in the DLQ. Alarm on runtime > p99 and DLQ depth.
Why: The heartbeat thread is alive, so the lease keeps extending, and the queue thinks everything's fine. 10 workers are stuck forever. With a 30-minute cap (p99 10 min × 3), the worker kills the job, lets the lease lapse, and the message's receive count goes up. After 3 attempts it's in the DLQ, which pages someone, and the 10 workers are back in the pool.
Staff: Heartbeat with progress (frames done), not just liveness, so a stuck process with a live heartbeat thread is caught.

Q: Why page on age of the oldest message instead of average wait?
A: The average hides the tail because healthy workers pull it down; the oldest message is the worst wait a user feels right now and maps to the SLA.
Why: 1,000 jobs waited 1 minute and 1 job has waited 60 minutes. Average: 1.06 minutes. Everything looks fine. That one user is furious. Oldest-message age: 60 minutes, alarm fires, someone finds the stuck worker. The SLA is a promise to every user, so the metric has to be the worst case.
