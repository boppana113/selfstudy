# Enums & errors

## 2026-11-25 · Pretest · 21% (✅ 0 · 🟨 3 · ❌ 4)

**Q1. Predict: `match p` over `Provider { Anthropic, OpenAI, Groq }` with no `Groq` arm.** ❌
- Said: `&Provider::Groq` at the call site is the problem; must instantiate first.
- Strong: E0004, non-exhaustive patterns: `&Provider::Groq` not covered. `match` must handle every variant. Passing `&Provider::Groq` is fine, because a unit variant is already a value. Fix: add a `Provider::Groq => "authorization"` arm. Avoid `_`, which would silently swallow future variants.
- Gap: exhaustive match / E0004.

**Q2. Option vs Result, with a gateway example of each.** 🟨
- Said: Option = value or nothing (key lookup). Result = T or E; unsure of a gateway use.
- Strong: `Option` is "there may be no value, and that's normal" (`find_key`). `Result` is "this can fail, and E says how", so the caller can act differently on each failure. Gateway: `Config::load -> Result<Config, ConfigError>` (missing file vs bad TOML), and request handling returning `Result<_, GatewayError>` where each variant maps to an HTTP status (401/403/502).
- Gap: what E is for.

**Q3. Predict: `fs::read_to_string(path)?` in a fn returning `Result<String, GatewayError>`.** ❌
- Said: don't know.
- Strong: E0277, `?` couldn't convert the error to `GatewayError`. `?` desugars to `match` with `return Err(From::from(e))`, and there's no `From<io::Error> for GatewayError`. Fix: write that impl (or thiserror `#[from]`), or `.map_err(|e| GatewayError::BadConfig(e.to_string()))?`.
- Gap: `?` calls From.

**Q4. unwrap vs expect vs ?.** ❌
- Said: unwrap gives Ok or Error; expect is a return message; ? unknown.
- Strong: All three extract the success value. `unwrap` panics on Err/None; `expect("msg")` panics with your message (use it when failure is impossible, and say why); `?` returns the error early to the caller, converting it via From. Request code uses `?` so one bad request becomes an error response, not a crashed task.
- Gap: unwrap/expect panic; ? propagates.

**Q5. Model Anthropic SSE events in Rust vs a Python class with all-optional fields.** 🟨
- Said: enum for the types; serde to validate the delta.
- Strong: `enum Event { MessageStart { input_tokens }, ContentBlockDelta { text }, MessageDelta { output_tokens }, MessageStop, Ping, Error { message } }`. Each variant carries only its own fields, so "a ping with text" can't be constructed and no reader has to check `type` and then unwrap Options. serde's `#[serde(tag = "type")]` deserializes straight into it, and `match` forces handling every variant.
- Gap: variants carry data; invalid states unrepresentable.

**Q6. thiserror vs anyhow.** ❌
- Said: haven't heard of them.
- Strong: thiserror derives Display/Error/From for your own error enum, for library code where callers match on variants (GatewayError → status). anyhow is one catch-all error type plus `.context()`, for app code (main/CLI) that only reports errors. The gateway uses both: thiserror in the core, anyhow in main.
- Gap: never seen.

**Q7. serde equivalent of `Usage.model_validate_json(s)`; missing field?** 🟨
- Said: Pydantic raises ValidationError; Rust equivalent unknown.
- Strong: `#[derive(Deserialize)] struct Usage { input_tokens: u32 }` and `serde_json::from_str::<Usage>(s)`, which returns `Err(serde_json::Error)` ("missing field `input_tokens`") instead of raising. `Option<T>` fields may be missing. The derive generates the parser at compile time, with no runtime reflection.
- Gap: serde_json::from_str returns Result.

**Watch while building:** E0277 the first time `?` meets `io::Error`/`toml::de::Error` (write the From impls by hand before thiserror) · reaching for `_` in matches on your own enums · `.expect` creeping back into non-test code.
