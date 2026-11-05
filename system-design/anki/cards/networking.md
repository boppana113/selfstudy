# Networking

## Real-time updates
Q: A comment is posted on API server A; viewers are connected to 300 SSE servers. How does it reach them?
A: The API publishes to a per-stream pub/sub channel, and connection servers subscribe for the streams their clients watch. The load balancer doesn't broadcast; it routes each request to one backend. Shard viewers by stream ID so each comment fans out to a handful of servers.

Q: A WebSocket box with 100k connections dies. Narrate recovery.
A: The connections are gone, so recovery is on the client. Clients detect a failed heartbeat and reconnect with jittered backoff so they don't stampede the other servers. The new server updates the connection registry, and the client replays from its last-seen sequence number. Messages are persisted before delivery, so nothing is lost.

Q: 10M concurrent WebSocket users. How many connection servers?
A: About 100k connections per box (memory-bound) gives about 100 servers. Run about 150 for failover and uneven stickiness. Autoscale on connections per box, with graceful draining.

## Load balancing
Q: L4 vs L7 load balancing, in one line each?
A: L4 balances connections (TCP); L7 balances requests (HTTP), so it can route by path or header, at the cost of terminating and parsing every request.

Q: Why does an L4 load balancer in front of gRPC leave new instances idle after a scale-out?
A: gRPC multiplexes requests over long-lived HTTP/2 connections, and L4 only balances when a connection opens. Existing connections stay pinned to the old backends. Use L7 or client-side balancing.

## Timeouts & retries
Q: A provider slows down for 30 seconds, and 200 servers retry 5× immediately. What happens?
A: Each request becomes up to 6 attempts, so load on an already struggling provider multiplies about 6×. That's a retry storm.

Q: What four things prevent a retry storm?
A: Explicit timeouts, exponential backoff with jitter, a retry budget (cap retries as a fraction of traffic), and a circuit breaker so you fail fast instead of piling on. Add an idempotency key so retries are safe.

## APIs
Q: Where does userId belong in an API request?
A: In the auth token, not the URL or body, so a client can't act as another user by changing a parameter.

Q: When does REST beat gRPC?
A: External or browser clients, human-readable debugging, and loose contracts. gRPC fits internal service-to-service calls that want strict schemas and low overhead.
