#!/usr/bin/env python3
"""Download a Hugging Face LFS blob with resumable parallel HTTP ranges."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Hugging Face resolve URL")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chunk-size", type=int, default=16 * 1024 * 1024)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--proxy", default="http://127.0.0.1:19893")
    parser.add_argument("--probe-only", action="store_true")
    return parser.parse_args()


def request(url, headers=None, timeout=120):
    req = url if isinstance(url, urllib.request.Request) else urllib.request.Request(url, headers=headers or {})
    return urllib.request.urlopen(req, timeout=timeout)


def metadata(url):
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    try:
        response = opener.open(req, timeout=120)
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 307, 308):
            raise
        headers = exc.headers
        location = headers.get("Location")
        exc.close()
    else:
        headers = response.headers
        location = response.geturl()
        response.read(1)
        response.close()
    if not location:
        raise RuntimeError("Hugging Face did not provide a redirect")
    size = int(headers["X-Linked-Size"])
    digest = headers["X-Linked-ETag"].strip('"').lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"unsupported LFS digest: {digest}")
    return location, size, digest


def download_chunk(url, destination, start, end):
    expected = end - start + 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size == expected:
        return
    if destination.exists() and destination.stat().st_size > expected:
        destination.unlink()
    for attempt in range(1, 11):
        present = destination.stat().st_size if destination.exists() else 0
        try:
            req = urllib.request.Request(
                url,
                headers={"Range": f"bytes={start + present}-{end}", "Connection": "close"},
            )
            with request(req, timeout=240) as response, destination.open("ab") as stream:
                if response.status != 206:
                    raise RuntimeError(f"range response HTTP {response.status}")
                while block := response.read(1024 * 1024):
                    stream.write(block)
            if destination.stat().st_size != expected:
                raise RuntimeError("chunk size mismatch")
            return
        except Exception:
            if attempt == 10:
                raise
            time.sleep(min(2 * attempt, 20))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    args = parse_args()
    os.environ.update(
        {
            "http_proxy": args.proxy,
            "https_proxy": args.proxy,
            "HTTP_PROXY": args.proxy,
            "HTTPS_PROXY": args.proxy,
        }
    )
    signed_url, size, digest = metadata(args.url)
    print(f"size={size} sha256={digest}", flush=True)
    if args.probe_only:
        destination = Path("/tmp/hf-range-probe.bin")
        download_chunk(signed_url, destination, 0, 1024 * 1024 - 1)
        print(f"PROBE_OK bytes={destination.stat().st_size}")
        destination.unlink()
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() and args.output.stat().st_size == size:
        actual = sha256(args.output)
        if actual != digest:
            raise RuntimeError(f"existing file SHA mismatch: {actual}")
        print("ALREADY_COMPLETE")
        return

    partial = args.output.with_name(args.output.name + ".prefix")
    legacy_partial = args.output.with_name(args.output.name + ".partial")
    if legacy_partial.exists() and not partial.exists():
        legacy_partial.rename(partial)
    if not partial.exists():
        partial.touch()
    present = partial.stat().st_size
    base = min(present, size) // args.chunk_size * args.chunk_size
    if present > base:
        with partial.open("r+b") as stream:
            stream.truncate(base)
    if present < base:
        raise RuntimeError("prefix unexpectedly shrank")

    chunks = []
    index = 0
    for start in range(base, size, args.chunk_size):
        end = min(start + args.chunk_size, size) - 1
        chunks.append((index, partial.parent / f".{args.output.name}.{index:06d}.part", start, end))
        index += 1
    chunk_dir = partial.parent / f".{args.output.name}.chunks"
    chunks = [(item[0], chunk_dir / f"{item[0]:06d}.part", item[2], item[3]) for item in chunks]

    pending = [item for item in chunks if not item[1].exists() or item[1].stat().st_size != item[3] - item[2] + 1]
    for batch_start in range(0, len(pending), args.batch_size):
        batch = pending[batch_start:batch_start + args.batch_size]
        signed_url, _, _ = metadata(args.url)
        started = time.monotonic()
        errors = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(download_chunk, signed_url, path, start, end): index
                for index, path, start, end in batch
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    errors.append((futures[future], repr(exc)))
        elapsed = max(time.monotonic() - started, 0.001)
        downloaded = sum(end - start + 1 for _, _, start, end in batch)
        print(
            f"batch={batch_start // args.batch_size + 1}/{(len(pending) + args.batch_size - 1) // args.batch_size} "
            f"bytes~={downloaded} elapsed={elapsed:.1f}s speed={downloaded / elapsed / 1024:.1f}KiB/s errors={errors[:3]}",
            flush=True,
        )

    incomplete = [
        path for _, path, start, end in chunks
        if not path.exists() or path.stat().st_size != end - start + 1
    ]
    if incomplete:
        raise RuntimeError(f"incomplete chunks: {incomplete[:5]}")
    merging = args.output.with_name(args.output.name + ".merging")
    with merging.open("wb") as output:
        with partial.open("rb") as prefix:
            shutil.copyfileobj(prefix, output, 8 * 1024 * 1024)
        for _, path, _, _ in chunks:
            with path.open("rb") as source:
                shutil.copyfileobj(source, output, 8 * 1024 * 1024)
    if merging.stat().st_size != size:
        raise RuntimeError("merged size mismatch")
    actual = sha256(merging)
    if actual != digest:
        raise RuntimeError(f"SHA mismatch expected={digest} actual={actual}")
    merging.replace(args.output)
    partial.unlink()
    for _, path, _, _ in chunks:
        path.unlink(missing_ok=True)
    chunk_dir.rmdir()
    print("HF_BLOB_OK")


if __name__ == "__main__":
    main()
