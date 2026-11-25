# Ownership & borrowing

## Moves
Q: Does this compile?
```rust
struct ApiKey { key: String }
let k = ApiKey { key: String::from("sk-123") };
let k2 = k;
println!("{}", k.key);
```
A: No. E0382, borrow of moved value: `let k2 = k;` moves ownership into `k2`, and `k` can't be used after that.
Why: `k` is still in scope, but the compiler marks it moved-from. Fixes: use `k2`, borrow with `&k`, or `.clone()` if you really need two owners.

Q: `struct ApiKey { id: u32 }`, then `let k2 = k;` and use `k.id`. Does it compile?
A: No, still E0382. A struct is only Copy if it derives `Clone, Copy`, even when every field is Copy.
Why: Copy is opt-in. `k` is an owner, not a reference, so assignment moves it unless the type is Copy.

## String vs &str
Q: What is `String` vs `&str`, and which should a read-only parameter take?
A: `String` owns a growable UTF-8 buffer on the heap. `&str` is a borrowed (pointer, length) view into string data someone else owns. Read-only parameters take `&str`.
Why: `&String` derefs to `&str`, so a `&str` parameter accepts both Strings and literals without cloning.

## Borrow rules
Q: Does this compile?
```rust
let mut keys = vec![String::from("sk-a")];
let first = &keys[0];
keys.push(String::from("sk-b"));
println!("{}", first);
```
A: No. E0502: `keys` can't be borrowed as mutable while `first` (a shared borrow) is still in use.
Why: `push` can reallocate and leave `first` dangling. The rule is many `&` or one `&mut`, never both. Fix: use `first` before the push, or clone it.

## Lifetimes
Q: Why doesn't `fn longest_key(a: &str, b: &str) -> &str` compile?
A: E0106, missing lifetime specifier. With two input references, the compiler can't tell which one the output borrows from. Fix: `fn longest_key<'a>(a: &'a str, b: &'a str) -> &'a str`.
Why: Elision only fills in the output lifetime when there's exactly one input reference (or `&self`).

## Returning borrows
Q: Why does `find_key(&self, key: &str)` return `Option<&ApiKey>` and not `Option<ApiKey>`?
A: The config owns the keys. Returning `&ApiKey` lends one out with no copy. An owned return would need a move out of `&self` (impossible) or a clone on every lookup.
Why: `Option` covers "not found" without null. The borrow ties the result's lifetime to `&self`.

## Drop
Q: What happens to a `String` when its owner goes out of scope?
A: `drop` runs at the closing brace and frees the heap buffer. The stack part (ptr, len, cap) goes away too.
Why: This is RAII: deterministic cleanup with no GC and no manual free.

## Partial moves
Q: Does this compile?
```rust
let cfg = ProviderConfig { name: "anthropic".to_string(), /* ... */ };
let names = vec![cfg.name];
let all = vec![cfg];
```
A: No. E0382, use of partially moved value: `vec![cfg.name]` moved the `name` String out, so `cfg` can't be moved as a whole.
Why: The struct now has a hole. Other fields are still usable. Fix: `cfg.name.clone()`. A `u32` field like `cfg.id` is fine because it's Copy.

## Moving out of a borrow
Q: Why doesn't this compile?
```rust
fn find_key(&self, key: &str) -> Option<ApiKey> {
    self.api_keys.iter().find(|k| k.key == key).map(|k| *k)
}
```
A: E0507, cannot move out of a shared reference. `*k` tries to take the `ApiKey` out of a config we only borrowed.
Why: The Vec would be left with a hole and the owner would later drop it again. Through `&` you can only read; return `&ApiKey`, or clone.

## Borrow scope
Q: Does this compile, and why?
```rust
let mut cfg = Config::load("config.example.toml");
let k = cfg.find_key("sk-gw-test-abc123").unwrap();
assert_eq!(k.id, 0);
cfg.api_keys.push(new_key);
```
A: Yes. The borrow held by `k` ends at its last use (the assert), so the push is allowed.
Why: Non-lexical lifetimes: borrows end at last use, not at the closing brace. Move the assert after the push and it's E0502.

## Ownership design
Q: Why does `ApiKey` store `providers: Vec<String>` and `project_id: u32` instead of `ProviderConfig` / `Project`?
A: `Config` already owns every provider and project. The key points at them by name or id, like a foreign key.
Why: Owned copies would duplicate data. `&ProviderConfig` inside `Config` would be a self-referential struct (stage 5).

## Exclusive borrows
Q: Does this compile?
```rust
let mut keys = vec![ApiKey { id: 1, key: String::from("sk-a") }];
let a = &mut keys[0];
let b = &mut keys[0];
a.id = 2;
b.id = 3;
```
A: No. E0499, cannot borrow `keys` as mutable more than once at a time.
Why: `&mut` is exclusive. If two existed, one could replace or free data the other still points at (aliasing); across threads that's a data race. Fix: reuse `a`, or finish with `a` before taking `b`.

## Borrowing parameters
Q: `fn log_key(k: ApiKey)` only reads `k.id`. After `log_key(k)`, the caller uses `k.key`. Which error, and what's the right signature?
A: E0382, borrow of moved value. Use `fn log_key(k: &ApiKey)` and call `log_key(&k)`.
Why: By-value parameters take ownership and drop it on return. The `&` goes on the type, not the name. E0507 is a different error: moving out of a borrow.

## Clone vs restructure
Q: You hold `key: &ApiKey` from `cfg` and need `cfg.record_usage(&mut self, ..)`. Why not just `.clone()` the key on the request path?
A: Clone copies the key String plus the providers Vec and its Strings: several heap allocations per request. Copy just the `Copy` fields you need (`key.id`) or reorder.
Why: Cost scales with request rate. Real fix: keep mutable usage out of read-only Config (separate store, stage 7). Clone is fine in tests and startup code.
Flip: When is cloning to satisfy the borrow checker fine?
