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
