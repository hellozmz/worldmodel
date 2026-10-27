#!/usr/bin/env bash
# Pull the official Track 2 image through a proxy with resumable OCI layers.
# This CPU-only helper avoids repeating a multi-gigabyte skopeo transfer when
# the proxy resets one HTTP stream. Verified blobs are kept in an OCI layout.

set -euo pipefail

IMAGE_DIGEST="${IMAGE_DIGEST:-sha256:243bb660d00b1dce57e82fc1486af2638404602eda3630af8458e9b6fa0b9c14}"
REPO="${REPO:-jostarxiong/havln-challenge-2026}"
DATA_DIR="${DATA_DIR:-/tmp/havln-oci-manual-20261027}"
PROXY="${PROXY:-http://127.0.0.1:19893}"
export http_proxy="$PROXY" https_proxy="$PROXY" HTTP_PROXY="$PROXY" HTTPS_PROXY="$PROXY"

mkdir -p "$DATA_DIR/blobs/sha256" "$DATA_DIR/attempts"
refresh_token() {
  curl -fsSL --http1.1 --retry 20 --retry-all-errors \
  "https://ghcr.io/token?service=ghcr.io&scope=repository:$REPO:pull" \
  | jq -r .token > "$DATA_DIR/token"
  test -s "$DATA_DIR/token"
}

refresh_token
curl -fsSL --http1.1 --retry 20 --retry-all-errors \
  -H "Authorization: Bearer $(cat "$DATA_DIR/token")" \
  -H "Accept: application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.v2+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.index.v1+json" \
  "https://ghcr.io/v2/$REPO/manifests/$IMAGE_DIGEST" -o "$DATA_DIR/manifest.json"

items=$(jq -r '"\(.config.digest) \(.config.size)", (.layers[] | "\(.digest) \(.size)")' \
  "$DATA_DIR/manifest.json")
total=$(printf '%s\n' "$items" | wc -l)
n=0
while read -r digest size; do
  n=$((n + 1))
  algo=${digest%%:*}
  hash=${digest##*:}
  final="$DATA_DIR/blobs/$algo/$hash"
  part="$DATA_DIR/attempts/$hash.part"

  if [[ -f $final ]] && [[ $(stat -c %s "$final") == "$size" ]]; then
    echo "[$n/$total] already complete $digest"
    continue
  fi

  echo "[$n/$total] downloading $digest ($size bytes), current=$(stat -c %s "$part" 2>/dev/null || echo 0)"
  for attempt in $(seq 1 100); do
    current=$(stat -c %s "$part" 2>/dev/null || echo 0)
    if [[ $current -eq "$size" ]]; then
      break
    fi
    if [[ $current -gt "$size" ]]; then
      echo "FATAL: partial blob exceeds expected size: $part" >&2
      exit 1
    fi

    # A failed stream leaves the partial file in place; curl -C - resumes it.
    refresh_token
    curl -fsSL --http1.1 --continue-at - --retry 20 --retry-delay 2 \
      --retry-all-errors --connect-timeout 30 --speed-time 120 --speed-limit 1024 \
      -H "Authorization: Bearer $(cat "$DATA_DIR/token")" \
      "https://ghcr.io/v2/$REPO/blobs/$digest" -o "$part" || true
    current=$(stat -c %s "$part" 2>/dev/null || echo 0)
    echo "attempt=$attempt current=$current expected=$size"
    [[ $current -eq "$size" ]] && break
    sleep 3
  done

  current=$(stat -c %s "$part" 2>/dev/null || echo 0)
  if [[ $current != "$size" ]]; then
    echo "FATAL: incomplete after retries: $digest ($current/$size)" >&2
    exit 1
  fi
  actual=$("${algo}sum" "$part" | awk '{print $1}')
  if [[ $actual != "$hash" ]]; then
    echo "FATAL: checksum mismatch: expected $digest, got $algo:$actual" >&2
    exit 1
  fi
  mv "$part" "$final"
  echo "[$n/$total] verified $digest"
done <<< "$items"

echo HAVLN_ALL_LAYERS_OK
