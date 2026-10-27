#!/usr/bin/env python3
"""Run SimpleVLN + camera-only social guard in the official Track 2 runtime.

This exporter is prepared but intentionally not executed in the current CPU-only
phase. Once a graphics-capable HA-VLN container and a separately authorized vLLM
service exist, it replays closed-loop episodes, records the exact six-action
sequences sent to the simulator, and packages complete runs.
"""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from .export_action_log import export
from .simplevln_agent import SimpleVLNHttpAgent
from .simplevln_social_agent import SocialSimpleVLNAgent
from .social_depth_guard import SocialDepthGuard


SPLITS = ("val_seen", "val_unseen")
ACTIONS = ("STOP", "MOVE_FORWARD", "TURN_LEFT", "TURN_RIGHT", "LOOK_UP", "LOOK_DOWN")
ACTION_NAMES = {0: "STOP", 1: "MOVE_FORWARD", 2: "TURN_LEFT", 3: "TURN_RIGHT"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("/data/havln2"))
    parser.add_argument("--source-root", type=Path, default=Path("/workspace/cma-deps/HA-VLN"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--vllm-base-url", required=True)
    parser.add_argument("--model-name", default="simplevln")
    parser.add_argument("--gpu-ids", nargs="+", type=int, default=[0])
    parser.add_argument("--episode-limit", type=int)
    parser.add_argument(
        "--splits",
        nargs="+",
        choices=("train", "val_seen", "val_unseen"),
        default=("val_seen", "val_unseen"),
        help="Use train for guard tuning; validation is only exported for final scoring",
    )
    parser.add_argument("--resolution-ratio", type=float, default=1.0)
    parser.add_argument("--stop-distance-m", type=float, default=0.80)
    parser.add_argument("--side-distance-m", type=float, default=1.05)
    parser.add_argument("--max-depth-m", type=float, default=10.0)
    parser.add_argument("--normalized-depth", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--dry-run", action="store_true", help="Prepare and inspect jobs without Habitat/GPU")
    parser.add_argument("--worker-task", type=Path, help=argparse.SUPPRESS)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_episodes(data_root: Path, split: str) -> list[dict]:
    path = data_root / "HA-R2R" / split / f"{split}.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    episodes = payload["episodes"]
    ids = [str(row["episode_id"]) for row in episodes]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate episode IDs in {path}")
    episodes.sort(key=lambda row: int(row["episode_id"]))
    return episodes


def check_rows(rows: list[dict], expected: set[str]) -> None:
    ids = [row["episode_id"] for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError("episode coverage is not exact")
    for row in rows:
        actions = row["actions"]
        if not 1 <= len(actions) <= 500 or any(action not in ACTIONS for action in actions):
            raise ValueError("invalid action sequence")
        if len(actions) < 500 and actions[-1] != "STOP":
            raise ValueError("sequence lacks terminal STOP")
        if "STOP" in actions[:-1]:
            raise ValueError("STOP occurs before the terminal action")


def runtime_environment(source: Path):
    import habitat
    import habitat_sim
    import habitat_extensions
    import vlnce_baselines
    import vlnce_baselines.common
    baseline = source / "agent/VLN-CE/vlnce_baselines"
    vlnce_baselines.__path__.append(str(baseline))
    vlnce_baselines.common.__path__.append(str(baseline / "common"))
    from vlnce_baselines.common.environments import HAVLNCEDaggerEnv
    from vlnce_baselines.config.default import get_config
    return habitat, habitat_sim, HAVLNCEDaggerEnv, get_config


def configure_environment(task: dict, job: dict):
    from habitat import Config
    from havln_scoring.runtime import quiet_runtime
    _, _, environment_class, get_config = runtime_environment(Path(task["source"]))
    config = get_config("/app/config/challenge_submission.yaml")
    config.defrost()
    config.EVAL.SPLIT = job["split"]
    cfg = config.TASK_CONFIG
    cfg.DATASET.SPLIT = job["split"]
    cfg.DATASET.DATA_PATH = task["data"] + "/HA-R2R/{split}/{split}.json.gz"
    cfg.DATASET.SCENES_DIR = task["data"] + "/scene_datasets"
    cfg.DATASET.EPISODES_ALLOWED = job["ids"]
    cfg.SIMULATOR.HABITAT_SIM_V0.GPU_DEVICE_ID = task["gpu"]
    cfg.SIMULATOR.HUMAN_GLB_PATH = task["data"] + "/HAPS2_0"
    cfg.SIMULATOR.HUMAN_INFO_PATH = task["data"] + "/Multi-Human-Annotations/human_motion.json"
    cfg.SIMULATOR.RECOMPUTE_NAVMESH_PATH = task["data"] + "/recompute_navmesh"
    # Match the public SimpleVLN evaluation contract (one forward RGB-D camera,
    # 90-degree FOV, 640x480). Only the resulting official six actions are exported.
    cfg.SIMULATOR.AGENT_0.RGB_SENSOR.WIDTH = 640
    cfg.SIMULATOR.AGENT_0.RGB_SENSOR.HEIGHT = 480
    cfg.SIMULATOR.AGENT_0.RGB_SENSOR.HFOV = 90
    cfg.SIMULATOR.AGENT_0.DEPTH_SENSOR.WIDTH = 640
    cfg.SIMULATOR.AGENT_0.DEPTH_SENSOR.HEIGHT = 480
    cfg.SIMULATOR.AGENT_0.DEPTH_SENSOR.HFOV = 90
    cfg.SIMULATOR.AGENT_0.DEPTH_SENSOR.MAX_DEPTH = task["guard"]["max_depth_m"]
    cfg.SIMULATOR.AGENT_0.DEPTH_SENSOR.NORMALIZE_DEPTH = task["guard"]["normalized_depth"]
    cfg.TASK.SENSORS = ["INSTRUCTION_SENSOR"]
    cfg.TASK.MEASUREMENTS = []
    cfg.ENVIRONMENT.ITERATOR_OPTIONS.SHUFFLE = False
    cfg.ENVIRONMENT.ITERATOR_OPTIONS.MAX_SCENE_REPEAT_STEPS = -1
    cfg.SEED = 0
    config.freeze()
    if list(cfg.TASK.POSSIBLE_ACTIONS) != list(ACTIONS):
        raise ValueError("official six-action vocabulary differs")
    # Silence only known renderer chatter; do not suppress exceptions.
    verbosity = nullcontext() if os.environ.get("HAVLN_SIMPLEVLN_VERBOSE") == "1" else quiet_runtime()
    return verbosity, Config, environment_class, config


def run_worker(task_path: Path) -> None:
    task = json.loads(task_path.read_text(encoding="utf-8"))
    habitat, habitat_sim, _, _ = runtime_environment(Path(task["source"]))
    if habitat.__version__ != "0.1.7" or habitat_sim.__version__ != "0.1.7":
        raise RuntimeError("SimpleVLN exporter requires the official Habitat 0.1.7 image")
    for job in task["jobs"]:
        shard = Path(task["output"]) / "shards" / f"{job['key']}.json"
        if shard.exists():
            existing = json.loads(shard.read_text(encoding="utf-8"))
            if existing["fingerprint"] != task["fingerprint"]:
                raise ValueError("shard provenance differs")
            check_rows(existing["rows"], set(job["ids"]))
            continue
        verbosity, _, environment_class, config = configure_environment(task, job)
        with verbosity, environment_class(config=config) as env:
            episodes = sorted(env.episodes, key=lambda value: int(value.episode_id))
            if set(str(value.episode_id) for value in episodes) != set(job["ids"]):
                raise ValueError("runtime episode coverage differs")
            env.habitat_env.episode_iterator = iter(episodes)
            rows = []
            for episode in episodes:
                observation = env.reset()
                if str(env.current_episode.episode_id) != str(episode.episode_id):
                    raise RuntimeError("reset resolved the wrong episode")
                base = SimpleVLNHttpAgent(
                    base_urls=task["vllm_base_url"],
                    model_name=task["model_name"],
                    resolution_ratio=task["resolution_ratio"],
                )
                agent = SocialSimpleVLNAgent(
                    base,
                    guard=SocialDepthGuard(
                        stop_distance_m=task["guard"]["stop_distance_m"],
                        side_distance_m=task["guard"]["side_distance_m"],
                        max_depth_m=task["guard"]["max_depth_m"],
                        normalized_depth=task["guard"]["normalized_depth"],
                    ),
                )
                trace: list[str] = []
                done = False
                for _ in range(500):
                    result = agent.act(observation, {}, str(episode.episode_id))
                    action = result["action"]
                    name = action if isinstance(action, str) else ACTION_NAMES[int(action)]
                    trace.append(name)
                    observation, _, done, _ = env.step(name)
                    if done:
                        break
                if not done:
                    raise RuntimeError("official step limit reached without termination")
                rows.append({"episode_id": str(episode.episode_id), "actions": trace})
        check_rows(rows, set(job["ids"]))
        atomic_json(shard, {"fingerprint": task["fingerprint"], "rows": rows})
        print(f"completed {job['key']}: {len(rows)} episodes", flush=True)


def prepare_jobs(args: argparse.Namespace) -> tuple[dict, list[dict], dict[str, list[str]]]:
    data_root = args.data_root.resolve()
    source_root = args.source_root.resolve()
    output = args.output_dir.resolve()
    if not (source_root / ".release.json").is_file():
        raise FileNotFoundError("pinned HA-VLN source release metadata is missing")
    for relative in ("HAPS2_0", "Multi-Human-Annotations/human_motion.json"):
        if not (data_root / relative).exists():
            raise FileNotFoundError(f"missing data asset: {data_root / relative}")
    jobs: list[dict] = []
    expected: dict[str, list[str]] = {}
    hashes: dict[str, str] = {}
    full_counts: dict[str, int] = {}
    for split in args.splits:
        all_episodes = load_episodes(data_root, split)
        full_counts[split] = len(all_episodes)
        episodes = all_episodes
        if args.episode_limit is not None:
            episodes = episodes[:args.episode_limit]
        expected[split] = [str(row["episode_id"]) for row in episodes]
        hashes[split] = sha256(data_root / "HA-R2R" / split / f"{split}.json.gz")
        scans: dict[str, list[str]] = {}
        for episode in episodes:
            scan = Path(episode["scene_id"]).parent.name
            scene = data_root / "scene_datasets/mp3d" / scan / f"{scan}.glb"
            if not scene.is_file():
                raise FileNotFoundError(f"missing licensed scene: {scene}")
            scans.setdefault(scan, []).append(str(episode["episode_id"]))
        jobs.extend(
            {"key": f"{split}-{scan}", "split": split, "ids": ids}
            for scan, ids in sorted(scans.items())
        )
    identity = {
        "exporter": sha256(Path(__file__)),
        "source_revision": json.loads((source_root / ".release.json").read_text())["revision"],
        "datasets": hashes,
        "human_annotations": sha256(data_root / "Multi-Human-Annotations/human_motion.json"),
        "vllm_base_url": args.vllm_base_url,
        "model_name": args.model_name,
        "resolution_ratio": args.resolution_ratio,
        "guard": {
            "stop_distance_m": args.stop_distance_m,
            "side_distance_m": args.side_distance_m,
            "max_depth_m": args.max_depth_m,
            "normalized_depth": args.normalized_depth,
        },
        "episode_limit": args.episode_limit,
        "splits": list(args.splits),
        "full_episode_counts": full_counts,
    }
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    task = {
        "data": str(data_root),
        "source": str(source_root),
        "output": str(output),
        "fingerprint": fingerprint,
        "vllm_base_url": args.vllm_base_url,
        "model_name": args.model_name,
        "resolution_ratio": args.resolution_ratio,
        "guard": identity["guard"],
        "splits": list(args.splits),
        "full_episode_counts": full_counts,
    }
    return task, jobs, expected


def run_export(args: argparse.Namespace) -> None:
    task, jobs, expected = prepare_jobs(args)
    print(json.dumps({"fingerprint": task["fingerprint"], "jobs": len(jobs), "episodes": {key: len(value) for key, value in expected.items()}}, indent=2))
    if args.dry_run:
        return
    output = Path(task["output"])
    output.mkdir(parents=True, exist_ok=True)
    (output / "shards").mkdir(exist_ok=True)
    if len(set(args.gpu_ids)) != len(args.gpu_ids) or any(value < 0 for value in args.gpu_ids):
        raise ValueError("GPU IDs must be distinct nonnegative ordinals")
    processes = []
    logs = []
    try:
        for ordinal, gpu in enumerate(args.gpu_ids):
            worker_task = dict(task, gpu=gpu, jobs=jobs[ordinal::len(args.gpu_ids)])
            task_path = output / f"worker-{gpu}.json"
            atomic_json(task_path, worker_task)
            log = (output / f"worker-{gpu}.log").open("a")
            logs.append(log)
            processes.append(subprocess.Popen([sys.executable, __file__, "--worker-task", str(task_path)], stdout=log, stderr=subprocess.STDOUT))
        codes = [process.wait() for process in processes]
        if any(codes):
            raise RuntimeError(f"worker failed with exit codes {codes}")
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait()
        for log in logs:
            log.close()
    action_dir = output / "actions"
    action_dir.mkdir(exist_ok=True)
    complete = (
        set(args.splits) == {"val_seen", "val_unseen"}
        and args.episode_limit is None
    )
    for split in args.splits:
        rows = []
        wanted = set(expected[split])
        for job in jobs:
            if job["split"] != split:
                continue
            shard = output / "shards" / f"{job['key']}.json"
            payload = json.loads(shard.read_text(encoding="utf-8"))
            rows.extend(payload["rows"])
        check_rows(rows, wanted)
        path = action_dir / f"{split}.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    if complete:
        export(action_dir, output / "submission.zip", 778, 1839)
    else:
        print("diagnostic run complete; no submission ZIP was created")


def main() -> None:
    args = parse_args()
    if args.worker_task:
        run_worker(args.worker_task)
    else:
        if args.episode_limit is not None and args.episode_limit <= 0:
            raise ValueError("episode limit must be positive")
        if len(set(args.splits)) != len(args.splits):
            raise ValueError("splits must be unique")
        run_export(args)


if __name__ == "__main__":
    main()
