# LLM Engineering Study Plan

Goal: an applied LLM engineer who understands the internals. Method: Stanford CS336 (Spring 2026) self-study, public materials only, scaled to one GPU and a small budget (see `curriculum.md`).

## Weekly rhythm (3 weekdays, 75 min each)

| When | What |
|---|---|
| Lecture day (1×) | `/llm-drill lecture <N>`: pretest → watch at 1.5x → drill + cards |
| Build days (2×) | `/llm-build`: work on the current assignment part; you write the code, tests are the done-check |
| Daily | Space "LLM · …" cards in your normal queue |

Lecture days turn into build days when lectures get more than 3 ahead of the current build stage (curriculum.md → Rhythm).

## Compute
Laptop (M1 Pro, `mps`) for debugging. GPU runs on Modal ($30/month free credit, $10/month cap of your own money), launched via `llm/practice/modal_run.py`. Every run gets logged in `progress.md`.

## Files
- `curriculum.md`: lectures, build stages, rules, mastery check
- `progress.md`: current stage and next lecture, scores, review dates, Modal spend
- `practice/`: refresher exercises and the Modal wrapper
- `notes/<slug>.md`: gaps and model answers per lecture or stage
- `cards/<slug>.md`: flashcards (same format as system-design); `python3 llm/space_sync.py [slug]` syncs them to Space as "LLM · <Topic>" decks
- `sessions/`: build session logs
- Assignment code: `~/cs336/<repo>` (separate private repos)
