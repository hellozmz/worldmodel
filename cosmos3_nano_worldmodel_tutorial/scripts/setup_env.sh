#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ ! -x .venv/bin/python ]]; then
  uv venv --python /usr/bin/python .venv
fi
source .venv/bin/activate
# vLLM 0.22 wheel links libcudart.so.13 while Torch uses the cu128 wheel.
export LD_LIBRARY_PATH="$ROOT/.venv/lib/python3.12/site-packages/nvidia/cu13/lib:$ROOT/.venv/lib/python3.12/site-packages/nvidia/cuda_runtime/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export UV_CACHE_DIR="$ROOT/cache/uv"
# Cosmos3 support was released in vLLM-Omni 0.22; CUDA 12.8 matches the H200 container.
uv pip install --torch-backend=cu128 "vllm==0.22.0" "vllm-omni==0.22.0" requests
python - <<'PY'
import torch, vllm
print("torch", torch.__version__, "cuda", torch.version.cuda)
print("vllm", vllm.__version__)
PY
