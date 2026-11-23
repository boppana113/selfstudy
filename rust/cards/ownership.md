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
