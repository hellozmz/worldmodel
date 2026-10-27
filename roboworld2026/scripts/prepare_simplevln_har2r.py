#!/usr/bin/env python3
"""Prepare a CPU-verifiable SimpleVLN data root for HA-R2R val_unseen.

SimpleVLN's bundled R2R-CE annotations and HA-R2R val_unseen have identical
navigation identities. This script links the human-aware instructions into
SimpleVLN's expected annotation layout and, when an authorized Matterport3D root
is supplied, links all Habitat scene files requested by SimpleVLN's manifest.
It does not run Habitat, download scenes, or use a GPU.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simplevln-root", type=Path, required=True)
    parser.add_argument("--har2r-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--mp3d-root", type=Path)
    parser.add_argument("--link-mode", choices=("symlink", "copy"), default="symlink")
    parser.add_argument("--fail-on-missing-scenes", action="store_true")
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_gz(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def install(source: Path, target: Path, mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        if target.is_symlink() and not target.exists():
            raise RuntimeError(f"broken existing symlink: {target}")
        if target.resolve() != source.resolve():
            raise RuntimeError(f"target already exists with another source: {target}")
        return
    if mode == "symlink":
        os.symlink(source.resolve(), target)
    else:
        shutil.copy2(source, target)


def source_candidates(mp3d_root: Path, scan: str, filename: str) -> list[Path]:
    relative = Path("mp3d") / scan / filename
    return [
        mp3d_root / relative,
        mp3d_root / "scene_datasets" / relative,
        mp3d_root / "scene_datasets" / "v1" / "tasks" / relative,
    ]


def check_navigation_compatibility(simplevln_root: Path, har2r_root: Path) -> dict[str, Any]:
    simple_path = simplevln_root / "eval_data/r2r/val_unseen/val_unseen.json.gz"
    ha_path = har2r_root / "val_unseen/val_unseen.json.gz"
    simple_payload = load_json_gz(simple_path)
    ha_payload = load_json_gz(ha_path)
    simple_episodes = simple_payload["episodes"]
    ha_episodes = ha_payload["episodes"]
    simple_by_id = {str(row["episode_id"]): row for row in simple_episodes}
    ha_by_id = {str(row["episode_id"]): row for row in ha_episodes}
    common = set(simple_by_id) & set(ha_by_id)
    fields = ("trajectory_id", "scene_id", "start_position", "start_rotation", "goals", "reference_path")
    mismatches = []
    for episode_id in common:
        left, right = simple_by_id[episode_id], ha_by_id[episode_id]
        if any(left.get(field) != right.get(field) for field in fields):
            mismatches.append(episode_id)
    compatible = (
        len(common) == len(simple_episodes) == len(ha_episodes) == 1839
        and not mismatches
    )
    if not compatible:
        raise ValueError(
            f"SimpleVLN/HA-R2R navigation mismatch: common={len(common)}, "
            f"field_mismatches={len(mismatches)}"
        )
    return {
        "episodes": len(common),
        "navigation_exact_match_count": len(common) - len(mismatches),
    }


def main() -> None:
    args = parse_args()
    if args.link_mode == "copy" and not args.mp3d_root:
        # Copying annotations is safe; this guard only clarifies that scene copy
        # also requires an explicitly supplied authorized source.
        pass

    vln_data = args.simplevln_root / "eval/data/vln_data"
    manifest_path = vln_data / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compatibility = check_navigation_compatibility(vln_data, args.har2r_root)
    ha_annotation = args.har2r_root / "val_unseen/val_unseen.json.gz"
    annotation_target = args.output_root / "eval_data/r2r/val_unseen/val_unseen.json.gz"
    install(ha_annotation, annotation_target, args.link_mode)

    present: list[str] = []
    missing: list[dict[str, str]] = []
    installed_count = 0
    for item in manifest["scene_files"]:
        relative = item["path"]
        parts = Path(relative).parts
        # .../scene_datasets/v1/tasks/mp3d/<scan>/<filename>
        scan, filename = parts[-2], parts[-1]
        target = args.output_root / relative
        source = None
        if args.mp3d_root:
            source = next((path for path in source_candidates(args.mp3d_root, scan, filename) if path.is_file()), None)
        if source is None:
            if target.exists() or target.is_symlink():
                present.append(relative)
            else:
                missing.append({"path": relative, "scan": scan})
            continue
        install(source, target, args.link_mode)
        installed_count += 1
        present.append(relative)

    instructions = f"""# Prepared HA-R2R val_unseen for SimpleVLN\n\nSet `VLN_DATA_ROOT` to this directory when invoking SimpleVLN:\n\n```bash\nVLN_DATA_ROOT={args.output_root} \\\npython {args.simplevln_root / 'eval/vln/eval.py'} \\\n  --exp-config {args.simplevln_root / 'eval/config/vln_r2r.yaml'} \\\n  --vllm_base-url http://localhost:8001/v1 \\\n  --split-num 1 --pass-k 1 --result-path <result-dir>\n```\n\nGPU/vLLM execution is intentionally not started by this preparation script.\nScene assets remain blocked until an authorized Matterport3D root is supplied.\n"""
    (args.output_root / "README.md").write_text(instructions, encoding="utf-8")

    result = {
        "format_version": 1,
        "output_root": str(args.output_root.resolve()),
        "annotation": str(annotation_target),
        "annotation_sha256": sha256(annotation_target),
        "navigation_compatibility": compatibility,
        "scene_manifest_count": len(manifest["scene_files"]),
        "scene_present_count": len(present),
        "scene_missing_count": len(missing),
        "scene_installed_now": installed_count,
        "missing_scene_files": missing,
        "all_scene_files_ready": not missing,
        "gpu_execution_started": False,
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    if args.fail_on_missing_scenes and missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
