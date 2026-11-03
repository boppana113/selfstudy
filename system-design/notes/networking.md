# Networking Essentials

## Drill: 2026-11-02 (score 42%)
### Solid
- Protocol choice by traffic shape (SSE for one-way, read-heavy fan-out)
- When REST beats gRPC (external clients, readability, loose contracts)
- Spots missing timeouts and idempotency keys right away
### Still weak
- Cross-server fan-out: thought the LB broadcasts; it routes each request to one backend. Need pub/sub per stream + co-locating viewers by stream ID
- L4 vs L7: L4 balances *connections*, L7 balances *requests*. Missed gRPC connection pinning behind L4; couldn't say when to pick L4 or what L7 costs
- Retries: had exponential backoff but missed jitter, retry budgets, circuit breakers, and the ~6× load amplification from 5 retries
- userId belongs in the auth token, not the URL or body
- Capacity numbers: didn't know ~100k WebSocket conns/box (memory-bound); no headroom (provision ~1.5×); autoscaling stateful servers needs connection-count metric + draining
- Connection server crash: thought connections could be "moved". Missed reconnect thundering herd (jittered backoff), connection registry update, and replay from the last-seen sequence number
### Interview-ready lines
- "The API publishes to a per-stream pub/sub channel. Connection servers subscribe for the streams their clients are watching, and I shard viewers by stream ID so each comment fans out to a handful of servers."
- "L4 balances connections, L7 balances requests. gRPC's long-lived HTTP/2 connections need L7 or client-side balancing, or one backend gets all the traffic."
- "Explicit timeout, an idempotency key per checkout, exponential backoff with jitter, a retry budget, and a circuit breaker so we fail fast instead of piling onto a struggling provider."
- "10M concurrent at ~100k per box is ~100 servers. I'd run ~150 for failover and uneven stickiness, and autoscale on connections per box with graceful draining."
- "Connections die with the box. Clients reconnect with jittered backoff, the registry updates, and they replay from their last-seen sequence number."
### Hold-in-mind questions
- Why does an L4 load balancer in front of gRPC leave new instances idle after a scale-out?
- A provider has a 30-second slowdown and 200 servers retry 5× immediately. Walk through what happens and the four fixes.
- A WebSocket box with 100k connections dies. Narrate the timeline from T0 until every user has every message.
- Comment posted on API server A; viewers on 300 SSE servers. How does it reach them?
### Re-read
- Load balancing (L4 vs L7), real-time updates (server-side fan-out), handling failures (timeouts/retries/circuit breakers)
### Delivery
- Habit: stopping at the conclusion or at "I'm not sure" ("they would create a new connection"; "I'm not sure how that translates"). Second session in a row (see long-running-tasks). When unsure, state an assumption and keep reasoning; for failure modes, narrate a timeline.
- Rewrite (Round 6): "When that box dies, its 100k connections are just gone, so recovery is on the client. Clients notice through a failed heartbeat and reconnect, but with jittered backoff, because if all 100k hit the other servers in the same second, we take those down too. That's part of why I provisioned headroom. The load balancer routes each client to a healthy server, and that server updates the user's entry in the connection registry. Then the client sends the last sequence number it saw, and we replay anything newer from the message store. Messages are persisted before delivery, so nothing's lost. The socket is just the pipe."
