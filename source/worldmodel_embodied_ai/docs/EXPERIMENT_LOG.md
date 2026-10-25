# World Model / Embodied AI Experiment Log

All workspace paths are inside `/mnt/models_2296/zmz/workspace/worldmodel_embodied_ai` on host `h200_1727`, container `zmz_dev_v2`, unless explicitly stated. Times in this section are UTC unless noted.

## 1. Environment baseline

Checked at 2026-10-25 01:41:54 UTC:

```bash
nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader
```

All 8 NVIDIA H200 GPUs reported `0 MiB / 143771 MiB` and 0% utilization. `/mnt/models_2296` had about 3.8 TiB available.

Container/runtime:

- container: `zmz_dev_v2`
- system Python: `3.12.12`
- isolated LeRobot environment: `04_lerobot_dataset/.venv`
- `include-system-site-packages = false`
- key versions: Torch `2.11.0+cu128`, LeRobot `0.6.2`, Transformers `5.4.0`
- persistent environment report: `04_lerobot_dataset/logs/environment_report.json`

The original system-site namespace package caused a misleading `KeyError: 'flash_attn'` import failure. Disabling system site packages fixed the import.

## 2. GPU execution caveat

When a CUDA process was started with `docker exec`, an external host-side supervisor repeatedly sent SIGTERM to the whole `zmz_dev_v2` container. Docker events recorded `container kill ... signal=15` and exit code 143, including:

- a minimal CUDA allocation probe;
- SmolVLA inference;
- the first tiny-policy/world-model attempts.

CPU analysis and import checks continued to run in the container. To finish the requested GPU experiments without further stopping the shared container, the GPU processes were launched from the host runtime using the same bind-mounted workspace and the container-created Python 3.12 virtual environment. Every affected JSON result includes an `execution_context` field stating this explicitly.

This is not a hidden claim that the GPU processes stayed inside the container cgroup. Once the host supervisor no longer stops CUDA `docker exec` jobs, the documented in-container commands remain the intended reproduction path.

## 3. Download and source inventory

| Artifact | Local path | Source / revision | Size or integrity |
|---|---|---|---|
| Cosmos3-Nano | `/mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel/model` | AtomGit mirror, commit `e59a53c25979a090fa8706c9acc0c254a6e89b92` | all 11 core LFS SHA256 checks passed |
| R2-Dreamer source | `02_dreamer_latent_rl/repos/r2dreamer` | `codeload.github.com/NM512/r2dreamer/refs/heads/main` | SHA256 `1dc3d7077f85bf87cf94afe74f47347a1ef42d5bd2d1a08e77e2e18c4b4767db` |
| LeRobot source | `04_lerobot_dataset/repos/lerobot` | `codeload.github.com/huggingface/lerobot/refs/heads/main` | SHA256 `7de6ed459e9e0db47a1c4ea54bdab104124de9fa93481fbe3dfd37ffff8a56b8`, version 0.6.2 |
| SmolVLA base | `03_vla_smolvla/models/smolvla_base` | `https://hf-mirror.com/lerobot/smolvla_base`, revision `5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6` | 873 MiB directory; weight SHA256 `7cd549ac2351fb069c0ddb3c34ad2d09cfc92b56a15dccdfc2e41467aaca01eb` |
| SmolVLM2 tokenizer/config | `03_vla_smolvla/models/smolvlm2_tokenizer` | tokenizer/config subset of `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` | 3.5 MiB |
| LeRobot PushT | `04_lerobot_dataset/datasets/pusht` | `lerobot/pusht`, revision `v3.0` / `7628202a2180972f291ba1bc6723834921e72c19` | 7.4 MiB |

Download logs:

- SmolVLA: `docs/download_hf.log`
- tokenizer: `03_vla_smolvla/logs/download_tokenizer.log`
- original Cosmos: `/mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel/logs/download_model.log`

## 4. Cosmos3-Nano prior successful run

The complete prior run is reused; no 36 GiB second download was performed.

- output: `/mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel/outputs/worldmodel_t2v_20261024_192234.mp4`
- request snapshot: `.../worldmodel_t2v_20261024_192234_request.json`
- result metadata: `.../worldmodel_t2v_20261024_192234.json`
- backend: vLLM-Omni 0.22.0, BF16, local Cosmos3-Nano service on GPU 4
- request: 448×256, 25 frames, 12 fps, 12 inference steps, guidance 6.0, seed 20261025
- HTTP: 200 `video/mp4`
- generation request time: 1.128 s
- output size: 408109 bytes
- SHA256: `a15b2695a263ef956d40a01d0e7c392f3de2c2b77144f8f9e220501ce035b613`
- ffprobe: H.264, 448×256, 12 fps, 25 frames, duration 2.083333 s
- detailed log: `/mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel/docs/RUN_LOG.md`

## 5. LeRobot PushT analysis

Command (successful in container):

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/04_lerobot_dataset
source .venv/bin/activate
python scripts/analyze_pusht.py
```

Outputs:

- `analysis/pusht_summary.json`
- `analysis/episode0_trajectory.png`
- `analysis/episode0_contact_sheet.png`

Verified facts:

- 25,650 frames;
- 206 episodes;
- one task, 10 fps;
- episode length min/mean/max: 49 / 124.515 / 246;
- state and action are both float32 vectors of shape `(2,)`;
- decoded image shape is `(3, 96, 96)`;
- task: “Push the T-shaped block onto the T-shaped target.”;
- this dataset copy has no successful episode according to its `next.success` field (`successful_episode_fraction = 0.0`).

## 6. Tiny imitation policy

Script: `04_lerobot_dataset/scripts/train_tiny_policy.py`

Intended in-container command:

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/04_lerobot_dataset
source .venv/bin/activate
python scripts/train_tiny_policy.py
```

Completed GPU fallback run:

- device: NVIDIA H200
- architecture: MLP `2 -> 256 -> 256 -> 2`
- parameters: 67,074
- episode split: 165 train / 41 validation, split by episode
- epochs: 300
- batch size: 1024
- best epoch: 215
- normalized validation MSE: 0.03816551229638517
- validation RMSE equivalent per action dimension: 19.2879 px
- allocated CUDA memory: 69,235,712 bytes
- runtime: 26.61 s
- checkpoint: `04_lerobot_dataset/policies/tiny_pusht_policy.pt`
- metrics: `04_lerobot_dataset/outputs/tiny_policy_metrics.json`
- plots: `04_lerobot_dataset/outputs/tiny_policy_loss_curve.png`, `.../tiny_policy_predictions.png`

Unnormalized baselines:

- action equals current state: MSE 404.8362
- action equals training mean: MSE 9778.3857
- action equals previous action: MSE 91.0640

Interpretation: the MLP learns useful state/action structure, but this is only a low-bar supervised imitation baseline and does not solve PushT.

## 7. Dreamer-style tiny world model

Script: `02_dreamer_latent_rl/scripts/train_tiny_worldmodel.py`

Intended in-container command:

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/02_dreamer_latent_rl
source ../04_lerobot_dataset/.venv/bin/activate
python scripts/train_tiny_worldmodel.py --steps 1200
```

Completed GPU fallback run:

- device: NVIDIA H200
- model: teaching-sized RSSM-like latent model
- recurrence: GRU, hidden size 128
- latent: 16-D Gaussian
- sequence length: 32
- steps: 1200, batch size 256
- training windows: 15,483
- validation windows: 3,781
- episode split: 165 train / 41 validation
- parameters: 105,412
- final validation loss: 0.25720933079719543
- validation observation MSE: 0.04346286083261172
- validation reward MSE: 0.04379233109454314
- validation done BCE: 0.009367235812048118
- validation KL: 0.11032491972049077
- 64-step open-loop rollout MSE per coordinate: 212.967529296875
- allocated CUDA memory: 75,051,520 bytes
- runtime: 48.39 s
- checkpoint: `02_dreamer_latent_rl/runs/tiny_pusht_worldmodel.pt`
- metrics: `02_dreamer_latent_rl/outputs/tiny_worldmodel_metrics.json`
- plots: `02_dreamer_latent_rl/outputs/worldmodel_loss_curve.png`, `.../worldmodel_rollout.png`

Claim boundary: this is a compact Dreamer-style dynamics lesson, not official DreamerV3 or R2-Dreamer performance.

## 8. SmolVLA GPU interface run

Script: `03_vla_smolvla/scripts/run_smolvla_gpu.py`

Intended in-container command:

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai
source 04_lerobot_dataset/.venv/bin/activate
python 03_vla_smolvla/scripts/run_smolvla_gpu.py
```

Completed GPU fallback run:

- model: local `lerobot/smolvla_base`
- tokenizer/config: local SmolVLM2 subset
- input frame: local PushT frame 0, episode 0
- original PushT state: shape `(2,)`, explicitly padded to SmolVLA shape `(6,)`
- input image: `(3, 96, 96)`
- device: NVIDIA H200
- parameters: 450,046,176
- trainable parameters: 99,880,992
- output action chunk: `(1, 50, 6)`
- first inference total: 491.409 ms
- warmed inference over five repeats: 144.595–145.244 ms
- warmed preprocess: about 0.266–0.360 ms
- allocated CUDA memory: 1,247,069,184 bytes
- weight load time: 13.006 s
- metrics: `03_vla_smolvla/outputs/smolvla_gpu_metrics.json`
- log: `03_vla_smolvla/logs/run_smolvla_gpu_hostgpu.log`

This verifies the complete local checkpoint → tokenizer/preprocessor → GPU action-expert → postprocessor path. It is **not** a semantically meaningful PushT evaluation because SmolVLA's 6-D embodiment does not match PushT's 2-D action space.

## 9. PushT closed-loop rollout

Script: `05_simulation_benchmarks/scripts/rollout_pusht.py`

Intended in-container command:

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/05_simulation_benchmarks
source ../04_lerobot_dataset/.venv/bin/activate
python scripts/rollout_pusht.py
```

Completed GPU fallback run:

- environment: `gym_pusht/PushT-v0`
- 10 episodes per policy
- 300 maximum steps per episode
- seed: 2026
- random policy success rate: 0/10, mean return 1.6239
- tiny policy success rate: 0/10, mean return 12.7285
- random mean final coverage: 0.0
- tiny-policy mean final coverage: 0.008148
- metrics: `05_simulation_benchmarks/outputs/pusht_rollout_summary.json`
- random video: `05_simulation_benchmarks/outputs/pusht_random.mp4`, SHA256 `32b6f98a68ebaceec66a19ec6a6383238f4dd58f129c3329730857ad7ff20253`
- tiny-policy video: `05_simulation_benchmarks/outputs/pusht_tiny_policy.mp4`, SHA256 `19b87509025e969695b53d00222987dc7e77cfd3e1c6bc4bbf08cf49d746e4d9`
- runtime: 14.008 s

Both policies fail the strict task criterion. The tiny policy improves cumulative coverage-oriented return over random, demonstrating that offline action prediction transfers only weakly and that closed-loop evaluation is essential.

## 10. Teaching package

- `docs/WORLDMODEL_EMBODIED_AI_SYLLABUS.md`
- `docs/DREAMER_GUIDE.md`
- `docs/VLA_GUIDE.md`
- `docs/LEROBOT_DATASET_GUIDE.md`
- `docs/GLOSSARY.md`
- `01_video_worldmodel_cosmos/README.md`

The syllabus maps all local artifacts to eight lessons and explicitly distinguishes video prediction, latent control, VLA policies, imitation datasets, and simulation evaluation.
