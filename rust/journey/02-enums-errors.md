# Stage 2 · enums-errors: Narrated walkthrough

> Open this with **Cmd+K V** (Markdown preview beside the editor). Keep a terminal open below it.
> You type every `▶ Type this` block yourself. Don't paste them. Each `✓ Checkpoint` is a question to answer out loud before you move on.
> This condenses Book ch. 6 and 9, plus the serde basics. Book links are there for when you want more depth. You shouldn't need them to keep going.

**Where this goes:** by the end, your gateway knows how each provider authenticates, can pull token usage out of an Anthropic stream, and returns typed errors that map to HTTP status codes, with no `.expect` left in library code.

**Your pretest gaps (2026-11-25, 21%), and where this guide covers them:**
- E0004, a non-exhaustive `match` (Q1): Part 2
- what the `E` in `Result<T, E>` is for in the gateway (Q2): Part 3
- `?` failing because the error types don't convert, and `From` (Q3): Part 5
- unwrap vs expect vs `?` (Q4): Part 4
- enum variants that carry data, "invalid states can't be represented" (Q5): Part 1
- thiserror vs anyhow (Q6): Part 6
- serde as Rust's Pydantic (Q7): Part 7

**Where code goes:** every type-along project lives in `~/selfstudy/rust/practice/<name>/` (`target/` is gitignored, so commit freely). The gateway is the one exception: it's its own repo (Part 9).

**Keyboard loop:** run `bacon` in the project folder. Then: edit → **Cmd+S** → bacon re-checks → **F8** jumps to the next error → **Cmd+.** applies a quick fix. **Ctrl+`** moves you between the terminal and the editor, and **Cmd+1** jumps to the editor.

▶ Type this (one scratch project for Parts 1–7):
```sh
cd ~/selfstudy/rust/practice
cargo new enums && cd enums
cargo add serde --features derive
cargo add serde_json thiserror anyhow
bacon
```
Each part adds code to `src/main.rs` and calls it from `main`. Once you've seen a part's error and fixed it, leave the fixed version in the file.

---

## Part 1: Enums whose variants carry data (Book ch. 6.1)

**The Python comparison (pretest Q5).** The Python version is one class with every field optional:

```python
class Event(BaseModel):
    type: str
    text: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
```

Nothing stops you from building `Event(type="ping", text="Hi", output_tokens=12)`. Every reader has to check `type` and then trust that the right fields are set.

A Rust enum is **one type with a fixed set of variants, and each variant holds its own fields**:

▶ Type this:
```rust
#[derive(Debug)]
enum Event {
    MessageStart { input_tokens: u32 },
    ContentBlockDelta { text: String },
    MessageDelta { output_tokens: u32 },
    MessageStop,
    Ping,
    Error { message: String },
}
```

A `Ping` has no fields at all. A `ContentBlockDelta` always has `text`, and it can't have `output_tokens`. **A ping carrying text can't be written down, so it can't happen.** That's what "make invalid states impossible to represent" means: the type rules the bad combinations out, where Pydantic would need a validator.

Variants come in three shapes, and all of them can be mixed in one enum:
```rust
enum Shape {
    Unit,                       // no data: Ping, MessageStop
    Tuple(u32, String),         // positional: Error(String)
    Struct { a: u32, b: bool }, // named fields: MessageStart { input_tokens }
}
```

**TS comparison:** this is a discriminated union (`{type: "ping"} | {type: "delta", text: string}`), except Rust checks that every `match` handles every case (Part 2). Your `Option<T>` is just this enum from the standard library:
```rust
enum Option<T> { Some(T), None }
enum Result<T, E> { Ok(T), Err(E) }
```

✓ **Checkpoint:** Why is `enum Event { Ping, Delta { text: String } }` better than `struct Event { kind: String, text: Option<String> }`?
<details><summary>answer</summary>In the struct, <code>kind: "ping"</code> with <code>text: Some(..)</code> is a legal value, so every reader has to check and trust it. In the enum, a ping with text can't be built, and a delta always has text, so there's no <code>Option</code> to unwrap.</details>

📖 Depth: [ch06-01 Defining an Enum](https://doc.rust-lang.org/book/ch06-01-defining-an-enum.html)

---

## Part 2: `match` must handle every variant (E0004) (Book ch. 6.2–6.3)

`match` takes a value apart by variant and pulls out its fields:

▶ Type this:
```rust
fn describe(e: &Event) -> String {
    match e {
        Event::MessageStart { input_tokens } => format!("start, {input_tokens} in"),
        Event::ContentBlockDelta { text } => format!("text: {text}"),
        Event::MessageDelta { output_tokens } => format!("{output_tokens} out"),
        Event::MessageStop => "stop".to_string(),
        Event::Ping => "ping".to_string(),
        Event::Error { message } => format!("error: {message}"),
    }
}
```
`match` is an expression, so each arm produces the function's return value. Because `e` is a `&Event`, the bound fields (`text`, `message`) are borrows: `&String`, not a moved `String`.

Now ▶ **delete the `Event::Ping` arm**, and read the error out loud:

**E0004 (non-exhaustive patterns: `&Event::Ping` not covered).** This is pretest Q1. Passing `&Provider::Groq` was fine. The bug was that the `match` had no arm for `Groq`. Run `rustc --explain E0004`.

**Why it matters:** when Anthropic adds a new event type and you add a variant, the compiler shows you **every `match` in the codebase** that needs updating. In Python, the new case quietly falls through an `if/elif` chain.

### `_` turns that check off
```rust
match p {
    Provider::Anthropic => "x-api-key",
    _ => "authorization",   // every other variant, including ones added later
}
```
This compiles, but when you add `Provider::GoogleVertex` it silently gets `"authorization"`. **Prefer listing variants.** Use `_` for open-ended values (integers, strings), not for your own enums.

### Shorter forms when you only care about one variant
```rust
if let Event::ContentBlockDelta { text } = &e { print!("{text}"); }

let Some(key) = cfg.find_key(k) else { return; };   // let-else: you used this in main
```

✓ **Checkpoint:** You add `Provider::Mistral`. Which `match` statements get an E0004: ones that list every variant, or ones with a `_` arm?
<details><summary>answer</summary>Only the ones that list every variant. That's the point: those are the places the compiler makes you decide. The <code>_</code> ones silently take the default, which may be wrong.</details>

📖 Depth: [ch06-02 match](https://doc.rust-lang.org/book/ch06-02-match.html) · [ch06-03 if let / let-else](https://doc.rust-lang.org/book/ch06-03-if-let.html)

---

## Part 3: `Option` vs `Result`, and what `E` is for (Book ch. 6.1, 9.2)

| | Variants | Means | Gateway example |
|---|---|---|---|
| `Option<T>` | `Some(T)` / `None` | "there might be no value, and that's normal" | `find_key` → `Option<&ApiKey>`: no such key |
| `Result<T, E>` | `Ok(T)` / `Err(E)` | "this can fail, and `E` says how" | `Config::load` → `Result<Config, ConfigError>`: file missing, or TOML invalid |

**What `E` is for (pretest Q2):** the caller needs to **act differently** on different failures. For a request, the gateway's `E` is a `GatewayError`: unknown key → 401, provider not allowed → 403, upstream down → 502. `None` can't tell you which of those happened.

**Errors are values you return, not exceptions.** A function that can fail says so in its signature. Nothing gets thrown past the caller, and you can't forget to handle a failure without the compiler noticing (there's a `#[must_use]` warning if you ignore a `Result`).

### Moving between them
▶ Type this:
```rust
#[derive(Debug)]
enum GatewayError { UnknownKey, ProviderNotAllowed(String) }

fn find(keys: &[&str], k: &str) -> Option<usize> {
    keys.iter().position(|x| *x == k)
}

fn lookup(keys: &[&str], k: &str) -> Result<usize, GatewayError> {
    find(keys, k).ok_or(GatewayError::UnknownKey)   // None → Err(UnknownKey)
}
```
The handful of methods you'll use most:
- `opt.ok_or(err)`: `Option` → `Result`. This is how "key not found" becomes a 401.
- `res.ok()`: `Result` → `Option`, throwing the error away.
- `x.map(f)`: change the value inside `Some`/`Ok`. `res.map_err(f)` changes the error inside `Err`.
- `opt.unwrap_or(default)`: take the value, or fall back to a default.

✓ **Checkpoint:** `project_for` returns `Option<&Project>`. When should a missing project be an `Option`, and when should it be an error?
<details><summary>answer</summary>Inside the lookup, "not found" is a normal outcome, so <code>Option</code> is right. At the request boundary, a key pointing at a missing project is a broken config, so the handler turns it into an error (500) with <code>ok_or</code>.</details>

📖 Depth: [ch09-02 Recoverable Errors with Result](https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html)

---

## Part 4: unwrap vs expect vs `?` (Book ch. 9.1–9.3)

Pretest Q4, and a favorite interview question. All three take the value out of an `Ok` (or `Some`). The difference is **what happens on `Err`/`None`**:

| | On `Err` / `None` | Use it when |
|---|---|---|
| `.unwrap()` | **panics** (crashes the thread) with a generic message | tests, quick scripts |
| `.expect("msg")` | **panics** with your message | it truly can't fail, and the message says why (`"PORT must be a number"`) |
| `?` | **returns the error early** to *your* caller | library and request code: almost always |

`unwrap` doesn't give you "Ok or Error". It gives you the value, or it crashes.

▶ Type this, run it, and read the panic:
```rust
fn part4_panic() {
    let a: u16 = "8080".parse().unwrap();
    println!("{a}");
    let b: u16 = "abc".parse().expect("PORT must be a number");
    println!("{b}");   // never reached
}
```
You'll see `panicked at ...: PORT must be a number: ParseIntError { kind: InvalidDigit }`. **In a server, a panic in a request handler crashes that task, and the client gets nothing useful.** That's why the gateway's request path uses `?`.

### What `?` actually does
```rust
fn parse_port(s: &str) -> Result<u16, std::num::ParseIntError> {
    let n: u16 = s.trim().parse()?;
    Ok(n)
}
```
`let n = expr?;` is shorthand for:
```rust
let n = match expr {
    Ok(v) => v,
    Err(e) => return Err(From::from(e)),   // ← note the From::from (Part 5)
};
```
It works on `Option` too: in a function that returns `Option`, `x?` returns `None` early.

▶ Type this (both are E0277, so read them out loud):
```rust
fn main_bad() {
    let n: u16 = "8080".parse()?;        // ← E0277: this fn returns (), not Result
}

fn first_key(keys: &[String]) -> Result<&String, String> {
    let k = keys.first()?;               // ← E0277: `?` on an Option in a fn that returns Result
    Ok(k)
}
```
Fixes: give the function a `Result` return type (for `main`, too: `fn main() -> Result<(), Box<dyn std::error::Error>>`), and turn the `Option` into a `Result` first: `keys.first().ok_or("no keys".to_string())?`.

✓ **Checkpoint:** In 20 seconds, the way you'd say it to an interviewer: unwrap vs expect vs `?`.
<details><summary>answer</summary>"unwrap and expect both panic on failure; expect lets me say why it should never happen. ? propagates the error to my caller, converting it with From. In library or request code I use ?, so one bad request becomes an error response instead of a crash; unwrap is for tests."</details>

📖 Depth: [ch09-01 panic!](https://doc.rust-lang.org/book/ch09-01-unrecoverable-errors-with-panic.html) · [ch09-03 To panic! or Not](https://doc.rust-lang.org/book/ch09-03-to-panic-or-not-to-panic.html)

---

## Part 5: `?` and `From`: when error types don't convert (E0277)

This is pretest Q3, the core of the stage. ▶ Type this:
```rust
#[derive(Debug)]
enum ConfigError { Read(std::io::Error), Parse(std::num::ParseIntError) }

fn load_port(path: &str) -> Result<u16, ConfigError> {
    let text = std::fs::read_to_string(path)?;   // ← E0277
    let port = text.trim().parse()?;
    Ok(port)
}
```
**E0277 (`?` couldn't convert the error to `ConfigError`).** `read_to_string` fails with an `io::Error`, but your function promises a `ConfigError`. `?` calls `From::from(e)` to convert it (look back at the desugaring in Part 4), and nobody has said *how* to turn an `io::Error` into a `ConfigError`.

**Fix: tell it how**, once per source error:
```rust
impl From<std::io::Error> for ConfigError {
    fn from(e: std::io::Error) -> Self { ConfigError::Read(e) }
}
impl From<std::num::ParseIntError> for ConfigError {
    fn from(e: std::num::ParseIntError) -> Self { ConfigError::Parse(e) }
}
```
Now both `?`s compile. (The other fix is `.map_err(ConfigError::Read)?` at the call site. That's handy when the same source error should map to different variants in different places.)

### Make it a real error: `Display` + `std::error::Error`
`Debug` is for developers. `Display` is the message a user or a log line sees:
```rust
impl std::fmt::Display for ConfigError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ConfigError::Read(e) => write!(f, "can't read config: {e}"),
            ConfigError::Parse(e) => write!(f, "bad port: {e}"),
        }
    }
}
impl std::error::Error for ConfigError {}
```
Then handle it at the top:
```rust
match load_port("nope.txt") {
    Ok(p) => println!("port {p}"),
    Err(e) => println!("{e}"),   // can't read config: No such file or directory (os error 2)
}
```
That's about 20 lines of boilerplate per error enum. Part 6 deletes it.

✓ **Checkpoint:** Pretest Q3, again. Why does `fs::read_to_string(path)?` fail in a function returning `Result<String, GatewayError>`, and what are the two fixes?
<details><summary>answer</summary>E0277: <code>?</code> converts the <code>io::Error</code> with <code>From::from</code>, and there's no <code>impl From&lt;io::Error&gt; for GatewayError</code>. Fix 1: write that impl (or derive it with thiserror's <code>#[from]</code>). Fix 2: <code>.map_err(|e| GatewayError::BadConfig(e.to_string()))?</code>.</details>

📖 Depth: [ch09-02, "A Shortcut for Propagating Errors: the ? Operator"](https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html#a-shortcut-for-propagating-errors-the--operator)

---

## Part 6: `thiserror` (libraries) vs `anyhow` (apps)

Pretest Q6. Two crates, two jobs:

| | What it gives you | Use it in |
|---|---|---|
| `thiserror` | a derive that writes the `Display`, `Error`, and `From` impls from Part 5 for you | **library code**, where callers `match` on your variants (`GatewayError` → status code) |
| `anyhow` | one catch-all `anyhow::Error` that any error converts into, plus `.context("...")` | **app code** (`main`, CLI glue), where you only print the error and exit |

Rule of thumb: **if a caller needs to act on *which* error it was, define an enum with thiserror. If the caller only reports it, use anyhow.**

▶ Type this (Part 5's enum, rewritten):
```rust
#[derive(Debug, thiserror::Error)]
enum ConfigError2 {
    #[error("can't read config")]
    Read(#[from] std::io::Error),
    #[error("bad port")]
    Parse(#[from] std::num::ParseIntError),
}

fn load_port2(path: &str) -> Result<u16, ConfigError2> {
    let text = std::fs::read_to_string(path)?;
    Ok(text.trim().parse()?)
}
```
`#[error("...")]` writes `Display`. `#[from]` writes the `From` impl, and it also records the inner error as the **source**, so the cause stays attached.

And the app side:
```rust
fn run() -> anyhow::Result<()> {
    use anyhow::Context;
    let port = load_port2("port.txt").context("loading port.txt")?;
    println!("port {port}");
    Ok(())
}
// in main:  if let Err(e) = run() { println!("Error: {e:#}"); }
// prints:   Error: loading port.txt: can't read config: No such file or directory (os error 2)
```
`{e:#}` prints the whole chain: your context, then each source. That's why the messages above don't repeat `{0}`. If you write `#[error("can't read config: {0}")]` *and* `#[from]`, the chain prints the OS error twice. Try it.

✓ **Checkpoint:** The gateway's request handler and its `main`: which crate does each use, and why?
<details><summary>answer</summary>The handler returns a thiserror <code>GatewayError</code>, because the HTTP layer matches on the variant to pick 401/403/502. <code>main</code> uses anyhow, because a startup failure (bad config) only needs a readable message and a non-zero exit.</details>

📖 Depth: [thiserror docs](https://docs.rs/thiserror) · [anyhow docs](https://docs.rs/anyhow)

---

## Part 7: serde, Rust's Pydantic

Pretest Q7. You've already used `#[derive(Deserialize)]` for the TOML config. Here's what it means.

| Pydantic | serde |
|---|---|
| `class Usage(BaseModel): input_tokens: int` | `#[derive(Deserialize)] struct Usage { input_tokens: u32 }` |
| `Usage.model_validate_json(s)` | `serde_json::from_str::<Usage>(s)` → `Result<Usage, serde_json::Error>` |
| missing field → raises `ValidationError` | missing field → **returns** `Err(...)`, which you handle with `?` |
| `x: int \| None = None` | `x: Option<u32>`, which is `None` if missing |
| `Field(alias="type")` | `#[serde(rename = "type")]` |
| discriminated union on `type` | `#[serde(tag = "type")]` on an enum |

The derive generates the parsing code **at compile time**, for your exact struct, so there's no runtime reflection. (Pydantic v2's core is Rust too: `pydantic-core`, which is the final stage of this track.)

▶ Type this:
```rust
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Usage { input_tokens: u32, cache_read_input_tokens: Option<u32> }

fn part7_basic() {
    let bad: Result<Usage, _> = serde_json::from_str(r#"{"output_tokens": 3}"#);
    println!("{:?}", bad.map_err(|e| e.to_string()));  // Err("missing field `input_tokens` at line 1 column 20")
    let ok: Usage = serde_json::from_str(r#"{"input_tokens": 25}"#).unwrap();
    println!("{ok:?}");  // cache_read_input_tokens: None
}
```
Extra JSON fields are ignored by default (`"id"`, `"model"`, and so on). That's what you want for a provider's API, which adds fields over time.

### The Event enum, straight from JSON
Each Anthropic SSE `data:` line is JSON with a `"type"` field. `tag = "type"` tells serde to read that field and pick the variant:
```rust
#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum Sse {
    MessageStart { message: Msg },          // "message_start"
    ContentBlockDelta { delta: Delta },     // "content_block_delta"
    MessageDelta { usage: OutUsage },       // "message_delta"
    MessageStop,
    Ping,
    #[serde(other)]
    Other,                                  // any type we don't model (content_block_start, ...)
}
#[derive(Debug, Deserialize)] struct Msg { usage: Usage }
#[derive(Debug, Deserialize)] struct Delta { text: Option<String> }
#[derive(Debug, Deserialize)] struct OutUsage { output_tokens: u32 }
```
▶ Feed it these lines in a loop and print each result:
```rust
r#"{"type":"message_start","message":{"id":"m1","usage":{"input_tokens":25,"output_tokens":1}}}"#
r#"{"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}"#
r#"{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hi"}}"#
r#"{"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":12}}"#
r#"{"type":"message_stop"}"#
```
Then remove `Other` and feed the `content_block_start` line again. What error do you get, and is that what you want for a provider that adds new event types?

✓ **Checkpoint:** Pretest Q7, again. What's the serde equivalent of `Usage.model_validate_json(s)`, and what happens on a missing required field?
<details><summary>answer</summary><code>serde_json::from_str::&lt;Usage&gt;(s)</code>. It returns <code>Err(serde_json::Error)</code> ("missing field `input_tokens`") instead of raising, so the caller handles it with <code>?</code> or <code>match</code>. A field typed <code>Option&lt;T&gt;</code> is allowed to be missing.</details>

📖 Depth: [serde.rs: derive](https://serde.rs/derive.html) · [enum representations (tag)](https://serde.rs/enum-representations.html) · [field attributes](https://serde.rs/field-attrs.html)

---

## Part 8: Rustlings (practice reps)

```sh
cd ~/selfstudy/rust/practice/rustlings && rustlings
```
Do these in order: `08_enums` → `12_options` → `13_error_handling`. Skip `10_modules` for now.

How they map to this guide: enums → Parts 1–2 · options → Part 3 · error_handling → Parts 4–5.
For every compiler error, say the code and what it protects against **before** you fix it.

---

## Part 9: Build: providers, the SSE parser, and GatewayError

### Read Pydantic's version first (10 min)
In the build session, Claude walks you through `providers/base.ts`, `anthropic.ts`, and the error paths in `handler.ts`. What to notice:
- Each provider decides **how to send the key** (Anthropic: `x-api-key`; OpenAI-style: `Authorization: Bearer`) and **how to read usage** out of the response.
- In TS, a failure is a thrown exception that some outer `catch` turns into an HTTP status. **In Rust, every failure becomes a variant you return, and the status code comes from one `match`.**

### Step 0: Leftovers from stage 1 (5 min)
- Run `cargo clippy`. Decide on each dead-code warning: is it used yet (add the use or a test), or is it coming soon (`#[allow(dead_code)]` with a comment)? Don't leave warnings.
- Retype `main` yourself (Claude wrote it in stage 1).

### Step 1: `Config::load` returns a `Result`
```rust
#[derive(Debug, thiserror::Error)]
pub enum ConfigError { /* Read(..), Parse(..) */ }

pub fn from_toml(s: &str) -> Result<Config, ConfigError> { todo!() }
pub fn load(path: &str) -> Result<Config, ConfigError> { todo!() }
```
- Write it **by hand first** (the `From` impls from Part 5), then switch to thiserror. `cargo add thiserror`.
- The TOML parse error type is `toml::de::Error`.
- **On purpose:** before writing the `From` impls, use `?` and read the E0277.
- **Tests:** one invalid TOML string → `Err(ConfigError::Parse(_))` (`assert!(matches!(..))`). One missing path → `Err(ConfigError::Read(_))`.
- `main` now has to handle the `Result`. Use `anyhow` there (`cargo add anyhow`, `fn main() -> anyhow::Result<()>`).

### Step 2: The provider decides the auth header
You already have `enum ProviderId` in `config.rs`. Give it a method:
```rust
impl ProviderId {
    pub fn auth_header(&self, secret: &str) -> (&'static str, String) { todo!() }
}
```
- Anthropic → `("x-api-key", secret)`. OpenAI, Groq → `("authorization", "Bearer <secret>")`. Look up Vertex (it's a Bearer token too).
- **No `_` arm.** List every variant.
- **Tests:** one per variant.
- **On purpose:** add a `Mistral` variant and read the E0004. Where else in the code did it point?

### Step 3: The Anthropic SSE parser (`src/sse.rs`)
An Anthropic stream looks like this:
```
event: message_start
data: {"type":"message_start","message":{"usage":{"input_tokens":25,"output_tokens":1}}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hi"}}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":12}}

event: message_stop
data: {"type":"message_stop"}
```
```rust
pub enum Event { MessageStart { .. }, ContentBlockDelta { .. }, MessageDelta { .. }, MessageStop, Ping, Error { .. }, Other }
pub fn parse_line(line: &str) -> Result<Option<Event>, serde_json::Error> { todo!() }
pub fn usage(stream: &str) -> Result<Usage, serde_json::Error> { todo!() }   // Usage { input_tokens, output_tokens }
```
- `parse_line`: only `data: ` lines carry an event (`line.strip_prefix("data: ")`). `event:` lines and blank lines → `Ok(None)`. Why `Result<Option<..>>` and not just `Option`?
- `usage`: loop over `stream.lines()`, use `?` on each parse, add up input tokens from `MessageStart` and output tokens from `MessageDelta`.
- Anthropic's error event is `{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}`. Model the nested struct.
- `cargo add serde_json`. Save the stream above as `tests/fixtures/anthropic_stream.txt`, and test `usage` on it: `input 25, output 12`.
- **Test:** a garbage `data:` line → `Err`.

### Step 4: `GatewayError` → HTTP status
```rust
#[derive(Debug, thiserror::Error)]
pub enum GatewayError { /* UnknownKey, ProviderNotAllowed(String), MissingProject(u32), Upstream(..), ... */ }

impl GatewayError {
    pub fn status(&self) -> u16 { todo!() }
}

impl Config {
    pub fn authorize(&self, key: &str, provider: &str) -> Result<&ApiKey, GatewayError> { todo!() }
}
```
- Choose the codes: 401, 403, 500, 502. Which variant gets which, and why?
- `authorize` chains the lookups: `find_key(..).ok_or(..)?`, then `allows`. No `if let` pyramid.
- `#[error("...")]` messages must **never contain the key** (like the redacted `Debug` in stage 1). Add a test for that.
- **Tests:** one per variant's status, and `authorize` returning each error.

### Step 5: Wire `main`
- `llm-gateway check <config.toml> <api-key> <provider>` prints `ok: key #3 → project "default"`, or `403 provider not allowed: openai`, and exits non-zero on an error.
- `cargo test` ✅ · `cargo clippy` with no warnings ✅ · no `.unwrap()`/`.expect()` outside tests and `main`.

**Stretch:** `impl FromStr for ProviderId` so `"anthropic".parse::<ProviderId>()` works in `check`. What's its `Err` type?

---

## Done when
- [ ] `load` returns `Result`; `auth_header`, `parse_line`/`usage`, and `authorize` + `status` have passing tests. `cargo clippy` is clean.
- [ ] You've triggered and read out loud **E0004** and **E0277** (both the `From` one and the `Option`-in-`Result` one), and run `rustc --explain` on each.
- [ ] The fixture stream gives `input 25, output 12`.
- [ ] In about 60 seconds, you can explain: how Rust handles errors without exceptions, unwrap vs expect vs `?`, and thiserror vs anyhow.

**Next:** `/rs-drill` (mastery check for stage 2), then stage 3 (`iterators-closures`), where `usage` gets rewritten as an iterator chain and costs come from genai-prices.
