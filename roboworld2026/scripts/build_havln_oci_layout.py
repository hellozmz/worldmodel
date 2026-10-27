#!/usr/bin/env python3
"""Convert verified GHCR blobs into a local OCI layout for offline skopeo."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--ref-name", default="track2")
    return parser.parse_args()


def canonical_bytes(value) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"


def blob_path(root: Path, digest: str) -> Path:
    algorithm, value = digest.split(":", 1)
    return root / "blobs" / algorithm / value


def verify_blob(root: Path, digest: str, size: int) -> None:
    path = blob_path(root, digest)
    if not path.is_file():
        raise FileNotFoundError(f"missing verified blob {digest}: {path}")
    actual_size = path.stat().st_size
    if actual_size != size:
        raise RuntimeError(f"size mismatch for {digest}: {actual_size}/{size}")


def main() -> None:
    args = parse_args()
    root = args.data_dir
    docker_manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    verify_blob(root, docker_manifest["config"]["digest"], docker_manifest["config"]["size"])
    for layer in docker_manifest["layers"]:
        verify_blob(root, layer["digest"], layer["size"])

    # The registry manifest is Docker v2s2. OCI consumers accept the same graph
    # structure after changing only descriptor media types, without modifying or
    # decompressing any content-addressed blob.
    oci_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            **docker_manifest["config"],
            "mediaType": "application/vnd.oci.image.config.v1+json",
        },
        "layers": [
            {
                **layer,
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            }
            for layer in docker_manifest["layers"]
        ],
    }
    manifest_bytes = canonical_bytes(oci_manifest)
    manifest_digest = "sha256:" + hashlib.sha256(manifest_bytes).hexdigest()
    manifest_path = blob_path(root, manifest_digest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(manifest_bytes)

    index = {
        "schemaVersion": 2,
        "manifests": [
            {
                "mediaType": oci_manifest["mediaType"],
                "digest": manifest_digest,
                "size": len(manifest_bytes),
                "annotations": {
                    "org.opencontainers.image.ref.name": args.ref_name,
                },
            }
        ],
    }
    (root / "index.json").write_bytes(canonical_bytes(index))
    (root / "oci-layout").write_text(
        json.dumps({"imageLayoutVersion": "1.0.0"}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"OCI_READY ref={args.ref_name} manifest={manifest_digest}")
    print(f"skopeo inspect oci:{root}:{args.ref_name}")
    print(
        "skopeo copy oci:%s:%s docker-archive:/tmp/havln-challenge.tar:"
        "ghcr.io/jostarxiong/havln-challenge-2026:track2" % (root, args.ref_name)
    )


if __name__ == "__main__":
    main()
