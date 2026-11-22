---
name: lld-pretest
description: Diagnostic quiz on a low-level design (LLD) topic BEFORE studying it on Hello Interview: OOP, design principles, design patterns, concurrency. Use when the user says "lld pretest" or starts a new low-level design topic.
argument-hint: "[topic-slug] [typed]  (omit topic to pick the next unstarted one; spoken mode is on unless 'typed')"
---

# LLD Pretest

Run `.claude/skills/sd-pretest/SKILL.md` exactly as written, with these substitutions:

- Paths: `system-design/curriculum.md` → `lld/curriculum.md`, `system-design/progress.md` → `lld/progress.md`, `system-design/notes/` → `lld/notes/`, `system-design/cards/` → `lld/cards/`, `system-design/space_sync.py` → `lld/space_sync.py`.
- Keep using `system-design/levels.md` and `system-design/spoken-mode.md` (shared).
- Phase 2 problems go to `/lld-drill <problem>`, not `/sd-mock`.
- Closing line: "Study the topic on Hello Interview, then run `/lld-drill <slug>`."

## LLD question shapes (use instead of the system design examples)
- **Recall**: "What problem does Strategy solve?"
- **Mechanism**: "Sketch the interface and classes for X" (a few lines of pseudocode are fine; in spoken mode, describe them).
- **Tradeoff**: "Decorator or subclass here? Factory or a plain `if`?"
- **Application**: a requirement snippet ("support card, PayPal, and Apple Pay at checkout") → which pattern, if any, and why.
- **Over-engineering check**: show a small design with a needless pattern; ask whether it earns its place.

## LLD level bars (applied on top of `levels.md`)
- 🟦 Mid: names the right pattern or principle and its basic shape.
- 🟩 Senior: ties it to the requirement cue, states what adding a new variant costs with and without it, and says when *not* to use it.
- 🟪 Staff: testability, thread safety, how the design evolves across services (Observer → pub/sub), and language idioms (Python kwargs vs Builder).
