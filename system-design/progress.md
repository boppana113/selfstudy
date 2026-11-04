# Progress

Updated automatically by `/sd-pretest`, `/sd-drill`, and `/sd-mock`. Safe to edit by hand.

**Status values:** `pretested` → `studied` → `drilled` → `solid`
**Scores** are percentages. **Next review** is set by `/sd-drill` using spaced repetition.

## Concepts

| Slug | Status | Pretest | Last drill | Drill score | Next review | Key gaps |
|---|---|---|---|---|---|---|
| delivery-framework | drilled | 50% | 2026-11-02 | 50% | 2026-11-06 | staff bar, quantified NFRs (latency, surge), estimates that change a decision, HLD one endpoint at a time, time sinks |
| long-running-tasks | studied | - | 2026-11-01 | 42% | 2026-11-04 | visibility timeout/heartbeat mechanics, idempotent retries (partial completion, gated notify), SQS vs Kafka, autoscale metric, show the math |
| networking | studied | - | 2026-11-02 | 42% | 2026-11-05 | cross-server fan-out (pub/sub), L4 vs L7 + gRPC conn pinning, jitter/retry budget/circuit breaker, WebSocket capacity + headroom, crash recovery (reconnect herd, seq replay) |
| ml-delivery-framework | pretested | 44% | - | - | - | task type from output, concrete label/objective, offline vs online rollout, LLM variant stages, monitoring and feedback loops |

## Mock Interviews

| Date | Problem | Level | Overall | Weakest area | File |
|---|---|---|---|---|---|
