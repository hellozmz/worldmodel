#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-18000}"
GPU="${CUDA_VISIBLE_DEVICES:-4}"
MODEL="$ROOT/model"

if [[ ! -f "$MODEL/model_index.json" ]]; then
  echo "ERROR: model index not found: $MODEL/model_index.json" >&2
  exit 1
fi
SHARD="$MODEL/transformer/diffusion_pytorch_model-00001-of-00007.safetensors"
if [[ ! -s "$SHARD" || $(stat -c%s "$SHARD") -lt 1000000000 ]]; then
  echo "ERROR: transformer shard 1 is still an LFS pointer or incomplete." >&2
  exit 1
fi

source "$ROOT/.venv/bin/activate"
export CUDA_VISIBLE_DEVICES="$GPU"
export HF_HOME="${HF_HOME:-$ROOT/cache/huggingface}"
export TOKENIZERS_PARALLELISM=false
export VLLM_LOGGING_LEVEL="${VLLM_LOGGING_LEVEL:-INFO}"
# vLLM 0.22 wheel links libcudart.so.13 while Torch uses the cu128 wheel.
export LD_LIBRARY_PATH="$ROOT/.venv/lib/python3.12/site-packages/nvidia/cu13/lib:$ROOT/.venv/lib/python3.12/site-packages/nvidia/cuda_runtime/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

echo "Starting Cosmos3-Nano vLLM-Omni on GPU $GPU, port $PORT"
exec vllm-omni serve "$MODEL" \
  --omni \
  --host 0.0.0.0 \
  --port "$PORT" \
  --init-timeout 1800 \
  --no-guardrails \
  --model-class-name Cosmos3OmniDiffusersPipeline \
  --served-model-name cosmos3-nano \
  "$@"
