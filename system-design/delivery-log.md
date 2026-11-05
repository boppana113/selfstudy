# Delivery Log

## Speak: 2026-11-04 (structure 75%, consequence-first 1/2)
- R1 (failure mode, kafka) 2/4: Payment consumer charges the card, crashes before committing the offset. What happens? Setup and length fine; no bottom line, and "charged twice" never said: went straight to the DB-check fix. User had assumed dedup already existed but didn't say so; coached to state assumptions out loud. No re-say (session shifted to the pausing/rambling discussion).
- R2 (failure mode, long-running-tasks, easy rep) 4/4: Why not transcode inside the upload request? Bottom line first ("the request times out"), consequence before fix (retry → processed multiple times), ~75 words, no stalls.
- Improved: "The client retries, and the process gets job multiple times. The fix is to go with an async pattern." (11-03 practice needed four tries to get consequence first.)
- Watch: say assumptions in the first sentence; pick the one-sentence anchor before speaking. User reports long word-search pauses and rambling in meetings: coached anchor-first, let the frame do the wording, time-buying phrases, plain word before precise term.

## Speak: 2026-11-05 (structure 69%, consequence-first 1/2)
- R1 (failure mode, kafka) 4/4: RF=3, acks=1, leader acks then dies before followers copy. What happens? Consequence before fix ("the producer doesn't know that the message was lost"). Content: acks=all waits for in-sync replicas, not partitions; explained ISR + min.insync.replicas=2 on request.
- R2 (design choice, kafka) 2/4: Partition key for driver location updates? Bottom line first, but no "because" (ordering per driver, even spread) and cost was a sizing plan, not a cost of the choice. Re-say landed; said "I picked" instead of "I'd pick".
- R3 (estimation, kafka) 3/4: 1M drivers / 4 s, 5k msg/s per consumer: min and provisioned partitions? Setup and math before number clean; 3× buffer had no reason. Content: 50 consumers in one group, not 50 groups (clarified). Re-say landed.
- R4 (failure mode, long-running-tasks) 2/4: 10 of 50 workers hung on poison video; why didn't queue size catch it, what to alarm on? Never said what the user sees; hedges ("whether or not the oldest jobs", "maybe an hour"). Coached the anchor ("queue size tells you how much is waiting, not how long"). Re-say: anchor landed, user impact still skipped.
- Improved: "The end result, the producer doesn't know that the message was lost and is not processed by a consumer." (last session's failure rep never said "charged twice")
- Watch: say "so the user sees ___" before the fix, especially when the setup is long; give a reason for every number and choice.
