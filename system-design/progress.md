# Progress

Updated automatically by `/sd-pretest`, `/sd-drill`, and `/sd-mock`. Safe to edit by hand.

**Status values:** `pretested` → `studied` → `drilled` → `solid`
**Scores** are percentages. **Next review** is set by `/sd-drill` using spaced repetition.

## Concepts

| Slug | Status | Pretest | Last drill | Drill score | Next review | Key gaps |
|---|---|---|---|---|---|---|
| delivery-framework | studied | 50% | 2026-11-10 | 25% | 2026-11-11 | staff bar (3rd miss): surge first + compare options & name the flip + question seat picking, cache past ~10k reads/s not 100k, URL count → code length (12B → 7 base62), number in the first answer + peak, time sinks |
| long-running-tasks | drilled | - | 2026-11-09 | 58% | 2026-11-12 | 0-row worker sends no email (1 row = permission; update before email), page on ApproximateAgeOfOldestMessage (3rd miss) + runtime cap makes DLQ fire, Kafka: decision first + 1 consumer/partition + per-partition offset HOL + max.poll replay loop (no built-in DLQ), scale-in: consequence then protect busy workers, no Lambda for ~10-min jobs |
| networking | drilled | - | 2026-11-12 | 50% | 2026-11-15 | hung dependency = pool exhaustion (500/s × 2 s = 1,000 workers) before double charge, breaker open → fallback for the request (approve small + score later, hold large) not just half-open, gRPC = HTTP/2 multiplexing (3rd miss, not binary encoding), say what the user sees (overloaded old boxes → slow, no downtime; recurring), MAX_CONNECTION_AGE is server-side ~5 min, ✅ circuit breaker + half-open (11-12) |
| ml-delivery-framework | drilled | 44% | 2026-11-08 | 50% | 2026-11-11 | data ACLs in LLM apps (filter retrieval by user groups before prompt, skipped twice), say user impact unprompted (12k good customers declined/day), fraud actions depend on the score (decline / step-up / review / approve), threshold from P(fraud)×amount vs false-decline cost (AUC compares models), model selection replaces training, retrieval over fine-tune = freshness/citations/permissions |
| kafka | drilled | - | 2026-11-22 | 75% | 2026-11-29 | fan-out/replay = consumer group per team + reset offsets by timestamp within retention (3rd miss: "new topic" first), replay cost = broker disk reads → quota (groups never block each other), downstream outage: Kafka is the buffer, pause consumer + let lag grow, never back-pressure producers (2× this session), no built-in DLQ (it's a topic), ✅ log-and-commit = silent loss → DLQ (11-22) |
| api-design | drilled | 44% | 2026-11-22 | 50% | 2026-11-25 | in-flight retries: claim key in_progress under unique constraint → 409, not "Stripe handles it" (3rd miss), nest only list/create (single fetch by id always top-level), name the cost even with the frame shown (recurring), ✅ completed retry replays stored response, ✅ GET /comments/987 + FK reasoning (11-22) |
| numbers | drilled | 44% | 2026-11-09 | 67% | 2026-11-12 | say what the number decides (365 TB ≈ 100× one box), storage = 2nd shard trigger (several TB/box), cache past ~10k reads/s, past 100k shard Redis not replicas, dead cache overloads DB → failover replica + coalescing, size at 70% + reason for 2× peak, never peak on storage |
| data-modeling | studied | 38% | 2026-11-10 | 25% | 2026-11-11 | hot growing partition → (id, hour) bucket (2nd miss), N:M = item per edge + flipped GSI not a list (2nd miss), no cross-service FK → validate + UserDeleted anonymize + nightly reconcile (2nd miss), say why a number matters (833/s vs ~1k/s partition), snapshot fields denormalize free, name GSI cost unprompted |
| caching | drilled | 31% | 2026-11-15 | 58% | 2026-11-18 | name the mechanism before the fix (noeviction rejects writes, no TTL = missed delete is permanent; recurring), coalescing lock needs expiry + serve stale via soft expiry, DB first then delete (racing writers, not TTL freshness), global anonymous → CDN + purge not more Redis, hit-rate killers = cold cache/bulk invalidation/hot-set eviction, ✅ hot key copies + 70% math |
| db-indexing | pretested | 19% | - | - | - | LSM unknown (memtable/SSTable/bloom), leftmost-prefix rule, covering index = index-only scan, geospatial (geohash/quadtree), inverted index for text, hash = equality only no ranges |

## Mock Interviews

| Date | Problem | Level | Overall | Weakest area | File |
|---|---|---|---|---|---|
