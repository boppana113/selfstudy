# Networking

## Real-time updates
Q: A comment is posted on API server A; viewers are connected to 300 SSE servers. How does it reach them?
A: The API publishes to a per-stream pub/sub channel, and connection servers subscribe for the streams their clients watch. The load balancer routes; it doesn't broadcast.
Why: Picture 50k viewers on stream 7, spread across 300 boxes. Server A stores the comment and publishes to Redis channel `stream:7`. The 40 SSE servers that have stream-7 viewers are subscribed to that channel; they get the message and write it to their open connections. The other 260 servers never see it. If viewers are sharded by stream ID, those 40 become 5, and fan-out cost drops.

Q: A WebSocket box with 100k connections dies. Narrate recovery.
A: The connections are gone, so recovery is on the client: detect the failed heartbeat, reconnect with jittered backoff, update the registry, replay from the last sequence number. Nothing is lost because messages are stored before delivery.
Why: 10:00:00 the box dies. 10:00:15 each client's heartbeat times out. Each waits a random 0–10 s and reconnects; the LB sends them to the other 99 boxes, ~1k each, which is fine. The new box writes "user X is on box 23" to the registry. The client says "I have up to sequence 1,042," and the server sends 1,043 onward from the message store. Without jitter, 100k reconnects in one second would topple the next box.

Q: 10M concurrent WebSocket users. How many connection servers?
A: ~100k connections per box gives ~100 servers; run ~150 for failover and uneven stickiness. Autoscale on connections per box.
Why: An idle WebSocket costs memory (tens of KB) and a file descriptor, not CPU, so 100k per box is the usual number. 10M / 100k = 100. But a box dying sends 100k reconnects to the rest, and stickiness never spreads evenly, so 150 keeps each box at ~67k with room for a failure.

Q: Can you move a live connection off a dying or draining server?
A: No. A connection ends with its box. Clients reconnect elsewhere with jittered backoff and replay from their last sequence number; state lives in the message store and registry, never on the socket.
Why: A TCP connection is a pair of addresses and ports on two machines. There's nothing to hand to another box. So the design assumes connections die: the server keeps no state on the socket that matters, every message is stored before it's pushed, and the client tracks where it was. Draining just makes the deaths gradual.

Q: Does SSE keep a connection open?
A: Yes. It's one long-lived HTTP response the server never finishes, so SSE servers are stateful like WebSocket servers. Polling is the one without a held connection.
Why: Picture the HTTP exchange. The client sends GET /events. The server replies 200 with `Content-Type: text/event-stream` and then just keeps writing `data: ...` lines without ever sending the end. The connection stays open for hours. That box now owns that client, so scaling and draining work like WebSockets. Polling closes after each response.

Q: Live comments, mostly reads: SSE or WebSockets?
A: SSE, because traffic is one-way and it's plain HTTP: works through L7 LBs and proxies, auto-reconnects with Last-Event-ID. Posting is a normal POST.
Why: Picture 100k viewers and 50 comments a second. All 100k need the push; a few post. SSE handles the push over normal HTTP, so every proxy and load balancer already understands it, and when a connection drops the browser reconnects on its own and sends `Last-Event-ID: 1042` so the server resumes. Posting a comment is a regular POST. WebSockets would add a protocol upgrade and custom reconnect logic for nothing.
Flip: WebSockets when the client sends often (typing indicators, cursors, games); with SSE, upstream is just HTTP requests.

Q: What metric do you autoscale SSE/WebSocket connection servers on, and how do you scale down?
A: Connections per box, not CPU. Scale down by draining: stop routing new connections, close existing ones gradually, then terminate.
Why: 90k idle connections use 5% CPU. CPU-based scaling sees an idle box and kills it, and 90k people reconnect at once. Connections per box sees "90k of 100k, add a box." Scaling down: mark the box as draining so the LB sends it nothing new, close connections at 1k/s over 90 s so clients reconnect in a trickle, then terminate.
Staff: Pre-scale before a scheduled event; autoscaling lags a surge.

## Load balancing
Q: Why do HTTP/1.1 clients rebalance after a scale-out behind L4, but gRPC clients don't?
A: HTTP/1.1 clients open and close connections constantly, so new ones land on new boxes. gRPC multiplexes everything over one long-lived HTTP/2 connection, so the L4 balancer never gets another pick.
Why: Picture adding 5 servers to 10. HTTP/1.1 client: its pool churns connections every few seconds; within a minute, a third of them are on the new boxes. gRPC client: it opened one connection at startup to server 3 and sends every request down it. The L4 balancer only chooses at connect time, and there's no new connect. The 5 new boxes sit at zero until clients restart or MAX_CONNECTION_AGE (~5 min) forces a reconnect.

Q: L4 vs L7 load balancing, in one line each?
A: L4 balances connections (TCP); L7 balances requests (HTTP), so it can route by path or header, at the cost of terminating and parsing every request.
Why: L4 sees bytes and picks a backend when the connection opens; every request on that connection goes to the same place. L7 opens the request, reads `/api/v2/...` or a header, and picks per request. That costs TLS termination and parsing on the balancer, and one more hop. It buys per-request routing and fixes the gRPC pinning problem.

Q: Why does an L4 load balancer in front of gRPC leave new instances idle after a scale-out?
A: gRPC multiplexes requests over long-lived HTTP/2 connections, and L4 only balances when a connection opens. Existing connections stay pinned. Use L7 or client-side balancing.
Why: 20 clients, each with one connection to one of 10 servers. Add 5 servers. No client opens a new connection, so the L4 balancer makes no new decision. The hot boxes stay hot, p99 stays high, and the new boxes idle. The user sees no improvement from the scale-out.

Q: What's the cost of fixing gRPC imbalance with an L7 balancer, and what's the cheap alternative?
A: L7 terminates TLS and parses HTTP/2, so it adds CPU, a hop of latency, and another tier to scale. If you own the clients, use client-side balancing; the cheap mitigation is MAX_CONNECTION_AGE so clients reconnect every few minutes.
Why: Picture an L7 proxy in the path: every request is decrypted, parsed, re-encrypted, and forwarded, ~1 ms and a fleet of proxies to run. Client-side balancing: the client gets a list of backends from service discovery and round-robins streams across them, no middle box. MAX_CONNECTION_AGE=5m: the server politely closes each connection after 5 minutes, the client reconnects, the L4 balancer picks again, and within 5 minutes of a scale-out load is even.
Staff: Alert on per-instance request rate, not connection count, to catch this.

## Timeouts & retries
Q: A provider is slow and every checkout waits out a full timeout before failing. What stops that?
A: A circuit breaker. Once errors or timeouts cross a threshold, it opens and calls fail in milliseconds; after a cooldown, half-open test calls close it if they succeed.
Why: Picture the provider at 10 s per response. Every checkout thread waits 10 s, then fails. Threads pile up, your servers run out of them, and now unrelated pages are slow too. With a breaker at 50% failures over 10 s: it opens, and the next checkouts fail in 1 ms with "payment unavailable, try again." After 30 s it lets 1 call through; if that succeeds, it closes. The provider's outage stays the provider's outage.
Staff: While open, accept the order and charge it async from a queue, so the user sees "processing".

Q: A provider slows down for 30 seconds, and 200 servers retry 5× immediately. What happens?
A: Each request becomes up to 6 attempts, so load on an already struggling provider multiplies ~6×. That's a retry storm.
Why: 200 servers × 50 req/s = 10k/s normally. The provider slows, requests time out, each retries 5 times with no delay: 60k/s. The provider, which was struggling at 10k, is now buried and can't recover. Your retries are what keep it down. The 30-second blip becomes a 30-minute outage.

Q: What four things prevent a retry storm?
A: Explicit timeouts, exponential backoff with jitter, a retry budget, and a circuit breaker. Plus an idempotency key so retries are safe.
Why: Each stops one failure. Timeouts: a request can't hang for minutes. Backoff with jitter: retries spread over seconds instead of landing at once (1 s, 2 s, 4 s, ± random). Retry budget: retries capped at 10% of traffic, so 10k/s can never become 60k/s. Breaker: once failures cross 50%, stop calling entirely. Idempotency key: when a retry does go through twice, the provider dedupes it.

Q: Jitter spreads retries out. Why isn't it enough on its own?
A: Total load is still up to 6× with 5 retries; jitter only smooths the timing. A retry budget caps retries as a fraction of traffic, and a breaker stops calls once the error rate crosses a threshold.
Why: 10k/s × 6 attempts = 60k/s of work. Jitter turns a 60k spike into a steady 60k. The provider still gets 6× its load, just evenly. The budget says "retries may be at most 1k/s" so the ceiling is 11k. The breaker says "it's failing 80%, stop" so the ceiling is zero until it recovers.

Q: What's a retry budget?
A: A cap on retries as a fraction of recent traffic (say 10%), so retries can never multiply load on a struggling dependency.
Why: The client keeps a counter: requests in the last minute, retries in the last minute. If retries would exceed 10% of requests, the retry is skipped and the call fails. In normal times, a 1% error rate retries freely. In an outage, retries hit the cap at 10%, so the provider sees 1.1× load instead of 6×, and has room to recover.

Q: How does an idempotency key prevent a double charge on retry?
A: Generate one key per checkout and send it on every retry. The provider dedupes on it and returns the original result instead of charging again.
Why: The checkout makes key `ck_8f3a`. Request 1 charges $50 and the response is lost in a timeout. Request 2 arrives with `ck_8f3a`. The provider looks it up, finds the $50 charge, returns that same success. The customer sees one charge. Without the key, request 2 is a new $50 charge.

## APIs
Q: Where does userId belong in an API request?
A: In the auth token, not the URL or body, so a client can't act as another user by changing a parameter.
Why: Picture `DELETE /users/123/posts/5` where 123 comes from the URL. A user changes 123 to 124 and deletes someone else's post. If the server takes the user from the verified token and ignores the URL's user id (or checks they match), the request fails. The token can't be forged without the other user's credentials.

Q: When does REST beat gRPC?
A: External or browser clients, human-readable debugging, loose contracts. gRPC fits internal service-to-service calls that want strict schemas and low overhead.
Why: Picture a public API. Partners want to curl it and read JSON; browsers don't speak gRPC natively; the contract has to tolerate clients that update yearly. Now picture 50 internal services calling each other 100k times a second: protobuf is 5–10× smaller than JSON, generated clients catch type errors at compile time, and HTTP/2 multiplexing cuts connection overhead.
