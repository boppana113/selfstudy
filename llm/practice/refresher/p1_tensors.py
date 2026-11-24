import torch

# x = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
# print(x.shape, x.dtype, x.device)  # torch.Size([2, 3]) torch.float32 cpu

# i = torch.tensor([1, 2, 3])
# print(i.dtype)  # torch.Size([2,3]) torch.float32 cpu

# print((i / 2).dtype, (i // 2).dtype)  # torch.float32 torch.int64

# # 1.1
# print(torch.zeros(2, 3, dtype=torch.bfloat16).element_size())  # 2
# print(torch.tensor(1e5, dtype=torch.float16))  # tensor(inf)       ← overflow
# print(
#     torch.tensor(1e5, dtype=torch.bfloat16)
# )  # tensor(99840.)    ← fits, but imprecise
# print(
#     torch.tensor(1000.0, dtype=torch.float16) + torch.tensor(0.1, dtype=torch.float16)
# )
# # tensor(1000.)     ← the 0.1 vanished

# 1.2
dev = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"dev={dev}")
a = torch.randn(3, 3, device=dev)
b = torch.randn(3, 3)  # cpu
b = b.to(dev)
a @ b
