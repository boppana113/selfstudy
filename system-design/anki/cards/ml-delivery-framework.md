# ML Delivery Framework

## Stages
Q: List the ML design framework stages in order.
A: Business goal → ML task framing → data and labels → features → model (baseline first) → training → offline eval → online eval → serving → monitoring and retraining.

Q: Where should the time go in an ML design interview?
A: Data, labels, metrics, and evaluation, more than infrastructure boxes.

## Business goal → ML objective
Q: For a video feed, the goal is watch time. What do you actually train on?
A: Per impression: P(watch > 30 s), and maybe expected watch time; rank by expected watch time. It rewards clickbait and binge loops, so keep long-term guardrails like next-day return and survey satisfaction.

Q: How do you choose the ML task type?
A: From the output you need: a label (classification), a number (regression), an ordered list (ranking), candidates from a huge pool (retrieval), or text (generation). Not from the product area.

Q: What should you propose before a deep model, and why?
A: A simple baseline (popularity, logistic regression, GBDT). It sets the bar the deep model has to beat and is often good enough.

## Labels & data
Q: Card fraud: where does the label come from, and what's the timing trap?
A: Chargebacks and disputes, which land days to weeks later. Train only on transactions past a ~60-day maturity window; otherwise recent fraud looks legitimate and the model under-predicts it.

Q: What is the selective-labels problem in fraud?
A: Transactions you block never get a label, so training data drifts toward what the old model allowed. Let a small random holdout through to keep the data unbiased.

Q: What should a fraud model optimize: counts or dollars?
A: Dollars. Output P(fraud) and threshold on expected loss, P(fraud) × amount, against the cost of declining a good customer.

## Offline metrics
Q: Harmful posts are 0.5% of traffic and the model hits 99.4% accuracy. Good?
A: No. Predicting "not harmful" for everything scores 99.5%, so 99.4% is worse than doing nothing. Use precision and recall at an operating point and PR-AUC, with the threshold set by the cost of a miss vs a wrong takedown.

## Rollout: shadow, canary, A/B
Q: What does shadow vs canary vs A/B each tell you?
A: Shadow tells you it works (serving correctness, latency, skew, disagreement with v1). Canary tells you it's safe (operational health on a small slice). The A/B tells you it's better (randomized, powered on business outcomes).

Q: What can a shadow deployment never tell you?
A: The effect of acting: customers churning after false declines, fraudsters adapting, review-queue load.

Q: Why can't a canary measure accuracy?
A: It's too small a slice to be statistically powered. It watches latency, errors, and block rate.

## LLM variant
Q: Building a support bot on an LLM API: what replaces training and data, and what gets harder?
A: Training becomes model selection (compare 2–3 models on your own eval set). Data becomes retrieval: chunking, indexing, and ACLs so customers never see internal docs. Evaluation becomes the hardest stage.

Q: How do you evaluate an LLM support bot?
A: Offline: a golden set of real tickets, scored by an LLM judge calibrated against humans for faithfulness and appropriate "I don't know". Online: resolution and escalation rate. Pin the model version and rerun evals on every prompt or model change.

Q: What are the safety concerns for an LLM support bot?
A: Prompt injection, hallucinated policies (made-up refunds), and PII leakage.
