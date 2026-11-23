# LLM Engineering Curriculum: CS336, self-study

**Source:** [Stanford CS336: Language Modeling from Scratch](https://cs336.stanford.edu/), Spring 2026 (Hashimoto, Liang). Everything used here is public: lectures on [YouTube](https://www.youtube.com/watch?v=JuoVZkPBiKk&list=PLoROMvodv4rMqXOcazWaTUHhq-yembLCV), slides in [stanford-cs336/lectures](https://github.com/stanford-cs336/lectures) or the [lecture viewer](https://cs336.stanford.edu/lectures/), and assignment repos with handouts and unit tests. Enrolled students also get Gradescope, Slack, office hours, and A3's training API. We do without all of those.

**Goal:** an **applied LLM engineer** who understands the internals. You won't train models at work. You will explain the KV cache, attention cost, quantization, and why RLHF changes behavior, and use that in interviews and in the Rust gateway. That goal is why we cut multi-GPU training, the pretraining-data pipeline, and leaderboard chasing.

**Not covered here:** agents, RAG, prompting, and app-level evals. Those stay in system-design Phase 6, unchanged for now. Trim Phase 6 later if it turns out to repeat this track.

## Rhythm

Three weekdays a week, 75 min each. System design, LLD, and Rust keep their slots.

| Day | Skill | What |
|---|---|---|
| Lecture day (1×/week) | `/llm-drill lecture <N>` | 5-min pretest → watch the lecture at 1.5x (~55 min) → 15-min drill, cards, re-say block |
| Build days (2×/week) | `/llm-build` | Work on the current stage's assignment part. You write the code; the unit tests are the done-check |
| Any day | Space "LLM · …" cards | In your normal daily queue |

**Gate:** once the next lecture is **more than 3 past the current build stage's last lecture** (the "Lectures" line on each stage), the lecture day becomes a build day. With the gate, the estimate is about 6–7 months, finishing around June 2027.

## Rules

- **You write every line.** Claude coaches, reviews, and explains test failures. Same rule as the Rust track.
- **The tests are the done-check.** Each assignment ships `tests/adapters.py`. You wire your code into it, and `uv run pytest` goes from `NotImplementedError` to green.
- **Debug on the laptop, run on the GPU.** The M1 Pro (16 GB, `mps`) is for correctness at toy size. Real runs go on **Modal** (Starter plan: $30/month free credit). The hard cap is **$10/month of your own money** on top of that. Before any GPU run, estimate the cost (GPU $/hr × expected time) and log it in `progress.md`.
- **Modal prices** (modal.com/pricing, 2026-11): T4 ~$0.59/hr · L4 ~$0.80/hr · A10 ~$1.10/hr · A100 40GB ~$2.10/hr · A100 80GB ~$2.50/hr · H100 ~$3.95/hr. Use the cheapest GPU that fits. Triton work runs fine on a T4 or L4.
- **Assignment code lives outside selfstudy**, in `~/cs336/<repo>` (cloned from `stanford-cs336`), pushed to a **private** GitHub repo (out of courtesy to the course: no public solutions). `selfstudy` tracks progress, notes, and cards only.
- **Mastery check (all 3) before moving to the next stage:**
  1. The stage's tests pass, or for the paper/sweep stages, the deliverable exists.
  2. You can explain the stage's mental model in about 60 seconds.
  3. You can answer one numbers question for the stage cold (param count, FLOPs, memory, or tokens/sec; see "Numbers" on each stage).

## Lectures (Spring 2026)

Slugs are used by `/llm-drill`, `progress.md`, and `cards/<slug>.md`. "PDF" lectures have slides in the lectures repo. "Viewer" lectures are executable lecture code at `https://cs336.stanford.edu/lectures/?trace=lecture_NN`.

| # | Slug | Topic | Materials | Feeds stage |
|---|---|---|---|---|
| 1 | `l01-tokenization` | Overview, tokenization | Viewer | a1-tokenizer |
| 2 | `l02-pytorch-accounting` | PyTorch, einops, resource accounting | Viewer | a1-transformer |
| 3 | `l03-architectures` | Architectures, hyperparameters | [PDF](https://github.com/stanford-cs336/lectures/blob/main/lecture_03.pdf) | a1-transformer |
| 4 | `l04-moe-attention-alts` | Attention alternatives, mixture of experts | [PDF](https://github.com/stanford-cs336/lectures/blob/main/lecture_04.pdf) | a1-training |
| 5 | `l05-gpus` | GPUs, TPUs | [PDF](https://github.com/stanford-cs336/lectures/blob/main/lecture_05.pdf) | a2-profiling |
| 6 | `l06-kernels-triton` | Kernels, Triton | Viewer | a2-flashattention |
| 7 | `l07-parallelism-1` | Parallelism | Viewer | a2-parallelism-math |
| 8 | `l08-parallelism-2` | Parallelism | [PDF](https://github.com/stanford-cs336/lectures/blob/main/lecture_08.pdf) | a2-parallelism-math |
| 9 | `l09-scaling-laws-1` | Scaling laws | [PDF](https://github.com/stanford-cs336/lectures/blob/main/lecture_09.pdf) | a3-scaling |
| 10 | `l10-inference` | Inference | Viewer | capstone |
| 11 | `l11-scaling-laws-2` | Scaling laws | [PDF](https://github.com/stanford-cs336/lectures/blob/main/lecture_11.pdf) | a3-scaling |
| 12 | `l12-evaluation` | Evaluation | Viewer | a5-eval |
| 13 | `l13-data-sources` | Data: sources, datasets | Viewer | (lecture only) |
| 14 | `l14-data-filtering` | Data: filtering, dedup, mixing, synthetic | Viewer | (lecture only) |
| 15 | `l15-sft-rlhf` | Mid/post-training: SFT, RLHF | [PDF](https://github.com/stanford-cs336/lectures/blob/main/lecture_15.pdf) | a5-grpo |
| 16 | `l16-rlvr` | Post-training: RLVR | [PDF](https://github.com/stanford-cs336/lectures/blob/main/lecture_16.pdf) | a5-grpo |
| 17 | `l17-alignment-multimodal` | Alignment, multimodality | Viewer | a5-dpo-safety |
| 18 | `l18-guest-selsam` | Guest: Daniel Selsam | Video only | optional |
| 19 | `l19-guest-fu` | Guest: Dan Fu | Video only | optional |

If a 2026 lecture has nothing readable, fall back to the [Spring 2025 page](https://cs336.stanford.edu/spring2025/).

## Build stages

### 0. `refresher`: PyTorch refresher + Modal (3 build sessions)
You haven't written PyTorch in a couple of years. This is minimal on purpose; A1 fills in the rest.
- **Session 1:** tensors, dtypes, devices (`cpu`/`mps`/`cuda`), broadcasting, `einops` (`rearrange`, `einsum`), autograd (`requires_grad`, `.backward()`, `.grad`, `no_grad`). Practice in `llm/practice/refresher/`.
- **Session 2:** a tiny MLP on a toy dataset (e.g. two moons or sklearn digits): `nn.Module`, `nn.Parameter`, `AdamW`, cross-entropy, a train/eval loop, `model.train()` vs `model.eval()`.
- **Session 3:** Modal. Sign up (Starter), `uv add modal`, `modal setup`. Write `llm/practice/modal_run.py`: a small wrapper that ships a local repo to a Modal GPU and runs one command there (`modal run modal_run.py --gpu T4 --cmd "uv run pytest"`). Confirm `torch.cuda.is_available()` on a T4 for a few cents. Every later GPU run uses this wrapper.
- **Skip:** Karpathy's "Let's build GPT" video. It gives away A1.
- **Done when:** the MLP trains on `mps`, and the Modal wrapper prints a GPU name.

### 1. `a1-tokenizer`: Byte-level BPE (A1 §2)
- **Repo:** [assignment1-basics](https://github.com/stanford-cs336/assignment1-basics), handout §2
- **Build:** BPE training (byte vocab init, regex pre-tokenization, merges, special tokens), parallelized pre-tokenization, `Tokenizer.encode/decode/encode_iterable`. Train on TinyStories on the laptop.
- **Model:** a tokenizer is a compression scheme learned from frequency. Merges are applied in the order they were learned, and the vocab size trades sequence length against the embedding table.
- **Numbers:** bytes per token on TinyStories vs OWT; how vocab size changes embedding params (V × d).
- **Interview:** "Why byte-level BPE?" "Why does an LLM miscount the letters in 'strawberry'?" "Why do token counts differ across providers?"
- **Lectures:** 1

### 2. `a1-transformer`: The Transformer LM (A1 §3)
- **Build:** Linear, Embedding, RMSNorm, SwiGLU, RoPE, scaled dot-product attention, causal multi-head self-attention, the pre-norm block, the full LM. Then do the resource-accounting questions (params, FLOPs per forward pass).
- **Model:** the residual stream is the bus; attention mixes across positions; the FFN works per position. Pre-norm keeps gradients healthy.
- **Numbers:** param count of GPT-2 XL from its config; FLOPs ≈ 2 × params × tokens per forward pass, plus the attention term.
- **Interview:** "Walk me through a Transformer block." "Why RoPE over learned positions?" "Why is attention O(n²), and where does that bite?"
- **Lectures:** 2–3

### 3. `a1-training`: Training loop + TinyStories run (A1 §4–7)
- **Build:** cross-entropy (numerically stable), AdamW from scratch, cosine LR schedule with warmup, gradient clipping, the data loader (np.memmap), checkpointing, the training loop, decoding (temperature, top-p). Run TinyStories on Modal. Do 1–2 ablations (e.g. no RMSNorm, NoPE) only if the budget allows. **Skip:** the OWT run and the leaderboard.
- **Model:** AdamW keeps 2 extra floats per param. The LR schedule matters more than most knobs. Loss curves tell you what broke.
- **Numbers:** training memory = params + grads + 2 Adam states (+ activations): bytes per param in fp32; TinyStories run cost on Modal.
- **Interview:** "How much memory does it take to train a 7B model?" "What do temperature and top-p actually do?" "The loss spiked to NaN at step 3k. What do you check?"
- **Lectures:** 4

### 4. `a2-profiling`: Profiling, mixed precision, memory (A2 §2–3)
- **Repo:** [assignment2-systems](https://github.com/stanford-cs336/assignment2-systems), handout §2–3 (on Modal: T4 or L4)
- **Build:** end-to-end benchmarking script (warmup, `cuda.synchronize`), Nsight Systems or the PyTorch profiler, mixed precision (bf16 autocast), memory profiling, activation checkpointing.
- **Model:** GPU work is async; most ops are memory-bound, not compute-bound. Mixed precision halves memory traffic.
- **Numbers:** arithmetic intensity of a matmul vs softmax; roofline for your GPU.
- **Interview:** "Why does mixed precision speed things up?" "Memory-bound vs compute-bound?" "What does activation checkpointing trade?"
- **Lectures:** 5

### 5. `a2-flashattention`: FlashAttention-2 in Triton (A2 §4)
- **Build:** benchmark naive PyTorch attention and `torch.compile`d attention; FlashAttention-2 forward pass (first in PyTorch tiles, then a Triton kernel); backward with recomputation (the Triton backward is optional).
- **Model:** tiling + online softmax means the n×n matrix never sits in HBM. You trade recompute for memory traffic.
- **Numbers:** HBM bytes moved by naive attention vs FA2 for a given seq len.
- **Interview:** "How does FlashAttention work, and why is it faster if it does more FLOPs?"
- **Lectures:** 6

### 6. `a2-parallelism-math`: Parallelism, on paper (A2 §8)
- **Build:** none (multi-GPU parts §5–7 skipped). Write answers to the §8 analysis questions in `llm/notes/a2-parallelism-math.md`: communication primitives, DP / FSDP / TP cost, 2D FSDP+TP.
- **Model:** each strategy shards something (data, params/optimizer state, or layers) and pays in a specific collective.
- **Numbers:** bytes communicated per step for DP vs FSDP for a given model.
- **Interview:** "How would you serve a 70B model that doesn't fit on one GPU?" "Data vs tensor vs pipeline parallelism?"
- **Lectures:** 7–8

### 7. `a3-scaling`: Your own IsoFLOP sweep (replaces A3)
A3's training API needs a Stanford ID, so you generate the data yourself.
- **Build:** using your A1 model and tokenizer on TinyStories (laptop `mps`, or a T4 if too slow): about 3 compute budgets × 4 model sizes, each run lasting minutes. Fit IsoFLOP curves → compute-optimal N(C) and D(C) power laws. Compare your exponent to Chinchilla's.
- **Model:** at a fixed compute budget there's an optimal model size. Chinchilla's rule is roughly 20 tokens per parameter.
- **Numbers:** C ≈ 6ND; given C, the Chinchilla-optimal N and D.
- **Interview:** "Why are modern models 'over-trained' past Chinchilla?" (inference cost)
- **Lectures:** 9, 11 (10 can be watched in between)

### 8. `a5-eval`: Eval harness for math reasoning (A5 §3)
- **Repo:** [assignment5-alignment](https://github.com/stanford-cs336/assignment5-alignment), handout §3 (on Modal)
- **Build:** a vLLM inference loop, zero-shot / few-shot / CoT prompts, the answer-grading function, baseline accuracy. This carries straight over to system-design `llm-evaluation`.
- **Model:** an eval is only as good as its grader. Format failures look like reasoning failures.
- **Numbers:** vLLM throughput (tokens/sec) on your GPU; cost of one full eval pass.
- **Interview:** "How do you know a model change made things better?"
- **Lectures:** 12

### 9. `a5-grpo`: GRPO, scaled down (A5 §4)
- **Build:** the GRPO components (group-normalized advantages, the policy-gradient loss, the train step with gradient accumulation) passing `tests/test_grpo.py`. Then a small run on a ~0.5B Qwen on one A100 (not the handout's model). **Skip:** §5–7 (Dr. GRPO, rejection fine-tuning, MaxRL, off-policy RL).
- **Model:** RL with verifiable rewards: sample a group, score it, push up the above-average ones. No reward model needed.
- **Numbers:** GPU memory for policy + vLLM on one card; cost of N GRPO steps.
- **Interview:** "SFT vs RLHF vs RLVR?" "Why did reasoning models suddenly get good?"
- **Lectures:** 15–16

### 10. `a5-dpo-safety`: Safety eval + DPO (A5 supplement, scaled down)
- **Build:** zero-shot safety eval (SimpleSafetyTests, plus a small MMLU/GSM8K check), the DPO loss, DPO on a small public preference set with a small public instruct model, then re-run the safety eval. The supplement mentions course-provided models and storage; swap in public Hugging Face checkpoints where it does.
- **Model:** DPO turns preference pairs into a classification loss with an implicit reward. Safety is a measured behavior, not a property.
- **Numbers:** DPO memory (policy + frozen reference); safety-eval cost.
- **Interview:** "DPO vs PPO-based RLHF?" "How would you measure whether a model is safer after tuning?"
- **Lectures:** 17

### 11. `capstone` (optional): Serve your model behind the Rust gateway
- **Build:** a small Python inference server for your A1 TinyStories model: a KV cache, sampling, SSE streaming. Add it to the Rust gateway as a local provider.
- **Model:** prefill is compute-bound and decode is memory-bound. The KV cache trades memory for not recomputing.
- **Numbers:** KV cache bytes per token = 2 × layers × d_model × bytes; TTFT vs tokens/sec.
- **Interview:** "Why is LLM inference memory-bound?" "What does continuous batching buy?"
- **Lectures:** 10

**Skipped entirely:** A4 (Common Crawl → pretraining data). Watch lectures 13–14 only.
