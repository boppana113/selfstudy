# Stage 0 · basics: Narrated walkthrough

> Open this with **Cmd+K V** (Markdown preview beside the editor). Keep a terminal open below it.
> You type every `▶ Type this` block yourself. Don't paste them. Each `✓ Checkpoint` is a question to answer out loud before you move on.
> Book links are there for when you want more depth. You shouldn't need them to keep going.

**Where this goes:** by the end you've built `tokencost`, a small CLI that prints what an LLM call costs. You'll use the same kind of logic again in the gateway's cost tracker (stage 3).

**Setup check (1 min):**
```sh
rustc --version     # you have 1.92
cargo --version
code --list-extensions | grep rust-analyzer   # install "rust-analyzer" if missing
```
rust-analyzer shows types inline and puts errors under the line as you type. Most of your learning will come from those hints, so make sure it's installed.

**Where code goes:** every project in this guide lives in `~/selfstudy/rust/practice/<name>/` (`target/` is gitignored, so commit your work freely).

**Keyboard loop:** run `bacon` in the project folder (`cargo install bacon` once). Then: edit → **Cmd+S** → bacon re-checks → **F8** jumps to the next error → **Cmd+.** applies a quick fix. **Ctrl+`** moves you between the terminal and the editor, and **Cmd+1** jumps to the editor.

---

## Part 1: Cargo is your `uv` + `pytest` + `ruff` (Book ch. 1)

You'll almost never call `rustc` directly. Cargo creates projects, builds them, runs them, tests them, and lints them.

▶ Type this:
```sh
cd ~/selfstudy/rust/practice
cargo new hello && cd hello
cargo run
```

Here's what you got:
- `Cargo.toml` plays the role of `pyproject.toml`: the package name, edition, and `[dependencies]`.
- `src/main.rs` holds `fn main()`, the entry point. A binary crate must have one.
- `target/` is where build output goes. It's gitignored.

| Command | What it does | Python equivalent |
|---|---|---|
| `cargo check` | type-check only, fast | mypy |
| `cargo build` | compile to `target/debug/` | — |
| `cargo run` | build + run | `python main.py` |
| `cargo test` | run `#[test]` functions | pytest |
| `cargo clippy` | lint | ruff |
| `cargo build --release` | optimized build | — |

`println!` ends in `!` because it's a **macro**: code that writes code at compile time. That's how `println!("{x}")` can check the format string while compiling. For now, read `!` as "macro, not function" and move on.

✓ **Checkpoint:** Why is `cargo check` the one you'll run most?
<details><summary>answer</summary>It skips code generation, so it's fast. It's the "does it type-check" loop. rust-analyzer runs it every time you save.</details>

📖 Depth: [ch01-03 Hello, Cargo](https://doc.rust-lang.org/book/ch01-03-hello-cargo.html)

---

## Part 2: The guessing game, narrated (Book ch. 2)

This chapter gives you a quick tour of most of the language. Build it once, and pay attention to the places marked ⚑. Each later stage goes deep on one of them.

▶ Type this (`cargo new guess`, then replace `src/main.rs`):
```rust
use std::io;

fn main() {
    println!("Guess a number 1-100:");

    let mut guess = String::new();          // ⚑ mut: variables are immutable unless you say so
    io::stdin()
        .read_line(&mut guess)              // ⚑ &mut: lend it, mutably (stage 1)
        .expect("failed to read line");     // ⚑ read_line returns a Result (stage 2)

    let guess: u32 = guess.trim().parse().expect("type a number");  // ⚑ shadowing
    println!("You guessed {guess}");
}
```

Read it line by line:
- **`let mut guess`**: in Python every name can be reassigned. In Rust a binding can't change unless it's marked `mut`. The compiler can then tell you which values change, and so can someone reading the code.
- **`&mut guess`**: we *lend* `guess` to `read_line` so it can append to it, and we keep owning it. Ownership is all of stage 1. For now, `&` means "borrow it".
- **`.expect(...)`**: `read_line` can fail, and instead of raising an exception it *returns* a `Result`. `.expect` says "crash with this message if it failed". That's fine for a toy program. Stage 2 replaces it with real handling.
- **`let guess: u32 = ...`**: a *new* variable with the same name. This is **shadowing**, and it's normal Rust style when you convert a value from one type to another (String → u32). `parse()` needs to know which type to produce, and the `: u32` annotation tells it.

Now add the rest:

▶ Type this (put it above `fn main`, then replace the body):
```rust
use std::cmp::Ordering;
use std::io;

fn main() {
    let secret = 42; // the Book uses the `rand` crate. Optional detour, see below

    loop {
        println!("Guess:");
        let mut guess = String::new();
        io::stdin().read_line(&mut guess).expect("read failed");

        let guess: u32 = match guess.trim().parse() {
            Ok(n) => n,
            Err(_) => {
                println!("numbers only");
                continue;
            }
        };

        match guess.cmp(&secret) {
            Ordering::Less => println!("too small"),
            Ordering::Greater => println!("too big"),
            Ordering::Equal => {
                println!("you win");
                break;
            }
        }
    }
}
```

- **`match`** is a `switch` statement that won't compile if you miss a case. `cmp` returns one of exactly three `Ordering` values, and if you delete one arm the compiler refuses to build (error E0004, which is the main error in stage 2).
- **`match` on `parse()`**: `Ok(n) => n` takes the number out of the result. `Err(_) => continue` skips bad input. This is how errors look in Rust: you `match` on a returned value instead of writing `try/except`.
- **`loop`** loops forever until it hits `break`.

**Optional detour (10 min): your first dependency.** Add `rand = "0.8"` under `[dependencies]` in `Cargo.toml`, then use `let secret = rand::thread_rng().gen_range(1..=100);` with `use rand::Rng;`. Run `cargo build` and watch it fetch the crate from crates.io. `Cargo.lock` then pins the versions, the same job `uv.lock` does.

✓ **Checkpoint:** Delete the `Ordering::Equal` arm and run `cargo check`. Before you read the error, say what you think it will complain about.

📖 Depth: [ch02 Guessing Game](https://doc.rust-lang.org/book/ch02-00-guessing-game-tutorial.html)

---

## Part 3: Common concepts (Book ch. 3)

### 3.1 Variables, `const`, shadowing
```rust
let x = 5;
// x = 6;          // E0384: cannot assign twice to immutable variable
let mut y = 5; y = 6;               // fine
const MAX_TOKENS: u32 = 200_000;    // must have a type; SCREAMING_CASE; known at compile time
let s = "42"; let s: u32 = s.parse().unwrap();  // shadowing: new variable, can change type
```
`mut` vs shadowing: `mut` changes the value in the same variable, and the type has to stay the same. Shadowing creates a new variable, which can have a different type.

▶ Type this: uncomment `x = 6`, run `cargo check`, and **read the error out loud** using the template in Part 4.

### 3.2 Types: Python has `int` and `float`, Rust makes you choose a size
| Rust | Use for |
|---|---|
| `i32` | the default integer |
| `u32` / `u64` | counts that can't be negative (token counts → `u32`) |
| `usize` | indexes and lengths (`vec.len()` returns this) |
| `f64` | the default float (money in a toy CLI. Real money code uses integer cents) |
| `bool`, `char` | `char` is a 4-byte Unicode scalar, not a byte |

Two things that will surprise you:
- **No implicit conversions.** `let total = tokens_u32 * price_f64;` won't compile. Write `tokens as f64 * price`.
- **Overflow panics in debug builds.** `let x: u8 = 255; x + 1` crashes when you run `cargo run`. In `--release` it wraps around silently.

**Compound types:**
```rust
let pair: (f64, f64) = (3.0, 15.0);   // tuple: fixed size, mixed types
let (input_price, output_price) = pair;  // destructure, like Python unpacking
let first = pair.0;
let arr = [1, 2, 3];                  // array: fixed length, lives on the stack
let v = vec![1, 2, 3];                // Vec: growable, like a Python list (Rustlings `vecs`)
```

### 3.3 Functions: the semicolon matters
```rust
fn cost(tokens: u32, price_per_million: f64) -> f64 {
    tokens as f64 / 1_000_000.0 * price_per_million   // no `;` → this value is returned
}
```
- Every parameter must have a type, and so must the return value (`-> f64`). Unlike Python, the hints are required.
- **Expressions vs statements:** a block's value is its last expression *without a semicolon*. Put `;` on that line and it becomes a statement, the function returns `()` (unit, Rust's `None`), and you get a type mismatch error. You'll hit this. Everyone does.
- `return x;` exists, but use it only to leave a function early.

### 3.4 Control flow: almost everything is an expression
```rust
let label = if tokens > 100_000 { "big" } else { "small" };  // if returns a value (no ternary)

let mut n = 0;
let doubled = loop { n += 1; if n == 10 { break n * 2; } };  // loop can return a value via break

for i in 0..3 { println!("{i}"); }          // 0,1,2   (range; 0..=3 includes 3)
for x in [10, 20, 30] { println!("{x}"); }  // like Python's for-in
while n > 0 { n -= 1; }
```
`if` conditions must be `bool`. Rust won't treat `if 0` or `if ""` as false the way Python does.

✓ **Checkpoint:** What does this return, and why?
```rust
fn f() -> i32 { let x = 3; x + 1; }
```
<details><summary>answer</summary>It doesn't compile. Because of the `;`, `x + 1;` is a statement, so the block evaluates to `()`, which doesn't match `i32` (E0308). rustc's <code>help:</code> line says "remove this semicolon".</details>

📖 Depth: [ch03 Common Concepts](https://doc.rust-lang.org/book/ch03-00-common-programming-concepts.html)

---

## Part 4: Reading a compiler error out loud (this is part of "done when")

rustc errors have the same layout every time. Read them in this order:

```
error[E0384]: cannot assign twice to immutable variable `x`     ← 1. code + one-line summary
 --> src/main.rs:3:5                                            ← 2. file:line:col
  |
2 |     let x = 5;
  |         - first assignment to `x`                           ← 3. the labels (the story)
3 |     x = 6;
  |     ^^^^^ cannot assign twice to immutable variable
  |
help: consider making this binding mutable                      ← 4. the suggested fix
  |
2 |     let mut x = 5;
```

**Say it like this:** "E0384, on line 3. I'm assigning to `x` a second time, but `x` was declared on line 2 without `mut`. It suggests `let mut x`."

Then run `rustc --explain E0384` for the long explanation with examples. Do this once for every new error code you meet this weekend.

---

## Part 5: Rustlings (practice reps)

```sh
cargo install rustlings   # once
cd ~/selfstudy/rust/practice && rustlings init && cd rustlings && rustlings
```
Do these in order: `intro` → `variables` → `functions` → `if` → `primitive_types` → `vecs`. **Stop before `move_semantics`.**

How they map to this guide: variables → 3.1 · functions → 3.3 · if → 3.4 · primitive_types → 3.2 · vecs → 3.2 (`Vec`).
Some `vecs` exercises use `.iter().map(...)`. Look at the pattern, but don't study iterators yet. That's stage 3.

---

## Part 6: Build `tokencost`

```sh
cd ~/selfstudy/rust/practice && cargo new tokencost && cd tokencost
cargo run -- claude-sonnet 1200 350     # `--` passes the args through to your program
# → claude-sonnet: 1200 in + 350 out = $0.008850
```

Below are the steps, the signatures, and what each step uses. You write the code.

1. **Read the args.** `let args: Vec<String> = std::env::args().collect();` `args[0]` is the program's path, so your inputs start at `args[1]`. If `args.len() != 4`, print a usage line and `std::process::exit(1)`.
2. **The price table.** `fn prices(model: &str) -> (f64, f64)` returns (input, output) dollars per million tokens, using a `match` on `model` with 3–4 models. For an unknown model, print the known names and exit. (`&str` here just means "borrowed text". Stage 1 explains it.)
   Example prices: `claude-sonnet` 3 / 15, `claude-haiku` 1 / 5, `claude-opus` 5 / 25.
3. **Parse the token counts.** `args[2].parse::<u32>()`. First write it with `.expect("...")`. Then upgrade to a `match` like the one in the guessing game, so `tokencost claude-sonnet abc 5` prints a friendly message instead of panicking.
4. **The math.** `fn cost(input: u32, output: u32, prices: (f64, f64)) -> f64`. Watch the `as f64` conversions, and watch the trailing-semicolon trap from 3.3.
5. **Print** with `{:.6}` formatting: `println!("{model}: ${:.6}", c)`.
6. **One test** at the bottom of `main.rs`:
   ```rust
   #[cfg(test)]
   mod tests {
       use super::*;
       #[test]
       fn sonnet_cost() {
           let c = cost(1_000_000, 0, prices("claude-sonnet"));
           assert!((c - 3.0).abs() < 1e-9);   // never use == on floats
       }
   }
   ```
7. `cargo test` ✅ · `cargo clippy` with no warnings ✅ · break something on purpose and read the error out loud ✅

**Stretch (optional):** add a 5th model. Accept `--batch` to halve the price. Print a cost per 1k calls.

---

## Done when
- [ ] `tokencost` runs and rejects bad input with a helpful message
- [ ] `cargo test` and `cargo clippy` are clean
- [ ] You've read at least 3 different error codes out loud and run `rustc --explain` on each
- [ ] You can answer: what's the difference between `mut` and shadowing? Why does a trailing `;` change what a function returns? What does `match` do when you've missed a case?

**Next:** `/rs-drill pretest ownership`, then `/rs-build` for stage 1 (config types, `find_key`). Its journey file will be `01-ownership.md`.
