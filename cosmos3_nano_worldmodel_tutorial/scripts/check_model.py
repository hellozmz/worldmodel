#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "model"
required = [
    "model_index.json",
    "text_tokenizer/tokenizer.json",
    "sound_tokenizer/diffusion_pytorch_model.safetensors",
    "transformer/diffusion_pytorch_model-00001-of-00007.safetensors",
    "transformer/diffusion_pytorch_model-00002-of-00007.safetensors",
    "transformer/diffusion_pytorch_model-00003-of-00007.safetensors",
    "transformer/diffusion_pytorch_model-00004-of-00007.safetensors",
    "transformer/diffusion_pytorch_model-00005-of-00007.safetensors",
    "transformer/diffusion_pytorch_model-00006-of-00007.safetensors",
    "transformer/diffusion_pytorch_model-00007-of-00007.safetensors",
    "vae/diffusion_pytorch_model.safetensors",
    "vision_encoder/model.safetensors",
]

def pointer(path):
    text = subprocess.check_output(
        ["git", "-C", str(MODEL), "cat-file", "-p", f"HEAD:{path}"], text=True
    )
    oid = next(x.split(":", 1)[1] for x in text.splitlines() if x.startswith("oid "))
    size = int(next(x.split(" ", 1)[1] for x in text.splitlines() if x.startswith("size ")))
    return oid, size

ok = True
print("Cosmos3-Nano model integrity/size check")
commit = subprocess.check_output(["git", "-C", str(MODEL), "rev-parse", "HEAD"], text=True).strip()
print("commit:", commit)
for rel in required:
    p = MODEL / rel
    if not p.exists():
        print(f"MISSING {rel}")
        ok = False
        continue
    actual = p.stat().st_size
    control = Path(str(p) + ".aria2")
    if control.exists():
        print(f"INCOMPLETE {rel}: aria2 control file remains: {control}")
        ok = False
    elif rel.endswith(".safetensors") and actual < 1024:
        expected_oid, expected_size = pointer(rel)
        print(f"POINTER {rel}: {actual} bytes, expected {expected_size}")
        ok = False
    else:
        print(f"OK      {rel}: {actual:,} bytes")
print("RESULT:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
