# Delivery Log

## Speak: 2026-11-04 (structure 75%, consequence-first 1/2)
- R1 (failure mode, kafka) 2/4: Payment consumer charges the card, crashes before committing the offset. What happens? Setup and length fine; no bottom line, and "charged twice" never said: went straight to the DB-check fix. User had assumed dedup already existed but didn't say so; coached to state assumptions out loud. No re-say (session shifted to the pausing/rambling discussion).
- R2 (failure mode, long-running-tasks, easy rep) 4/4: Why not transcode inside the upload request? Bottom line first ("the request times out"), consequence before fix (retry → processed multiple times), ~75 words, no stalls.
- Improved: "The client retries, and the process gets job multiple times. The fix is to go with an async pattern." (11-03 practice needed four tries to get consequence first.)
- Watch: say assumptions in the first sentence; pick the one-sentence anchor before speaking. User reports long word-search pauses and rambling in meetings: coached anchor-first, let the frame do the wording, time-buying phrases, plain word before precise term.
