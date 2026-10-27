#!/usr/bin/env python3
"""Download the official Track 2 GHCR image in resumable parallel ranges.

The image contains one 6.1 GB blob. A single proxy connection is throttled to
roughly 40 KiB/s for GitHub's blob CDN, while independent HTTP ranges achieve
usable throughput. This CPU-only downloader verifies every chunk and final blob
digest, and can resume incomplete chunks without restarting the layer.
"""

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


IMAGE_DIGEST = "sha256:243bb660d00b1dce57e82fc1486af2638404602eda3630af8458e9b6fa0b9c14"
REPOSITORY = "jostarxiong/havln-challenge-2026"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("/tmp/havln-oci-manual-20261027"))
    parser.add_argument("--chunk-size", type=int, default=8 * 1024 * 1024)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-passes", type=int, default=100)
    parser.add_argument("--proxy", default="http://127.0.0.1:19893")
    return parser.parse_args()


def request(url, *, headers=None, timeout=90):
    req = url if isinstance(url, urllib.request.Request) else urllib.request.Request(
        url, headers=headers or {}
    )
    return urllib.request.urlopen(req, timeout=timeout)


def token(data_dir, proxy):
    url = f"https://ghcr.io/token?service=ghcr.io&scope=repository:{REPOSITORY}:pull"
    with request(url, timeout=120) as response:
        payload = json.load(response)
    value = payload.get("token")
    if not isinstance(value, str) or not value:
        raise RuntimeError("GHCR returned an empty token")
    return value


def signed_blob_url(digest, data_dir, proxy):
    last_error = None
    for attempt in range(30):
        try:
            bearer = token(data_dir, proxy)
            url = f"https://ghcr.io/v2/{REPOSITORY}/blobs/{digest}"
            opener = urllib.request.build_opener(NoRedirect)
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {bearer}", "Range": "bytes=0-0"},
            )
            try:
                response = opener.open(req, timeout=120)
            except urllib.error.HTTPError as exc:
                if exc.code not in (301, 302, 307, 308):
                    raise
                location = exc.headers.get("Location")
                exc.close()
            else:
                location = response.geturl()
                response.read(1)
                response.close()
            if not location:
                raise RuntimeError(f"GHCR did not provide a blob redirect for {digest}")
            return location
        except Exception as exc:
            last_error = exc
            if attempt >= 29:
                raise
            time.sleep(min(2.0 * (attempt + 1), 20.0))
    raise RuntimeError(f"could not obtain signed URL for {digest}: {last_error!r}")


def download_chunk(signed_url, destination, *, blob_start, blob_end):
    expected = blob_end - blob_start + 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size == expected:
        return destination, 0.0
    if destination.exists() and destination.stat().st_size > expected:
        destination.unlink()

    started = time.monotonic()
    attempts = 0
    while True:
        attempts += 1
        present = destination.stat().st_size if destination.exists() else 0
        range_start = blob_start + present
        try:
            req = urllib.request.Request(
                signed_url,
                headers={
                    "Range": f"bytes={range_start}-{blob_end}",
                    "Connection": "close",
                },
            )
            with request(req, timeout=180) as response, destination.open("ab") as stream:
                if response.status != 206:
                    raise RuntimeError(f"range request returned HTTP {response.status}")
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    stream.write(block)
            if destination.stat().st_size != expected:
                raise RuntimeError(
                    f"chunk size mismatch: {destination.stat().st_size}/{expected}"
                )
            return destination, time.monotonic() - started
        except Exception:
            if attempts >= 5:
                raise
            time.sleep(min(2.0 * attempts, 10.0))


def digest_path(data_dir, digest):
    algorithm, value = digest.split(":", 1)
    return data_dir / "blobs" / algorithm / value


def sha256(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def download_blob(
    digest,
    size,
    *,
    data_dir,
    chunk_size,
    workers,
    batch_size,
    max_passes,
    proxy,
):
    final = digest_path(data_dir, digest)
    if final.exists() and final.stat().st_size == size:
        print(f"SKIP {digest} ({size} bytes)", flush=True)
        return

    algorithm, value = digest.split(":", 1)
    chunk_root = data_dir / "chunks" / value
    chunk_root.mkdir(parents=True, exist_ok=True)
    jobs = []
    for start in range(0, size, chunk_size):
        index = start // chunk_size
        jobs.append((index, chunk_root / f"{index:06d}.part"))

    for pass_number in range(1, max_passes + 1):
        pending = [
            (index, path)
            for index, path in jobs
            if not path.exists()
            or path.stat().st_size != min(chunk_size, size - index * chunk_size)
        ]
        if not pending:
            break
        print(
            f"PASS {pass_number}/{max_passes} {digest}: {len(pending)} chunks pending",
            flush=True,
        )
        for batch_start in range(0, len(pending), batch_size):
            batch = pending[batch_start:batch_start + batch_size]
            signed_url = signed_blob_url(digest, data_dir, proxy)
            before = sum(path.stat().st_size for _, path in batch if path.exists())
            started = time.monotonic()
            errors = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(
                        download_chunk,
                        signed_url,
                        path,
                        blob_start=index * chunk_size,
                        blob_end=min((index + 1) * chunk_size, size) - 1,
                    ): index
                    for index, path in batch
                }
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as exc:
                        errors.append((futures[future], repr(exc)))
            after = sum(path.stat().st_size for _, path in batch if path.exists())
            elapsed = max(time.monotonic() - started, 0.001)
            print(
                f"  batch {batch_start // batch_size + 1}: {len(batch)} chunks, "
                f"{after - before} bytes, {elapsed:.1f}s, "
                f"{(after - before) / elapsed / 1024:.1f} KiB/s",
                flush=True,
            )
            if errors:
                print(f"  chunk errors: {errors[:4]}", flush=True)
    else:
        raise RuntimeError(f"blob did not complete in {max_passes} passes: {digest}")

    still_pending = []
    for index, path in jobs:
        expected = min(chunk_size, size - index * chunk_size)
        if not path.exists() or path.stat().st_size != expected:
            still_pending.append(path)
    if still_pending:
        raise RuntimeError(f"incomplete chunks remain: {still_pending[:8]}")

    merge_path = data_dir / "attempts" / f"{value}.merging"
    merge_path.parent.mkdir(parents=True, exist_ok=True)
    with merge_path.open("wb") as output:
        for _, path in jobs:
            with path.open("rb") as source:
                shutil.copyfileobj(source, output, 8 * 1024 * 1024)
    if merge_path.stat().st_size != size:
        raise RuntimeError(
            f"merged blob size mismatch: {merge_path.stat().st_size}/{size}"
        )
    actual = sha256(merge_path)
    if algorithm != "sha256" or actual != value:
        raise RuntimeError(f"digest mismatch for {digest}: sha256:{actual}")
    final.parent.mkdir(parents=True, exist_ok=True)
    merge_path.replace(final)
    for _, path in jobs:
        path.unlink(missing_ok=True)
    chunk_root.rmdir()
    print(f"VERIFIED {digest} ({size} bytes)", flush=True)


def main():
    args = parse_args()
    if args.chunk_size < 1024 * 1024:
        raise SystemExit("chunk size must be at least 1 MiB")
    if not 1 <= args.workers <= 64 or not 1 <= args.batch_size <= 128:
        raise SystemExit("workers and batch size must be in [1, 64]/[1, 128]")
    os.environ.update(
        {
            "http_proxy": args.proxy,
            "https_proxy": args.proxy,
            "HTTP_PROXY": args.proxy,
            "HTTPS_PROXY": args.proxy,
        }
    )
    args.data_dir.mkdir(parents=True, exist_ok=True)
    (args.data_dir / "attempts").mkdir(exist_ok=True)
    (args.data_dir / "blobs" / "sha256").mkdir(parents=True, exist_ok=True)

    manifest_path = args.data_dir / "manifest.json"
    if not manifest_path.is_file():
        bearer = token(args.data_dir, args.proxy)
        req = urllib.request.Request(
            f"https://ghcr.io/v2/{REPOSITORY}/manifests/{IMAGE_DIGEST}",
            headers={
                "Authorization": f"Bearer {bearer}",
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            },
        )
        with request(req, timeout=120) as response:
            manifest = json.load(response)
        manifest_path.write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    blobs = [(manifest["config"]["digest"], int(manifest["config"]["size"]))]
    blobs.extend((row["digest"], int(row["size"])) for row in manifest["layers"])
    total = sum(size for _, size in blobs)
    print(
        f"Downloading {len(blobs)} verified blobs; total {total} bytes",
        flush=True,
    )
    for digest, size in blobs:
        download_blob(
            digest,
            size,
            data_dir=args.data_dir,
            chunk_size=args.chunk_size,
            workers=args.workers,
            batch_size=args.batch_size,
            max_passes=args.max_passes,
            proxy=args.proxy,
        )
    print("HAVLN_ALL_LAYERS_OK", flush=True)


if __name__ == "__main__":
    main()
