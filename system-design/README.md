# System Design Study Plan (Hello Interview)

## The loop

```
/sd-pretest <topic>   →  study it on Hello Interview  →  /sd-drill <topic>
        ↑                                                     │
        └──── /sd-drill review (spaced repetition) ◄──────────┘
                     every ~4 topics: /sd-mock <problem>
```

`/sd-speak` runs ~10-minute delivery reps on questions you already know, graded only on how the answer is structured. Use it on days with no review due, or before a mock.

**Rule: one new concept at a time.** Don't pretest the next concept until the current one has been drilled (≥ 50%). Each day is one review (~10 min, most overdue first; the rest wait a day) plus work on the single current concept.

## Suggested pacing: ML / AI engineering track (~8–10 weeks at ~1 hr/day)

This is the active track. It follows the "Study order" in `curriculum.md`.

| Week | Focus | Mocks |
|---|---|---|
| 1 | Delivery framework, ML delivery framework, numbers, API design, data modeling | `url-shortener` (general baseline) |
| 2 | Caching, CAP, networking, problem framing & metrics, training data | `harmful-content-detection` |
| 3 | Features, embeddings & retrieval, LLM fundamentals, prompting | `visual-search`, `enterprise-rag` |
| 4 | RAG, vector DBs, LLM evaluation | `enterprise-rag` (redo), `chat-assistant` |
| 5 | Recsys & ranking, model architectures, ML serving, A/B testing, monitoring | `video-recommendations`, `ads-ctr-prediction` |
| 6 | Agents, LLM serving, guardrails, cost & reliability, fine-tuning | `support-agent`, `llm-inference-platform` |
| 7 | Kafka, Redis, blob storage, stream processing, scaling patterns | `fraud-detection`, `dropbox` |
| 8+ | Mostly mocks (3 ML/AI to 1 general), plus daily `/sd-drill review` | 3–4 per week |

## Suggested pacing: general track (~6–8 weeks at ~1 hr/day)

| Week | Focus | Mocks |
|---|---|---|
| 1 | Delivery framework, networking, API design, data modeling, numbers | `url-shortener` (mid) |
| 2 | Indexing, caching, sharding, consistent hashing, CAP | `dropbox` |
| 3 | Redis, Kafka, Postgres, DynamoDB/Cassandra | `ticketmaster`, `news-feed` |
| 4 | Elasticsearch, blob storage, stream processing, coordination, API gateway | `whatsapp`, `youtube` |
| 5 | Patterns: realtime, contention, scaling reads/writes | `uber`, `live-comments` |
| 6 | Patterns: blobs, long-running tasks, multi-step, geo | `top-k`, `payment-system` |
| 7+ | Mostly mocks at your target level, plus `/sd-drill review` daily | 3–4 per week |

Daily: start each session with `/sd-drill review` if anything is due (5–10 min).

## Files
- `curriculum.md`: topics and the testable points each skill quizzes on
- `progress.md`: status, scores, review schedule, mock history
- `delivery-log.md`: `/sd-speak` sessions and the consequence-first rate
- `levels.md`: per-answer grade by level (below mid / mid / senior / staff), used by drills and pretests
- `notes/<topic>.md`: gaps and interview-ready lines per topic
- `anki/cards/<topic>.md`: flashcards per topic and subtopic; `python3 anki/build.py` builds `anki/system-design.txt` for Anki import
- `sessions/`: mock interview transcripts and scorecards
