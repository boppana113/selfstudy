# Progress

Updated automatically by `/sd-pretest`, `/sd-drill`, and `/sd-mock`. Safe to edit by hand.

**Status values:** `pretested` → `studied` → `drilled` → `solid`
**Scores** are percentages. **Next review** is set by `/sd-drill` using spaced repetition.

## Concepts

| Slug | Status | Pretest | Last drill | Drill score | Next review | Key gaps |
|---|---|---|---|---|---|---|
| delivery-framework | drilled | 50% | 2026-11-02 | 50% | 2026-11-06 | staff bar, quantified NFRs (latency, surge), estimates that change a decision, HLD one endpoint at a time, time sinks |
| long-running-tasks | drilled | - | 2026-11-04 | 50% | 2026-11-07 | notify gating = single conditional UPDATE + rows affected (not ACID/read-then-write), Kafka: 1 consumer/partition + partition cap + max.poll rebalance, page on age of oldest message + max-runtime cap, estimation: don't double peak, say intermediate number |
| networking | studied | - | 2026-11-05 | 25% | 2026-11-06 | connections can't be moved (3rd miss: dead/draining box → clients reconnect + replay), SSE holds a long-lived HTTP response (stateful), fan-out fix = per-stream pub/sub + hash by stream ID, autoscale on conns/box not CPU + drain, name retry budget + circuit breaker, L4/gRPC: HTTP/2 multiplexing + MAX_CONNECTION_AGE, say what the user sees |
| ml-delivery-framework | studied | 44% | 2026-11-04 | 38% | 2026-11-06 | LLM variant (model selection replaces training, data → retrieval+ACLs, eval hardest, cost/query, safety), imbalanced metrics (trivial-baseline number, PR-AUC), canary = ops health not accuracy, fraud selective labels + dollar-weighted objective |
| kafka | studied | - | 2026-11-04 | 42% | 2026-11-06 | (partial redrill 11-05: R1 Mid, R2 Senior; resume R3) ordering is per partition (say unprompted), min.insync cost = availability, commit-after → duplicates (state consequence), retry topic/DLQ, adding partitions breaks key ordering |
| api-design | pretested | 44% | - | - | - | cursor vs offset (deep scan, shifting pages), user_id from token not body, idempotency key lifecycle + concurrent retries, WebSocket/GraphQL concrete costs, versioning + deprecation, nesting depth / action endpoints |

## Mock Interviews

| Date | Problem | Level | Overall | Weakest area | File |
|---|---|---|---|---|---|
