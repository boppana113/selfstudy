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
| kafka | drilled | - | 2026-11-06 | 58% | 2026-11-09 | fan-out = consumer group per team + reset offsets by timestamp (not a new topic), hash(key) mod N remaps keys on repartition, poison message: max.poll rebalance ping-pong + retry topic/DLQ (log-and-commit = silent loss), consumers > partitions idle (say unprompted), idempotency at provider not local check, say what the user sees, min.insync cost = availability |
| api-design | pretested | 44% | - | - | - | cursor vs offset (deep scan, shifting pages), user_id from token not body, idempotency key lifecycle + concurrent retries, WebSocket/GraphQL concrete costs, versioning + deprecation, nesting depth / action endpoints |

## Mock Interviews

| Date | Problem | Level | Overall | Weakest area | File |
|---|---|---|---|---|---|
