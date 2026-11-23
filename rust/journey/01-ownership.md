# Stage 1 · ownership: Narrated walkthrough

> Open this with **Cmd+K V** (Markdown preview beside the editor). Keep a terminal open below it.
> You type every `▶ Type this` block yourself. Don't paste them. Each `✓ Checkpoint` is a question to answer out loud before you move on.
> This condenses Book ch. 4, 5, and 8. Book links are there for when you want more depth. You shouldn't need them to keep going.

**Where this goes:** by the end, your gateway loads its config (projects, users, API keys, providers) from a TOML file and can look up the API key on an incoming request with `find_key`. Every later stage calls `find_key` first.

**Your pretest gaps (2026-11-22), and where this guide covers them:** borrowing vs mutating (Part 2) · `String` vs `&str` (Part 3) · returning `&T` vs `T` (Parts 4, 6) · lifetimes / E0106 (Part 6) · Drop (Part 1).

**Where code goes:** every type-along project lives in `~/selfstudy/rust/practice/<name>/` (`target/` is gitignored, so commit freely). The gateway is the one exception: it's its own repo (Part 8).

**Keyboard loop:** run `bacon` in the project folder. Then: edit → **Cmd+S** → bacon re-checks → **F8** jumps to the next error → **Cmd+.** applies a quick fix. **Ctrl+`** moves you between the terminal and the editor, and **Cmd+1** jumps to the editor.

▶ Type this (one scratch project for Parts 1–6):
```sh
cd ~/selfstudy/rust/practice
cargo new own && cd own
bacon
```
Each part adds a function to `src/main.rs` and calls it from `main`. Once you've seen a part's error and fixed it, leave the fixed version in the file.

---

## Part 1: Ownership: one owner, freed when it leaves scope (Book ch. 4.1)

**The Python comparison.** In Python, `b = a` makes two names point at one object, and a garbage collector frees it once nothing points at it anymore. Rust has no GC. Instead it has **three rules**:

1. Every value has exactly one **owner** (a variable, a struct field, a Vec slot).
2. When the owner goes out of scope, the value is **dropped**, which frees its memory.
3. Assigning it or passing it to a function **moves** ownership. The old name becomes unusable.

**Why a `String` moves.** A `String` is three words on the stack (pointer, length, capacity) that point at bytes on the heap:

```
stack: k = [ ptr | len 6 | cap 6 ] ──► heap: s k - 1 2 3
```

`let k2 = k;` copies those three words. If both `k` and `k2` stayed usable, both would free the same heap buffer at `}` (a double free). So Rust marks `k` as **moved-from**, and only `k2` frees the buffer.

▶ Type this, then run it and **read the error out loud**:
```rust
#[derive(Debug)]
struct ApiKey { id: u32, key: String }

fn take(k: ApiKey) { println!("took {:?}", k); }   // k is dropped at this `}`

fn part1() {
    let k = ApiKey { id: 1, key: String::from("sk-123") };
    take(k);                 // ownership moves into `take`
    println!("{}", k.id);    // ← E0382
}
```
**E0382 (borrow of moved value).** This is one of the three errors this stage is about. Run `rustc --explain E0382`. Three fixes, from best to worst:
- **Restructure.** Finish using `k` before you give it away (move the `println!` above `take`).
- **Borrow.** Make it `fn take(k: &ApiKey)` and call `take(&k)`. That's Part 2.
- **Clone.** Call `take(k.clone())` (add `Clone` to the derive). It works, but it copies the heap bytes. Reach for this last.

### Copy vs Clone
- **Copy**: a bitwise copy happens implicitly on assignment, and the original stays usable. Only for types with no heap data and no cleanup: `u32`, `f64`, `bool`, `char`, `&T`, and tuples of these.
- **Clone**: an explicit `.clone()` that may allocate (`String`, `Vec`).
- **A struct is never Copy unless you derive it.** `struct ApiKey { id: u32 }` still moves. Add `#[derive(Clone, Copy)]` and it's copied instead. You can't derive Copy on a struct that holds a `String`.

### Drop = RAII
At the closing `}`, Rust calls `drop` on every owned value in reverse order of declaration. A `String`'s drop frees its heap buffer. The same thing closes files, releases locks, and closes sockets, with no `with` block or `finally` needed: **when the owner goes out of scope, the resource is released.**

▶ Type this:
```rust
struct Noisy(&'static str);
impl Drop for Noisy {
    fn drop(&mut self) { println!("drop {}", self.0); }
}

fn part1_drop() {
    let _a = Noisy("a");
    let _b = Noisy("b");
    println!("end of scope");
}   // prints: end of scope, drop b, drop a
```

✓ **Checkpoint:** `let x: u32 = 5; let y = x; println!("{x}");` Does it compile? What about the same thing with `String::from("5")`?
<details><summary>answer</summary>The u32 version compiles, because u32 is Copy, so <code>y</code> gets its own copy. The String version fails with E0382: the String moved into <code>y</code>.</details>

📖 Depth: [ch04-01 What is Ownership?](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html)

---

## Part 2: Borrowing: a reader-writer lock the compiler checks (Book ch. 4.2)

A **reference** lets code use a value without taking ownership. The owner keeps it, and the reference must not outlive the owner.

| | Syntax | How many at once | Can mutate? |
|---|---|---|---|
| shared borrow | `&T` | any number | no |
| exclusive borrow | `&mut T` | exactly one, and no `&` alongside it | yes |

**Many readers or one writer, never both.** It's an `RwLock`, except the compiler checks it at compile time and it costs nothing at runtime.

▶ Type this, and read the error out loud:
```rust
fn part2() {
    let mut keys = vec![String::from("sk-a"), String::from("sk-b")];
    let first = &keys[0];             // shared borrow of `keys` starts
    keys.push(String::from("sk-c"));  // ← E0502: needs &mut keys
    println!("{first}");              // shared borrow still in use here
}
```
**E0502** is the second of this stage's errors (and pretest Q4). It's not about types. **Why it matters:** `push` may reallocate the Vec's buffer to a new address, which would leave `first` pointing at freed memory. In C++ that's a use-after-free. In Rust it doesn't compile.

**Fix:** move the `println!` above the `push`. A borrow lasts until its **last use**, not until the end of the scope (this is called "non-lexical lifetimes"). Once `first` isn't used anymore, `push` is allowed.

▶ Type this too (two `&mut` at once):
```rust
let mut s = String::new();
let a = &mut s;
let b = &mut s;    // ← E0499
a.push('x'); b.push('y');
```
**Why two `&mut` are banned:** if two writers could hold `&mut` to the same value, one of them (or another thread) could change it while the other is in the middle of reading or writing it. Ruling it out at compile time removes data races and iterator invalidation entirely.

### Borrowing in function parameters
```rust
fn print_key(k: &ApiKey) { println!("{}", k.id); }   // reads it
fn rotate(k: &mut ApiKey) { k.key.push_str("-v2"); } // changes it
fn consume(k: ApiKey) { /* owns it, dropped here */ }
```
Pick the weakest one that works: `&T` if you only read, `&mut T` if you change it, owned `T` if the function keeps it (stores it, or sends it somewhere).

✓ **Checkpoint:** Why is it safe to have 10 `&keys` at once but not one `&keys` plus one `&mut keys`?
<details><summary>answer</summary>Readers can't invalidate each other, but a writer can, for example by reallocating or freeing what the reader points at. So sharing and mutating are each fine alone, and never allowed together.</details>

📖 Depth: [ch04-02 References and Borrowing](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html)

---

## Part 3: `String` vs `&str` and slices (Book ch. 4.3)

| | What it is | Owns? | Python / TS analogy |
|---|---|---|---|
| `String` | (ptr, len, cap) → a growable UTF-8 buffer on the heap | yes | a `str` you own and can append to |
| `&str` | (ptr, len) → a view into UTF-8 bytes someone else owns | no | a read-only window, like a `memoryview` |
| `Vec<T>` / `&[T]` | the same pair, for any element type | yes / no | `list` / a read-only view of a list |

A string literal `"sk-123"` is a `&'static str`: a view into bytes baked into the binary.

**The rules of thumb:**
- **Function parameters:** take `&str`. Callers can pass `&my_string` (it auto-converts, which is called *deref coercion*) or a literal.
- **Struct fields:** use `String`. The struct should own its data. A `&str` field would borrow from something else, and then the struct needs a lifetime (stage 5).
- **Return values:** return `String` if you built new text, or `&str` if you're pointing into something the caller already owns.

▶ Type this:
```rust
fn is_live_key(key: &str) -> bool { key.starts_with("sk-live-") }

fn part3() {
    let owned = String::from("sk-live-abc");
    println!("{}", is_live_key(&owned));        // &String → &str, automatically
    println!("{}", is_live_key("sk-test-xyz")); // literal is already &str
    let prefix: &str = &owned[0..7];            // slice: a view, no allocation
    println!("{prefix}");
}
```
Slices index **bytes**, not characters. `&s[0..1]` on `"é"` panics because it cuts a character in half. API keys are ASCII, so it's fine here.

✓ **Checkpoint:** Why does `fn is_live_key(key: &String)` work but get flagged by clippy?
<details><summary>answer</summary>It only accepts <code>&String</code>, so a caller holding a literal has to allocate a String first. <code>&str</code> accepts both. Clippy's lint is <code>ptr_arg</code>.</details>

📖 Depth: [ch04-03 The Slice Type](https://doc.rust-lang.org/book/ch04-03-slices.html)

---

## Part 4: Structs and methods: `&self`, `&mut self`, `self` (Book ch. 5)

```rust
#[derive(Debug, Clone)]
struct ApiKey {
    id: u32,
    key: String,            // owned: the struct owns its data
    project_id: u32,
    user_id: Option<u32>,   // optional field, like `user?: number` in TS
}

impl ApiKey {
    fn new(id: u32, key: &str, project_id: u32) -> Self {      // associated fn (no self), like a @classmethod
        ApiKey { id, key: key.to_string(), project_id, user_id: None }
    }
    fn is_project(&self, p: u32) -> bool { self.project_id == p } // reads
    fn assign_user(&mut self, u: u32) { self.user_id = Some(u); } // changes it
    fn into_key(self) -> String { self.key }                      // consumes the struct
}
```
The three receivers are the three parameter kinds from Part 2: **`&self`** borrows it to read, **`&mut self`** borrows it to change, and **`self`** takes ownership (the caller can't use it afterwards). Call them as `k.is_project(1)` and Rust adds the `&` or `&mut` for you.

### You can't move out of a borrow
This is the snippet that explains `find_key`'s signature. ▶ Type this:
```rust
struct Config { api_keys: Vec<ApiKey> }

impl Config {
    fn find_owned(&self, key: &str) -> Option<ApiKey> {
        for k in &self.api_keys {           // k: &ApiKey
            if k.key == key { return Some(*k); }  // ← E0507
        }
        None
    }
}
```
**E0507 (cannot move out of `*k`, which is behind a shared reference).** `&self` means you're only *borrowing* the config. You can't take a key out of it and hand it away, because the config would be left with a hole in it. You have two options:
- `Some(k.clone())`: allocates a copy of the key string **on every request**. That's wasteful.
- Return `Option<&ApiKey>`, which **lends** the key out. No copy, and the config still owns it. ✅ That's `find_key`.

✓ **Checkpoint:** Pretest Q6, again: why does `find_key(&self, key: &str)` return `Option<&ApiKey>` and not `Option<ApiKey>`?
<details><summary>answer</summary>The config owns the keys. Lending a <code>&ApiKey</code> costs nothing. An owned return would need a move out of a borrow (E0507) or a clone on every lookup. The <code>Option</code> is "not found", without null.</details>

📖 Depth: [ch05 Structs](https://doc.rust-lang.org/book/ch05-00-structs.html)

---

## Part 5: Collections and ownership: `Vec`, `HashMap` (Book ch. 8)

Collections **own** their elements. Pushing a value moves it in, and dropping the collection drops everything inside.

```rust
use std::collections::HashMap;

let mut by_id: HashMap<u32, ApiKey> = HashMap::new();
let k = ApiKey::new(3, "sk-live-abc", 1);
by_id.insert(k.id, k);            // k moves into the map. `k` is unusable now (E0382 if you try)

let found: Option<&ApiKey> = by_id.get(&3);    // get lends: Option<&V>
if let Some(k) = by_id.get_mut(&3) { k.assign_user(2); }  // get_mut lends mutably
```
**Notice that `HashMap::get` returns `Option<&V>`.** The standard library makes the same choice you're making with `find_key`: lookups lend, they don't give values away.

**The three ways to loop:**
```rust
for k in &keys { }       // k: &ApiKey     read; keys still usable after
for k in &mut keys { }   // k: &mut ApiKey change in place
for k in keys { }        // k: ApiKey      consumes the Vec; keys is gone after
```
`for k in keys` followed by using `keys` later is a common E0382. The fix is almost always `&keys`.

✓ **Checkpoint:** `let mut m = HashMap::new(); m.insert(1, "a".to_string()); let v = m.get(&1); m.insert(2, "b".to_string()); println!("{v:?}");` Which error is it, and why?
<details><summary>answer</summary>E0502. <code>v</code> is a shared borrow into the map, and <code>insert</code> needs <code>&mut m</code> (it might rehash and move every value). It's the same shape as the Vec push in Part 2.</details>

📖 Depth: [ch08 Collections](https://doc.rust-lang.org/book/ch08-00-common-collections.html)

---

## Part 6: Returning references, and your first lifetime (E0106) (Book ch. 10.3, briefly)

A returned `&T` has to point into something that outlives the function call. The compiler needs to know **which input** that is.

▶ Type this:
```rust
fn longest_key(a: &str, b: &str) -> &str {      // ← E0106
    if a.len() > b.len() { a } else { b }
}
```
**E0106 (missing lifetime specifier)** is the third of this stage's errors (and pretest Q5). The result borrows from `a` *or* `b`, and the compiler won't guess which. You name it:
```rust
fn longest_key<'a>(a: &'a str, b: &'a str) -> &'a str { ... }
```
Read `'a` as "the result is valid for as long as both inputs are." **A lifetime annotation doesn't change how long anything lives.** It's a label that lets the compiler check your claim.

**Why you usually don't write them (the elision rules):**
1. Each input reference gets its own lifetime.
2. If there's exactly **one** input reference, the output gets that lifetime.
3. If there's `&self` or `&mut self`, the output gets `self`'s lifetime.

So `fn find_key(&self, key: &str) -> Option<&ApiKey>` needs no annotation: rule 3 ties the result to `&self`. That's correct, because the key lives in the config and not in the `key: &str` you searched with.

**The one you can't fix with a lifetime:**
```rust
fn make_key() -> &String { let s = String::from("sk"); &s }  // E0106, and `'static` won't save it
```
`s` is dropped at the `}`, so the reference would dangle. Return the owned `String` instead.

✓ **Checkpoint:** Why does `fn first_word(s: &str) -> &str` compile with no `'a`?
<details><summary>answer</summary>Elision rule 2: there's only one input reference, so the output must borrow from it.</details>

📖 Depth: [ch10-03 Lifetimes](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html) (only the first half for now. Stage 5 covers the rest.)

---

## Part 7: Rustlings (practice reps)

```sh
cd ~/selfstudy/rust/practice/rustlings && rustlings
```
Do these in order: `move_semantics` → `structs` → `strings` → `hashmaps`. **Skip `enums` and `modules`** (stage 2).

How they map to this guide: move_semantics → Parts 1–2 · structs → Part 4 · strings → Part 3 · hashmaps → Part 5.
For every compiler error, say the code and what it protects against **before** you fix it.

---

## Part 8: Build: gateway config and `find_key`

### Read Pydantic's version first (10 min)
In the build session, Claude walks you through `deploy/example.config.ts` (the config shape) and `gateway/src/types.ts`. What to notice:
- **Projects** have users and optional spending limits (daily/weekly/monthly).
- **API keys** belong to a project, optionally to a user, and list which **providers** they're allowed to use.
- **Providers** have a `providerId`, a `baseUrl`, and `credentials` read from an env var.
- In TS, every object is a reference that's shared and can be changed from anywhere. **In Rust you have to decide who owns each piece.** The `Config` owns everything, and everyone else borrows from it.

### Step 0: Create the repo
```sh
cd ~ && cargo new --bin llm-gateway && cd llm-gateway   # cargo new already runs git init
cargo add serde --features derive
cargo add toml
```
Two crates: `serde` is Rust's Pydantic (it validates data into typed structs), and `toml` parses the file. For now, read `#[derive(Deserialize)]` as "can be built from TOML". Stage 2 opens it up.

### Step 1: The types (`src/config.rs`)
Write these structs. Every field is owned (`String`, not `&str`). Why?
- `Config { projects: Vec<Project>, users: Vec<User>, api_keys: Vec<ApiKey>, providers: Vec<ProviderConfig> }`
- `Project { id: u32, name: String, spending_limit_daily: Option<f64> }`
- `User { id: u32, project_id: u32, name: String, spending_limit_daily: Option<f64> }`
- `ApiKey { id: u32, key: String, project_id: u32, user_id: Option<u32>, providers: Vec<String> }`
- `ProviderConfig { name: String, provider_id: String, base_url: String, credentials_env: String }`. This holds the **name** of the env var, never the secret itself. (`provider_id` becomes an enum in stage 2.)

Derive `Debug, Deserialize`. Add `mod config;` in `main.rs`.

**Test first:** build a `Config` by hand in a `#[test]` and assert `config.api_keys.len() == 1`.

⚠️ `#[derive(Debug)]` on `ApiKey` will print the raw key string in any `{:?}`. Note that, and we'll fix it in step 4.

### Step 2: Load from TOML
- Write `config.example.toml` using `[[projects]]`, `[[users]]`, `[[api_keys]]`, `[[providers]]` arrays-of-tables. Use fake keys only, like `sk-gw-test-...`.
- `fn from_toml(s: &str) -> Config` uses `toml::from_str(s).expect("bad config")`. (A real `Result` comes in stage 2.)
- `fn load(path: &str) -> Config` uses `std::fs::read_to_string`.
- **Test:** parse an inline TOML string (`r#"..."#`) and check one field from each section.

Question to answer: `from_toml` takes `&str`, but the returned `Config` has owned `String`s. Where did the bytes get copied?

### Step 3: `find_key`
```rust
impl Config {
    pub fn find_key(&self, key: &str) -> Option<&ApiKey> { todo!() }
}
```
- **Tests first:** one for a key that exists (`Some`, check its `id`) and one for a key that doesn't (`None`).
- Hint: `for k in &self.api_keys { ... }`. Then try rewriting it as `self.api_keys.iter().find(...)` (stage 3 previews this).
- **On purpose:** change the return type to `Option<ApiKey>` and read the E0507. Change it back.
- **On purpose:** in a test, hold `let k = cfg.find_key(..)`, then `cfg.api_keys.push(..)`, then use `k`. Read the E0502. Why is the compiler right?

### Step 4: Lookups that chain borrows
- `fn project_for(&self, key: &ApiKey) -> Option<&Project>` follows `key.project_id`.
- `fn allows(&self, key: &ApiKey, provider: &str) -> bool` checks whether `key.providers` contains it. (Watch for `&String` vs `&str` comparison friction. `.iter().any(|p| p == provider)` works.)
- **Redaction:** replace `#[derive(Debug)]` on `ApiKey` with a hand-written `impl std::fmt::Debug` that prints `key: "sk-gw-…"` (the first 6 chars and an ellipsis). Test that `format!("{:?}", k)` doesn't contain the full key.
- **On purpose (E0106):** write a free function `fn find_in(keys: &[ApiKey], key: &str) -> Option<&ApiKey>`. Read the error. Elision fails because there are two input refs. Add `'a` to the right inputs. Which one should the result borrow from, `keys` or `key`?

### Step 5: Wire `main`
- `llm-gateway check <config.toml> <api-key>` prints `key #3 → project "default", providers: [anthropic]`, or `unknown key`.
- It never prints the key itself.
- `cargo test` ✅ · `cargo clippy` with no warnings ✅

**Stretch:** build a `HashMap<String, usize>` index (key → position in `api_keys`) so `find_key` is O(1). Why not `HashMap<&str, &ApiKey>` stored inside `Config` itself? (You'll find out in stage 5. It's a self-referential struct.)

---

## Done when
- [ ] Config loads from TOML. `find_key`, `project_for`, and `allows` have passing tests. `cargo clippy` is clean.
- [ ] You've triggered and read out loud **E0382, E0502, E0507, E0106**, and run `rustc --explain` on each.
- [ ] `Debug` output never shows a full key.
- [ ] In about 60 seconds, you can explain ownership and borrowing, String vs &str, and why `find_key` returns `Option<&ApiKey>`.

**Next:** `/rs-drill` (mastery check for stage 1), then stage 2 (`enums-errors`), where `provider_id` becomes an enum and `.expect` becomes `Result`.
