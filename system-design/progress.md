# Progress

Updated automatically by `/sd-pretest`, `/sd-drill`, and `/sd-mock`. Safe to edit by hand.

**Status values:** `pretested` → `studied` → `drilled` → `solid`
**Scores** are percentages. **Next review** is set by `/sd-drill` using spaced repetition.

## Concepts

| Slug | Status | Pretest | Last drill | Drill score | Next review | Key gaps |
|---|---|---|---|---|---|---|
| delivery-framework | drilled | 50% | 2026-11-02 | 50% | 2026-11-06 | staff bar, quantified NFRs (latency, surge), estimates that change a decision, HLD one endpoint at a time, time sinks |
| long-running-tasks | drilled | - | 2026-11-03 | 50% | 2026-11-06 | notify gating (conditional update, not S3), Kafka offsets/HOL blocking/partition cap, alarm on age of oldest message + scale-in draining, Little's Law (include duration), state the consequence before the fix |
| networking | studied | - | 2026-11-02 | 42% | 2026-11-05 | cross-server fan-out (pub/sub), L4 vs L7 + gRPC conn pinning, jitter/retry budget/circuit breaker, WebSocket capacity + headroom, crash recovery (reconnect herd, seq replay) |
| ml-delivery-framework | studied | 44% | 2026-11-04 | 38% | 2026-11-05 | LLM variant (model selection replaces training, data → retrieval+ACLs, eval hardest, cost/query, safety), imbalanced metrics (trivial-baseline number, PR-AUC), canary = ops health not accuracy, fraud selective labels + dollar-weighted objective |
| kafka | studied | - | 2026-11-04 | 42% | 2026-11-05 | consumer-group assignment (1 consumer per partition, extras idle), ordering is per partition, ISR + min.insync.replicas=2, commit-after → duplicates (state consequence), retry topic/DLQ, adding partitions breaks key ordering |

## Mock Interviews

| Date | Problem | Level | Overall | Weakest area | File |
|---|---|---|---|---|---|
