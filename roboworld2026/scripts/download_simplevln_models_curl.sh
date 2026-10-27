#!/usr/bin/env bash
# Download SimpleVLN weights through a stall-resistant, resumable curl stream.
# No model is loaded and no GPU is used.

set -euo pipefail

export http_proxy="${http_proxy:-http://127.0.0.1:19893}"
export https_proxy="${https_proxy:-http://127.0.0.1:19893}"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
export HF_HUB_DISABLE_TELEMETRY=1

ROOT="${ROOT:-/mnt/models_2296/zmz/workspace/roboworld2026/data/hf_models}"
mkdir -p "$ROOT"

download_model() {
  local repo=$1 revision=$2
  local name=${repo##*/}
  local dir="$ROOT/$name"
  local url="https://huggingface.co/$repo/resolve/$revision/model.safetensors"
  mkdir -p "$dir"

  echo "[$(date -u +%FT%TZ)] small files: $repo"
  local file
  for file in .gitattributes chat_template.jinja config.json generation_config.json processor_config.json tokenizer.json tokenizer_config.json; do
    if [[ -s "$dir/$file" ]]; then continue; fi
    local temporary="$dir/$file.partial"
    for attempt in $(seq 1 20); do
      if curl -fsSL --http1.1 --retry 10 --retry-delay 2 --retry-all-errors \
        --connect-timeout 30 --speed-time 60 --speed-limit 128 \
        "https://huggingface.co/$repo/resolve/$revision/$file" -o "$temporary"; then
        mv "$temporary" "$dir/$file"
        break
      fi
      [[ $attempt -eq 20 ]] && return 1
      sleep 2
    done
  done

  local headers=/tmp/${name}.headers
  for attempt in $(seq 1 30); do
    if curl -fsSIL --http1.1 --max-time 180 "$url" >"$headers"; then break; fi
    echo "metadata retry=$attempt"
    sleep 3
  done
  tr -d '\r' <"$headers" >"$headers.clean"
  local size etag
  size=$(awk '{key=tolower($1)} key=="x-linked-size:"{v=$2} END{print v}' "$headers.clean")
  etag=$(awk '{key=tolower($1)} key=="x-linked-etag:"{gsub(/"/,"",$2); v=$2} END{print v}' "$headers.clean")
  if [[ ! "$size" =~ ^[0-9]+$ ]] || [[ ! "$etag" =~ ^[0-9a-f]{64}$ ]]; then
    echo "FATAL: could not read size/SHA from Hugging Face headers" >&2
    return 1
  fi
  echo "model size=$size sha256=$etag"

  local partial="$dir/model.safetensors.partial"
  local inherited
  inherited=$(find "$dir/.cache/huggingface/download" -type f -name "*.$etag.incomplete" -print -quit 2>/dev/null || true)
  if [[ -n "$inherited" && ! -e "$partial" ]]; then
    mv "$inherited" "$partial"
  fi
  touch "$partial"

  for attempt in $(seq 1 200); do
    local current
    current=$(stat -c %s "$partial")
    if [[ "$current" -eq "$size" ]]; then break; fi
    if [[ "$current" -gt "$size" ]]; then
      echo "FATAL: partial file exceeds model size" >&2
      return 1
    fi
    echo "[$(date -u +%FT%TZ)] $repo attempt=$attempt current=$current/$size"
    local continue_args=(-C -)
    if [[ "$current" -eq 0 ]]; then continue_args=(); fi
    curl -fL --http1.1 "${continue_args[@]}" \
      --retry 20 --retry-delay 2 --retry-all-errors \
      --connect-timeout 30 --speed-time 60 --speed-limit 1024 \
      "$url" -o "$partial" || true
  done

  if [[ "$(stat -c %s "$partial")" != "$size" ]]; then
    echo "FATAL: incomplete model after retries" >&2
    return 1
  fi
  local actual
  actual=$(sha256sum "$partial" | awk '{print $1}')
  if [[ "$actual" != "$etag" ]]; then
    echo "FATAL: SHA mismatch expected=$etag actual=$actual" >&2
    return 1
  fi
  mv "$partial" "$dir/model.safetensors"
  echo "[$(date -u +%FT%TZ)] OK $repo"
}

download_model honglyhly/SimpleVLN_Qwen35_4B_RL eb761c4e18a6a14859b0fb3f018aad78f37542df
download_model honglyhly/SimpleVLN_Qwen35_9B_RL 6eb5243341a6d25a192c231d9b8cd4438ae6b9f4
echo SIMPLEVLN_CURL_DOWNLOAD_OK
