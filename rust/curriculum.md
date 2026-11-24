# Rust Curriculum: an LLM gateway, modeled on Pydantic's

**Project:** a local LLM gateway in Rust that you run every day. Claude Code (via `ANTHROPIC_BASE_URL`) and Pydantic AI scripts send their traffic through it. It covers the same features as the [Pydantic AI Gateway](https://github.com/pydantic/pydantic-ai-gateway) (TypeScript on Cloudflare Workers, archived 2026-03; AGPL, so read it for ideas and don't copy code).

**Why this project:** last time Rust had no real use. This one runs all week, so bugs you notice on weekdays become Saturday's work. In each stage you read the matching Pydantic TypeScript file first, then write it in Rust, so you see exactly what Rust makes you decide that TypeScript let you skip (who owns the request body, what can cross threads, errors as values). The last stage follows how pydantic-core is built: a Rust core exposed to Python.

**Goal:** a Rust job. Every stage lists the interview questions it prepares you for.

## Starting point

**You don't need to know any Rust.** Each stage's "Testable points" and "Interview" lines are what you'll be able to do when you finish it, not what you need before you start. Pretests are expected to go badly, and the "Expected errors" are errors you're supposed to hit.

Your Dec 2025 attempt (Book ch. 1–4) has mostly faded, so begin with stage 0 below. It's a refresher on the basics, so it has a lighter mastery check than the other stages.

### 0. `basics`: Refresher (1 weekend)
- **Read:** Rust Book ch. 1–3 (setup and cargo, the guessing game, variables / types / functions / control flow). Skim it, and type the examples instead of just reading them.
- **Practice:** [Rustlings](https://github.com/rust-lang/rustlings) `intro` → `variables` → `functions` → `if` → `primitive_types` → `vecs`. Stop before `move_semantics`, because stage 1 covers that.
- **Build:** `cargo new tokencost` in `rust/practice/` (all journey projects and drills live there). It's a CLI: `tokencost claude-sonnet 1200 350` prints the cost from a hard-coded price table. You'll use `std::env::args`, `parse::<u32>()`, `match` on the model name, a function or two, and a helpful message for bad input. Write one `#[test]`.
- **Done when:** it runs, `cargo test` and `cargo clippy` are clean, and you can read a compiler error out loud: what the error code is, which line it points to, and what the `help:` line suggests.
- **Don't worry yet about:** `&` vs owned values, `String` vs `&str`, or `Result`/`?`. Use `.unwrap()` and `.clone()` freely. Stages 1–2 deal with them properly.

## Rules

- **No TypeScript needed.** "Read first" files get translated in `/rs-build` into a Pydantic-style sketch plus example data. You read the translation, not the TS.
- **Build it by hand before using the library.** Your own error enum before `thiserror`, your own LRU before the `lru` crate, your own middleware chain before `tower`. The library comes afterwards, as a comparison.
- **The compiler error is part of the lesson.** Each stage names the error you're meant to run into. Fix it yourself before asking.
- **Mastery check (all 4) before moving to the next stage:**
  1. The piece works, its tests pass, and `cargo clippy` is clean.
  2. You can explain the stage's mental model in about 60 seconds.
  3. You can predict the compiler error for 3 code snippets.
  4. You can solve the stage's interview problem in Rust from scratch, without the project open.
- **In every stage:** tests, clippy, `rustc --explain <code>`, and never logging API keys or auth headers. The gateway listens on 127.0.0.1 only.

## Stages

Slugs are used by `/rs-build`, `/rs-drill`, `progress.md`, and `cards/<slug>.md`.

### 1. `ownership`: Ownership & borrowing
- **Read first (Pydantic):** `deploy/example.config.ts` and `gateway/src/types.ts` (projects, users, API keys, providers)
- **Build:** config types (`Project`, `User`, `ApiKey`, `ProviderConfig`) loaded from a TOML file, and `fn find_key(&self, key: &str) -> Option<&ApiKey>`
- **Model:** each value has one owner, and that owner frees it. Borrowing works like a reader-writer lock the compiler checks: many `&` or one `&mut`, never both.
- **Expected errors:** E0382 (use after move), E0502 (changing something while it's borrowed), E0106 (missing lifetime when you return a reference)
- **Testable points:** move vs Copy vs Clone; `String` vs `&str` and slices; why `find_key` returns `Option<&ApiKey>` and not an owned value; Drop and RAII; when to clone and when to restructure
- **Interview:** "Explain ownership and borrowing." "String vs &str?" "Why can't you have two `&mut`?"
- **Reading:** Rust Book ch. 4, 5, 8

### 2. `enums-errors`: Modeling with enums & errors
- **Read first:** `gateway/src/providers/base.ts`, `anthropic.ts`, and the error paths in `handler.ts`
- **Build:** an `enum Provider { Anthropic, OpenAI, ... }` that adds the right auth header; an Anthropic SSE parser (`enum Event { MessageStart, ContentBlockDelta, MessageDelta, MessageStop, Ping, Error }`) that pulls out token usage; a `GatewayError` enum that maps to HTTP status codes
- **Model:** make invalid states impossible to represent (the same idea as a Pydantic model, enforced at compile time). Errors are values you return, not exceptions.
- **Expected errors:** E0004 (non-exhaustive match), `?` failing because the error types don't convert
- **Testable points:** Option and Result, exhaustive `match`, `?` and `From`, a custom error enum, `thiserror` (libraries) vs `anyhow` (apps), serde as Rust's version of Pydantic
- **Interview:** "How does Rust do error handling without exceptions?" "unwrap vs expect vs ?"
- **Reading:** Rust Book ch. 6, 9; serde docs

### 3. `iterators-closures`: Collections, iterators, closures
- **Read first:** `gateway/src/refreshGenaiPrices.ts`, and the [genai-prices](https://github.com/pydantic/genai-prices) data format
- **Build:** cost calculation (tokens × price per model, using genai-prices data) and a usage aggregator: cost per project / user / key per day, from a JSONL log
- **Expected errors:** a closure captures `&mut` while something else is still borrowed; E0373 (closure may outlive borrowed value)
- **Testable points:** the `HashMap` entry API, iterator adapters and why they're zero-cost, `iter` vs `into_iter` vs `iter_mut`, Fn / FnMut / FnOnce, `move` closures
- **Interview:** "Fn vs FnMut vs FnOnce?" "Are iterators slower than loops?"
- **Reading:** Rust Book ch. 13

### 4. `traits-generics`: Traits & generics
- **Read first:** `gateway/src/providers/base.ts` (the base class each provider extends) and `cache/adapter.d.ts`
- **Build:** a `Provider` trait (auth, URL, usage extraction) to replace the enum from stage 2 (compare the two); a `CacheBackend` trait; a `Policy` trait (cost limit, model allowlist, secret redaction) chained as `Vec<Box<dyn Policy>>`; `impl Iterator` for the SSE parser
- **Expected errors:** E0038 (trait is not dyn-compatible), missing trait bounds
- **Testable points:** generics vs `dyn` (generics compile a separate copy per type; `dyn` looks up methods at runtime through a vtable), when you'd pick an enum vs a trait, associated types, std traits (Display, From, Default, Iterator), the orphan rule
- **Interview:** "When `dyn Trait` vs generics?" "Enum vs trait object for a fixed set of variants?"
- **Reading:** Rust Book ch. 10, 17, 19.2

### 5. `lifetimes`: Lifetimes
- **Build:** rewrite the SSE parser so `Event<'a>` borrows from the input buffer (zero-copy); make redaction return `Cow<'_, str>` so it only allocates when it actually changes something
- **Model:** a lifetime is the compiler's proof that a reference can't outlive its data. It doesn't change how long anything lives.
- **Expected errors:** E0106, E0597 (borrowed value doesn't live long enough), E0515 (returning a reference to a local)
- **Testable points:** the elision rules, structs that hold references, what `'static` really means (`&'static` vs `T: 'static`), `Cow`
- **Interview:** "What is a lifetime?" "What does `T: 'static` mean?"
- **Reading:** Rust Book ch. 10.3; Crust of Rust: Lifetime Annotations

### 6. `smart-pointers`: Smart pointers & interior mutability
- **Read first:** `gateway/src/cache/index.ts` (they cache in Redis/KV; yours is in-memory)
- **Build:** an LRU response cache, twice: (a) an `Rc<RefCell<Node>>` doubly linked list with `Weak` back pointers, (b) a Vec plus indices (an arena). Benchmark and compare them.
- **Expected errors:** RefCell `BorrowMutError` panic at runtime; reference cycles leaking memory
- **Testable points:** Box / Rc / Weak / Cell / RefCell, why linked lists are hard in Rust, checking borrows at compile time vs at runtime, Deref
- **Interview:** "Implement an LRU cache in Rust." "Box vs Rc vs Arc?" "When does RefCell panic?"
- **Reading:** Rust Book ch. 15; *Learning Rust With Entirely Too Many Linked Lists*

### 7. `threads-sync`: Threads & shared state
- **Read first:** `gateway/src/rateLimiter.ts`
- **Build:** a blocking proxy with one thread per connection (std::net plus a blocking HTTP client), a token bucket rate limiter, and per-key cost limits shared across threads
- **Expected errors:** "`Rc<...>` cannot be sent between threads safely" (your stage 6 LRU, which forces the switch to `Arc<Mutex>`); E0373 on `thread::spawn` without `move`
- **Testable points:** Send and Sync, Arc, Mutex vs RwLock vs atomics, channels (mpsc), deadlocks, lock poisoning, scoped threads
- **Interview:** "What are Send and Sync?" "Why is Rc not Send?" "Implement a thread-safe rate limiter."
- **Reading:** Rust Book ch. 16; Mara Bos, *Rust Atomics and Locks* ch. 1–3

### 8. `async`: Async foundations
- **Read first:** `gateway/src/gateway.ts` and `handler.ts` (the request flow)
- **Build:** port the proxy to tokio + hyper; add timeouts, retries with exponential backoff plus jitter, and fallback to another provider (a TODO in Pydantic's gateway, so you go further than they did); record/replay tests in the style of their `proxy-vcr`, so tests don't spend API money
- **Model:** a future is a state machine that does nothing until it's polled. The runtime decides when to poll it.
- **Expected errors:** "future cannot be sent between threads safely" (a std `MutexGuard` held across `.await`); `spawn` needing `'static`
- **Testable points:** why futures do nothing until awaited, `spawn` requiring `'static + Send`, std vs tokio Mutex, `select!`, cancellation safety, blocking inside async code (`spawn_blocking`)
- **Interview:** "Async vs threads: when do you pick each?" "What happens if you block inside async code?"
- **Reading:** the tokio tutorial; Crust of Rust: async/await

### 9. `streaming-pin`: Streaming & Pin
- **Build:** pass SSE through to the client while tapping token usage as it streams, without buffering the whole response; record cost when the stream ends (this is why Pydantic calls their cost limits "soft")
- **Expected errors:** `Unpin` not satisfied; "cannot move out of pinned"
- **Testable points:** the Stream trait, Pin and Unpin (why a future can't move in memory once polled), backpressure, what to do when the client disconnects mid-stream
- **Interview:** "Why does Pin exist?"
- **Reading:** *Asynchronous Programming in Rust* (Pin chapter); fasterthanli.me "Pin and suffering"

### 10. `tower-middleware`: Middleware the way the industry does it
- **Build:** rewrite auth → cost limit → rate limit → cache → retry/fallback → provider as `tower` Service/Layer middleware
- **Testable points:** the `Service` trait (`poll_ready` + `call`), Layer, associated types, boxed futures, why the middleware is generic code and not `dyn`
- **Interview:** "Design middleware for an async server in Rust."
- **Reading:** "Inventing the Service trait" (tokio blog); tower docs

### 11. `production`: Production
- **Read first:** `gateway/src/otel/` (OpenTelemetry GenAI attributes)
- **Build:** `tracing` spans using OTel GenAI attributes, exported over OTLP (optionally to Logfire, the same place Pydantic sends theirs); persist limits in SQLite (they use Cloudflare D1, which is SQLite); graceful shutdown; a `gw stats` command; criterion benchmarks and a flamegraph
- **Testable points:** graceful shutdown with a cancellation token, structured logging, redacting credentials at every boundary, finding and cutting allocations
- **Interview:** "How do you shut down an async server gracefully?" "How do you profile Rust?"

### 12. `pyo3`: Rust under a Python API (the pydantic-core design)
- **Read first:** pydantic-core's layout (`src/` Rust, `python/` package, maturin build)
- **Build:** expose the cost calculator or the SSE usage parser to Python with PyO3 + maturin; call it from a Pydantic AI script; benchmark it against pure Python
- **Testable points:** the GIL and `allow_threads`, converting between Python and Rust types, why pydantic, uv, Ruff and Polars are built this way
- **Interview:** "Why rewrite a Python library's core in Rust?"

### 13. `depth` (optional): For interviews
- A minimal async executor you write yourself, `macro_rules!`, and `unsafe` basics (what it unlocks, what still holds)
- **Reading:** *Rust for Rustaceans*

## Traffic sources
- Claude Code: `ANTHROPIC_BASE_URL=http://127.0.0.1:<port>`. Check in stage 7 or 8 whether this works with your login type. Unsetting the variable restores direct access immediately.
- Pydantic AI scripts: point the Anthropic provider at the gateway with an API key. These definitely work and can replay traffic for tests.
