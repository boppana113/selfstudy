# Stage 0 · refresher: Narrated walkthrough (sessions 1–3)

> Open with **Cmd+K V**. Terminal below it.
> Type every `▶ Type this` block yourself, no pasting. Answer each `✓ Checkpoint` out loud before you move on.
> Every output and error shown here was produced by actually running the snippet (torch 2.15, einops 0.8, M1 `mps`).

**Where this goes:** A1 bans `nn.Linear`, `nn.Embedding`, `F.softmax` and friends. You build them from `nn.Parameter` and raw tensor ops. So this refresher is about raw tensors, shapes, and autograd, not about the high-level `nn` layers.

| Session | Part | Done when |
|---|---|---|
| 1 | 1–4: tensors, dtypes, devices, broadcasting, einops, autograd | you can explain every error in Part 4 without looking |
| 2 | 5–7: an MLP from `nn.Parameter`, AdamW, train/eval loop | ≥ 95% test accuracy on two moons, on `mps` |
| 3 | 8–9: Modal wrapper | a T4 prints its name for a few cents |

**Setup (once, 2 min):**
```sh
cd ~/selfstudy/llm/practice
uv init refresher && cd refresher
uv add torch einops scikit-learn
uv run python -c "import torch; print(torch.__version__, torch.backends.mps.is_available())"
```
Put each part in its own file (`p1_tensors.py`, …) and run it with `uv run python p1_tensors.py`. In VS Code, select the `.venv` interpreter so you get hover types.

---

# Session 1

## Part 1: Tensors are NumPy arrays that know their device and can take gradients

▶ Type this (`p1_tensors.py`):
```python
import torch

x = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
print(x.shape, x.dtype, x.device)    # torch.Size([2, 3]) torch.float32 cpu

i = torch.tensor([1, 2, 3])
print(i.dtype)                       # torch.int64
print((i / 2).dtype, (i // 2).dtype) # torch.float32 torch.int64
```

Same as NumPy: indexing, slicing, `@`, `.sum(dim=...)` (NumPy calls it `axis`), `.mean`, `.max`. Two things differ:
- **The default float is `float32`**, not NumPy's `float64`. Mixing in data from NumPy (`float64`) is a common silent dtype leak. Use `torch.tensor(arr, dtype=torch.float32)`.
- **Integers default to `int64`.** Token IDs and class labels are `int64` ("Long"). Loss functions require that.

### 1.1 dtypes: what you'll see in CS336

| dtype | bytes | range / precision | used for |
|---|---|---|---|
| `float32` | 4 | the safe default | master weights, optimizer state |
| `float16` | 2 | max ≈ 65,504 → overflows | old mixed precision |
| `bfloat16` | 2 | fp32's range, ~3 significant digits | modern training + inference |
| `int64` | 8 | — | token IDs, labels |

▶ Type this:
```python
print(torch.zeros(2, 3, dtype=torch.bfloat16).element_size())   # 2
print(torch.tensor(1e5, dtype=torch.float16))   # tensor(inf)       ← overflow
print(torch.tensor(1e5, dtype=torch.bfloat16))  # tensor(99840.)    ← fits, but imprecise
print(torch.tensor(1000., dtype=torch.float16) + torch.tensor(0.1, dtype=torch.float16))
                                                # tensor(1000.)     ← the 0.1 vanished
```
That last line is why weights are kept in fp32 even when the math runs in bf16: tiny updates (lr × grad) added to a big weight disappear in low precision.

**Applied view:** "a 7B model in bf16" = 7e9 × 2 bytes = 14 GB just for the weights. You'll do this arithmetic constantly.

### 1.2 Devices

```python
dev = "mps" if torch.backends.mps.is_available() else "cpu"   # on Modal: "cuda"
a = torch.randn(3, 3, device=dev)
b = torch.randn(3, 3)            # cpu
a @ b
```
▶ Type this and run it. Expected error:
```
RuntimeError: Tensor for argument #2 'mat2' is on CPU, but expected it to be on GPU
```
Every tensor in an op must be on the same device. The fix is `b.to(dev)`. Models move with `model.to(dev)`.

Also run `torch.zeros(2, device="mps", dtype=torch.float64)`:
```
TypeError: Cannot convert a MPS Tensor to float64 dtype as the MPS framework doesn't support float64.
```
Mac-only gotcha. It's one more reason the float32 default matters.

✓ **Checkpoint:** A test passes on `cpu` and fails on `cuda` with "expected all tensors to be on the same device". Where do you look first?
<details><summary>answer</summary>Any tensor you create <em>inside</em> <code>forward</code> (a mask, <code>torch.arange</code> for positions, a RoPE cache) without <code>device=x.device</code>. Parameters move with <code>.to()</code>; tensors you build on the fly don't.</details>

📄 Depth: [PyTorch tensors tutorial](https://pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html)

---

## Part 2: Broadcasting and views

### 2.1 Broadcasting: the same rules as NumPy

Line shapes up **from the right**. Each pair of dims must be equal, or one of them must be 1 (or missing).

▶ Type this (`p2_broadcast.py`):
```python
x = torch.randn(4, 3)        # (batch, features)
bias = torch.randn(3)        # (features,)
print((x + bias).shape)      # (4, 3)  ← bias lines up with the last dim

col = torch.randn(4)         # one value per row
x + col                      # error
```
```
RuntimeError: The size of tensor a (3) must match the size of tensor b (4) at non-singleton dimension 1
```
Fix: `x + col[:, None]` (shape `(4, 1)`, broadcasts across columns). `col.unsqueeze(-1)` does the same.

**The bug that doesn't error.** This is the dangerous one:
```python
pred = torch.randn(8, 1)     # model output, (batch, 1)
target = torch.randn(8)      # labels, (batch,)
print((pred - target).shape) # torch.Size([8, 8])  ← not (8,)!
```
`(8,1)` and `(8,)` broadcast to `(8,8)`. A loss computed from this is wrong, and nothing complains. **Defense:** write the shape in a comment on every line that makes a tensor, and `assert x.shape == (...)` when unsure.

### 2.2 Views vs copies

▶ Type this:
```python
t = torch.arange(6)
v = t.view(2, 3)
v[0, 0] = 100
print(t)                     # tensor([100, 1, 2, 3, 4, 5])  ← same memory

tt = v.T                     # transpose: a view with swapped strides
tt.view(6)                   # error
```
```
RuntimeError: view size is not compatible with input tensor's size and stride ... Use .reshape(...) instead.
```
`view` needs contiguous memory; `.T` isn't. `reshape` copies if it has to. Rule: use `reshape` (or einops) and stop thinking about it. This error shows up in attention after you transpose heads.

✓ **Checkpoint:** `logits` is `(batch, seq, vocab)` and `targets` is `(batch, seq)`. What shapes do you flatten them to for a per-token loss?
<details><summary>answer</summary><code>(batch*seq, vocab)</code> and <code>(batch*seq,)</code>. In einops: <code>rearrange(logits, "b s v -> (b s) v")</code>. You'll write exactly this in A1's training loop.</details>

---

## Part 3: einops, the shape language CS336 uses everywhere

Manual `view`/`transpose`/`permute` chains are where attention bugs hide. einops writes the shape change as a string, and it checks the sizes for you.

▶ Type this (`p3_einops.py`):
```python
import torch
from einops import rearrange, einsum, reduce

x = torch.randn(2, 5, 8)     # (batch, seq, d_model)

# split d_model into 2 heads of size 4, move heads before seq
h = rearrange(x, "b s (h d) -> b h s d", h=2)
print(h.shape)               # (2, 2, 5, 4)

# and back
back = rearrange(h, "b h s d -> b s (h d)")
print(torch.equal(back, x))  # True

# attention scores: every query position against every key position
q = torch.randn(2, 5, 4)     # (batch, seq, d_k)
k = torch.randn(2, 5, 4)
scores = einsum(q, k, "b i d, b j d -> b i j")
print(scores.shape)          # (2, 5, 5)
print(torch.allclose(scores, q @ k.transpose(-1, -2)))  # True

# a linear layer, written as einsum
W = torch.randn(8, 3)        # (d_in, d_out)
print(einsum(x, W, "b s d_in, d_in d_out -> b s d_out").shape)  # (2, 5, 3)

print(reduce(x, "b s d -> b d", "mean").shape)  # (2, 8)  mean over seq
```

How to read `einsum`: any letter that appears in the inputs but **not** in the output gets summed over. In `b i d, b j d -> b i j`, `d` disappears, so it's a dot product over `d`. That's QKᵀ.

▶ Trigger the size check on purpose:
```python
rearrange(x, "b s (h d) -> b h s d", h=3)
```
```
EinopsError: ... Shape mismatch, can't divide axis of length 8 in chunks of 3
```
That's the same reason `d_model` must be divisible by `num_heads`.

**Note:** `einops.einsum` takes the tensors first and the pattern last, and allows multi-letter names (`d_in`). `torch.einsum` takes the pattern first and only single letters. Use the einops one.

✓ **Checkpoint:** Write the einsum pattern for applying attention weights `(b, h, i, j)` to values `(b, h, j, d)`.
<details><summary>answer</summary><code>"b h i j, b h j d -> b h i d"</code>. <code>j</code> (key positions) is summed out: each query's output is a weighted sum of value vectors.</details>

📄 Depth: [einops basics](https://einops.rocks/1-einops-basics/)

---

## Part 4: Autograd

PyTorch records every op on tensors that have `requires_grad=True`, building a graph. `.backward()` walks that graph in reverse and **adds** gradients into `.grad`.

▶ Type this (`p4_autograd.py`):
```python
w = torch.tensor(3.0, requires_grad=True)

loss = (w * 2 - 1) ** 2      # d/dw = 2·(2w−1)·2 = 4·(2w−1) = 20 at w=3
loss.backward()
print(w.grad)                # tensor(20.)

loss = (w * 2 - 1) ** 2
loss.backward()
print(w.grad)                # tensor(40.)  ← accumulated, not replaced
w.grad.zero_()
```
**Gradients accumulate.** That's why every training loop calls `optimizer.zero_grad()`. (It's also a feature: gradient accumulation over micro-batches, which you'll use in A5.)

Now the four errors you will hit. Trigger each one:

```python
# 1. backward twice through the same graph
loss = (w * 2 - 1) ** 2
loss.backward(); loss.backward()
# RuntimeError: Trying to backward through the graph a second time ...
#   → the graph is freed after backward. Recompute the forward pass.

# 2. updating a weight in place outside no_grad
w -= 0.1
# RuntimeError: a leaf Variable that requires grad is being used in an in-place operation.
#   → fix: with torch.no_grad(): w -= lr * w.grad   (this is what an optimizer step does)

# 3. backward on a non-scalar
a = torch.tensor([1., 2.], requires_grad=True)
(a * 2).backward()
# RuntimeError: grad can be implicitly created only for scalar outputs
#   → the loss must be one number. You forgot a .mean() or .sum().

# 4. numpy on a tracked tensor
a.numpy()
# RuntimeError: Can't call numpy() on Tensor that requires grad. Use tensor.detach().numpy() instead.
```

`torch.no_grad()` turns off recording:
```python
with torch.no_grad():
    z = w * 2
print(z.requires_grad)       # False
```
Use it for eval and for the optimizer update. It saves memory too, since nothing is stored for a backward pass.

### 4.1 The softmax overflow (you'll implement softmax in A1)

▶ Type this:
```python
logits = torch.tensor([1000., 1001., 1002.])
e = torch.exp(logits)
print(e / e.sum())           # tensor([nan, nan, nan])   exp(1000) = inf, inf/inf = nan

m = logits - logits.max()    # softmax(x) == softmax(x - c) for any constant c
e = torch.exp(m)
print(e / e.sum())           # tensor([0.0900, 0.2447, 0.6652])
```
Subtracting the max makes the largest exponent `exp(0) = 1`, so nothing overflows. A1's `softmax` and `cross_entropy` tests check exactly this.

✓ **Checkpoint (end of session 1):** Explain out loud, one sentence each: why `(8,1) - (8,)` is dangerous; why `.grad` doubled; why weights stay fp32 when the math runs in bf16.
<details><summary>answer</summary>It silently broadcasts to <code>(8,8)</code>. <code>backward</code> adds into <code>.grad</code>, and nobody zeroed it. Small updates vanish when added to large numbers in low precision (1000 + 0.1 = 1000 in fp16).</details>

📄 Depth: [autograd tutorial](https://pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)

---

# Session 2

## Part 5: An `nn.Module` built from `nn.Parameter`

`nn.Module` is a class that keeps track of its parameters and submodules. `nn.Parameter` is a tensor that (a) has `requires_grad=True` and (b) gets registered when you assign it to `self`. That registration is how `model.parameters()`, `.to(dev)`, and `state_dict()` find it.

▶ Type this: see registration fail on purpose:
```python
import torch, torch.nn as nn

class Bad(nn.Module):
    def __init__(self):
        super().__init__()
        self.w = torch.randn(2, 2)            # plain tensor, not a Parameter

print(len(list(Bad().parameters())))           # 0  ← the optimizer would see nothing
```
No error, and your model never trains. If a loss stays flat, check this.

### Build step (you write it): `p5_mlp.py`

A 2-layer MLP for 2D points → 2 classes. **Use `nn.Parameter` + `@`, not `nn.Linear`** (practice for A1).

- `__init__(self, d_in, d_hidden, n_classes)`: weights `w1 (d_in, d_hidden)`, `b1 (d_hidden,)`, `w2 (d_hidden, n_classes)`, `b2 (n_classes,)`.
- `forward(self, x)`: `(batch, d_in) → relu → (batch, n_classes)` **logits** (raw scores, no softmax).
- Init hint: `torch.randn(d_in, d_out) * (2 / d_in) ** 0.5` for the ReLU layer. Biases start at zero.
- Optional: `nn.Dropout(0.1)` after the ReLU (needed for Part 7's train/eval demo).

**Check:** `MLP(2, 64, 2)` should have **322** parameters (`sum(p.numel() for p in m.parameters())`), and `[n for n, _ in m.named_parameters()]` should list your four names.

✓ **Checkpoint:** Where does 322 come from?
<details><summary>answer</summary>2·64 + 64 + 64·2 + 2 = 128 + 64 + 128 + 2 = 322. Being able to count params from the shapes is exactly A1's resource-accounting question, at a bigger scale.</details>

---

## Part 6: Loss and optimizer

### 6.1 Cross-entropy

`F.cross_entropy(logits, targets)` takes:
- `logits`: `(N, C)` raw scores. **Not** softmaxed; it does log-softmax inside, stably.
- `targets`: `(N,)` of `int64` class indices.

▶ Trigger both target errors:
```python
import torch.nn.functional as F
logits = torch.randn(4, 2)
F.cross_entropy(logits, torch.tensor([0., 1., 1., 0.]))
# RuntimeError: expected target dtype to be Long or Byte, but got Float
F.cross_entropy(logits, torch.tensor([0, 1, 1, 0])[:, None])
# RuntimeError: 0D or 1D target tensor expected, multi-target not supported
```

**Sanity number:** at random init, loss ≈ ln(C), because the model spreads probability evenly. For 2 classes that's 0.69. For GPT-2's vocab (50,257) it's ≈ 10.8. If your first LM loss is far from ln(vocab), something is off before training even starts.

### 6.2 AdamW

```python
opt = torch.optim.AdamW(model.parameters(), lr=1e-2, weight_decay=0.01)
```
After one step, inspect `opt.state[model.w1].keys()` → `['step', 'exp_avg', 'exp_avg_sq']`. That's 2 extra tensors the size of every parameter: the first and second moments. You'll write AdamW yourself in A1 §4.

**Applied view:** fp32 training memory ≈ 4 bytes (weights) + 4 (grads) + 8 (two Adam moments) = **16 bytes/param**, before activations. A 7B model needs ~112 GB just for that. This is stage 3's Numbers question.

---

## Part 7: The train/eval loop

### Build step (you write it): `p7_train.py`

Data:
```python
from sklearn.datasets import make_moons
X, y = make_moons(n_samples=2000, noise=0.2, random_state=0)   # X float64, y int64
```
Convert to tensors (watch the dtype, Part 1), split 1600 train / 400 test, move to `mps`.

The loop, as a hint list. Write it yourself:
1. `model.train()`
2. sample a batch of 64 indices: `torch.randint(0, n_train, (64,), device=dev)`
3. forward → `F.cross_entropy` → **`opt.zero_grad()` → `loss.backward()` → `opt.step()`**
4. every 100 steps: `model.eval()`, then under `torch.no_grad()`: test accuracy = `(logits.argmax(-1) == y_test).float().mean()`
5. 300 steps, lr `1e-2`.

**Target:** ≥ 95% test accuracy. (The reference run got ~97% at step 299.)

Then `torch.save(model.state_dict(), "mlp.pt")` and load it back into a fresh `MLP` with `load_state_dict`. A1 asks you to checkpoint like this, plus the optimizer state.

### 7.1 `train()` vs `eval()`

They don't turn gradients on or off. They switch layers like dropout between training and inference behavior. ▶ Type this after training:
```python
model.eval();  print(torch.equal(model(X_test[:3]), model(X_test[:3])))   # True
model.train(); print(torch.equal(model(X_test[:3]), model(X_test[:3])))   # False (dropout is random)
```
`eval()` ≠ `no_grad()`. For evaluation you want **both**.

### 7.2 Break it on purpose (5 min, worth it)

Run each change and see what the loss does, then undo it:

| Bug | What happened in the reference run |
|---|---|
| `F.softmax` before `cross_entropy` | loss stalls at ~0.34; it **can't go below 0.31** for 2 classes, because the "logits" are now squashed into [0, 1] |
| delete `opt.zero_grad()` (with SGD lr 0.1) | loss ends ~0.47 vs ~0.17, bouncing around: each step uses the sum of every past gradient |
| model on `mps`, data on `cpu` | `RuntimeError: ... 'mat1' is on CPU, but expected it to be on GPU` |

✓ **Checkpoint (end of session 2):** Your loss is flat from step 0. Name three things to check, in order.
<details><summary>answer</summary>(1) Are the weights registered, i.e. is <code>len(list(model.parameters()))</code> &gt; 0? (2) Is <code>zero_grad → backward → step</code> all there, in order? (3) Is the lr sane, and is the initial loss ≈ ln(C)? (Bonus: is there an accidental softmax before the loss?)</details>

📄 Depth: [optimization loop tutorial](https://pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)

---

# Session 3

## Part 8: Modal in 5 minutes

Modal runs a Python function in a container on a cloud GPU. You describe the container in code, and billing is per second, only while the function runs.

Three pieces:
- **`modal.App`**: a named group of functions.
- **`modal.Image`**: the container (`debian_slim()`, then add packages and files).
- **`@app.function(gpu=..., timeout=...)`**: runs remotely. **`@app.local_entrypoint()`** runs on your laptop, and its parameters become CLI flags (`def main(gpu: str, cmd: str)` → `--gpu T4 --cmd "..."`).

▶ Type this (setup):
```sh
# 1. sign up at modal.com (Starter plan, $30/month free credit)
cd ~/selfstudy/llm/practice
uv add --project refresher modal
uv run --project refresher modal setup        # opens the browser to log in
```
In the Modal dashboard, **set a workspace spending limit** (Settings → Usage/Billing). That's your hard stop for the $10 cap, independent of anything in code.

📄 Depth: [Modal "Hello, world"](https://modal.com/docs/examples/hello_world), [GPU guide](https://modal.com/docs/guide/gpu)

## Part 9: Build `llm/practice/modal_run.py`

**Goal:** from any assignment repo,
```sh
modal run ~/selfstudy/llm/practice/modal_run.py --repo ~/cs336/assignment1-basics --gpu T4 --cmd "uv run pytest"
```
ships the repo to a GPU, runs the command, and streams the output back.

### Build step (you write it). Pieces and hints:

1. **Image:** `modal.Image.debian_slim(python_version="3.12").pip_install("uv")`.
2. **Shipping the repo:** the simplest robust way is to send it as an argument. In the local entrypoint, tar the repo into bytes in memory (`tarfile` + `io.BytesIO`, mode `"w:gz"`). **Exclude** `.venv`, `.git`, `data`, `__pycache__`, `*.pt`, or you'll upload gigabytes. Pass the bytes to the remote function, which extracts them into `/root/repo`.
   (Modal also has `Image.add_local_dir`, but the path is fixed when the module is imported, which fights with a `--repo` flag.)
3. **Remote function:** `@app.function(image=..., timeout=20 * 60)`. **Always set a timeout.** Inside: extract, then `subprocess.run(cmd, shell=True, cwd="/root/repo", check=...)`. The output streams to your terminal by itself.
4. **Choosing the GPU at run time:** `run_remote.with_options(gpu=gpu).remote(tar_bytes, cmd)`.
5. **Don't reinstall torch every run:** `uv sync` downloads ~2 GB of CUDA wheels, which costs GPU time. Mount a Volume as the uv cache:
   `volumes={"/root/.cache/uv": modal.Volume.from_name("uv-cache", create_if_missing=True)}`. The first run is slow; later ones reuse it.

### First run (≈ 2–4 min on a T4 at $0.59/hr ≈ $0.03)

Estimate first, then log it (habit for every later run). Use the refresher project itself as the repo:
```sh
modal run modal_run.py --repo ./refresher --gpu T4 \
  --cmd "uv run python -c 'import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name())'"
```
**Done when** it prints `True Tesla T4`. Then add a row to `llm/progress.md` → Modal spend, and check the dashboard's real number against your estimate.

**Expected snags:**
- The tarball is huge or slow to upload → your exclude list missed `.venv`.
- `uv: command not found` in the container → the image didn't `pip_install("uv")`.
- `torch.cuda.is_available()` is `False` → you forgot `with_options(gpu=...)`, so it ran on CPU.
- The run hangs → the timeout saves you. That's why it's there.

✓ **Checkpoint (end of session 3):** Why debug on the laptop and only run on Modal after the tests pass?
<details><summary>answer</summary>Modal bills per second of GPU time, including the time a broken run spends crashing, retrying, and reinstalling. Shape bugs and NaNs show up at toy size on <code>mps</code> for free. The GPU is for runs that are already correct and need speed.</details>

> ⚠ The Modal API calls above (`debian_slim`, `pip_install`, `Volume.from_name`, `with_options(gpu=)`) were checked against modal 1.6.4's signatures, but I haven't run them end to end (no account here). If the API moved, the Modal docs win.

---

## Stage 0 done when
- [ ] The MLP gets ≥ 95% on two moons on `mps` (Session 2)
- [ ] `modal_run.py` prints a GPU name (Session 3), and the spend is logged
- [ ] 60-second mental model: *tensors carry dtype + device; autograd records ops and accumulates grads into `.grad`; a training step is zero_grad → forward → loss → backward → step; train/eval switches layer behavior, no_grad switches recording.*
- [ ] Numbers: bytes/param for fp32 + AdamW training (16), and bf16 weights for a 7B model (14 GB)

Next: stage 1, `a1-tokenizer`, and lecture 1.
