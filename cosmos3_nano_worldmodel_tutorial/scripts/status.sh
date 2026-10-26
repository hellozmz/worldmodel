#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-18000}"
printf '%s\n' '== process =='
pgrep -af "vllm serve.*cosmos3_nano_worldmodel/model" || true
printf '%s\n' '== API =='
curl --noproxy "*" -sS --max-time 5 "http://127.0.0.1:${PORT}/v1/models" | python -m json.tool || true
printf '%s\n' '== GPU =='
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv
