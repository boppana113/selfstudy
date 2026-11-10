# Progress

Updated automatically by `/sd-pretest`, `/sd-drill`, and `/sd-mock`. Safe to edit by hand.

**Status values:** `pretested` → `studied` → `drilled` → `solid`
**Scores** are percentages. **Next review** is set by `/sd-drill` using spaced repetition.

## Concepts

| Slug | Status | Pretest | Last drill | Drill score | Next review | Key gaps |
|---|---|---|---|---|---|---|
| delivery-framework | drilled | 50% | 2026-11-02 | 50% | 2026-11-06 | staff bar, quantified NFRs (latency, surge), estimates that change a decision, HLD one endpoint at a time, time sinks |
| long-running-tasks | drilled | - | 2026-11-09 | 58% | 2026-11-12 | 0-row worker sends no email (1 row = permission; update before email), page on ApproximateAgeOfOldestMessage (3rd miss) + runtime cap makes DLQ fire, Kafka: decision first + 1 consumer/partition + per-partition offset HOL + max.poll replay loop (no built-in DLQ), scale-in: consequence then protect busy workers, no Lambda for ~10-min jobs |
| networking | drilled | - | 2026-11-07 | 50% | 2026-11-10 | circuit breaker (2nd miss: threshold → open, fail fast; half-open probes), gRPC: HTTP/2 multiplexing over one conn + MAX_CONNECTION_AGE ~5 min, say what the user sees (hot boxes keep p99 high), ✅ connections can't be moved (11-07 api-design R6) |
| ml-delivery-framework | drilled | 44% | 2026-11-08 | 50% | 2026-11-11 | data ACLs in LLM apps (filter retrieval by user groups before prompt, skipped twice), say user impact unprompted (12k good customers declined/day), fraud actions depend on the score (decline / step-up / review / approve), threshold from P(fraud)×amount vs false-decline cost (AUC compares models), model selection replaces training, retrieval over fine-tune = freshness/citations/permissions |
| kafka | drilled | - | 2026-11-06 | 58% | 2026-11-09 | fan-out = consumer group per team + reset offsets by timestamp (not a new topic), hash(key) mod N remaps keys on repartition, poison message: max.poll rebalance ping-pong + retry topic/DLQ (log-and-commit = silent loss), consumers > partitions idle (say unprompted), idempotency at provider not local check, say what the user sees, min.insync cost = availability |
| api-design | drilled | 44% | 2026-11-07 | 58% | 2026-11-10 | say user impact + cost unprompted (recurring), concurrent retries: insert key in_progress first + 409, cursor = index seek no offset, own id → top-level (nest only list/create), GraphQL: N+1/DataLoader + persisted queries + depth limits, versioning: additive first + v1 adapter over v2 + min-version forced upgrade |
| numbers | drilled | 44% | 2026-11-09 | 67% | 2026-11-12 | say what the number decides (365 TB ≈ 100× one box), storage = 2nd shard trigger (several TB/box), cache past ~10k reads/s, past 100k shard Redis not replicas, dead cache overloads DB → failover replica + coalescing, size at 70% + reason for 2× peak, never peak on storage |

## Mock Interviews

| Date | Problem | Level | Overall | Weakest area | File |
|---|---|---|---|---|---|
