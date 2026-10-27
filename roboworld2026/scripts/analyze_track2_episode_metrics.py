#!/usr/bin/env python3
"""Summarize official Track 2 episode metrics without episode-specific tuning."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics", nargs="+", type=Path)
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[index]


def summarize(rows: list[dict]) -> dict:
    split_names = sorted({row.get("split", "unknown") for row in rows})
    summaries = {}
    for split in split_names:
        selected = [row for row in rows if row.get("split", "unknown") == split]
        goal_reached = [float(row["distance_to_goal"]) <= 3.0 for row in selected]
        collision_free = [int(row.get("adjusted_collision_count", 0)) == 0 for row in selected]
        steps = [float(row.get("steps_taken", len(row.get("actions", [])))) for row in selected]
        raw = [int(row.get("raw_collision_count", 0)) for row in selected]
        adjusted = [int(row.get("adjusted_collision_count", 0)) for row in selected]
        summaries[split] = {
            "episodes": len(selected),
            "geometric_goal_reached": sum(goal_reached),
            "collision_free": sum(collision_free),
            "episode_metric_success": sum(float(row["success"]) > 0 for row in selected),
            "leaderboard_collision_free_success": sum(
                a and b for a, b in zip(goal_reached, collision_free)
            ),
            "goal_reached_but_collided": sum(a and not b for a, b in zip(goal_reached, collision_free)),
            "step_limit_reached": sum(bool(row.get("step_limit_reached")) for row in selected),
            "step_buckets": {
                "<=100": sum(value <= 100 for value in steps),
                "101-200": sum(100 < value <= 200 for value in steps),
                "201-300": sum(200 < value <= 300 for value in steps),
                "301-400": sum(300 < value <= 400 for value in steps),
                "401-499": sum(400 < value < 500 for value in steps),
                ">=500": sum(value >= 500 for value in steps),
            },
            "steps": {
                "mean": statistics.fmean(steps) if steps else None,
                "p50": percentile(steps, 0.50),
                "p90": percentile(steps, 0.90),
                "p99": percentile(steps, 0.99),
                "max": max(steps) if steps else None,
                "remaining_to_500_p10": 500 - percentile(steps, 0.90),
            },
            "raw_collision_histogram": dict(sorted(Counter(raw).items())),
            "adjusted_collision_histogram": dict(sorted(Counter(adjusted).items())),
            "raw_collision_mean": statistics.fmean(raw) if raw else None,
            "adjusted_collision_mean": statistics.fmean(adjusted) if adjusted else None,
        }
    return summaries


def main() -> None:
    args = parse_args()
    rows = []
    for path in args.metrics:
        with path.open(encoding="utf-8") as stream:
            rows.extend(json.loads(line) for line in stream if line.strip())
    identities = [(row.get("split"), str(row.get("episode_id"))) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate split/episode rows")
    result = {"format_version": 1, "rows": len(rows), "splits": summarize(rows)}
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
