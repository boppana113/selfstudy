# Delivery Framework

## Stages & timing
Q: List the delivery framework stages with rough timings.
A: Requirements (~5m) → Core entities (~2m) → API (~5m) → [Data flow] → High-level design (~10–15m) → Deep dives (~10m).
Why: The order is front-to-back through the system. Requirements say what to build, entities say what's stored, the API says how it's called, the HLD connects the boxes so every functional requirement works, and the deep dives spend the remaining time on the non-functional ones. Timings add to ~40 minutes, leaving a few for questions. If the HLD isn't done by minute 25, the deep dives won't happen.

Q: What are the three most common time sinks before the HLD?
A: Too many functional requirements, estimates that don't change any decision, and full schemas instead of core entities.
Why: Picture spending 8 minutes listing 7 functional requirements for a chat app. Only 3 (send, receive, history) are going to get designed; the rest get mentioned and dropped. Then 5 minutes computing storage for a system that clearly fits one box. Then 5 minutes writing every column of the messages table. That's minute 18 with no boxes on the board, and the deep dives, where the level is decided, get 5 minutes.

## Requirements & NFRs
Q: Give four measurable non-functional requirements for Ticketmaster, including the surge.
A: Booking is strongly consistent (no double-booked seats). Search under 500 ms at p99. Seat maps can be a few seconds stale. The on-sale surge handles ~10M concurrent users for a hot event.
Why: Each one changes a decision later. Strong consistency on booking means a lock or conditional update in the booking deep dive. 500 ms search means an index like Elasticsearch, not LIKE queries. Seat maps being a few seconds stale means they can be cached and pushed, not read from the booking table. 10M concurrent means a waiting room, because no database takes that in one second.

Q: What's wrong with an NFR like "the system should scale"?
A: It's untestable and decides nothing. State a number and a scope.
Why: "Scale" could mean 100 users or 100M. Compare: "10M users hit one event's on-sale at the same minute." Now the surge is clearly the hard problem and the waiting room follows. "Search returns in under 500 ms at p99" tells you a search index is needed. A vague NFR costs you the deep dives, because nothing in it points at one.

## Estimation
Q: When should you do a back-of-envelope estimate?
A: Only when the number changes a design decision. Otherwise skip it and say so.
Why: Picture estimating write QPS for a URL shortener: 100M/month is ~40 writes/s. Any database handles that, so the number changes nothing, and the 2 minutes spent on it come out of the deep dives. Now read QPS: ~4k/s, 8k at peak, which is close to one Postgres box, so that number decides "add a cache and a CDN." Do that one, say what it decided, and move on.

Q: For a URL shortener, which estimates change a design decision?
A: Read QPS (cache or not, shard or not), total URL count (short-code length), and total storage (one box or not).
Why: Walk each. Reads at ~8k/s peak are near a single box, so a cache goes in. 12B URLs over 10 years need 7 base62 characters, since 6 only gives 57B and random codes need headroom. Storage at ~500 bytes × 12B is ~6 TB, which fits one box with care. Write QPS (~40/s) decides nothing, so you skip it out loud.

Q: URL shortener at 100M new URLs/month, 100:1 reads. Shard? Cache?
A: No sharding: ~40 writes/s is nothing. Yes cache: ~4k reads/s, ~8k at peak, is close to one Postgres box, and redirects are hot, so cache them and put a CDN in front.
Why: 100M / 2.5M seconds per month ≈ 40 writes/s. One Postgres primary does 10k+. Reads are 100× that: 4k/s average, 8k/s at peak. That's within one box but with no headroom, and most reads are for a few popular links, so Redis absorbs 90%+ of them and the DB sees a few hundred per second.
Staff: Say out loud that write QPS changes nothing here and skip it.

Q: URL shortener: how long should the short code be?
A: 7 base62 characters. 6 gives ~57B, which 12B URLs would fill too densely for random codes; 7 gives ~3.5T.
Why: 100M/month × 12 × 10 years = 12B URLs. Base62 (a–z, A–Z, 0–9) at 6 characters is 62⁶ ≈ 57B, so 12B would use 20% of the space, and random generation collides often. 62⁷ ≈ 3.5T puts 12B at under 1%, so collisions are rare and there's room for growth.

## HLD & deep dives
Q: Which requirements does the HLD satisfy, and which do the deep dives satisfy? Who picks deep-dive topics?
A: The HLD satisfies the functional requirements; the deep dives satisfy the non-functional ones. At senior and above, the candidate proposes the deep dives.
Why: Picture the HLD for Ticketmaster: client → API → booking service → database. That already lets a user search, view, and book. What it doesn't do yet is survive 10M users at once, or stop two users buying one seat. Those are the NFRs, and each becomes a deep dive. A mid-level candidate waits to be asked; a senior says "the two hard parts are the surge and seat contention, let me start with the surge."

Q: How do you build the HLD without overbuilding?
A: One endpoint at a time: trace the request path with the simplest components, and add a piece only where a non-functional requirement calls for it.
Why: Picture starting with "load balancer, API gateway, 3 microservices, Kafka, Redis, Elasticsearch" before any request has been traced. The interviewer asks why Kafka is there and there's no answer. Instead: POST /bookings goes client → API → database. That works. Then: "10M users at once would crush this," so the waiting room goes in front, with a reason attached. Every box on the board has a sentence explaining it.

## Level bar
Q: Name three things a staff candidate does in Ticketmaster that a senior doesn't.
A: Ranks the hard problems unprompted and spends time on the one most likely to break (the surge). Compares alternatives, picks by context, and names what would change the choice. Questions the requirements themselves and keeps the design small.
Why: Picture two candidates at minute 25. The senior says "let me deep dive on booking consistency" and designs a seat lock well. The staff candidate says "three things could break this: the surge, seat contention, and search. The surge takes the whole system down, so that's first." Then, in booking: "row lock, version check, or a Redis hold. Hold, because users need time to pay. If there were no hold step, I'd use the plain conditional update." Then: "do hot events need seat picking at all?" Each move shows ownership of where the time goes.

Q: What opening line signals staff-level ownership of the deep dives?
A: "Before going deeper, let me rank the hard problems, because I want to spend our time on the one most likely to break."
Why: It does three things in one sentence. It takes the steering wheel from the interviewer. It shows the candidate has a list, not just the first idea. And it gives a reason for the order. Compare the senior version: "I'd like to talk about booking consistency," which picks one problem without showing the others were considered.

Q: Ticketmaster: which hard problem goes first, and why?
A: The on-sale surge, because it takes the whole system down. Then seat contention, then search. Handle the surge with a virtual waiting room that admits users at a controlled rate.
Why: Picture a stadium show going on sale at 10:00. 10M people refresh in the same second. The seat map service, the booking database, everything behind the API gets 10M requests at once and falls over, and nobody books anything. Seat contention matters only once people are inside, and slow search annoys them but doesn't lose the sale. The waiting room holds everyone at a static page and lets 1,000 through per second, so the rest of the system sees a load it was sized for.

Q: Inside the booking deep dive, what does a staff candidate do that a senior doesn't?
A: Compares options, picks by context, and names what would flip the choice. "Only one buyer wins" is the problem itself, not a staff behavior.
Why: Picture the seat question. A senior designs one answer: a Redis hold with a 10-minute TTL, done well. A staff candidate puts three on the board: a row lock (simple, but holds a DB lock while the user types a card number), an optimistic version check (no lock, but the user finds out at payment that the seat is gone), and a Redis hold (reserves for 10 minutes, costs a second system). Picks the hold because users need time to pay. Then: "if the product didn't have a hold step, I'd drop Redis and use the conditional update."

Q: What requirement would a staff candidate question in Ticketmaster?
A: Whether hot events need seat picking at all. Best-available assignment removes most of the contention, so the hardest deep dive gets smaller.
Why: Picture the on-sale for a stadium show. With seat picking, 10,000 people click the same front-row seat and 9,999 get an error and try again, so contention is the system's hardest problem. With "best available in section 112," the system hands out seats from a pool in order, and contention drops to a counter decrement. A staff candidate asks the product question before building the hard thing, because the cheapest fix is to not need it.
