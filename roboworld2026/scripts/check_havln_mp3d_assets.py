#!/usr/bin/env python3
"""Check authorized Matterport3D scene coverage for RoboWorld Track 2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    expected = list(manifest["expected_glb_relative_paths"])

    missing = []
    present = []
    zero_size = []
    for relative in expected:
        path = args.data_root / relative
        if not path.is_file():
            missing.append(relative)
        else:
            present.append(relative)
            if path.stat().st_size == 0:
                zero_size.append(relative)

    result = {
        "format_version": 1,
        "data_root": str(args.data_root.resolve()),
        "expected_count": len(expected),
        "present_count": len(present),
        "missing_count": len(missing),
        "zero_size_count": len(zero_size),
        "missing": missing,
        "zero_size": zero_size,
        "coverage": len(present) / len(expected) if expected else 0.0,
    }
    print(json.dumps(result, indent=2))
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if missing or zero_size:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
