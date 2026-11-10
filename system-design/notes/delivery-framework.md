# Delivery Framework

## Pretest: 2026-11-01 (score 50%)
### Gaps
- ✅ (2026-11-02) Purpose of HLD vs deep dives: HLD satisfies functional reqs, deep dives satisfy non-functional reqs; candidate drives deep-dive selection at senior+ (thought deep dives = re-checking requirements/edge cases)
- Stage list: missing Core Entities, API, HLD/Deep Dive split; used "conceptual / low-level / summary" model; no timings
- Staff bar: thought it means "has seen the problem before" rather than ranking multiple hard problems, nuanced tradeoffs, ops, evolution
### Partial
- NFRs: good per-feature C vs A instinct for booking, but didn't call out vague/generic NFRs or quantify
- API: clean 1:1 mapping, but didn't state the principle; missing search params/pagination, booking body, auth via header
- Estimation: knows not to front-load, missing the "only when it changes a decision" rule
- HLD construction: knows not to draw everything up front, but treats LB/cache/queue as default additions rather than added when a requirement demands; missing "one endpoint at a time, trace the request path"
- Levels: mid vs senior distinction correct
- ✅ (2026-11-02) NFRs: per-feature C vs A now solid; still needs numbers (see drill)
### Solid
- Core entities at the right level of detail
### Hold-in-mind questions
- Which requirements does the HLD satisfy, and which do the deep dives satisfy? Who picks deep-dive topics?
- Rewrite Ticketmaster's non-functional requirements so they're specific and measurable.
- What concretely separates a staff-level answer from a senior one?

## Drill: 2026-11-02 (score 50%)
### Solid
- HLD satisfies functional reqs, deep dives satisfy NFRs; candidate proposes deep dives
- Picks deep dives tied to NFRs (Ticketmaster: booking consistency, search)
- Per-feature C vs A instinct; stage order (with a nudge on API)
### Still weak
- Staff bar: still described the senior bar ("proactively identify problems, weigh tradeoffs"). Staff = ranks hard problems unprompted, chooses by context and names what would change the choice, questions requirements, ops/evolution, fewer components
- Quantified NFRs: rewrite had only one number, no latency target; demanded strongly consistent seat maps (contradicts per-feature C/A); missed the on-sale surge NFR
- Time sinks: couldn't name what eats time (too many FRs, unused estimates, early schemas)
- Estimation: right to defer, but picked a number that changes nothing (server replicas). Use read QPS → cache/no shard, URL count → code length, storage → one box
- HLD construction: needed nudge to see unjustified components; didn't state "one endpoint at a time, trace the request, then add for NFRs"
### Interview-ready lines
- "Before going deeper, let me rank the hard problems, because I want to spend our time on the one most likely to break."
- "Booking is strongly consistent. Search returns in under 500ms at p99 with 10M concurrent users. Seat maps can be a few seconds stale."
- "Peak around 10k reads per second, so a single database plus a cache is fine and I won't shard."
- "Let me get each endpoint working with the simplest path, then add components where the non-functional requirements call for them."
- "I'll keep this to three functional requirements so we have time for the deep dives."
### Hold-in-mind questions
- Name three concrete things a staff candidate does in Ticketmaster that a senior doesn't.
- Give four measurable Ticketmaster NFRs, including the surge.
- For a URL shortener, which two estimates change a design decision, and what's the decision?
- What are the three most common time sinks before the HLD?
### Delivery
- Habit (RECURRING, 3rd session): stopping at "I'm not sure" instead of reasoning out loud (R3 "I'm not sure. Can you give me the answer?", R6 "I think... I'm not sure."). Recovery phrase: "Let me reason from what I know..."
- Rewrite (Round 3): "Both seniors solved the problems the interviewer pointed them at. The staff candidate got ahead of that. Right after requirements, they said 'the hard parts are seat contention, the on-sale surge, and search; the surge is what takes us down, so I'll spend the most time there.' Then in the booking deep dive, they compared row locks, optimistic concurrency and Redis holds, picked one for this traffic, and said what would change their mind. They even asked whether hot events need seat selection at all. And they kept the design small: no component without a reason."

## Drill: 2026-11-10 (score 25%; Below mid 1 · Mid 1 · Senior 0 · Staff 0)
### Questions
**R1 (explain it) ⬜ Below mid**: You're in a Ticketmaster interview, just past requirements. What would a staff candidate do from here that a senior wouldn't? Three concrete things.
- Follow-up: Contention and multi-user consistency are the same problem. Which problem is missing, which gets the most time, and what does staff do inside the booking deep dive that senior doesn't?
- You said: Staff ranks the hard problems (ticket-state contention, consistency for concurrent buyers, search availability). Follow-up: "I don't quite know", added search; in the deep dive staff "guarantees only one buyer wins", which is the problem itself, not a staff behavior.
- Re-answer: ranking came through (surge, contention, search; most time on surge), but still only behavior 1 of 3.
- Strong answer: "Right after requirements I'd rank the hard parts: the on-sale surge, seat contention, and search. The surge is what takes us down, so I'd spend the most time there, with a virtual waiting room that admits users at a controlled rate. In the booking deep dive I'd compare a row lock, an optimistic version check, and a Redis hold with a 10-minute TTL, pick the hold because users need time to pay, and say a plain conditional update wins if we didn't need holds. And I'd question the requirement: does a stadium on-sale need seat picking at all? Best-available assignment removes most of the contention."
- Staff adds: ops (what to alert on during an on-sale, e.g. waiting-room admit rate and hold expiry rate), fewer components, how the design evolves.

**R2 (estimation) 🟦 Mid**: You're designing a URL shortener. Which two estimates would you actually do, and what decision does each drive?
- Follow-up: 100M new URLs/month, 100:1 read:write. Run both numbers: shard? cache? And which estimate decides the short-code length?
- You said: Write QPS → shard (past ~10k writes/s); read QPS → replicas/Redis (said cache past 100k reads/s). Math: 100M/month ≈ 3.3M/day ÷ 100k s ≈ 33 writes/s, ×100 ≈ 3,300 reads/s, so one box, no shard, no Redis. Didn't answer code length.
- Strong answer: "Two estimates change decisions here. Reads: 100M a month is about 40 writes a second, and at 100 to 1 that's 4k reads a second, maybe 8k at peak. That's near what one Postgres box serves, and redirects are hot and latency-sensitive, so I'd put a cache in front, and a CDN, since a code's target never changes. Writes are tiny, so no sharding for throughput. Second, the total URL count sets the code length: over 10 years that's about 12 billion, and base62 at 7 characters is about 3.5 trillion, so 7 characters is plenty. Storage is 12 billion times about 500 bytes, around 6 TB, which is the one number I'd watch for a second shard trigger."
- Staff adds: write QPS is the estimate that doesn't change anything here, so say so and skip it; 301 vs 302 decides whether the CDN kills click analytics.
### Gap to senior
- Staff bar (3rd miss): rank the problems with the surge first, compare options and name what flips the pick, question the requirement (seat picking on hot events). "Only one buyer wins" is the problem, not a staff behavior.
- On-sale surge missing from the Ticketmaster hard-problem list (said it only after the hint).
- Cache threshold backwards: cache past ~10k reads/s (one box), not 100k; 100k is where you shard Redis.
- URL shortener: total URL count → code length (12B over 10 years → 7 base62 chars); storage over the retention window → one box or not.
- Put a number on the estimate in the first answer; include peak (~2× avg) for reads.
### Staff stretch
- Ops during an on-sale: alert on waiting-room admit rate, hold expiry rate, oversell reconciliation.
- Say which estimate you're skipping and why (write QPS for a shortener).
### Interview-ready lines
- "The hard parts are the surge, seat contention and search. The surge is what takes us down, so I'll start there."
- "For holds I'd compare a row lock, a version check and a Redis hold with a TTL. I'd pick the hold because users need time to pay; if we didn't need holds, a conditional update is simpler."
- "Before designing seat locking, do hot events need seat picking? Best-available assignment removes most of the contention."
- "About 4k reads a second, maybe 8k at peak, is close to one box, and redirects are hot, so I'd cache them."
- "About 12 billion URLs over 10 years; base62 at 7 characters is 3.5 trillion, so 7 characters."
### Delivery
- Habit (RECURRING, 4th session): stopping at "I don't know" instead of reasoning ("I don't quite know", "I can't come up with two better problems"). The re-answer with the unsure frame worked: it produced surge-first ranking right away.
- Rewrite (R2): "Two estimates change decisions here. 100M URLs a month is about 40 writes a second, and at 100 to 1 that's 4k reads a second, maybe 8k at peak. That's close to one Postgres box, and redirects are hot, so I'd cache them and put a CDN in front. Writes are tiny, so no sharding. The other is total URLs: over 10 years about 12 billion, and 7 base62 characters gives 3.5 trillion, so 7 characters is plenty."
- Did well: R2 follow-up ran setup → math → conclusion in order ("33 writes per second... well below 10,000... therefore sharding is not needed").
- Frame reminders: on (re-answers: 1)
