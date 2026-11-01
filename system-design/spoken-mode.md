# Spoken Mode

Shared rules for `/sd-pretest`, `/sd-drill`, and `/sd-mock`. Spoken mode is **on by default**. It's off only when the arguments include `typed`.

The user answers by voice dictation and sends the transcript unedited. The goal is to practice *saying* answers the way they would in a real interview, not writing them.

## At the start of the session
Say this once, briefly: "Spoken mode: answer by dictation (mic key or Fn twice) and send it without editing. Messy is fine. That's the point."

## How to ask questions
- Phrase every question the way an interviewer would *say* it: short, conversational, and with at most two parts. No tables, bullet lists, or code blocks in a question.
- Exception: "spot the flaw" and similar formats may show a short design, but keep the spoken prompt to one sentence.
- In mocks, keep interviewer turns to 1–3 sentences.

## If an answer looks typed
Signs: markdown bullets or numbering, backticks, headings, or perfectly edited prose for a long answer. Flag it once per session, in one line: "This looks typed. Try dictating the next one, even if it comes out rough." Then grade it normally.

## Feedback on delivery (after each answer)
After the content grade, add **one** line starting with 🗣️ about *how* it was said. Pick the single most useful of:

- **Bottom line first**: did they open with the answer or decision, or build up to it? ("Lead with 'I'd use optimistic locking' and then explain.")
- **Signposting**: for multi-part answers, did they announce the structure? ("There are three things to consider…")
- **Concision**: ramble or repetition, or too terse to show reasoning. Rough guide: a single-concept answer is 30–90 seconds spoken (~75–225 words).
- **Precision**: hedges ("kind of", "I guess", "maybe something like"), or vague words ("scalable", "fast", "handles load") where a specific mechanism or number belongs.
- **Tradeoff phrasing**: "I'd pick X because ___, and the cost is ___" vs. just naming X.

If the delivery was strong, say so in a few words. Don't invent a problem.

## End of session: delivery summary
Add a short **Delivery** section to the results:
1. The **one delivery habit** that showed up most, with a quote from their own answer.
2. A **rewrite**: take one of their actual answers and rewrite it the way a strong candidate would *say* it, 30–45 seconds' worth, conversational, not bullets.
3. One thing they did well in how they spoke.

## Saving
- `/sd-pretest` and `/sd-drill`: add a `### Delivery` subsection to the session's entry in `system-design/notes/<slug>.md` containing the habit and the rewrite.
- `/sd-mock`: fold delivery evidence into the **Communication** dimension of the scorecard, and include the Delivery section in the session file.
- If the same delivery habit appears in 3+ sessions (check the notes files and sessions), call it out as a recurring pattern.
