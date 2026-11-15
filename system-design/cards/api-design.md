# API Design

## Resource modeling, plural nouns, nesting
Q: How deep should you nest REST resources, e.g. users → posts → comments?
A: One level at most: `/posts/{id}/comments`. Anything with its own global id is top-level, so a client never needs the parent id just to fetch it. The cost of deep paths is being locked into one access pattern.
Why: Picture a notification that says "someone replied to your comment." It carries comment_id 987 and nothing else. With `/users/{u}/posts/{p}/comments/987` the app has to look up the post and then the author before it can fetch the comment: two extra round trips, ~100 ms on mobile, for a single read. With `/comments/987` it's one call. The relationship still exists; it lives in the row (comments.post_id), not in the URL.
Flip: Nest when the child has no meaning outside the parent and is never fetched alone, like line items on an invoice.

Q: A push notification links to comment 987. What URL fetches it, and why not /users/{u}/posts/{p}/comments/987?
A: `GET /comments/987`. The deep path forces the client to find the post and author first, which the notification doesn't carry.
Why: Walk the request. The notification payload has comment_id only. Deep path: the app calls `/comments/987` anyway to learn post_id, then the post to learn user_id, then the deep URL: three calls to do one. Top-level path: one call, and the server joins to post and author if the response needs them. The comment-to-post link is a column, comments.post_id, so nothing is lost by dropping it from the URL.

Q: Comments are top-level at /comments/{id}. Then what are /posts/{id}/comments for?
A: Listing and creating a post's comments. GET filters by post_id; POST takes post_id from the path and the author from the token.
Why: Picture the post page loading. It needs "all comments on post 42," and that's a query scoped to a parent: `WHERE post_id = 42 ORDER BY created_at`. The parent is the real context, so the path says so. Creating one is the same: the client knows the post it's commenting on, so post_id comes from the path, not the body where it could be forged. After that, the comment has its own id and is fetched, edited, and deleted at `/comments/{id}`.

Q: Cancel an order: DELETE, PATCH status, or POST /orders/{id}/cancel?
A: `POST /orders/{id}/cancel`. The cost is one more endpoint; what you get is the business rules in one place.
Why: Walk through what cancelling does: refund the card, put the stock back, email the customer, and refuse if the order already shipped. DELETE says the order no longer exists, but the customer still wants to see it as "cancelled" in their history. A generic `PATCH {status: "cancelled"}` lets a client set any status, so the server has to detect the transition and run the side effects anyway, and a client could PATCH straight to "delivered." An action endpoint takes the transition by name, runs the checks (409 if shipped), and does the side effects.
Flip: Plain PATCH is fine for fields with no rules behind them, like a shipping note.

## Pagination
Q: Why does offset pagination break on a live feed?
A: Two ways: deep pages get slower because the database scans and throws away every skipped row, and new inserts shift the pages so users see duplicates or miss items.
Why: Picture a feed sorted newest first. A user is on page 50 (OFFSET 1000): Postgres reads 1,020 rows and returns 20, and page 500 reads 10,020. Now 3 new posts arrive between page loads. Everything shifts down by 3, so the next page starts 3 items earlier than it should, and the user sees the last 3 posts of the previous page again. Delete 3 posts and they skip 3 instead.
Flip: Offset is fine for small, static lists, like an admin table of 200 rows where users want to jump to page N.

Q: What does a cursor encode, and what does the next-page query look like?
A: The last item's sort key plus a tiebreaker, e.g. (created_at, id), base64-encoded. The cost is no jumping to page N.
Why: The client got 20 posts, the last one created at 10:00:05 with id 884. The cursor is that pair, encoded. Next page: `WHERE (created_at, id) < ('10:00:05', 884) ORDER BY created_at DESC, id DESC LIMIT 20`. That's an index seek: Postgres jumps straight to the spot and reads 20 rows, whether it's page 2 or page 2,000. New posts land above the cursor, so they never shift the page. The id breaks ties when two posts share a timestamp.
Staff: Keep it opaque so you can change what it encodes without breaking clients.

## Auth placement
Q: Where does user identity go on POST /posts, and why not a user_id in the body?
A: In the `Authorization: Bearer <token>` header; the server derives user_id from the verified token. A user_id in the body lets any caller post as anyone.
Why: Picture a curious user opening dev tools. They see `{"user_id": 123, "text": "..."}` in the request, change 123 to 1, and send it. If the server trusts the body, that post now belongs to user 1. With a token, the server verifies the signature or looks up the session and takes the user from that. The caller can't forge it without the other user's credentials.

Q: JWT vs session token: the tradeoff?
A: A JWT is verified with no lookup but can't be revoked before it expires; a session token can be revoked instantly but costs a store lookup per request.
Why: Walk a request with each. JWT: the server checks the signature, reads user_id from the payload, done, zero network calls. But if the user is banned at 10:00 and the JWT expires at 11:00, they keep posting for an hour. Session token: the server hits Redis for the session on every call (under 1 ms), and banning the user is one DELETE. Short JWTs (15 min) plus a refresh token get most of both: cheap checks, and a ban takes effect at the next refresh.
Flip: Sessions when instant revocation matters (banking, admin tools); JWTs when the verifying service can't reach a session store.

## Idempotency and versioning
Q: Idempotency key on POST: who generates it, and what does a retry get back?
A: The client generates a UUID once per user action and reuses it on every retry. The server stores key → response and returns the original response, same resource id, instead of creating a duplicate.
Why: Picture a user tapping "Post." The app makes a UUID, sends it in a header, and the request times out. The app retries with the same UUID. The server finds the key in its table, sees the post it created the first time, and returns that same 201 and post id. Without the key, the retry is a fresh request, and the user has two posts. The key is per user with a TTL around 24 h so the table doesn't grow forever.

Q: The first POST succeeded but the phone timed out. Why not answer the retry with an "already created" error?
A: Because the phone never saw the first response, so an error makes the app show "failed" with no post id. Replay the original response instead.
Why: Walk it from the phone. Request 1 creates post 555, but the response is lost in a tunnel. The app shows a spinner and retries. If the server says 409 "already exists," the app has no post id and no success, so it shows an error, and the user taps Post again with a new key, creating a duplicate. If the server replays `201 {id: 555}`, the app shows the post as if the first try had worked.

Q: Two retries with the same idempotency key arrive at the same time. What happens?
A: A unique constraint on the key, or an insert-if-absent "in progress" row, lets exactly one proceed; the other waits for the stored response or gets a 409.
Why: Both retries check the table, both see no row, both create a post: that's the race. Insert the key first, before doing the work. Request A inserts (key, in_progress) and wins. Request B's insert fails on the unique constraint, so it either polls for A's stored response or returns 409 "in progress" and the client retries in a second. Either way, exactly one post exists.

Q: Rolling out a breaking response change to millions of mobile clients?
A: Prefer additive changes. If you must break, version the API, run both side by side, and enforce a minimum app version. The cost is maintaining two surfaces for months.
Why: Picture 5M installed apps parsing `author` as a string. You change it to an object and ship v2 of the backend. Every old app crashes on the next feed load, and you can't force 5M phones to update tonight. So v2 goes at `/v2/posts` and v1 keeps returning the string. You track traffic per version, watch v1 drop over weeks, and when the long tail is under ~1% a min-version check tells those apps to update.
Flip: Internal services you control can break and deploy together; versioning is for clients you don't control.

Q: You ship v2 of an API. How do you avoid maintaining two backends for v1 and v2?
A: Implement v1 as a thin adapter that calls v2 and reshapes the response into the old format. The cost is a long tail of adapter code until v1 is retired.
Why: Without the adapter, a bug fix in the feed query has to land twice, and the two drift. With it, a v1 request runs the v2 handler, then one function turns `author: {name: "x"}` back into `author: "x"`. One code path, one set of tests, and the adapter is ~50 lines that get deleted when v1 traffic hits zero.

Q: How do you actually get mobile users off v1 when you can't force app updates?
A: The app sends its version on every request; once v1 traffic is under ~1%, a min-supported-version check shows a blocking "update to continue" screen. Without it, old apps break at the cutoff.
Why: Picture the day you turn v1 off. Apps that never updated just get 404s and show a blank feed with no explanation. If instead the app had been checking `/config` at launch since day 1, you flip min_version to 4.2, and those users see "Please update" with a store link. The 1% threshold is where the support cost of breaking them is lower than running v1.
Staff: Ship the min-version check in v1 from day 1; apps without it can never be forced to upgrade.

## REST vs RPC vs GraphQL vs WebSocket
Q: Adding instant DMs to a REST app: what do you use, and what do you give up?
A: Keep REST for sending and history, and add WebSockets (or SSE for one-way push) for delivery. You give up statelessness: connections are pinned to a box.
Why: Walk a message. Alice POSTs it over REST; it's stored. Bob needs to see it in under a second without polling, so Bob's app holds a WebSocket open to connection server 7. The API has to know Bob is on server 7 (a connection registry), and server 7 has to be told (pub/sub). If server 7 restarts, Bob's connection dies and he reconnects elsewhere, then replays from his last sequence number. Scaling is now on connections per box, and nothing on the socket is HTTP-cacheable.
Flip: If "instant" means a few seconds and volume is low, long polling on plain REST avoids all of that.

Q: Two concrete costs of GraphQL over REST?
A: N+1 resolver queries, and losing HTTP/CDN caching because everything is a POST to one endpoint.
Why: Picture `{ posts { author { name } } }` for 20 posts. The posts resolver runs one query, then the author resolver runs once per post: 21 queries instead of 2. DataLoader batches those 20 author lookups into one. Then caching: REST's `GET /posts/42` can be cached by URL at the CDN; GraphQL's `POST /graphql` with a body can't, so every read reaches your servers. Add depth and cost limits too, or a client can ask for friends-of-friends-of-friends and take the database down.
Staff: For one screen's five calls, a BFF or aggregated endpoint is often cheaper than adopting GraphQL.

Q: GraphQL sends everything as a POST to one endpoint. How do you get CDN caching back?
A: Persisted queries: the client sends a hash of a pre-registered query as a GET, so caches key on the URL. It also blocks arbitrary queries from untrusted clients.
Why: At build time the app registers its 30 queries with the server, each getting a hash. At runtime the feed query is `GET /graphql?id=abc123&vars={...}`. Same URL for everyone on the same page, so the CDN serves it. And since only registered hashes are accepted, no one can send a hand-written 10-level query.

Q: A deploy restarts half your WebSocket chat servers. What happens, and how do you make it smooth?
A: Those users disconnect and reconnect elsewhere with jittered backoff, then replay from their last sequence number. Drain gracefully instead of hard-killing so you don't get a reconnect herd.
Why: Picture 50 servers at 100k connections each going down at once: 5M clients reconnect in the same second against the remaining 50 boxes, which were sized for 100k each. That's the herd. Draining: mark the server as not accepting new connections, send close frames to its clients spread over 5 minutes, and only then stop it. Each client reconnects after a random 0–5 s delay, updates the registry, and asks for messages since sequence 1,042, which it gets because messages were stored before delivery.
Staff: Replay only works if messages are durably stored before delivery.
