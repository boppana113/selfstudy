# Rust Progress

Updated by `/rs-build` and `/rs-drill`. Safe to edit by hand.

**⏸ PAUSED 2026-11-25** for the DSA interview sprint (see `dsa/README.md`). Resume at the current stage below after MAANG loops (~Mar 2027). Weekend Space cards can continue.

**Gateway repo:** `~/llm-gateway` → https://github.com/boppana113/llm-gateway (public, created 2026-11-23)
**Current stage:** `enums-errors`: pretested 2026-11-25 → work through `journey/02-enums-errors.md` → `/rs-build`. (Ownership open items: 60s explain, clippy dead-code.)
**Prior attempt:** Rust Book ch. 1–4 in Dec 2025 (`~/task-vault`), stopped at ownership.

**Status values:** `pretested` → `building` → `built` (mastery items 1 done) → `mastered` (all 4 mastery items) 
**Next review** follows the same spaced schedule as system-design `/sd-drill`.

## Stages

| Slug | Status | Pretest | Built | Last drill | Drill score | Next review | Key gaps |
|---|---|---|---|---|---|---|---|
| basics | mastered | — | 2026-11-22 | — | — | — | — |
| ownership | built | 29% (2026-11-22) | — | 2026-11-24 | 67% | 2026-11-29 | error codes E0499/E0507/E0515; String vs &str = ownership; clone cost per request; clippy dead-code |
| enums-errors | pretested | 21% (2026-11-25) | — | — | — | — | E0004 exhaustive match; ? calls From (E0277); unwrap/expect panic, ? propagates; thiserror vs anyhow; serde from_str returns Result |

## Build log

| Date | Stage | What got built | Errors hit | Next |
|---|---|---|---|---|
| 2026-11-22 | basics | tokencost CLI: args, parse, match, cost fn, 1 test (test written by Claude) | ParseIntError panic via unwrap | stage 1 pretest |
| 2026-11-24 | ownership | gateway steps 1–3: config types, TOML load, find_key, 4 tests | E0063, E0382 (partial move), E0507, E0502 | step 4: project_for, allows, Debug redaction, E0106 |
| 2026-11-24 | ownership | steps 4–5: project_for, allows, redacted Debug, find_in, `check` CLI (main written by Claude, then let-else) | E0106, E0425 (scope), E0423/E0603 (`::`, privacy) | clippy dead-code decision; retype main; `/rs-drill` |
