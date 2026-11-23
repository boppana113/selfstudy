---
name: lld-drill
description: Interviewer-style drill on a low-level design (LLD) topic or problem (parking lot, vending machine, elevator) AFTER studying it, with pushback, over-engineering critiques, and spaced-repetition reviews. Use when the user says "lld drill", "lld review", or "quiz me on design patterns / OOP / LLD".
argument-hint: "[topic-slug | problem | review] [typed]  (spoken mode is on unless 'typed')"
---

# LLD Drill

Run `.claude/skills/sd-drill/SKILL.md` exactly as written, with these substitutions:

- Paths: `system-design/curriculum.md` → `lld/curriculum.md`, `system-design/progress.md` → `lld/progress.md`, `system-design/notes/` → `lld/notes/`, `system-design/cards/` → `lld/cards/`, `system-design/space_sync.py` → `lld/space_sync.py`.
- Keep using `system-design/levels.md` and `system-design/spoken-mode.md` (shared). Warm-up rewrites come from `lld/notes/` first, falling back to `system-design/notes/`.
- `review` mode covers LLD concepts only. If system design reviews are also due, mention it in one line.
- Skip the "every 4th concept suggest `/sd-mock`" step; instead, after `design-principles`, `oop-concepts`, and `design-patterns` are drilled, suggest `/lld-drill parking-lot`.

## LLD round formats (use these in place of scale-it-up and estimation)
- **Requirement → design**: a short requirement snippet; ask which classes and interfaces, and which pattern if any.
- **Spot the over-engineering / smell**: 6–10 lines of pseudocode with a type-switch chain, a needless Singleton, a subclass explosion, or a pattern that doesn't earn its place. Ask what's wrong and the fix.
- **Extend it**: "Now add X." Grade by how many existing classes have to change (open/closed).
- **Pattern duel**: Factory vs Strategy, Decorator vs subclass, Observer vs direct calls. Pick and defend, then argue the other side.
- **Failure mode**: a subscriber throws, two threads grab the same spot, an invalid transition is called. What happens?
- **Explain it**: "Walk me through the state diagram / call flow in 60 seconds."

## Problem mode (slug in Phase 2, e.g. `parking-lot`)
Run it like a 35-minute LLD interview: requirements → entities → relationships → key methods in code (the user writes it; never write it for them) → walk one use case → one or two "now add X" extensions. Score requirements, entity design, use of patterns, code clarity, and extensibility, each on the `levels.md` scale. Save a transcript to `lld/sessions/YYYY-MM-DD-<problem>.md` and add a row to the Problems table in `lld/progress.md`.

## Rule
Don't reproduce Hello Interview's paid content (text or code). Use general LLD knowledge and your own examples.
