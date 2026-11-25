# Ownership & borrowing

## 2026-11-22 · Pretest · 29% (✅ 0 · 🟨 4 · ❌ 3)

**Q1. Predict: `let k2 = k;` then use `k.key` (ApiKey { key: String }).** 🟨
- Said: won't compile, k "no longer exists", replaced by k2.
- Strong: E0382, borrow of moved value. Assignment moves ownership of the `ApiKey` (and its heap String) into `k2`. `k` is still in scope, but the compiler marks it moved-from and rejects any use of it. Fix: use `k2`, borrow (`let k2 = &k;`), or `.clone()` if two owners are really needed.
- Gap: vocabulary ("move", E0382).

**Q2. Same, with `ApiKey { id: u32 }`.** 🟨
- Said: no, moved, "reference error".
- Strong: Still E0382. A `u32` field doesn't make the struct Copy. Only types that implement `Copy` are copied on assignment, and a struct needs `#[derive(Clone, Copy)]` for that. `k` is an owner, not a reference.
- Gap: owner vs reference; Copy is opt-in.

**Q3. String vs &str; parameter type for read-only.** 🟨
- Said: String is a "class constructor"; &str for borrowing; use &str.
- Strong: `String` owns a growable UTF-8 buffer on the heap (ptr, len, cap). `&str` is a borrowed view: a pointer and a length into string data someone else owns (a String, or a literal in the binary). Take `&str` for read-only parameters, because `&String` derefs to it, so callers can pass either one without cloning.
- Gap: String = owned heap buffer.

**Q4. Predict: `let first = &keys[0]; keys.push(..); println!(first)`.** ❌
- Said: type isn't specified.
- Strong: E0502, cannot borrow `keys` as mutable because it is also borrowed as immutable. `push` may reallocate the Vec and leave `first` dangling, so the rule (many `&` or one `&mut`, never both) blocks it. Fix: finish using `first` before the push, or clone the String.
- Gap: shared borrow blocks mutation.

**Q5. Why doesn't `fn longest_key(a: &str, b: &str) -> &str` compile?** ❌
- Said: don't know.
- Strong: E0106, missing lifetime specifier. With two input references, elision can't tell which one the output borrows from. Write `fn longest_key<'a>(a: &'a str, b: &'a str) -> &'a str`: the result is valid only while both inputs are.
- Gap: E0106 / lifetime elision.

**Q6. Why does `find_key` return `Option<&ApiKey>` and not `Option<ApiKey>`?** ❌
- Said: don't know.
- Strong: The Config owns the keys. Returning `&ApiKey` lends one out without copying or removing it. Returning `ApiKey` would mean either moving it out of the config (impossible through `&self`) or cloning it on every request. The `Option` covers the key not being found, with no null.
- Gap: lend vs move vs clone.

**Q7. What happens to a String when its owner goes out of scope?** 🟨
- Said: removed from the stack.
- Strong: Rust calls `drop` at the closing brace. The stack part (ptr/len/cap) goes away, and `String`'s Drop frees the heap buffer. This is RAII: the owner going out of scope frees the resource deterministically, with no GC and no manual free.
- Gap: Drop frees the heap.

**Watch while building:** E0502 when you mutate the config while holding a key ref · `&str` params vs owned `String` struct fields · writing `find_key` returning `Option<&ApiKey>` and hitting the lifetime it implies.

## 2026-11-24 · Drill · 67% (✅ 2 · 🟨 4 · ❌ 0)

**R1. Predict: two `&mut keys[0]` (`a`, `b`) both used.** 🟨
- Said: won't compile, only one mutable borrow; reason "race condition"; fix: one borrow.
- Strong: E0499, cannot borrow `keys` as mutable more than once. `&mut` is an exclusive borrow: if two existed, one could replace or free data (e.g. reassign the String) while the other still points at it. Single-threaded this is an aliasing bug; across threads it's a data race, which is why the same rule makes Rust data-race-free. Fix: reuse `a`, or end `a`'s last use before taking `b`.
- Gap: error code; aliasing vs race.

**R2. Predict: `log_key(k: ApiKey)` then use `k.key`.** 🟨
- Said: k moved into log_key and dropped; fix: borrow, wrote `log_key(&k: ApiKey)`.
- Strong: E0382, borrow of moved value. Passing by value moves ownership into the function, which drops it on return. A read-only function should take `k: &ApiKey` (the `&` goes on the type) and the caller passes `&k`.
- Gap: E0382 vs E0507 confusion; `&` on the type, not the name.

**R3. Explain: String vs &str.** 🟨
- Said: String to write/append, &str to read. Follow-up: fields are String because Config must own data after the TOML is gone (correct).
- Strong: `String` owns a heap buffer; `&str` is a borrowed (ptr, len) view into bytes someone else owns (a String, a slice, or a literal). The line is owned vs borrowed, not mutable vs read-only. Struct fields own (`String`) so they outlive the source text; read-only parameters take `&str` because `&String` derefs to it for free.
- Gap: framed as mutability, not ownership.

**R4. Predict: `fn label(k: &ApiKey) -> &str { let s = format!(..); &s }`.** ✅
- Said: s dropped at return, &s dangles; fix: return String.
- Strong: E0515, cannot return reference to local variable. A function can return borrows only of its inputs; anything it creates must be returned owned.
- Gap: didn't know E0515 (new code).

**R5. Design: clone the key vs restructure to avoid E0502 before `record_usage(&mut self)`.** 🟨
- Said: A (clone), simpler. Follow-up: clone copies to heap, doesn't scale with many keys.
- Strong: clone copies one ApiKey (key String + providers Vec of Strings) = several allocations per request, so cost scales with request rate, not key count. On the hot path, copy the `Copy` fields you need (`key.id` is 4 bytes) or reorder. Real fix: usage doesn't belong in read-only Config; keep it in a separate store so recording never needs `&mut cfg` (stage 7).
- Gap: picked by simplicity, not cost; per-request vs per-key.

**R6. Code it: `keys_for_project(keys: &[ApiKey], project_id: u32) -> Vec<&ApiKey>`.** ✅ self-reported (marked finished by user; code not reviewed).
- Strong: `keys.iter().filter(|k| k.project_id == project_id).collect()`. No annotation needed: one input reference, so elision ties the returned `&ApiKey`s to `keys`.

**Gaps:** error-code recall (E0499, E0382 vs E0507, E0515) · owned-vs-borrowed framing for String/&str · clone cost reasoning · `&T` param syntax.
