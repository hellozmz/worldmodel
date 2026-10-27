# Track 2 CPU-only status — 2026-10-27

## Constraint honored

No CARLA, Habitat, vLLM, PyTorch CUDA, CMA, renderer, or other GPU workload was
started. Existing unrelated GPU jobs were not touched. The only active work is
CPU-side data download, checksum verification, source analysis, packaging, and
unit testing.

## Completed without GPUs

### Official HAPS 2.0 asset bundle

The 8,332,789,125-byte archive completed, matched the official SHA-256, and
extracted successfully:

```text
c5bc75ffcec1b1b83b9ffc1f7177a02fabcdacbb6a0a7a02368afa5bbc209741
486 motion directories
116,640 files
14 GiB extracted
```

Marker:

```text
/mnt/models_2296/zmz/workspace/roboworld2026/data/havln2/downloads/haps-extracted.json
```

### SimpleVLN compatibility finding

Public SimpleVLN was cloned at commit `89b72a59c8f7feb805c0918e43dd5bfbdd7c48cc`.
All 20 of its CPU regression checks pass.

A new compatibility checker found that all 1,839 HA-R2R `val_unseen` navigation
episodes exactly match SimpleVLN's R2R-CE `val_unseen` episodes in:

- episode ID;
- trajectory ID;
- scene ID;
- start position and rotation;
- goal;
- reference path.

There are no missing or extra episode IDs, and maximum reference-path error is
0.0 m. The difference is instruction text: HA-R2R uses much longer human-aware
instructions (mean 688.2 characters versus 139.1 in the static R2R file). This
makes a SimpleVLN closed-loop policy directly compatible at the navigation-task
level; dynamic-human avoidance still has to come from forward RGB-D.

Report:

```text
roboworld2026/artifacts/simplevln_har2r_compatibility.json
```

### CPU-only social navigation implementation

Added and tested:

- `roboworld2026/track2/social_depth_guard.py`
  - uses only the forward depth image;
  - suppresses unsafe forward actions;
  - waits when no side corridor is clear;
  - creates a short side-step plan when a clear side region is visible;
  - never reads human annotations, simulator state, GPS, or privileged metrics.
- `roboworld2026/track2/simplevln_agent.py`
  - Habitat-0.1.7-compatible HTTP implementation of the public SimpleVLN prompt,
    bounded visual history, action-chunk parser, decoding settings, and endpoint
    round-robin;
  - avoids importing SimpleVLN's newer Habitat-0.3.3 evaluator dependencies.
- `roboworld2026/track2/simplevln_social_agent.py`
  - preserves SimpleVLN's pending navigation intent while replacing unsafe moves.
- `roboworld2026/track2/export_action_log.py`
  - exact split/episode coverage and six-action ZIP contract validation.
- `roboworld2026/track2/run_simplevln_social_export.py`
  - prepared official-runtime exporter with scan-based resume shards and `--dry-run`;
  - not executed because it requires a graphics device.

All current Track 2 utility tests pass locally and in the H200 container without
allocating a GPU.

### Official result diagnosis

The v4 official episode output was re-summarized with unambiguous names. In
`val_unseen`:

- 495 / 1,839 episodes geometrically reached the goal;
- only 138 were collision-free successes (the leaderboard SR);
- 357 reached the goal but collided;
- 1,629 episodes used 100 or fewer actions, and only 12 exceeded 400 actions.

Thus there is generally enough of the 500-action budget for a reactive detour.
The dominant loss is social collision, not action-budget overflow.

Report:

```text
roboworld2026/artifacts/track2_v4_official_episode_summary.json
```

## Still running or prepared (CPU/network only)

1. Strong public SimpleVLN checkpoints are downloading sequentially:
   - `SimpleVLN_Qwen35_4B_RL`;
   - `SimpleVLN_Qwen35_9B_RL`.
2. The official GHCR image is downloading through a resumable parallel-range
   helper rather than repeated non-resumable `skopeo` transfers.
3. Once all image blobs verify, a local OCI layout will be converted offline and
   loaded with Docker; no container execution is needed until then.

## Remaining hard blocker

No licensed Matterport3D assets were found under the searched shared roots.
SimpleVLN requires 44 files for the 11 `val_unseen` scenes (GLB, navmesh, house,
and semantic PLY), and all 44 are currently missing. A user-authorized
Matterport3D root remains the main prerequisite for legitimate local replay.

## GPU-authorized execution sequence

1. Supply and mount the licensed MP3D root.
2. Load the verified official HA-VLN image.
3. Serve the already downloaded SimpleVLN checkpoint with vLLM.
4. Run `run_simplevln_social_export.py --episode-limit 1` as a smoke test.
5. Tune the RGB-D guard only on training/diagnostic episodes, not validation.
6. Replay complete seen/unseen validation splits once parameters are fixed.
7. Export with `export_action_log.py`, run the official validator, and only then
   consider a Codabench submission.

No additional Track 2 submission is being burned while the only available policy
is the known low-scoring open-loop reference-path family.
