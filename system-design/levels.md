# Answer Levels

Shared grading scale for `/sd-drill` and `/sd-pretest`. Each answer is graded by the **level it reached**, follow-up included. The target level is **senior**.

| Grade | Bar |
|---|---|
| ⬜ Below mid | Core mechanism wrong or missing, or "I don't know" with no reasoning. |
| 🟦 Mid | Mechanism correct, but needed prompting to get there. Names the fix without the consequence. No specific numbers or settings. |
| 🟩 Senior | Correct without prompting. States the consequence before the fix, gives a tradeoff with a reason, names the specific setting, metric, or number. |
| 🟪 Staff | Senior, plus second-order effects: operations (alerting, migration, reconciliation), how the system evolves, when they'd choose differently, effects on other systems. |

A level counts only if everything below it is also covered. A staff-flavored remark on top of a wrong mechanism is still below mid.

## Points (for the session %)
Below mid = 0, Mid = 1, Senior = 2, Staff = 2. Staff is capped at the senior score because senior is the target; this keeps spaced-repetition thresholds and past scores comparable. Staff answers still show in the level breakdown.

## Triage ladder
When teaching an answer, sort what a full answer covers into rungs, and mark which rung they reached:

```
**Reached: 🟦 Mid**
- ✓ Mid: <what they had, or what was missing for mid>
- → Senior: <what's missing for senior>
- → Staff: <stretch items, optional>
```

Use ✓ for a rung they reached and → for one they didn't. Put each point on the lowest rung where it's expected, and keep each rung to 1–3 items. Misconceptions go on the rung they block, stated directly ("Backwards: each partition has exactly one consumer per group").

## Session breakdown
Report the count at each level, for example `Below mid 1 · Mid 5 · Senior 0 · Staff 0`, and save it next to the score.
