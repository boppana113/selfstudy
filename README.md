# selfstudy

Personal study workspace, driven by Claude Code skills.

## Current focus (from 2026-11-25 until MAANG loops, ~Mar 2027)

**DSA sprint.** Interviews start in the new year and coding rounds are the gate. DSA 4 weekdays + Saturday, LLM 1 weekday, system design 1 session/week (Sunday). **Rust and LLD are paused.** See [dsa/README.md](dsa/README.md).

## DSA / coding interviews (current priority)

LeetCode-style practice run like a real interview, with a debrief after every session. See [dsa/README.md](dsa/README.md).

| Skill | Use |
|---|---|
| `/dsa pretest` | One-time placement: pattern sprint + 3 timed problems → writes the narrated plan |
| `/dsa [stage]` | Daily session: LeetCode sync, re-solve, 2 problems, debrief |
| `/dsa mock [meta\|google\|amazon]` | Company-format mock with a hiring scorecard |
| `/dsa call [company]` | Live voice interview in Chrome (hands-free, interruptible), debriefed from the transcript |
| `/dsa review` | Cold re-solves only |

## System design (ML / AI engineering track)

Interview prep built around Hello Interview. See [system-design/README.md](system-design/README.md) for the study loop and schedule.

| Skill | Use |
|---|---|
| `/sd-pretest [topic]` | Diagnostic quiz before studying a topic |
| `/sd-drill [topic \| review]` | Interviewer-style practice and spaced-repetition reviews |
| `/sd-mock [problem] [mid\|senior\|staff]` | Full mock interview with a scorecard |

Skills live in [.claude/skills/](.claude/skills/). Progress is tracked in [system-design/progress.md](system-design/progress.md).

## Low-level design

Classes, interfaces, OOP, and design patterns, following Hello Interview's LLD track. See [lld/README.md](lld/README.md).

| Skill | Use |
|---|---|
| `/lld-pretest [topic]` | Diagnostic quiz before studying a topic |
| `/lld-drill [topic \| problem \| review]` | Drills, problem breakdowns (e.g. `parking-lot`), spaced reviews |

## Rust (weekends, job-focused)

Build an LLM gateway in Rust modeled on Pydantic's AI Gateway, one concept stage at a time. See [rust/README.md](rust/README.md).

| Skill | Use |
|---|---|
| `/rs-build [stage]` | Saturday: read Pydantic's version, then build the stage (you write the code) |
| `/rs-drill [pretest\|review] [stage]` | Sunday: interview drill, predict-the-error, coding problem, spaced reviews |

## LLM engineering (3 weekdays, CS336 self-study)

Stanford CS336 (Spring 2026) from public materials, scaled to one GPU on Modal, aimed at applied LLM engineer roles. See [llm/README.md](llm/README.md).

| Skill | Use |
|---|---|
| `/llm-drill [lecture N\|stage slug\|review]` | Lecture day: pretest → watch → drill; stage mastery drills; spaced reviews |
| `/llm-build [stage]` | Build day: the current assignment part (you write the code, tests are the done-check) |
