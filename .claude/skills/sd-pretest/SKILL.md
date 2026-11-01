---
name: sd-pretest
description: Diagnostic quiz on a system design concept BEFORE studying it on Hello Interview. Finds what the user already knows, surfaces gaps, and gives a targeted reading guide. Use when the user says "pretest", "test me before I read", or starts a new system design topic.
argument-hint: "[topic-slug] [typed]  (omit topic to pick the next unstarted one; spoken mode is on unless 'typed')"
---

# System Design Pretest

You are running a short **diagnostic** before the user studies a topic. The goal is to map what they know, not to teach. Retrieval attempts before studying (the pretesting effect) improve retention even when the answers are wrong, so wrong answers are expected and fine.

Arguments: `$ARGUMENTS`

## 1. Pick the topic

1. Read `system-design/curriculum.md` and `system-design/progress.md` (relative to the project root).
2. If an argument was given, match it to a slug (fuzzy match is fine: "consistent hash" → `consistent-hashing`). If it matches a Phase 4 or Phase 7 problem, tell the user to use `/sd-mock` instead and stop.
3. With no argument, pick the first concept that isn't in the progress table yet. Follow the curriculum's "Study order" section if it has one; otherwise use curriculum order (Phases 0–3, 5, 6).
4. Tell the user which topic you're testing and that it takes about 8 questions. Ask them to answer from memory, with no looking things up, and remind them that "I don't know" is a useful answer.
5. Unless the arguments include `typed`, read `system-design/spoken-mode.md` and follow it for the whole session: question phrasing, a 🗣️ delivery line after each one-line grade, the Delivery section in the results, and saving.

## 2. Ask questions ONE AT A TIME

Ask 8 questions total (fewer if they're clearly at 0 or clearly at mastery after 5). Build them from the topic's **testable points** in the curriculum, and cover as many distinct points as possible.

Mix these question types:
- **Recall** (1-2): "What is X / what problem does it solve?"
- **Mechanism** (2): "How does X actually work under the hood?"
- **Tradeoff** (2-3): "When would you choose X over Y? What do you give up?"
- **Application** (2): a concrete interview scenario, e.g. "You're designing a ticket booking system and two users click 'buy' on the same seat. Walk me through what happens."

Adapt: if they nail a question, make the next one harder on a different point. If they miss one, move to a different point rather than drilling the same hole.

After each answer, give **one line only**: ✅ solid / 🟡 partial / ❌ missed / ⏭️ didn't know, plus at most a few words of why. **Do not explain the correct answer yet.** Holding the explanation keeps the reading productive. Then ask the next question.

Score each answer: 2 = solid, 1 = partial, 0 = missed or didn't know.

## 3. Results

After the last question, give:

1. **Score**: X/16 (as a percentage too).
2. **Knowledge map**: a table of each testable point with ✅ / 🟡 / ❌ / (not tested).
3. **Brief answers**: one or two sentences per question showing what a strong answer included, for the ones they missed or got partially.
4. **Reading guide for Hello Interview**: 3–5 specific things to pay close attention to in the article or video, ordered by gap size. Point them to concepts, not page numbers (you don't know the article's exact text).
5. **Hold-in-mind questions**: 2–3 questions to answer *while* reading. They'll be asked again in `/sd-drill`.
6. If they scored ≥ 85%, say they can skim the article and go straight to `/sd-drill <slug>`.

## 4. Save

1. Write `system-design/notes/<slug>.md` (create, or append a dated section if it exists):
   ```
   ## Pretest: YYYY-MM-DD (score NN%)
   ### Gaps
   - ...
   ### Partial
   - ...
   ### Hold-in-mind questions
   - ...
   ```
2. Update the Concepts table in `system-design/progress.md`: add or update the row for the slug with status `pretested`, the pretest %, and a short "Key gaps" list (3–6 words each, comma-separated). Leave the drill columns as `-`.
3. Close with: "Study the topic on Hello Interview, then run `/sd-drill <slug>`."

## Rules
- Never quote or claim to reproduce Hello Interview's paid content. Use general system design knowledge.
- Keep questions grounded in how the concept shows up in an interview, not trivia.
- Use today's date from the environment for all dates.
