# API Design

## Pretest: 2026-11-05 (score 44%; Below mid 1 · Mid 7 · Senior 0 · Staff 0)
### Questions
**Q1 🟦 Mid**: Instagram API: how do you lay out URLs for posts and comments, and when do you nest vs keep top-level?
- You said: users → posts → comments, nested in that order.
- Strong answer: Plural nouns, with the verb carrying the action: `GET /posts/{id}`, `POST /posts`, `GET /posts/{id}/comments`. I nest only one level, and only when the child is meaningless without its parent and is listed in its context. Anything with its own global id stays top-level, so I'd never make clients send `/users/{u}/posts/{p}` just to fetch a post. Deep paths lock you into one access pattern.

**Q2 ⬜ Below mid**: Feed returns posts newest-first and the user scrolls thousands. How do you paginate, and why?
- You said: 20 per page, rendered as the user scrolls; didn't name a mechanism.
- Strong answer: Cursor pagination. Offset has two problems on a feed: the database scans and discards every skipped row, so deep pages get slow, and new posts shift everything, so users see duplicates or miss items. Each response returns an opaque cursor encoding the last item's (created_at, id), and the next query is `WHERE (created_at, id) < cursor ORDER BY ... LIMIT 20`, an index seek that's stable under inserts. The cost is no random access to page N, which a feed doesn't need.

**Q3 🟦 Mid**: On `POST /posts`, how does the server know who the user is, and where does that go?
- You said: body holds content (images as presigned URLs); identity token in the headers.
- Strong answer: `Authorization: Bearer <token>`, either a JWT or a session token. The gateway or server verifies it and derives user_id from it. I never accept a user_id in the body, because anyone could put someone else's id there and post as them. JWTs are stateless and fast to verify but hard to revoke before they expire; session tokens need a lookup but can be killed instantly.

**Q4 🟦 Mid**: Flaky mobile POST times out and retries. How do you avoid duplicate posts?
- You said: idempotency key in the header; the server checks whether it's seen the key.
- Strong answer: The client generates a UUID once per user action and sends it as `Idempotency-Key` on every retry of that action. The server stores key → response (scoped per user, TTL around 24h). A retry gets the original response back, same post id and status, instead of creating a second post. A unique constraint on the key settles two concurrent retries: one inserts, the other waits or gets a 409.

**Q5 🟦 Mid**: Breaking change to the post response with millions of mobile clients. How do you roll it out?
- You said: new version in the path, e.g. POST /posts/v2.
- Strong answer: Prefer additive changes so most changes never need a new version. When one does, version as a prefix (`/v2/posts`) or a header, and run v1 and v2 side by side. Track traffic per version, announce a deprecation window, and use a minimum-supported-version forced upgrade, because old mobile app versions never fully disappear. The cost is maintaining two contracts until v1 traffic drains.

**Q6 🟦 Mid**: Adding DMs that must show up instantly. Same REST API? If not, what, and what do you give up?
- You said: not the same API; WebSocket for real-time, replay messages if the server crashes.
- Strong answer: Keep REST for sending messages and loading history; add a WebSocket channel for push delivery. What I give up: connections are stateful and long-lived, so I need sticky routing, a connection registry, scaling on connections per box, and reconnect plus replay from the last sequence number when a box dies. There's also no HTTP caching. If push were one-way, SSE would be simpler.

**Q7 🟦 Mid**: Clients need five REST calls for the post screen; someone suggests GraphQL. When is it right, and what does it cost?
- You said: good for multiple client types who pick the fields they want in one call; cost is complexity of a GraphQL server.
- Strong answer: GraphQL fits when many clients need different shapes of a connected graph and over-fetching or round trips hurt, like mobile on slow networks. The concrete costs: resolvers cause N+1 queries unless you batch with DataLoader. Everything is a POST to one endpoint, so HTTP and CDN caching are gone. Arbitrary queries can be very expensive, so you need depth and cost limits. Rate limiting and monitoring per operation get harder. For one screen, a BFF or aggregated endpoint is often cheaper.

**Q8 🟦 Mid**: Cancel an order: DELETE, PATCH status, or POST /orders/{id}/cancel?
- You said: PATCH /orders/{id}; DELETE is wrong because the order happened; POST /cancel implies async.
- Strong answer: Not DELETE, because the order still exists with a cancelled state. I'd use `POST /orders/{id}/cancel`, because cancelling is a state transition with business rules and side effects: refund, restock, and a 409 if it already shipped. A generic `PATCH status` lets clients set arbitrary statuses and hides that logic. An action endpoint can be fully synchronous; it doesn't imply async. PATCH is fine for plain field edits.

### Gap to mid
- Cursor vs offset pagination: name it, and know what a cursor encodes

### Gap to senior
- Pagination: offset's two failures (deep-scan cost, shifting pages → duplicates/misses); cursor = (created_at, id) index seek
- Auth: server derives user_id from the verified token; user_id in the body = impersonation; JWT vs session revocation tradeoff
- Idempotency: client-generated per action, server stores key → response with TTL, retry returns the original response, unique constraint for concurrent retries
- Versioning: /v2 prefix, run both, deprecation window, forced upgrade for old mobile apps, prefer additive changes
- Protocol costs said concretely: WebSocket (stateful, sticky, connection-count scaling, reconnect/replay); GraphQL (N+1, no HTTP caching, query cost limits)
- Nesting rules: one level max, globally addressable resources stay top-level; action endpoints for state transitions with side effects

### Hold-in-mind questions
- Why does offset pagination give duplicates or missed items on a live feed, and what does a cursor query look like?
- On a retry with the same idempotency key, what exactly does the server return, and what if two retries arrive at once?
- Name two concrete costs of GraphQL over REST.

### Delivery
- Habit (RECURRING; same root as kafka "fix before consequence" and long-running-tasks "reasoning unsaid"): naming the fix and stopping, without the cost or what the user gets ("the cost of this, however, is more added complexity"; Q4 never said what the retry returns). Bottom line came late in Q3 and Q6.
- Rewrite (Q2): "I'd use cursor pagination, not offset. Offset has two problems on a feed. The database has to scan and throw away every skipped row, so deep pages get slow. And new posts shift everything down, so the user sees duplicates. With a cursor, each response returns an opaque cursor, which is basically the last post's timestamp and id. The next request says 'give me 20 older than that', which is an index seek, and it stays stable as new posts come in. The cost is no jumping to page 50, and nobody does that on a feed."
- Did well: no "I'm not sure" this session; committed to an answer every time; Q4 opened with its bottom line.

## Drill: 2026-11-06 (partial, 3 of 6 rounds; not scored; Below mid 0 · Mid 3 · Senior 0 · Staff 0)
### Questions
**R1 (Failure mode) 🟦 Mid**: Your Instagram feed uses offset pagination, 20 per page. A user sees a post on page 3 they already saw on page 2. Why, and what would you change?
- Follow-up: What exactly goes inside the cursor, and what query does the server run for the next page?
- You said: New posts push older ones down between page loads, so the user sees duplicates; switch to cursor; cost is no count and no jumping ahead. Follow-up: opaque cursor, but guessed the server "applies some offset" from the last cursor.
- Strong answer: "New posts land at the top between page loads and shift everything down, so the user sees the same post twice, and deep offsets also scan and discard every skipped row. I'd return an opaque cursor encoding the last post's created_at and id. The next query is WHERE (created_at, id) < cursor ORDER BY created_at DESC, id DESC LIMIT 20: an index seek at any depth, no offset, stable under inserts. The cost is no jumping to page N."
- Staff adds: sign the cursor against tampering; ranked feeds page through a precomputed feed list or snapshot id.

**R2 (Spot the flaw) 🟦 Mid**: What's wrong with these endpoints?
```
GET    /users/{user_id}/posts/{post_id}/comments/{comment_id}
POST   /users/{user_id}/posts/{post_id}/comments
         body: { "user_id": 42, "text": "nice!" }
DELETE /orders/{order_id}        # cancels the order
```
- Follow-up: A push notification links to comment 987. What does the client need to know to fetch it, and how would you lay out the URL?
- You said: user_id in the body lets anyone comment as anyone, take it from the bearer token; cancel should be POST /orders/{id}/cancel. Said the first path looked fine; with the hint, didn't see the issue.
- Re-answer (cancel, design-choice frame): reasoning came through (business-rule check, error if shipped, switch to DELETE only to erase the record); skipped the cost slot.
- Strong answer: "Three problems. A comment has its own id, but this path makes the client know the post author and post first, which a notification doesn't carry, so I'd use GET /comments/987 and nest one level only for lists and creates: POST /posts/{id}/comments. user_id in the body lets anyone comment as anyone, so the author comes from the token. And cancel isn't a delete; the order still exists, cancelled, with a refund, a restock, and a 409 if it shipped, so POST /orders/{id}/cancel."
- Staff adds: make cancel idempotent; deep paths hard-code one access pattern and break when ownership changes.

**R3 (Failure mode) 🟦 Mid**: The phone times out on "Post" and retries with the same idempotency key, but the first request went through. What does the server send back on the retry, and what if the retry arrives while the first is still processing?
- Follow-up: The phone never saw the first response. If the retry gets an "already created" error, what does the app show, and what should the server return instead?
- You said: The key blocks the duplicate; the user sees "post already created." Read the concurrent case as the retry arriving first. Follow-up: thought "already created" is acceptable.
- Strong answer: "The retry gets the original response replayed: the same 201 and post id. The phone never saw the first response, so an error would make the app say 'failed' and the user would post again. For the concurrent case, the first request inserts the key as in_progress before doing the work, under a unique constraint on user and key, so the second insert fails and it returns a 409 'still processing' or waits and replays. Otherwise both check, find nothing, and both create a post."
- Staff adds: per-user keys with ~24h TTL; same key with a different body → 422; in_progress timeout for crashed requests.
### Gap to senior
- Cursor query has no offset: WHERE (created_at, id) < cursor, an index seek; id is the tiebreaker
- Nesting: anything with its own id is top-level (GET /comments/987); nest one level only for list/create; the relationship lives in the FK (comments.post_id), not the URL
- Idempotent retry replays the original response (same 201 + id), not an "already created" error
- Concurrent retries: insert the key as in_progress first, under a unique constraint; second gets 409 or waits
- Name the cost in design-choice answers (cancel endpoint)
### Resume
- Tomorrow: re-answer R3 follow-up with the unsure frame, then R4–R6 (GraphQL concrete costs, versioning + deprecation for mobile, WebSocket costs for DMs), then score the full drill.
### Hold-in-mind questions
- A notification links to comment 987. What URL fetches it, and why not nest it under the post?
- On a retry with the same key, what exactly does the server return, and why not an error?
### Delivery
- Habit (RECURRING): unsure frame opened, then a guess instead of reasoning. R1 follow-up: "I'm not sure... it would probably take your last cursor ID, apply some offset"; R3: "I'm not sure what the right behavior is, but I would imagine an already created message is acceptable."
- Rewrite (R3): "The first request already created the post, so the retry shouldn't create another one. The server looks up the key and replays the stored response, the same 201 and post id. That matters because the phone never saw the first response; if I sent an error, the app would say the post failed and the user would tap again. For the concurrent case, the first request writes the key as in progress before it does any work, with a unique constraint, so the second one fails that insert and gets a 409, retry shortly."
- Did well: R1 went cause → what the user sees → fix → cost, unprompted; R2 named the impersonation consequence for user_id in the body.
- Frame reminders: on (re-answers: 1)
