# Rust Progress

Updated by `/rs-build` and `/rs-drill`. Safe to edit by hand.

**Gateway repo:** `~/llm-gateway` (created in stage 1, step 0)
**Current stage:** `ownership`
**Prior attempt:** Rust Book ch. 1–4 in Dec 2025 (`~/task-vault`), stopped at ownership.

**Status values:** `pretested` → `building` → `built` (mastery items 1 done) → `mastered` (all 4 mastery items) 
**Next review** follows the same spaced schedule as system-design `/sd-drill`.

## Stages

| Slug | Status | Pretest | Built | Last drill | Drill score | Next review | Key gaps |
|---|---|---|---|---|---|---|---|
| basics | mastered | — | 2026-11-22 | — | — | — | — |
| ownership | pretested | 29% (2026-11-22) | — | — | — | — | E0502 shared-vs-mut borrow; lifetimes/E0106 unknown; returning refs vs owned; String = owned heap buffer |

## Build log

| Date | Stage | What got built | Errors hit | Next |
|---|---|---|---|---|
| 2026-11-22 | basics | tokencost CLI: args, parse, match, cost fn, 1 test (test written by Claude) | ParseIntError panic via unwrap | stage 1 pretest |
