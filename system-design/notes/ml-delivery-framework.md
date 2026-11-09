# ML Delivery Framework

## Pretest: 2026-11-03 (score 44%)
### Gaps
- Task type selection: answered with product areas ("content moderation", "recsys") instead of classification / regression / retrieval; no reasoning from output type.
### Partial
- End-to-end stages: missing ML-task framing, offline vs online eval split, monitoring/retraining.
- Business goal → ML objective: said "recommendation problem" but no concrete label (e.g. P(watch > 30s), expected watch time) or ranking objective.
- Baseline first: right instinct, but no concrete baseline (popularity, LR, GBDT) and didn't frame it as the bar to beat.
- Offline → online: knew offline ≠ online, but conflated shadow deployment (no user exposure) with A/B testing; no proxy-metric point or guardrails.
- Time allocation: data + modeling, but left out metrics/evaluation as the heaviest-weighted area.
- LLM variant: only covered eval metrics; missed model selection over training, retrieval/context, cost/latency per query, safety, doc ACLs.
- Monitoring: feature drift + retraining, but reactive; missed concept drift, feedback loops, prediction-distribution and online-metric monitoring, scheduled retraining.
### Hold-in-mind questions
- For the video feed, what exact label would you train on, and what does the naive version of it get wrong?
- What does shadow vs canary vs A/B each tell you that the others can't?
- Which stages of the framework disappear or change when the "model" is an LLM API?
### Delivery
- Habit (RECURRING, 4th session): naming a category instead of committing to a specific answer and its reason ("essentially an alignment problem", "harmful posts equals content moderation"). Same root as earlier sessions: the reasoning stays unsaid.
- Rewrite (Q2): "Watch time is the business goal, but I need something to train on per impression. I'd predict the probability that the user watches more than 30 seconds, and probably the expected watch time too, then rank candidates by expected watch time. The risk is that this rewards clickbait and binge loops, so I'd keep longer-term guardrails like next-day return and survey satisfaction, and maybe blend them into the score."

## Drill: 2026-11-04 (score 38%)
Stopped after 4 of 6 rounds (user tired). Score is over the 4 rounds asked.
### Questions
**R1 (Scenario) 🟡**: You're designing fraud detection for card payments, and the goal is to reduce fraud losses. What exact label would you train on, and what does the naive version of that label get wrong?
- Follow-up: There's usually no labeling team in payments. Where does the fraud label come from, and how long after the transaction do you know it?
- You said: Binary is_fraud label, risk is mislabeling by a labeling team. After follow-up: comes from customer reports, arrives late so labels aren't updated at training time.
- Re-answer: Reasoning came through (report → analyst review → late label → 60–90 day window); missed the model impact (under-predicts fraud).
- Strong answer: "The label is is_fraud from chargebacks and disputes, which land days to weeks later, so I only train on transactions past a 60-day maturity window; otherwise recent fraud looks legitimate and the model under-predicts it. There's also selective labels: anything we block never gets a label, so I'd let a small random holdout through to keep the training data unbiased. And the goal is dollars, not counts, so I'd output P(fraud) and threshold on expected loss, P(fraud) times amount, against the cost of declining a good customer. Chargebacks also include friendly fraud, so the label is noisy."

**R2 (Explain it) 🟡**: Fraud model v2 beats v1 offline. Walk me through shadow, canary, and A/B as rollout steps. What does each tell you that the others can't?
- Follow-up: In shadow, v2 never blocks anything. What can shadow never tell you, especially in fraud?
- You said: Shadow verifies v2 works on live data without user exposure; canary is risk mitigation on a small group, measuring live accuracy; A/B is a 50/50 split to see if v2 beats v1. Follow-up: shadow can't tell you if v2 outperformed because labels are delayed.
- Strong answer: "Shadow tells me it works, canary tells me it's safe, and the A/B tells me it's better. Shadow scores live traffic with no effect, so it checks serving correctness, latency, training-serving skew, and where v2 disagrees with v1. What it can never show is the effect of acting: declined good customers churning, fraudsters adapting, review queue load. Canary is a small slice watching operational health, like latency, errors, and block rate; it's too small to measure accuracy. The A/B is randomized and powered on business outcomes like fraud loss in dollars and false-decline rate, with a readout delayed for label maturity."

**R3 (Spot the flaw) 🟡**: What's wrong with this plan?
```
Goal: flag harmful posts (~0.5% of all posts)
1. Label 200k posts with human reviewers
2. Random 80/20 train/test split
3. Go straight to a fine-tuned transformer
4. Offline metric: accuracy — we hit 99.4%
5. Ship to 100% of traffic once offline beats target
```
- Follow-up: If the model predicted "not harmful" for every post, what accuracy would it get?
- You said: Use a stratified split, start with an LR baseline, accuracy is skewed by the split, need an A/B before 100%. (Math slip: said 4,000 positives; it's 1,000.) After follow-up: accuracy is misleading with few positives; use precision, recall, AUC.
- Re-answer: Reasoning came through, but said 99% instead of 99.5%.
- Strong answer: "The big one is accuracy: predicting 'not harmful' for everything scores 99.5%, so 99.4% is worse than doing nothing. I'd use precision and recall at an operating point and PR-AUC, and pick the threshold from the cost of a miss versus a wrong takedown. Also, 1,000 positives is thin, so I'd use reports or heuristics to label likely-harmful posts first. I'd split by time or user to avoid near-duplicate leakage, start with a TF-IDF logistic regression baseline, and roll out through shadow, canary, and A/B with human review for medium-confidence posts."

**R4 (Scenario) ❌**: You're designing a customer support bot on an LLM API that answers from help docs. Which stages of the framework disappear, and which change?
- Follow-up: If training and features go away, what replaces them, and which stages get harder?
- You said: Data, features, and modeling disappear. Follow-up: training gets harder.
- Re-answer: asked (unsure frame), session ended before answer.
- Strong answer: "Training turns into model selection, data turns into retrieval, and evaluation becomes the hard part. I'd start with requirements: a quality bar, time-to-first-token budget, and cost per conversation. Instead of training, I compare two or three models on my own eval set. The data work becomes chunking and indexing the docs, with access control so customers never get internal docs. Evaluation is a golden set of real tickets with an LLM judge calibrated against humans, scoring faithfulness and appropriate 'I don't know', plus resolution and escalation rate online. Then safety, meaning prompt injection, hallucinated policies, and PII, and monitoring with a pinned model version and evals rerun on every prompt or model change."
### Still weak
- LLM variant stages: what replaces training (model selection), data → retrieval/context + ACLs, eval as the hardest stage, cost per query, safety, pinned versions
- Imbalanced metrics: lead with the trivial-baseline number (99.5%); PR-AUC over ROC-AUC
- Canary checks operational health, not accuracy; shadow can't show the effects of acting
- Fraud labels: selective labels (blocked transactions never labeled), dollar-weighted objective
### Interview-ready lines
- "Training turns into model selection, data turns into retrieval, and evaluation becomes the hard part."
- "With 0.5% positives, predicting 'no' for everything scores 99.5%, so 99.4% is worse than doing nothing."
- "Shadow tells me it works, canary tells me it's safe, and the A/B tells me it's better."
- "I train on chargeback labels after a 60-day maturity window and threshold on expected loss, P(fraud) times amount."
### Delivery
- Habit (RECURRING, 5th session): stopping at a short conclusion with no reasoning out loud. "Data and features and modeling are two components that would disappear." / "Training gets harder." Also vague words where a number belonged ("skewed" ×3 instead of "99.5%").
- Rewrite (R4): "So with an API model, training mostly goes away. I'm choosing a model, not building one, so I'd compare two or three on my own eval set for quality, latency, and cost per conversation. Data doesn't disappear, though; it becomes retrieval. How I chunk and index the help docs, and making sure a customer can't pull internal docs. The stage that gets hardest is evaluation: a golden set of real tickets, an LLM judge I've checked against humans, and online I'd watch resolution and escalation rate. Then safety, like prompt injection and made-up refund policies, and I'd pin the model version and rerun evals on every change."
- Did well: clear signposting and walking through items in order (R2 "first, let's start with shadow"; R3 step by step).
- Frame reminders: on (re-answers: 3)

## Drill: 2026-11-08 (score 50%; Below mid 0 · Mid 2 · Senior 0 · Staff 0)
Review mode, 2 rounds.
### Questions
**R1 (Scenario) 🟦 Mid**: You're designing an internal assistant that answers employee questions from Confluence and Slack using a hosted LLM API. Compared to a classic ML design, what takes the place of training and data collection, and which stage becomes the hardest?
- Follow-up: Fine-tune on the docs or retrieve at query time? Which would you pick, and given Slack has private channels, what can go wrong?
- You said: "Augmenting the LLM" with company data, then evals are hardest. Follow-up: retrieval at query time; fine-tuning is laborious and needs model weights. Skipped the private-channel part.
- Re-answer: Reasoning came through ("docs and Slack change constantly"; switch to fine-tuning for a specific response format). Still no private-channel risk.
- Strong answer: "Training turns into model selection, data turns into retrieval with access control, and evaluation becomes the hard part. I'd retrieve at query time because the docs change daily, retrieval can cite sources, and fine-tuning doesn't reliably teach facts. The big risk is permissions: every chunk carries its source's ACL at index time, and retrieval filters by the user's groups before anything reaches the prompt, so nobody gets a private exec channel quoted back. Eval is hardest because there's no single right answer: a golden set of real employee questions, an LLM judge checked against humans, scoring faithfulness and appropriate 'I don't know'."
- Staff adds: incremental re-indexing including deletes and permission changes; pinned model version with evals rerun on every change; prompt injection planted in Slack messages.
- Correction: "no weights, so no fine-tuning" is wrong; many hosted APIs offer fine-tuning. The real reasons are freshness, citations, facts, and per-user permissions.

**R2 (Estimation) 🟦 Mid**: 10M transactions/day, 0.1% fraud. The model flags 20,000/day, 8,000 are fraud. Precision, recall, and is it good enough to auto-decline everything flagged?
- Follow-up: That's 12,000 good customers declined daily. Instead of auto-declining, what would you do with the 20,000, and how would you set the threshold?
- You said: 10,000 fraud; precision 8,000/20,000 = 40%; recall 8,000/10,000 = 80%; not good enough because of false flags. Follow-up: tune the threshold to raise precision without hurting recall much, "look at the AUC".
- Re-answer: asked (failure-mode frame, say what the user sees); user skipped.
- Strong answer: "Precision is 40% and recall is 80%, so 60% of declines hit real customers. That's 12,000 good people a day whose card fails at checkout, and some churn. So I wouldn't auto-decline everything. I'd act differently depending on the score: auto-decline the top band where precision is 90%+, send the middle band to a step-up check like 3-D Secure or an SMS code, send the next band to an analyst queue sized to team capacity, and approve the rest. I set the cutoffs from expected cost: decline when P(fraud) times amount beats the cost of a false decline, so a $2,000 laptop gets declined at a lower score than a $5 coffee."
- Staff adds: fraudsters adapt to the threshold; random holdout for selective labels; monitor false-decline rate per merchant.
- Correction: AUC summarizes all thresholds (for comparing models); the threshold is one point on the PR curve, picked by business cost.
### Gap to senior
- Data access control in LLM apps: ACL per chunk at index time, filter retrieval by the user's groups before the prompt (asked directly, skipped twice)
- Say user impact unprompted: "12,000 good customers declined a day" (recurring across topics)
- Fraud actions depend on the score: decline / step-up auth / review queue / approve, not one threshold
- Threshold from expected cost (P(fraud) × amount vs cost of a false decline); AUC compares models, doesn't pick a threshold
- What replaces training: model selection on your own eval set (quality, latency, cost per query)
- Why retrieval over fine-tuning: freshness, citations, facts, permissions (not "no weights")
### Staff stretch
- Incremental re-indexing with deletes and permission changes; prompt injection via Slack
- Fraudster adaptation; false-decline rate per merchant
### Interview-ready lines
- "I'd filter retrieval by the user's permissions at query time, so a private channel never reaches the prompt. A system-prompt rule isn't access control."
- "At 40% precision, 12,000 good customers a day get declined, so I wouldn't auto-decline everything."
- "Top scores get declined, the middle band gets a step-up check, and borderline cases go to analysts."
- "I set the cutoff where P(fraud) times amount beats the cost of a false decline. AUC is for comparing models."
- "Training turns into model selection, data turns into retrieval with access control, and evaluation becomes the hard part."
### Delivery
- Habit (RECURRING, 6th session): short conclusions with the reasoning and user impact unsaid, plus answering one half of a two-part question. "This model is not good enough because it falsely flags a lot of non-positive transactions." / follow-up in R1 dropped the private-channel half entirely.
- Rewrite (R2): "Precision is 8,000 over 20,000, so 40%, and recall is 8,000 over 10,000, so 80%. The problem is the 60% that aren't fraud. That's 12,000 real customers a day whose card gets declined at checkout, and some of them leave. So I wouldn't auto-decline everything. I'd decline only the top scores, send the middle band to a step-up check like an SMS code, and put borderline ones in front of an analyst. And I'd set those cutoffs on dollars: decline when the probability times the amount is more than what a false decline costs us."
- Did well: setup before every number in R2 ("0.1% of 10 million is 10,000"), with the formula said out loud; bottom line first in the R1 follow-up ("I'd start with retrieving at query time").
- Frame reminders: on (re-answers: 1, one skipped by user)
