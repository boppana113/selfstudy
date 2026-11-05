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

## Scaling & alerting
Q: What do you autoscale job workers on?
A: Backlog per worker, with separate scale-out and scale-in thresholds and a cooldown so it doesn't flap. On scale-in, protect busy workers or let them drain.

Q: What do you page on for a job queue, and why isn't queue size enough?
A: Age of the oldest message, tied to the SLA. It's the unluckiest user's wait, and it catches stuck workers and poison messages even when the backlog looks normal. Also alarm on DLQ depth and stale heartbeats.

Q: 5 jobs per second, 8-minute average duration. How many workers?
A: Little's Law: rate × duration. 5/s × 480 s = 2,400 jobs in flight, so 2,400 busy workers, about 3,000 with headroom.
