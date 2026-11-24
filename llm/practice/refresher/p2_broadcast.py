import torch

x = torch.randn(4, 3)  # (batch, features)
bias = torch.randn(3)  # (features,)
print((x + bias).shape)  # (4, 3)  ← bias lines up with the last dim

col = torch.randn(4)  # one value per row
# x + col  # error
x + col[:, None]  # corrected - broadcasting to all columns

# (8,1) and (8,) broadcast to (8,8). A loss computed from this is wrong, and nothing complains. Defense: write the shape in a comment on every line that makes a tensor, and assert x.shape == (...) when unsure.

pred = torch.randn(8, 1)  # model output, (batch, 1)
target = torch.randn(8)  # labels, (batch,)
print((pred - target).shape)  # torch.Size([8, 8])  ← not (8,)!

t = torch.arange(6)
v = t.view(2, 3)
v[0, 0] = 100
print(t)

tt = v.T
# tt.view(
#     6
# )  # RuntimeError: view size is not compatible with input tensor's size and stride ... Use .reshape(...) instead.
tt.reshape(2, 3)
print(tt)
