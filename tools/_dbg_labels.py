import pathlib
import sys
import collections
import torch

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from align_lyrics import BUNDLE, SR, read_wav

wav = read_wav(pathlib.Path("timing/wav/rise_vocals.wav"))
model = BUNDLE.get_model(with_star=True).eval()
chunk = wav[int(134 * SR) : int(136 * SR)].unsqueeze(0)
with torch.inference_mode():
    out = model(chunk)
print("type", type(out), "len", len(out) if isinstance(out, tuple) else "-")
for k, o in enumerate(out if isinstance(out, tuple) else [out]):
    print(k, getattr(o, "shape", o))
em = out[0][0]
# Safely print a few rows without assuming the tensor is that large
print("row0", [round(float(x), 2) for x in em[0]])
if em.shape[0] > 100:
    print("row100", [round(float(x), 2) for x in em[100]])
else:
    print("row100", "<tensor too small for index 100>")
print("softmax sum", float(em.softmax(-1).sum(-1).mean()))
top = em.argmax(-1)

print("top counts", collections.Counter(top.tolist()).most_common(6))
print("exp sum", float(em.exp().sum(-1).mean()), "max", float(em.exp().max(-1).values.mean()))
