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
