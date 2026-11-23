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
