#!/usr/bin/env python3
"""Validate and package closed-loop Track 2 action logs.

The GPU evaluator may write one JSON Lines file per split. This CPU-only
exporter checks exact episode coverage and the official six-action contract
before a ZIP is allowed near Codabench.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile


ALLOWED_ACTIONS = {
    "STOP",
    "MOVE_FORWARD",
    "TURN_LEFT",
    "TURN_RIGHT",
    "LOOK_UP",
    "LOOK_DOWN",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-zip", type=Path, required=True)
    parser.add_argument("--val-seen-count", type=int, default=778)
    parser.add_argument("--val-unseen-count", type=int, default=1839)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: row must be an object")
            rows.append(value)
    return rows


def validate_split(rows: list[dict], split: str, expected_count: int) -> dict:
    by_id: dict[str, dict] = {}
    for row in rows:
        if row.get("split") not in (None, split):
            raise ValueError(f"{split}: row belongs to {row.get('split')!r}")
        episode_id = row.get("episode_id")
        if not isinstance(episode_id, str) or not episode_id:
            raise ValueError(f"{split}: invalid episode_id {episode_id!r}")
        if episode_id in by_id:
            raise ValueError(f"{split}: duplicate episode ID {episode_id}")
        actions = row.get("actions")
        if not isinstance(actions, list) or not actions:
            raise ValueError(f"{split}/{episode_id}: actions must be non-empty")
        if len(actions) > 500:
            raise ValueError(f"{split}/{episode_id}: action budget exceeded ({len(actions)})")
        invalid = sorted(set(actions) - ALLOWED_ACTIONS)
        if invalid:
            raise ValueError(f"{split}/{episode_id}: invalid actions {invalid}")
        if "STOP" in actions:
            if actions.count("STOP") != 1 or actions[-1] != "STOP":
                raise ValueError(f"{split}/{episode_id}: STOP must occur once at the end")
        elif len(actions) < 500:
            raise ValueError(f"{split}/{episode_id}: sequences shorter than 500 require STOP")
        by_id[episode_id] = {"episode_id": episode_id, "actions": actions}
    if len(by_id) != expected_count:
        raise ValueError(
            f"{split}: expected {expected_count} unique episodes, got {len(by_id)}"
        )
    ordered = [by_id[key] for key in sorted(by_id, key=lambda value: int(value) if value.isdigit() else value)]
    return {"format_version": 1, "split": split, "episodes": ordered}


def export(input_dir: Path, output_zip: Path, val_seen_count: int, val_unseen_count: int) -> None:
    payloads = {}
    for split, expected_count in (("val_seen", val_seen_count), ("val_unseen", val_unseen_count)):
        jsonl = input_dir / f"{split}.jsonl"
        json_file = input_dir / f"{split}.json"
        if jsonl.is_file():
            rows = load_jsonl(jsonl)
        elif json_file.is_file():
            rows = json.loads(json_file.read_text(encoding="utf-8"))
        else:
            raise FileNotFoundError(f"missing {jsonl} or {json_file}")
        payloads[split] = validate_split(rows, split, expected_count)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    partial = output_zip.with_suffix(output_zip.suffix + ".partial")
    with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for split in ("val_seen", "val_unseen"):
            filename = f"{split}.json"
            data = json.dumps(payloads[split], ensure_ascii=False, separators=(",", ":")).encode()
            archive.writestr(filename, data)
    partial.replace(output_zip)
    print(f"PACKED {output_zip} val_seen={val_seen_count} val_unseen={val_unseen_count}")


def main() -> None:
    args = parse_args()
    export(args.input_dir, args.output_zip, args.val_seen_count, args.val_unseen_count)


if __name__ == "__main__":
    main()
