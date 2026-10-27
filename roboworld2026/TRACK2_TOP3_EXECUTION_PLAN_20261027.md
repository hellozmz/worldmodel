# Track 2 top-3 execution plan — 2026-10-27

## Current official state

- Best Phase 1 submission: `1011919` (`track2_reference_path_v3_wait1.zip`)
- Score: **9.2529875484**
- Rank: 12/16 public leaderboard rows
- Top-3 threshold: **67.2286182689**
- v4 (`1012376`, pure-pursuit lookahead 1.0 m) finished at **9.0072756124**, so it is worse and was not added to the public best-score row.

## Diagnosis from official scoring output

The official v4 output was downloaded and inspected. It contains complete metrics for all
2,617 Phase 1 episodes:

- `val_unseen`: 1,839 episodes
- Geometric goal reach (`distance <= 3 m`): 495 / 1,839
- Collision-free episodes: only 138 / 1,839
- Official SR: 0.07504078
- NE: 5.46606 m
- TCR: 21.47254

Thus the archive format and static reference-path reconstruction are not the issue. The
open-loop path reaches many goals, but repeatedly collides with dynamic humans. Waiting
actions and pure-pursuit variants do not solve this. A legitimate top-3 policy needs local
closed-loop RGB-D replay and social navigation.

## Compliance boundary

The official terms explicitly state:

- validation splits must not be used for model training or fine-tuning;
- `human_motion.json` or ground-truth human states/trajectories must not be directly read for validation/test planning;
- human positions must be inferred from camera observations during evaluation;
- ground-truth human information from training episodes may be used as privileged training supervision.

Therefore we will not copy validation human trajectories, tune episode-specific avoidance, or submit a validation-overfit action package.

## Completed CPU-only preparation

- Full HA-R2R CE archive downloaded and extracted:
  - 10,819 train episodes;
  - 778 `val_seen`;
  - 1,839 `val_unseen`.
- Official CMA checkpoint downloaded and SHA-256 verified:
  - `e70dce940c6ae16aa63c41f3b2411884448a3ccd083b06da156d297b5f4a52dc`.
- Checkpoint installed in the expected CMA path.
- `human_motion.json` downloaded and hash verified for later **training-only** supervision.
- HAPS 2.0 download resumed with HTTP/1.1 and robust retries.
- Official HA-VLN Docker image is being pulled through the proxy with `skopeo`.

## Remaining hard blocker

No licensed Matterport3D mesh set exists under the current workspace. Without
`scene_datasets/mp3d/<scan>/<scan>.glb`, Habitat cannot replay even one episode, train a
closed-loop policy, or export actions from a camera-based agent.

Required from a user-authorized Matterport3D source:

```text
<authorized-data-root>/scene_datasets/mp3d/<scan>/<scan>.glb
```

At minimum, all scans referenced by train plus the relevant validation/test phase bundle.

## Once MP3D is available

1. Finish HAPS extraction and verify all GLBs.
2. Run the official Docker image with the data mounted.
3. Reproduce CMA baseline locally.
4. Add a person detector / human-motion predictor using only forward RGB-D.
5. Combine CMA navigation with a social costmap and reactive stop/detour policy.
6. Use training episodes only for supervised human-motion augmentation.
7. Replay all validation episodes locally and submit only a legally generated action package.

## CPU-only addendum

See `TRACK2_CPU_ONLY_STATUS_20261027.md`. HAPS 2.0 is fully downloaded and
verified, SimpleVLN navigation identities are an exact match for all 1,839
`val_unseen` episodes, public SimpleVLN tests pass, and a camera-only RGB-D
social guard plus official action exporter are implemented and unit-tested.
Matterport3D remains the hard blocker.
