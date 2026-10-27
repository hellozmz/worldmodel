#!/usr/bin/env bash
# CPU-only download of the strongest public SimpleVLN checkpoints.
# These are not loaded or served here; this only prepares assets for later,
# explicitly GPU-authorized evaluation.

set -euo pipefail

export http_proxy="${http_proxy:-http://127.0.0.1:19893}"
export https_proxy="${https_proxy:-http://127.0.0.1:19893}"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
export HF_HUB_DISABLE_TELEMETRY=1

ROOT="${ROOT:-/mnt/models_2296/zmz/workspace/roboworld2026/data/hf_models}"
mkdir -p "$ROOT"

download_one() {
  local repo=$1
  local revision=$2
  local name=${repo##*/}
  echo "[$(date -Is)] START $repo@$revision"
  for attempt in $(seq 1 100); do
    if huggingface-cli download "$repo" \
      --revision "$revision" \
      --local-dir "$ROOT/$name" \
      --local-dir-use-symlinks False \
      --max-workers 1; then
      echo "[$(date -Is)] OK $repo"
      return 0
    fi
    echo "[$(date -Is)] RETRY $repo attempt=$attempt"
    sleep 5
  done
  echo "FATAL: $repo did not finish after 100 attempts" >&2
  return 1
}

download_one honglyhly/SimpleVLN_Qwen35_4B_RL eb761c4e18a6a14859b0fb3f018aad78f37542df
download_one honglyhly/SimpleVLN_Qwen35_9B_RL 6eb5243341a6d25a192c231d9b8cd4438ae6b9f4
echo SIMPLEVLN_MODELS_DOWNLOAD_OK
