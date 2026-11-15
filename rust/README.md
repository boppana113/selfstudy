# Rust Study Plan

Goal: a Rust job. Method: build one infra project that you actually use, an LLM gateway modeled on Pydantic's (see `curriculum.md`).

## Weekly rhythm (weekends only)

| When | What | Time |
|---|---|---|
| Saturday | `/rs-build`: read the matching Pydantic file, then build this stage's piece of the gateway | ~2–3 h |
| Sunday | `/rs-drill`: interview drill on the current stage, plus reviews that are due | ~1 h |
| Weekdays | Space "Rust · …" cards in your normal daily queue. Run the gateway; write down bugs for Saturday | ~2 min |

A new stage starts with `/rs-drill pretest <slug>` before building. A stage is done only after it passes the mastery check (curriculum.md → Rules).

## Files
- `curriculum.md`: stages, the Pydantic file to read, what to build, testable points, interview questions
- `progress.md`: current stage, scores, review dates, gateway repo path
- `notes/<slug>.md`: gaps and model answers per stage
- `cards/<slug>.md`: flashcards (same format as system-design); `python3 rust/space_sync.py [slug]` syncs them to Space as "Rust · <Topic>" decks
- `sessions/`: build session logs (what was built, which errors you hit, what's next)
