# System Design Curriculum

Ordered to follow Hello Interview's structure: Delivery Framework → Core Concepts → Key Technologies → Patterns → Problem Breakdowns.
Each topic lists the **testable points**: what the `/sd-pretest` and `/sd-drill` skills check you on. Section names may not match the site exactly, so rename slugs to match what you see in your subscription.

Workflow per topic: `/sd-pretest <slug>` → read the Hello Interview article/video → `/sd-drill <slug>` → spaced reviews via `/sd-drill review`.
After each phase (or every ~4 topics), run `/sd-mock` on a problem that uses what you just learned.

## Study order (ML / AI engineering track)

The skills follow this order when no topic is given. ML and AI loops usually include one general system design round, so the general concepts are kept but trimmed to what shows up most.

1. `delivery-framework`, `ml-delivery-framework`
2. `numbers`, `api-design`, `data-modeling`, `caching`, `cap-consistency`, `networking`
3. `problem-framing-metrics`, `training-data`, `feature-engineering`, `embeddings-retrieval`
4. `llm-fundamentals`, `prompting-structured-output`, `rag`, `vector-databases`, `llm-evaluation`
5. `recsys-ranking`, `model-architectures`, `ml-serving`, `ab-testing`, `ml-monitoring`
6. `agents-tool-use`, `llm-serving-inference`, `llm-safety-guardrails`, `llm-cost-reliability`, `fine-tuning`, `training-infra`
7. `kafka`, `redis`, `blob-storage`, `stream-processing`, `sharding`, `db-indexing`, `scaling-reads`, `long-running-tasks`
8. Everything else in Phases 1–3, as time allows

To switch back to the general track, delete this section. The skills then fall back to curriculum order.

**Sources for Phases 5–6:** use Hello Interview's ML content where your subscription has it. Otherwise these books map closely: *Machine Learning System Design Interview* (Aminian & Xu) for Phase 5 problems, *Designing Machine Learning Systems* (Huyen) for Phase 5 concepts, and *AI Engineering* (Huyen) for Phase 6.

---

## Phase 0: Delivery Framework

### `delivery-framework`: The Interview Delivery Framework
- Order and rough timing: Requirements (~5m) → Core Entities (~2m) → API/Interface (~5m) → [Data Flow] → High-Level Design (~10-15m) → Deep Dives (~10m)
- Functional requirements as "Users should be able to…"; limit to the top 3
- Non-functional requirements quantified and specific to the system (not "it should scale"): latency targets, consistency vs availability per feature, scale, durability
- Back-of-envelope estimation: only when it changes a design decision
- Core entities vs. a full schema; APIs mapped 1:1 to functional requirements
- HLD satisfies the functional reqs; deep dives satisfy the non-functional reqs
- Level expectations: mid-level (breadth, guided), senior (drives, some depth), staff (drives, finds the hard problems, makes tradeoffs without being prompted)

---

## Phase 1: Core Concepts

### `networking`: Networking Essentials
- OSI layers that matter: L3 (IP), L4 (TCP vs UDP), L7 (HTTP)
- TCP guarantees vs. UDP use cases (video, gaming, DNS)
- HTTP methods, idempotency, status codes, keep-alive
- REST vs gRPC vs GraphQL: when to use each
- Real-time: polling, long polling, SSE, WebSockets, WebRTC: tradeoffs and the infra each one needs (stateful connections, L4 vs L7 LB)
- Load balancing: L4 vs L7, algorithms (round robin, least connections, consistent hashing), health checks
- Timeouts, retries with exponential backoff + jitter, idempotency keys, circuit breakers
- Regionalization / latency from physical distance, CDNs

### `api-design`: API Design
- Resource modeling, plural nouns, nesting
- Pagination: offset vs cursor; why cursor wins at scale
- Auth placement (JWT/session token in header, never user id in body)
- Idempotency for writes, versioning
- Choosing REST vs RPC vs GraphQL vs WebSocket for the interface

### `data-modeling`: Data Modeling
- Relational vs document vs wide-column vs key-value vs graph: fit by access pattern
- Normalization vs denormalization tradeoffs
- Designing schema from access patterns; partition key / primary key choice
- Modeling 1:N and N:M relationships in SQL vs NoSQL
- Foreign keys, constraints, and when you give them up

### `db-indexing`: Database Indexing
- B-tree vs LSM-tree (read vs write optimized, compaction, SSTables, bloom filters)
- Hash indexes, composite indexes and column order (leftmost prefix), covering indexes
- Geospatial: geohash, quadtree, R-tree; PostGIS / Redis GEO
- Inverted indexes for full-text search
- Cost of indexes on writes

### `caching`: Caching
- Where: client, CDN, in-process, distributed (Redis/Memcached), DB buffer cache
- Patterns: cache-aside, write-through, write-behind, read-through
- Eviction: LRU, LFU, TTL
- Invalidation strategies and consistency issues
- Failure modes: thundering herd / cache stampede (request coalescing, jittered TTLs), hot keys (replication, key splitting), cache penetration
- When *not* to cache

### `sharding`: Sharding & Partitioning
- Vertical vs horizontal partitioning
- Shard key selection: cardinality, even distribution, query locality
- Range vs hash vs directory-based sharding
- Hot partitions / celebrity problem and mitigations
- Cross-shard queries and transactions; resharding cost
- Replication: leader-follower, multi-leader, leaderless; read replicas and replication lag

### `consistent-hashing`: Consistent Hashing
- Why mod-N hashing breaks on resize
- Hash ring, virtual nodes, minimal key movement
- Where it's used: DynamoDB/Cassandra, distributed caches, LB stickiness

### `cap-consistency`: CAP Theorem & Consistency Models
- CAP stated correctly (partition tolerance isn't optional, so the real choice is C vs A during a partition)
- Per-feature choice (e.g., booking = consistency, profile views = availability)
- Strong, linearizable, read-your-writes, causal, eventual
- Quorums (R + W > N), PACELC
- How the C/A choice drives tech choices

### `numbers`: Numbers to Know / Estimation
- Latency ladder: memory ~100ns, SSD ~100µs, network in-DC ~0.5ms, cross-region ~50-150ms
- Single-box capacity: a modern DB handles ~10k+ TPS and TBs of storage; Redis ~100k+ ops/s; one app server ~thousands of concurrent conns (WebSocket box ~100k+)
- QPS from DAU, storage from object size × count × retention
- Knowing when scale *doesn't* require sharding

---

## Phase 2: Key Technologies

### `redis`: Redis
- Data structures: strings, hashes, sets, sorted sets, lists, streams, geo, HyperLogLog, bloom
- Use cases: cache, distributed lock (and its pitfalls), rate limiter, leaderboard, pub/sub, sessions
- Single-threaded model, persistence (RDB/AOF), cluster mode and hash slots, hot keys

### `kafka`: Kafka / Message Queues
- Topics, partitions, offsets, consumer groups, brokers, replication (ISR)
- Ordering is per-partition only; partition key choice
- Delivery semantics: at-most/at-least/exactly-once; idempotent consumers
- Retention, replay, backpressure, DLQs
- Kafka vs SQS vs RabbitMQ; queue vs stream

### `postgres`: PostgreSQL / Relational DBs
- ACID, isolation levels (read committed, repeatable read, serializable), MVCC
- Row locks, `SELECT ... FOR UPDATE`, optimistic concurrency (version column)
- Scaling: read replicas, partitioning, connection pooling, when to shard
- JSONB, full-text, PostGIS extensions as "good enough" alternatives

### `dynamodb`: DynamoDB
- Partition key + sort key, GSIs vs LSIs
- Single-table design, access-pattern-first modeling
- Consistency options, conditional writes, transactions, DAX, Streams
- Hot partitions and adaptive capacity

### `cassandra`: Cassandra / Wide-Column Stores
- Partition key + clustering columns, query-first modeling, denormalization
- Leaderless replication, tunable consistency, gossip
- LSM write path, tombstones, compaction
- Good fit: write-heavy time series, chat messages

### `elasticsearch`: Elasticsearch / Search
- Inverted index, analyzers/tokenization, relevance scoring
- Shards and replicas, near-real-time refresh
- Keeping ES in sync with the primary DB (CDC), not as the source of truth
- Geo queries, aggregations

### `api-gateway`: API Gateway & Load Balancers
- Responsibilities: routing, auth, rate limiting, TLS termination, request validation
- Gateway vs load balancer; when to skip mentioning it

### `blob-storage`: Blob Storage & CDN
- S3 semantics, durability, metadata in DB with object in blob store
- Presigned URLs (upload/download direct to S3), multipart upload
- CDN for static/media, cache keys, invalidation

### `stream-processing`: Flink / Stream Processing
- Stateful stream processing, windows (tumbling, sliding, session)
- Event time vs processing time, watermarks, late data
- Checkpointing for fault tolerance; Lambda vs Kappa architecture

### `coordination`: ZooKeeper / Distributed Coordination
- Leader election, distributed config, service discovery
- Consensus basics (Raft/Paxos/ZAB), why you need a quorum
- Fencing tokens for distributed locks

---

## Phase 3: Patterns

### `realtime-updates`: Real-time Updates
- Client delivery: polling vs long polling vs SSE vs WebSockets
- Server-side fan-out: pub/sub (Redis), connection registry, consistent hashing of users to servers
- Scaling stateful connection servers, reconnection and missed-message catch-up

### `contention`: Dealing with Contention
- Pessimistic locking, optimistic concurrency control, isolation levels
- Distributed locks with TTL (Redis), reservation/hold pattern with expiry
- Queue-based serialization for hot items; virtual waiting rooms
- Double-booking / overselling scenarios

### `scaling-reads`: Scaling Reads
- Indexes → read replicas → caching → CDN → denormalization/materialized views
- Precomputation (fan-out on write) vs fan-out on read; hybrid for celebrities

### `scaling-writes`: Scaling Writes
- Vertical scaling first, then sharding; write batching; buffering with queues
- Write-optimized stores (LSM, Cassandra), sharded counters
- Load shedding and backpressure

### `large-blobs`: Handling Large Blobs
- Presigned URLs, multipart/chunked resumable uploads, chunk fingerprinting/dedup
- Upload-complete notifications (S3 events) and state reconciliation
- Download via CDN, range requests

### `long-running-tasks`: Managing Long-Running Tasks
- Async worker pattern: API returns job id, queue, worker pool, status polling/push
- Retries, idempotency, DLQs, visibility timeouts, heartbeats

### `multi-step-processes`: Multi-Step Processes
- Sagas (choreography vs orchestration), compensating actions
- Durable execution / workflow engines (Temporal, Step Functions)
- Outbox pattern, exactly-once side effects via idempotency

### `geo-proximity`: Proximity / Geospatial Search
- Geohash vs quadtree vs H3; Redis GEO vs PostGIS vs ES geo
- High-frequency location updates (in-memory, TTL), driver matching

---

## Phase 4: Problem Breakdowns (use with `/sd-mock`)

Ordered roughly by difficulty. Run a mock *before* reading the breakdown, then read it and compare.

| Slug | Problem | Key concepts exercised |
|---|---|---|
| `url-shortener` | Bit.ly | short-code generation, caching, scaling reads |
| `dropbox` | Dropbox / file sync | large-blobs, presigned URLs, chunking, sync |
| `ticketmaster` | Ticketmaster | contention, reservation holds, search, waiting room |
| `news-feed` | Facebook News Feed | fan-out on write vs read, celebrities, caching |
| `whatsapp` | WhatsApp / chat | websockets, realtime-updates, message delivery guarantees |
| `leetcode` | LeetCode | long-running-tasks, sandboxed execution, leaderboards |
| `uber` | Uber | geo-proximity, contention (driver matching), high-freq writes |
| `rate-limiter` | Distributed rate limiter | token bucket/sliding window, Redis, atomicity |
| `tinder` | Tinder | geo, swipe consistency, matching |
| `youtube` | YouTube | large-blobs, transcoding pipeline, CDN, adaptive streaming |
| `top-k` | YouTube Top-K / trending | stream-processing, count-min sketch, windows |
| `web-crawler` | Web crawler | queues, politeness, dedup, fault tolerance |
| `ad-click-aggregator` | Ad click aggregator | stream-processing, idempotency, reconciliation |
| `yelp` | Yelp | geo search, ratings aggregation, contention |
| `live-comments` | FB Live Comments | realtime fan-out, SSE, pub/sub partitioning |
| `post-search` | FB Post Search | inverted index, write-heavy indexing, ranking |
| `google-docs` | Google Docs | OT/CRDT, websockets, document servers |
| `online-auction` | Online auction | contention, realtime bids, consistency |
| `job-scheduler` | Distributed job scheduler | long-running-tasks, time-based partitioning, at-least-once |
| `payment-system` | Payment system | multi-step-processes, idempotency, ledger, reconciliation |
| `strava` | Strava | high-freq location writes, leaderboards |
| `distributed-cache` | Distributed cache | consistent hashing, replication, eviction |
| `notification-system` | Notification system | queues, fan-out, retries, preferences |
| `metrics-monitoring` | Metrics / monitoring | time-series storage, aggregation, alerting |

---

## Phase 5: ML System Design

### `ml-delivery-framework`: The ML Design Interview Framework
- Stages: clarify the business goal → frame it as an ML task → data and labels → features → model (baseline first) → training → offline evaluation → online evaluation → serving → monitoring and retraining
- Translating the business goal into an ML objective (e.g. "increase watch time" → predict P(watch > 30s), rank by expected watch time)
- Choosing the task type: classification, regression, ranking, retrieval, generation
- Always propose a simple baseline (heuristic, logistic regression, GBDT) before deep models
- Where the time goes: ML interviews weigh data, metrics, and evaluation more than infrastructure boxes
- The LLM application variant: requirements (quality bar, latency, cost) → high-level design → retrieval/context → model choice → evaluation → serving → safety → monitoring

### `problem-framing-metrics`: Problem Framing & Metrics
- Offline metrics: precision/recall/F1, ROC-AUC vs PR-AUC (imbalanced data), log loss, calibration
- Ranking metrics: NDCG, MAP, MRR, recall@k
- Online metrics: CTR, conversion, dwell time, retention, revenue, plus guardrail metrics
- Proxy-metric pitfalls (optimizing clicks gets you clickbait), multi-objective tradeoffs
- Picking the decision threshold from the business cost of false positives vs false negatives

### `training-data`: Training Data & Labels
- Label sources: human annotation, implicit feedback (clicks, watches), weak supervision, LLM labeling
- Biases: position bias, selection bias, popularity bias, feedback loops
- Label leakage; splitting train/test by time, not randomly
- Class imbalance: resampling, class weights, focal loss; negative sampling strategies
- Delayed labels (fraud, conversions) and data freshness

### `feature-engineering`: Features & Feature Stores
- Categorical features: one-hot, hashing trick, learned embeddings; normalizing numerical features
- Feature crosses, user-history and sequence features, context features (time, device)
- Feature stores: online vs offline stores, point-in-time correctness
- Training-serving skew: causes and prevention
- Batch-computed vs real-time (streaming) features

### `embeddings-retrieval`: Embeddings & Retrieval
- Two-tower models, contrastive loss, in-batch negatives, hard negatives
- Approximate nearest neighbor search: HNSW, IVF, product quantization; the recall vs latency vs memory tradeoff
- Pretrained vs fine-tuned embeddings; when an embedding model needs retraining (and reindexing)
- Measuring retrieval quality (recall@k on held-out pairs)

### `recsys-ranking`: Recommendation & Ranking Systems
- Multi-stage funnel: candidate generation (thousands) → ranking (hundreds) → re-ranking (tens)
- Candidate sources: collaborative filtering, matrix factorization, two-tower, content-based, graph
- Ranking with multi-task objectives (click, like, share, dwell) combined into a score
- Re-ranking for diversity, freshness, business rules, fairness
- Cold start for new users and items; exploration vs exploitation (bandits)

### `model-architectures`: Model Choices
- When to use logistic regression or GBDT vs deep models (data size, latency, interpretability)
- Recommendation and ads architectures: Wide & Deep, DLRM, DCN at a conceptual level
- Transformers and sequence models for user history and text; CNN/ViT for images; multimodal
- Justifying model complexity by the gain over the baseline

### `training-infra`: Training Infrastructure
- Data parallel vs model, tensor, and pipeline parallelism; why huge models need sharding (FSDP/ZeRO)
- Checkpointing, fault tolerance, GPU utilization
- Hyperparameter search, experiment tracking, reproducibility
- Retraining cadence: scheduled vs triggered; continual and online learning

### `ml-serving`: Model Serving
- Batch vs online vs streaming inference; precomputing predictions when possible
- Latency budgets across the funnel; caching predictions and embeddings
- Model compression: quantization, distillation, pruning
- GPU batching and autoscaling; CPU vs GPU serving economics
- Safe rollout: shadow mode, canary, rollback, model registry and versioning

### `ab-testing`: Online Experimentation
- Randomization unit (user, session, request), sample size and power, minimum detectable effect
- Novelty and primacy effects, network effects (cluster randomization), interleaving for ranking
- Guardrail metrics; explaining why offline gains don't show up online
- Holdouts for measuring long-term effects

### `ml-monitoring`: ML Monitoring & Feedback Loops
- Data drift vs concept drift; monitoring feature and prediction distributions
- Monitoring with delayed or missing labels (proxy signals, sampled human review)
- Degenerate feedback loops (the model trains on its own recommendations)
- Retraining triggers, alerting, and model performance dashboards

---

## Phase 6: AI / LLM Engineering

### `llm-fundamentals`: LLM Fundamentals for System Design
- Transformers and attention at interview depth; tokens, context windows, why cost and latency scale with tokens
- Sampling: temperature, top-p; determinism limits
- The KV cache and why long contexts are expensive
- The prompt vs RAG vs fine-tune decision: what each fixes (behavior vs knowledge vs format)
- Choosing models: frontier vs small vs open-weight; the capability, cost, and latency triangle

### `prompting-structured-output`: Prompting, Tools & Structured Output
- System prompts, few-shot examples, reasoning/thinking modes
- Structured outputs (JSON schema), validating and repairing output
- Tool and function calling: tool schema design, parallel tool calls
- Prompt versioning and treating prompts as code

### `rag`: Retrieval-Augmented Generation
- Ingestion pipeline: parsing, chunking strategy (size, overlap, structure-aware), embedding, keeping the index fresh
- Hybrid search (BM25 + dense), reranking with cross-encoders, query rewriting and decomposition
- Metadata filtering and **permission-aware retrieval** (ACLs per document)
- Context assembly, citations and grounding, the "lost in the middle" problem
- Failure modes: retrieval misses vs generation errors, and how to tell them apart

### `vector-databases`: Vector Databases
- HNSW vs IVF and their tradeoffs; filtered vector search
- pgvector vs dedicated vector databases vs Elasticsearch/OpenSearch: when each fits
- Sharding and replication of vector indexes; rebuilding when the embedding model changes
- Measuring recall in production

### `agents-tool-use`: Agents & Tool Use
- The agent loop: model → tool call → result → model; stopping conditions
- Tool design, planning, short-term vs long-term memory, context management and compaction
- Single agent vs multi-agent orchestration; MCP for tool integration
- Failure modes: loops, runaway cost, compounding errors; step and budget limits
- Human-in-the-loop approvals, sandboxing code execution, least-privilege tool access

### `llm-evaluation`: LLM Evaluation
- Golden datasets and how to build and maintain them
- LLM-as-judge: rubrics, pairwise vs pointwise, judge bias, calibrating against human labels
- RAG metrics: faithfulness/groundedness, answer relevance, context precision and recall
- Regression evals in CI on every prompt or model change
- Online signals: thumbs up/down, edits, retries, task completion; A/B tests for LLM features

### `llm-serving-inference`: LLM Serving & Inference
- Latency metrics: time to first token (TTFT), tokens per second, streaming
- Continuous batching, paged attention / KV cache management (vLLM), speculative decoding
- Quantization (INT8/INT4) and its quality tradeoffs; tensor parallelism for large models
- Prompt caching and prefix reuse; model routing and cascades (try a small model first)
- GPU capacity estimates: tokens/sec per GPU → GPUs needed for a target QPS

### `fine-tuning`: Fine-Tuning & Adaptation
- SFT, LoRA/PEFT, preference tuning (RLHF, DPO) at a conceptual level
- Data curation and quality over quantity; synthetic data
- When fine-tuning beats prompting or RAG, and when it doesn't; distilling into smaller models
- Evaluating a fine-tuned model against the base model

### `llm-safety-guardrails`: Safety & Guardrails
- Prompt injection, direct and indirect (via retrieved docs or tool results), and mitigations
- Input and output filtering, moderation classifiers, PII detection and redaction
- Reducing hallucination: grounding, citations, abstaining ("I don't know")
- Abuse prevention: rate limits, quotas, jailbreak monitoring

### `llm-cost-reliability`: Cost, Reliability & Observability
- Estimating token cost per request and per user
- Caching: exact-match, semantic, prompt/prefix caching
- Provider fallbacks, timeouts, retries, handling rate limits; an AI gateway layer
- Tracing multi-step LLM calls, logging prompts and responses (with privacy controls)

---

## Phase 7: ML & AI Problems (use with `/sd-mock`)

### ML system design

| Slug | Problem | Key concepts exercised |
|---|---|---|
| `video-recommendations` | Video recommendations (home feed) | recsys-ranking, embeddings-retrieval, multi-task objectives, cold start |
| `feed-ranking` | Social news feed ranking | recsys-ranking, problem-framing-metrics, ab-testing |
| `ads-ctr-prediction` | Ad click-through prediction | feature-engineering, calibration, model-architectures, ml-serving |
| `search-ranking` | Product/e-commerce search ranking | embeddings-retrieval, ranking metrics, training-data (position bias) |
| `harmful-content-detection` | Harmful content detection | multimodal models, class imbalance, human review loop |
| `fraud-detection` | Payment fraud detection | delayed labels, real-time features, thresholds, ml-monitoring |
| `people-you-may-know` | Friend recommendations | graph features, candidate generation, recsys-ranking |
| `eta-prediction` | ETA prediction for rides/delivery | regression, real-time features, ml-serving |
| `visual-search` | Visual similarity search | embeddings-retrieval, vector-databases, training-data |
| `spam-detection` | Email/message spam detection | training-data, adversarial drift, ml-monitoring |

### AI / LLM system design

| Slug | Problem | Key concepts exercised |
|---|---|---|
| `chat-assistant` | ChatGPT-style chat app at scale | llm-serving-inference, streaming, conversation storage, rate limits |
| `enterprise-rag` | Q&A over company documents | rag, permission-aware retrieval, llm-evaluation |
| `support-agent` | Customer support agent with actions | agents-tool-use, human-in-the-loop, guardrails, eval |
| `code-completion` | Code completion assistant | latency (TTFT), context assembly, small models, caching |
| `llm-inference-platform` | Multi-tenant LLM serving platform | continuous batching, GPU scheduling, routing, quotas |
| `answer-engine` | Web search answer engine with citations | rag, web retrieval, reranking, grounding |
| `llm-eval-platform` | LLM evaluation & regression platform | llm-evaluation, LLM-as-judge, pipelines |
| `doc-extraction` | Document extraction pipeline (invoices, forms) | structured output, long-running-tasks, human review |
| `ai-gateway` | AI gateway (routing, caching, fallbacks) | llm-cost-reliability, semantic cache, rate limiting |
| `llm-moderation` | LLM-powered content moderation at scale | cost cascades, llm-safety-guardrails, ml-monitoring |
