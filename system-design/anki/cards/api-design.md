# API Design

## Resource modeling, plural nouns, nesting
Q: How deep should you nest REST resources, e.g. users → posts → comments?
A: One level at most: `/posts/{id}/comments`. Anything with its own global id stays top-level (`GET /posts/{id}`), so clients never need the parent's id just to fetch it. Deep paths lock you into one access pattern.

Q: A push notification links to comment 987. What URL fetches it, and why not /users/{u}/posts/{p}/comments/987?
A: `GET /comments/987`. The comment has its own id, and the notification doesn't carry the post or its author, so a deep path forces extra lookups. The comment-to-post link lives in the data (comments.post_id), not the URL.

Q: Comments are top-level at /comments/{id}. Then what are /posts/{id}/comments for?
A: Listing and creating a post's comments: `GET` filters WHERE post_id = id, and `POST` takes post_id from the path and the author from the token. Nest one level, only where the parent is the real context.

Q: Cancel an order: DELETE, PATCH status, or POST /orders/{id}/cancel?
A: Not DELETE, because the order still exists, now cancelled. `POST /orders/{id}/cancel` fits a state transition with business rules and side effects (refund, restock, 409 if shipped), while a generic PATCH lets clients set arbitrary statuses. Action endpoints can be synchronous.

## Pagination
Q: Why does offset pagination break on a live feed?
A: Two ways. Deep offsets make the database scan and discard every skipped row, so pages get slower. New inserts shift everything, so users see duplicates or miss items.

Q: What does a cursor encode, and what does the next-page query look like?
A: An opaque (base64) encoding of the last item's sort key plus a tiebreaker, e.g. (created_at, id). The next query is `WHERE (created_at, id) < :cursor ORDER BY created_at DESC, id DESC LIMIT 20`, an index seek that's stable under inserts. The cost is no jumping to page N.
Staff: Keep it opaque so you can change what it encodes without breaking clients.

## Auth placement
Q: Where does user identity go on POST /posts, and why not a user_id in the body?
A: `Authorization: Bearer <JWT or session token>`. The server derives user_id from the verified token. A user_id in the body can be set to anyone's id, which lets a caller impersonate other users.

Q: JWT vs session token: the tradeoff?
A: A JWT is verified statelessly (signature only, no lookup) but can't easily be revoked before it expires, so keep it short-lived and add a refresh token. A session token needs a store lookup per request but can be revoked instantly.

## Idempotency and versioning
Q: Idempotency key on POST: who generates it, and what does a retry get back?
A: The client generates a UUID once per user action and reuses it on every retry. The server stores key → response (per user, TTL around 24h) and returns the original response, with the same resource id, instead of creating a duplicate.

Q: The first POST succeeded but the phone timed out. Why not answer the retry with an "already created" error?
A: The phone never saw the first response, so an error makes the app show "failed" with no post id, and the user posts again. Replay the stored original response (same 201 and post id) so the retry looks like the first success.

Q: Two retries with the same idempotency key arrive at the same time. What happens?
A: A unique constraint on the key (or an insert-if-absent "in progress" record) lets exactly one proceed. The other waits for the stored response or gets a 409, so there's never a double create.

Q: Rolling out a breaking response change to millions of mobile clients?
A: Prefer additive changes. If you must break, version with a prefix (`/v2/posts`) or a header, run v1 and v2 side by side, track traffic per version, and set a deprecation window. Old app versions never disappear, so enforce a minimum-supported-version upgrade.

Q: You ship v2 of an API. How do you avoid maintaining two backends for v1 and v2?
A: Implement v1 as a thin adapter that calls v2 and reshapes the response into the old format. One code path, so bug fixes land once; the cost is a long tail of adapter code until v1 is retired.

Q: How do you actually get mobile users off v1 when you can't force app updates?
A: The app sends its version on every request; track v1 traffic, and once it's under ~1%, a min-supported-version check at launch shows a blocking "update to continue" screen. Without it, old apps just break at the cutoff.
Staff: Ship the min-version check in v1 from day 1; apps without it can never be forced to upgrade.

## REST vs RPC vs GraphQL vs WebSocket
Q: Adding instant DMs to a REST app: what do you use, and what do you give up?
A: Keep REST for sending and history; add WebSockets (or SSE if push is one-way) for delivery. You give up statelessness: sticky routing, a connection registry, scaling on connections per box, reconnect plus replay from the last sequence number, and no HTTP caching.

Q: Two concrete costs of GraphQL over REST?
A: N+1 resolver queries (fix with DataLoader batching), and losing HTTP/CDN caching because everything is a POST to one endpoint. Also: arbitrary queries need depth and cost limits, and rate limiting gets harder.
Staff: For one screen's five calls, a BFF or aggregated endpoint is often cheaper than adopting GraphQL.

Q: GraphQL sends everything as a POST to one endpoint. How do you get CDN caching back?
A: Persisted queries: the client sends a hash of a pre-registered query as a GET, so CDNs and HTTP caches can key on the URL. It also blocks arbitrary queries from untrusted clients.

Q: A deploy restarts half your WebSocket chat servers. What happens, and how do you make it smooth?
A: Connections can't move, so those users disconnect and reconnect elsewhere with jittered backoff, updating the connection registry, then replay from their last per-conversation sequence number. Drain instead of hard-killing: stop routing new connections and send close frames spread over minutes to avoid a reconnect herd.
Staff: Replay only works if messages are durably stored before delivery.
