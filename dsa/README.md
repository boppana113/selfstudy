# DSA / Coding Interview Plan

Goal: pass MAANG coding rounds. Warm-up interviews in Jan 2027, MAANG loops in Feb–Mar 2027 (ask recruiters for 4–6 weeks of prep time, which is normal). Method: practice the interview, not just the answer, with a debrief after every session. See `curriculum.md`.

## Weekly rhythm (DSA sprint, until loops are done)

| When | What | Time |
|---|---|---|
| Mon, Tue, Thu, Fri | `/dsa`: sync, 1 due re-solve, 2 new problems, debrief | ~75 min |
| Wed | One LLM session (`/llm-drill` or `/llm-build`) | 75 min |
| Sat | `/dsa mock <company>` + `/dsa review` | ~2 h |
| Sun | `/sd-mock` or `/sd-drill review` (system design kept warm) | ~1 h |
| From week 5 | 1 human mock a week (Pramp free, or interviewing.io) | 1 h |

Rust and LLD are **paused** until loops are done (their progress files say where to resume).

## Before each session
- Turn off Copilot/autocomplete (status bar → Copilot icon → disable). Interviews use plain editors.
- Dictate your thinking: ⌘D in the Claude panel, send it unedited.
- In a problem: `hint`, `time?`, `done`.

## Files
- `curriculum.md`: stages, problems per stage, readiness bar, company mock formats
- `plan.md`: your narrated plan (written after the pretest, "This week" refreshed weekly)
- `progress.md`: stage status, re-solve queue, mock scorecards
- `log.md`: every attempt, with clock time, hints, verdict
- `debriefs/`: one short debrief per session (read the latest before the next session)
- `patterns/NN-<slug>.md`: narrated pattern guide, written when a stage starts
- `practice/`: your solution files (plain Python, no scaffolding)
- `cards/`: pattern-recognition flashcards → `python3 dsa/space_sync.py` → Space "DSA · …" decks
- `lc_sync.py`: pulls your public LeetCode profile (`boppana113`) into `lc-snapshot.md` / `lc-history.json`. Runs automatically at each session start. Solves you do on your own get picked up too.
