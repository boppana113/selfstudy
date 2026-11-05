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

## Drill: 2026-11-05 (review, score 25%; Below mid 1 · Mid 1 · Senior 0 · Staff 0)
### Questions
**R1 (Explain it) ⬜ Below mid**: gRPC services behind an L4 load balancer. You scale out from 4 instances to 8, but the 4 new ones sit nearly idle. Why, and what would you change?
- Follow-up: The LB sees the new instances right away and health checks pass. Clients already have connections open to the original 4. Where do their next thousand requests go?
- You said: The LB didn't know about the new instances and needs its NAT table updated. Follow-up: "I'm not sure how to answer this."
- Re-answer: Reasoning came through after teaching (connections pinned → traffic stays on old 4 → max connection age), but "what the user sees" was still missing.
- Strong answer: "L4 balances connections, not requests. gRPC runs on HTTP/2 and multiplexes everything over one long-lived connection, so existing clients stay pinned to the original 4 and only rare new connections reach the new ones. The old 4 run hot, so latency climbs while half the fleet idles. I'd put an L7 balancer like Envoy in front so each request is balanced, at the cost of terminating TLS and parsing HTTP/2, or use client-side balancing if I own the clients."
- Staff adds: Server-side MAX_CONNECTION_AGE forces periodic reconnects as a cheap mitigation; alert on per-instance request rate, not connection count.

**R2 (Failure mode) 🟦 Mid**: A payment provider has a 30-second slowdown, and 200 servers each retry failed calls 5 times immediately. Walk through what happens and what you'd change.
- Follow-up: What stops the double charge? Jitter spreads retries but each failed call still becomes up to 6; what caps total load?
- You said: Consequence first (customer charged multiple times, stampede overwhelms the provider); fix was jittered retries. Follow-up: idempotency key; "backward pressure so clients don't make new requests."
- Strong answer: "Every failed call becomes up to six, so a provider that's already slow gets about 6× the load and the slowdown turns into an outage, and any retry that went through after a timeout double-charges the customer. I'd send one idempotency key per checkout, reused on every retry, so the provider dedupes. I'd set an explicit timeout, retry with exponential backoff and jitter, and cap retries with a budget, say 10% of traffic. And a circuit breaker opens after the error rate crosses a threshold, so we fail fast and stop piling on until it recovers."
- Staff adds: When the breaker is open, queue the checkout and tell the user payment is pending instead of failing it; alert on breaker state.

### Gap to senior
- L4 vs L7 (2nd miss): L4 balances connections, L7 balances requests. gRPC pins long-lived HTTP/2 connections, so an L4 balancer leaves new instances idle. "The LB doesn't know about the new instances" is the wrong mechanism.
- Retry storm: say the ~6× number; the caps are a retry budget and a circuit breaker, not vague "backpressure." Idempotency key must be the same across retries.
- State what the user sees (old instances run hot → latency/timeouts).

### Staff stretch
- MAX_CONNECTION_AGE as a cheap rebalance; alert on per-instance request rate
- Open breaker → queue checkout as "payment pending" instead of failing it

### Interview-ready lines
- "L4 balances connections and gRPC holds one long-lived HTTP/2 connection, so after a scale-out the old instances keep all the traffic. I'd use L7 or client-side balancing."
- "Five immediate retries turn a slowdown into 6× load. I'd add a timeout, backoff with jitter, a retry budget, a circuit breaker, and one idempotency key per checkout reused on every retry."

### Delivery
- Habit (RECURRING, 4th notes file): stopping at "I'm not sure" (R1: "I'm not sure how to answer this.") instead of reasoning from what you know ("gRPC keeps connections open...").
- Rewrite (R2): "Every failed call becomes up to six, so the provider gets about six times the load while it's already slow, and it falls over. Worse, a retry that lands after a timeout charges the customer twice. So first, one idempotency key per checkout, reused on every retry. Then a timeout, backoff with jitter, and a retry budget so retries can't exceed about ten percent of traffic. And a circuit breaker, so once errors cross a threshold we fail fast instead of piling on."
- Did well: R2 opened with the consequences (double charge, stampede) before the fix, unprompted.
- Frame reminders: on (re-answers: 1)
