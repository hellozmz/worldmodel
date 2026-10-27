#!/usr/bin/env python3
"""Check whether SimpleVLN's R2R-CE episodes match HA-R2R navigation episodes.

SimpleVLN supplies a strong static-navigation policy. HA-R2R reuses the same
routes but augments instructions with human-aware context and adds dynamic
people in the official Track 2 simulator. This CPU-only check verifies that the
navigation identities are compatible before any GPU evaluation is requested.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import statistics
from pathlib import Path
from typing import Any


NAVIGATION_FIELDS = (
    "trajectory_id",
    "scene_id",
    "start_position",
    "start_rotation",
    "goals",
    "reference_path",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simplevln-root", type=Path, required=True)
    parser.add_argument("--har2r-root", type=Path, required=True)
    parser.add_argument("--split", default="val_unseen", choices=("val_unseen",))
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def load_episodes(root: Path, split: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = root / "eval_data" / "r2r" / split / f"{split}.json.gz"
    if not path.is_file():
        path = root / split / f"{split}.json.gz"
    if not path.is_file():
        raise FileNotFoundError(f"cannot find {split} annotations under {root}")
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    episodes = payload.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        raise ValueError(f"no episodes in {path}")
    return episodes, payload


def route_error(left: list[list[float]], right: list[list[float]]) -> float:
    if len(left) != len(right):
        return math.inf
    return max(
        math.sqrt(
            sum((float(a) - float(b)) ** 2 for a, b in zip(point_a, point_b))
        )
        for point_a, point_b in zip(left, right)
    )


def main() -> None:
    args = parse_args()
    simple_episodes, simple_payload = load_episodes(args.simplevln_root, args.split)
    ha_episodes, ha_payload = load_episodes(args.har2r_root, args.split)

    simple_by_id = {str(row["episode_id"]): row for row in simple_episodes}
    ha_by_id = {str(row["episode_id"]): row for row in ha_episodes}
    if len(simple_by_id) != len(simple_episodes):
        raise ValueError("duplicate SimpleVLN episode IDs")
    if len(ha_by_id) != len(ha_episodes):
        raise ValueError("duplicate HA-R2R episode IDs")

    common = sorted(set(simple_by_id) & set(ha_by_id), key=int)
    missing_in_ha = sorted(set(simple_by_id) - set(ha_by_id), key=int)
    extra_in_ha = sorted(set(ha_by_id) - set(simple_by_id), key=int)
    mismatched_fields: dict[str, list[str]] = {name: [] for name in NAVIGATION_FIELDS}
    mismatched_episode_ids: set[str] = set()
    route_errors: list[float] = []
    instruction_equal = 0
    simple_lengths: list[int] = []
    ha_lengths: list[int] = []

    for episode_id in common:
        left = simple_by_id[episode_id]
        right = ha_by_id[episode_id]
        for field in NAVIGATION_FIELDS:
            if field not in left or field not in right or left[field] != right[field]:
                mismatched_fields[field].append(episode_id)
                mismatched_episode_ids.add(episode_id)
        if left.get("reference_path") and right.get("reference_path"):
            route_errors.append(route_error(left["reference_path"], right["reference_path"]))
        left_text = left.get("instruction", {}).get("instruction_text", "")
        right_text = right.get("instruction", {}).get("instruction_text", "")
        instruction_equal += int(left_text == right_text)
        simple_lengths.append(len(left_text))
        ha_lengths.append(len(right_text))

    def mean(values: list[int] | list[float]) -> float | None:
        return statistics.fmean(values) if values else None

    result = {
        "format_version": 1,
        "split": args.split,
        "simplevln_episodes": len(simple_episodes),
        "har2r_episodes": len(ha_episodes),
        "common_episode_ids": len(common),
        "missing_in_har2r": missing_in_ha,
        "extra_in_har2r": extra_in_ha,
        "navigation_exact_match_count": len(common) - len(mismatched_episode_ids),
        "mismatched_episode_ids_by_field": mismatched_fields,
        "instruction_equal_count": instruction_equal,
        "instruction_mean_chars_simplevln": mean(simple_lengths),
        "instruction_mean_chars_har2r": mean(ha_lengths),
        "route_max_error_mean_m": mean(route_errors),
        "route_max_error_max_m": max(route_errors) if route_errors else None,
        "simplevln_scenes": sorted({row["scene_id"] for row in simple_episodes}),
        "har2r_scenes": sorted({row["scene_id"] for row in ha_episodes}),
        "instruction_vocab_equal": simple_payload.get("instruction_vocab")
        == ha_payload.get("instruction_vocab"),
        "compatible_navigation_layout": (
            len(common) == len(simple_episodes) == len(ha_episodes)
            and not any(mismatched_fields.values())
        ),
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    if not result["compatible_navigation_layout"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
