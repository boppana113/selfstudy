# Networking

## Real-time updates
Q: A comment is posted on API server A; viewers are connected to 300 SSE servers. How does it reach them?
A: The API publishes to a per-stream pub/sub channel, and connection servers subscribe for the streams their clients watch. The load balancer doesn't broadcast; it routes each request to one backend. Shard viewers by stream ID so each comment fans out to a handful of servers.

Q: A WebSocket box with 100k connections dies. Narrate recovery.
A: The connections are gone, so recovery is on the client. Clients detect a failed heartbeat and reconnect with jittered backoff so they don't stampede the other servers. The new server updates the connection registry, and the client replays from its last-seen sequence number. Messages are persisted before delivery, so nothing is lost.

Q: 10M concurrent WebSocket users. How many connection servers?
A: About 100k connections per box (memory-bound) gives about 100 servers. Run about 150 for failover and uneven stickiness. Autoscale on connections per box, with graceful draining.

Q: Can you move a live connection off a dying or draining server?
A: No. A connection ends with its box. Clients reconnect elsewhere with jittered backoff and replay from their last sequence number; the state lives in the message store and connection registry, never on the socket.

Q: Does SSE keep a connection open?
A: Yes. It's one long-lived HTTP response the server never finishes and keeps writing events to, so SSE servers are stateful like WebSocket servers. Polling is the one without a held connection.

Q: Live comments, mostly reads: SSE or WebSockets?
A: SSE, because traffic is one-way and it's plain HTTP: works through L7 LBs and proxies, and the browser auto-reconnects with Last-Event-ID for replay. Posting is a normal POST. Switch to WebSockets for high-frequency client sends (typing indicators, cursors).

Q: What metric do you autoscale SSE/WebSocket connection servers on, and how do you scale down?
A: Connections per box, not CPU: idle connections are memory-bound and barely use CPU. Scale down by draining: stop routing new connections, close existing ones gradually so clients reconnect elsewhere with jitter, then terminate.
Staff: Pre-scale before a scheduled event; autoscaling lags a surge.

## Load balancing
Q: L4 vs L7 load balancing, in one line each?
A: L4 balances connections (TCP); L7 balances requests (HTTP), so it can route by path or header, at the cost of terminating and parsing every request.

Q: Why does an L4 load balancer in front of gRPC leave new instances idle after a scale-out?
A: gRPC multiplexes requests over long-lived HTTP/2 connections, and L4 only balances when a connection opens. Existing connections stay pinned to the old backends. Use L7 or client-side balancing.

Q: What's the cost of fixing gRPC imbalance with an L7 balancer, and what's the cheap alternative?
A: L7 has to terminate TLS and parse HTTP/2, so it adds CPU, an extra hop of latency, and another tier to scale. If you own the clients, use client-side balancing; the cheap mitigation is server-side MAX_CONNECTION_AGE, which forces clients to reconnect every few minutes so load rebalances.
Staff: Alert on per-instance request rate, not connection count, to catch this.

## Timeouts & retries
Q: A provider slows down for 30 seconds, and 200 servers retry 5× immediately. What happens?
A: Each request becomes up to 6 attempts, so load on an already struggling provider multiplies about 6×. That's a retry storm.

Q: What four things prevent a retry storm?
A: Explicit timeouts, exponential backoff with jitter, a retry budget (cap retries as a fraction of traffic), and a circuit breaker so you fail fast instead of piling on. Add an idempotency key so retries are safe.

Q: Jitter spreads retries out. Why isn't it enough on its own?
A: Total load is still up to 6× with 5 retries; jitter only smooths the timing. A retry budget caps retries as a fraction of traffic, and a circuit breaker stops calls entirely once the error rate crosses a threshold.

Q: What's a retry budget?
A: A cap on retries as a fraction of recent traffic (say 10%), so retries can never multiply load on a struggling dependency. Backoff and jitter only spread retries out in time.

Q: How does an idempotency key prevent a double charge on retry?
A: Generate one key per checkout and send the same key on every retry. The provider dedupes on it and returns the original result instead of charging again.

## APIs
Q: Where does userId belong in an API request?
A: In the auth token, not the URL or body, so a client can't act as another user by changing a parameter.

Q: When does REST beat gRPC?
A: External or browser clients, human-readable debugging, and loose contracts. gRPC fits internal service-to-service calls that want strict schemas and low overhead.
