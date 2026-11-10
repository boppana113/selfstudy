# Delivery Framework

## Stages & timing
Q: List the delivery framework stages with rough timings.
A: Requirements (~5m) → Core entities (~2m) → API (~5m) → [Data flow] → High-level design (~10–15m) → Deep dives (~10m).

Q: What are the three most common time sinks before the HLD?
A: Too many functional requirements (keep the top 3), estimates that don't change any decision, and writing full schemas instead of core entities.

## Requirements & NFRs
Q: Give four measurable non-functional requirements for Ticketmaster, including the surge.
A: Booking is strongly consistent (no double-booked seats). Search returns in under 500 ms at p99. Seat maps can be a few seconds stale. The on-sale surge handles about 10M concurrent users for a hot event.

Q: What's wrong with an NFR like "the system should scale"?
A: It's generic and untestable. State a number and a scope: a latency target, consistency vs availability per feature, the peak load, durability.

## Estimation
Q: When should you do a back-of-envelope estimate?
A: Only when the number changes a design decision. Otherwise defer it.

Q: For a URL shortener, which estimates change a design decision?
A: Read QPS decides cache vs no cache and whether to shard. The total URL count decides the short-code length. Total storage decides whether one database box is enough.

Q: URL shortener at 100M new URLs/month, 100:1 reads. Shard? Cache?
A: ~40 writes/s, so no sharding for throughput. ~4k reads/s (~8k at peak) is close to one Postgres box and redirects are hot, so cache them and put a CDN in front.
Staff: Say out loud that write QPS changes nothing here and skip it.

Q: URL shortener: how long should the short code be?
A: ~100M/month over 10 years is ~12B URLs. Base62 at 6 chars is ~57B and at 7 chars is ~3.5T, so 7 characters gives plenty of headroom.

## HLD & deep dives
Q: Which requirements does the HLD satisfy, and which do the deep dives satisfy? Who picks deep-dive topics?
A: The HLD satisfies the functional requirements; the deep dives satisfy the non-functional ones. At senior and above, the candidate proposes the deep dives.

Q: How do you build the HLD without overbuilding?
A: One endpoint at a time: trace the request path with the simplest components, then add pieces only where a non-functional requirement calls for them. No component without a reason.

## Level bar
Q: Name three things a staff candidate does in Ticketmaster that a senior doesn't.
A: Ranks the hard problems unprompted and spends time on the one most likely to break (the surge). Compares alternatives, picks by context, and names what would change the choice. Questions the requirements themselves (do hot events need seat selection?) and keeps the design small. Staff candidates also cover ops and evolution.

Q: What opening line signals staff-level ownership of the deep dives?
A: "Before going deeper, let me rank the hard problems, because I want to spend our time on the one most likely to break."

Q: Ticketmaster: which hard problem goes first, and why?
A: The on-sale surge (millions hitting one event at once), because it's what takes the whole system down. Then seat contention, then search. Handle the surge with a virtual waiting room that admits users at a controlled rate.

Q: Inside the booking deep dive, what does a staff candidate do that a senior doesn't?
A: Compares options (row lock, version check, Redis hold with a TTL), picks by context (hold, because users need time to pay), and names what would flip it (no holds → plain conditional update). "Only one buyer wins" is the problem itself, not a staff behavior.

Q: What requirement would a staff candidate question in Ticketmaster?
A: Whether hot events need seat picking at all. Best-available assignment removes most of the contention, so the hardest deep dive gets smaller.
