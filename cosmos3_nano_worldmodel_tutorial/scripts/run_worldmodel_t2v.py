#!/usr/bin/env python3
"""Submit one short text-to-video world simulation request to Cosmos3-Nano."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("COSMOS_BASE_URL", "http://127.0.0.1:18000").rstrip("/")
OUTPUT_DIR = ROOT / "outputs"
PROMPT = (
    "Physical AI world-model simulation: a small autonomous delivery robot navigates "
    "through a bright warehouse. It slows down, turns left around a stacked cardboard "
    "box, and its shadow and reflected highlights move consistently. The camera follows "
    "smoothly while shelves show stable parallax."
)
NEGATIVE_PROMPT = "blurry, distorted objects, jittery motion, physically impossible movement, low quality"
EXTRA_PARAMS = {
    "use_resolution_template": False,
    "use_duration_template": False,
    "guardrails": False,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ffprobe(path: Path) -> dict:
    if subprocess.run(["which", "ffprobe"], capture_output=True).returncode == 0:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-count_frames", "-show_entries",
             "stream=width,height,r_frame_rate,nb_read_frames,duration,codec_name",
             "-of", "json", str(path)],
            capture_output=True, text=True, check=True,
        )
        return {"available": True, **json.loads(p.stdout)}  # type: ignore[arg-type]
    try:
        import av
        with av.open(str(path)) as container:
            stream = container.streams.video[0]
            frames = 0
            for _ in container.decode(video=True):
                frames += 1
            return {
                "available": True,
                "probe": "pyav",
                "stream": {
                    "width": stream.width,
                    "height": stream.height,
                    "average_rate": str(stream.average_rate),
                    "duration": float(stream.duration or 0.0),
                    "codec_name": stream.codec_context.name,
                    "nb_read_frames": frames,
                },
            }
    except Exception as exc:
        return {"available": False, "error": repr(exc)}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output = OUTPUT_DIR / f"worldmodel_t2v_{stamp}.mp4"
    data = {
        "model": "cosmos3-nano",
        "prompt": PROMPT,
        "negative_prompt": NEGATIVE_PROMPT,
        "size": os.environ.get("COSMOS_SIZE", "448x256"),
        "num_frames": os.environ.get("COSMOS_NUM_FRAMES", "25"),
        "fps": os.environ.get("COSMOS_FPS", "12"),
        "num_inference_steps": os.environ.get("COSMOS_STEPS", "12"),
        "guidance_scale": os.environ.get("COSMOS_GUIDANCE", "6.0"),
        "max_sequence_length": "4096",
        "flow_shift": "10.0",
        "seed": os.environ.get("COSMOS_SEED", "20261025"),
        "extra_params": json.dumps(EXTRA_PARAMS, separators=(",", ":")),
    }
    request_path = OUTPUT_DIR / f"worldmodel_t2v_{stamp}_request.json"
    request_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    print(f"POST {BASE_URL}/v1/videos/sync", flush=True)
    # The container may carry a forwarding proxy for Internet access. Local API
    # requests must bypass it; otherwise requests tries 127.0.0.1:19893.
    session = requests.Session()
    session.trust_env = False
    started = time.perf_counter()
    response = session.post(
        f"{BASE_URL}/v1/videos/sync",
        data=data,
        headers={"Accept": "video/mp4"},
        timeout=int(os.environ.get("COSMOS_TIMEOUT", "1800")),
    )
    elapsed = time.perf_counter() - started
    response.raise_for_status()
    output.write_bytes(response.content)

    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "request_file": str(request_path),
        "output_file": str(output),
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "elapsed_seconds": round(elapsed, 3),
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "media": ffprobe(output),
    }
    metadata_path = output.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(json.dumps(metadata, ensure_ascii=False, indent=2))

    log = ROOT / "docs" / "RUN_LOG.md"
    with log.open("a", encoding="utf-8") as f:
        f.write(
            f"\n- {metadata['timestamp_utc']}：文本到视频世界模型推演完成，"
            f"输入 `{request_path.name}`，输出 `{output.name}`，"
            f"耗时 {elapsed:.1f}s，大小 {metadata['bytes']} bytes，SHA256 `{metadata['sha256']}`。\n"
        )


if __name__ == "__main__":
    main()
