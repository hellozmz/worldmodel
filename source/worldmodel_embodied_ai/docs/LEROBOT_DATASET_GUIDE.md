# LeRobot PushT Dataset Guide

Local dataset:

```text
04_lerobot_dataset/datasets/pusht
```

Task: push a T-shaped block onto a T-shaped target.

## Layout

- frames and actions: `data/chunk-000/file-000.parquet`
- video: `videos/observation.image/chunk-000/file-000.mp4`
- episode metadata: `meta/episodes/chunk-000/file-000.parquet`
- dataset metadata: `meta/info.json`, `meta/stats.json`, `meta/tasks.parquet`

Important fields:

```text
observation.state  float32[2]
action             float32[2]
observation.image  video, decoded as float32[3,96,96]
next.reward        float
next.done          bool
next.success       bool
episode_index      int
frame_index        int
timestamp          float
```

## Analysis command

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/04_lerobot_dataset
source .venv/bin/activate
python scripts/analyze_pusht.py
```

Outputs:

```text
analysis/pusht_summary.json
analysis/episode0_trajectory.png
analysis/episode0_contact_sheet.png
```

## Loading with LeRobot

```python
from lerobot.datasets.lerobot_dataset import LeRobotDataset

dataset = LeRobotDataset(
    "lerobot/pusht",
    root="/mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/04_lerobot_dataset/datasets/pusht",
    download_videos=False,
)
frame = dataset[0]
```

## Avoid leakage

Use:

```python
train_episodes = first 80% by episode id or seeded shuffle
val_episodes   = remaining 20%
```

Do not randomly split rows: adjacent video frames are nearly duplicates.

## Environment note

The venv is:

```text
04_lerobot_dataset/.venv
```

It was installed from the local source at `04_lerobot_dataset/repos/lerobot` with SmolVLA, dataset, and PushT extras. `pyvenv.cfg` must keep `include-system-site-packages = false`; a system namespace package previously caused a misleading `KeyError: 'flash_attn'`.

## Exercises

1. Verify episode length statistics.
2. Identify state/action min/max and explain units.
3. Compare state and action trajectories.
4. Inspect contact-sheet frames around contact events.
5. Implement a second split and measure validation variance.
