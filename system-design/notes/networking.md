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

## Drill: 2026-11-05 (redrill, score 25%; Below mid 3 · Mid 3 · Senior 0 · Staff 0)
### Questions
**R1 (Explain it) 🟦 Mid**: Internal gRPC service behind an L4 LB. After a deploy, one instance is at 90% CPU and the rest at 20%. Why, and what would you change?
- Follow-up: What does L7 cost you, and if you own clients and server, what could you do instead?
- You said: Long-lived connections, L4 assigns each connection once, uneven → one instance gets more work; replace with L7. Follow-up: "slower routing"; server policy forcing reconnects; "add more instances."
- Strong answer: "gRPC multiplexes every request over one long-lived HTTP/2 connection, and L4 only balances connections. So after the rolling deploy, whichever instance came up first kept everyone's connections, and its p99 spiked while the rest idled. I'd move to L7 or client-side balancing. L7 costs TLS termination and an extra hop, so if I own the clients I'd do client-side balancing plus MAX_CONNECTION_AGE to force periodic rebalancing."
- Staff adds: Alert on per-instance request rate; a service mesh gives L7 balancing without a central LB.

**R2 (Estimation) 🟦 Mid**: 200 checkout servers × 500 calls/s to a payment provider; provider slows, every call times out, 5 immediate retries. What load does the provider see, and what caps it?
- Follow-up: Jitter spreads retries but each failure still becomes 6 calls; what puts a ceiling on total? What about a retry that lands after a timeout?
- You said: 100k → 600k, stampede; jitter + backoff. Follow-up: "some means of capping requests using recent attempts" (= retry budget, unnamed); idempotency key prevents double charge.
- Strong answer: "That's 100k becoming 600k, so 6× on a provider that's already slow, and the slowdown turns into an outage. Backoff and jitter spread the retries out, but a retry budget is what caps them, at about 10% of traffic. A circuit breaker stops calling entirely once errors cross a threshold. And one idempotency key per checkout, reused on every retry, prevents double charges."
- Staff adds: Open breaker → queue checkout as "payment pending"; alert on breaker state.

**R3 (Failure mode) ⬜ Below mid**: WebSocket server with 100k connections dies. Narrate until every user has every missed message.
- Follow-up: Messages sent during the 10s gap went to a dead socket. How do users get them, and how does the system learn each user's new server?
- You said: Heartbeat fails, reconnect via gateway, headroom exists. Follow-up: missed messages "moved to the new server"; "some database that records connection state."
- Re-answer: Came through nearly verbatim (backoff+jitter, registry, seq replay, persisted before delivery); "what the user sees" still missing.
- Strong answer: "When that box dies, its 100k connections are just gone, so recovery is on the client. Clients notice the failed heartbeat and reconnect with jittered backoff so they don't take down the next servers. The new server updates the user's entry in the connection registry. The client sends the last sequence number it saw and we replay anything newer from the message store. The user sees a few seconds of 'reconnecting', then the missed messages in order."
- Staff adds: Alert on reconnect rate; LB rate limiting; session-resume token to skip full re-auth.

**R4 (Spot the flaw) ⬜ Below mid**: Live comments design:
```
- Viewers open an SSE connection; L4 LB assigns them round-robin across 300 SSE servers
- POST /comments hits any API server, which writes the comment to Postgres
- The API server then sends the comment through the load balancer to the SSE servers
- As a backup, each SSE server polls Postgres every 5s for new comments
```
- Follow-up: When one comment goes through the LB, how many SSE servers get it? For a popular stream, how many servers have its viewers?
- You said: Polling is wasteful; API should fan out itself. Follow-up: only one server gets it; popular stream needs "more than one server."
- Strong answer: "The LB routes one request to one backend, so 299 servers never see the comment, and round-robin puts every popular stream's viewers on all 300. I'd have the API publish to a per-stream pub/sub channel, SSE servers subscribe only to streams their viewers watch, and an L7 LB hashes viewers by stream ID so each comment reaches a handful of servers. Polling goes away."
- Staff adds: Split mega-streams across N servers; sample/batch comments; show author's own comment optimistically.

**R5 (Tradeoff duel) ⬜ Below mid**: Live comments, mostly reads. SSE or WebSockets?
- Follow-up: If SSE doesn't hold a connection, how does the server push instantly? What would make you switch?
- You said: SSE; one-way vs bidirectional; "SSE doesn't maintain any connection." Follow-up: "I'm not sure what I'm saying."
- Re-answer: Came through with the unsure frame: reasoned to long-lived HTTP response, gave cost (SSE fleet, sharding) and switch trigger (slightly off: "users writing to each other").
- Strong answer: "SSE, because traffic is one-way and it's plain HTTP: one long-lived response the server keeps writing events to, so it works through L7 LBs and proxies, and the browser auto-reconnects with Last-Event-ID for replay. Posting is a normal POST. The cost is it's server-to-client only, and HTTP/1.1 caps ~6 connections per domain. I'd switch to WebSockets for high-frequency client sends like typing indicators or cursors."
- Staff adds: HTTP/2 multiplexes SSE streams; SSE can share the API's L7 tier.

**R6 (Scale it up) 🟦 Mid**: 10M concurrent SSE viewers. How many connection servers, and what do you autoscale on?
- Follow-up: Scaling 150 → 75 after the event: what happens to viewers on removed servers, and is CPU the trigger?
- You said: 100k/box → 100 min, 1.5× → 150 for spikes; 5M → 75. Follow-up: viewers "get moved"; autoscale on average CPU.
- Strong answer: "Assuming ~100k connections per box, memory-bound, 10M is 100 servers; I'd run 150 so a dead box's connections and uneven stickiness have room. Idle connections barely use CPU, so I'd autoscale on connections per box. Scaling down, I stop routing new connections to a box, then close its connections gradually so clients reconnect with jitter elsewhere, and terminate it when empty."
- Staff adds: Pre-scale before a scheduled event (autoscaling lags a surge); cap drain rate.

### Gap to senior
- **Connections can't be moved** (3rd time: 11-02 crash, R3, R6). A dead or draining box's connections end; clients reconnect elsewhere; state lives in the message store + registry, never on the socket.
- SSE holds one long-lived HTTP response open. Both SSE and WebSockets are stateful connection servers; the difference is direction and plumbing.
- Live-comment fan-out fix: per-stream pub/sub + hash viewers by stream ID (spotted the LB flaw, couldn't give the fix).
- Autoscale connection servers on connections per box, not CPU; scale-down = drain.
- Name both retry caps: retry budget (~10%) and circuit breaker. Same idempotency key on every retry.
- L4/gRPC: say HTTP/2 multiplexing, MAX_CONNECTION_AGE by name, L7 cost = TLS termination + extra hop. More instances doesn't help.
- State what the user sees (p99 spike; "reconnecting…" then messages in order).

### Staff stretch
- Pre-scale for scheduled events; cap drain rate
- Session-resume token on reconnect; alert on reconnect rate
- Mega-stream: split across N servers, sample comments

### Interview-ready lines
- "You can't move a connection. When a box dies or drains, clients reconnect elsewhere with jitter and replay from their last sequence number."
- "SSE is one long-lived HTTP response the server keeps writing to, so it's still a stateful connection, just one-way."
- "API publishes to a per-stream channel, SSE servers subscribe for their viewers' streams, and I hash viewers by stream ID."
- "Idle connections are memory-bound, so I autoscale on connections per box, and scale down by draining."

### Delivery
- Habit: stopping at "I'm not sure" (R5: "I take that back. I'm not sure what I'm saying."). RECURRING (5th time). But R2 broke it: "I don't know the exact mechanism, but I will provide some means of capping…" reasoned to a retry budget unprompted, and R5's re-answer with the unsure frame reached the right mechanism.
- Rewrite (R6): "Assuming about 100k connections per box, since idle connections are memory-bound, 10 million viewers is 100 servers. I'd run 150, so if one dies its 100k clients have somewhere to land. I wouldn't autoscale on CPU, because idle connections barely use it. I'd scale on connections per box. And scaling down, you can't move a connection, so I stop sending new ones to a box, close its connections gradually so clients reconnect elsewhere with jitter, then kill it when it's empty."
- Did well: R2 and R6 estimation had setup → formula → number cleanly; both re-answers landed.
- Frame reminders: on (re-answers: 2)
