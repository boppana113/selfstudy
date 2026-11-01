# Delivery Framework

## Pretest: 2026-11-01 (score 50%)
### Gaps
- Purpose of HLD vs deep dives: HLD satisfies functional reqs, deep dives satisfy non-functional reqs; candidate drives deep-dive selection at senior+ (thought deep dives = re-checking requirements/edge cases)
- Stage list: missing Core Entities, API, HLD/Deep Dive split; used "conceptual / low-level / summary" model; no timings
- Staff bar: thought it means "has seen the problem before" rather than ranking multiple hard problems, nuanced tradeoffs, ops, evolution
### Partial
- NFRs: good per-feature C vs A instinct for booking, but didn't call out vague/generic NFRs or quantify
- API: clean 1:1 mapping, but didn't state the principle; missing search params/pagination, booking body, auth via header
- Estimation: knows not to front-load, missing the "only when it changes a decision" rule
- HLD construction: knows not to draw everything up front, but treats LB/cache/queue as default additions rather than added when a requirement demands; missing "one endpoint at a time, trace the request path"
- Levels: mid vs senior distinction correct
### Solid
- Core entities at the right level of detail
### Hold-in-mind questions
- Which requirements does the HLD satisfy, and which do the deep dives satisfy? Who picks deep-dive topics?
- Rewrite Ticketmaster's non-functional requirements so they're specific and measurable.
- What concretely separates a staff-level answer from a senior one?
