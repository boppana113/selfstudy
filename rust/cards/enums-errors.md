# Enums & errors

## Exhaustive match
Q: Does this compile?
```rust
enum Provider { Anthropic, OpenAI, Groq }
fn auth_header(p: &Provider) -> &'static str {
    match p {
        Provider::Anthropic => "x-api-key",
        Provider::OpenAI => "authorization",
    }
}
```
A: No. E0004, non-exhaustive patterns: `&Provider::Groq` not covered. Add a `Groq` arm.
Why: `match` must cover every variant, so adding a variant makes the compiler list every match to update. A `_` arm turns that off, so avoid it on your own enums.

## Option vs Result
Q: Option vs Result: what is the `E` in `Result<T, E>` for, in the gateway?
A: `Option` = no value is a normal outcome (`find_key`). `Result` = it can fail, and `E` says how, so the caller can act differently: `GatewayError` variants map to 401/403/502; `ConfigError` separates missing file from bad TOML.
Why: `None` can't tell the caller which failure happened.

## ? and From
Q: Does this compile?
```rust
enum GatewayError { BadConfig(String), NoKey }
fn load(path: &str) -> Result<String, GatewayError> {
    let text = std::fs::read_to_string(path)?;
    Ok(text)
}
```
A: No. E0277, `?` couldn't convert the error to `GatewayError`. Fix: `impl From<std::io::Error> for GatewayError`, or `.map_err(|e| GatewayError::BadConfig(e.to_string()))?`.
Why: `x?` desugars to `match x { Ok(v) => v, Err(e) => return Err(From::from(e)) }`.

## unwrap / expect / ?
Q: unwrap vs expect vs `?`?
A: unwrap and expect both panic on Err/None (expect with your message). `?` returns the error early to the caller, converting it with From. Request code uses `?`; unwrap is for tests; expect for "can't fail, and here's why".
Why: a panic in a handler kills the request task; `?` turns it into an error response.

## Enums with data
Q: Why model Anthropic events as `enum Event { Ping, ContentBlockDelta { text: String }, ... }` instead of one struct with `kind: String` and Option fields?
A: Each variant carries only its own fields, so invalid combinations (a ping with text) can't be built, and `match` forces handling every variant.
Why: "make invalid states unrepresentable": the type does what a Pydantic validator would.

## thiserror vs anyhow
Q: thiserror vs anyhow: which goes where in the gateway?
A: thiserror for library errors callers match on (`GatewayError` → status code); anyhow in `main`/CLI where errors are only reported, with `.context("...")`.
Why: rule of thumb: if the caller acts on which error it was, use an enum (thiserror); if it only prints it, use anyhow.

## serde
Q: What's the serde equivalent of Pydantic's `Usage.model_validate_json(s)`, and what happens on a missing required field?
A: `#[derive(Deserialize)] struct Usage { input_tokens: u32 }` + `serde_json::from_str::<Usage>(s)`. A missing field returns `Err` ("missing field `input_tokens`"), not an exception. `Option<T>` fields may be missing.
Why: the derive generates the parser at compile time; errors are values handled with `?`.
