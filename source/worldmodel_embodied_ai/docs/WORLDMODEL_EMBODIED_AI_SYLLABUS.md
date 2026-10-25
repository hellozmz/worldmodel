# World Models & Embodied AI: 8-Lesson Study Plan

All paths below are inside `/mnt/models_2296/zmz/workspace/worldmodel_embodied_ai`. The workspace is organized by technical role, not merely by model name.

## Map of the field

| Direction | Core question | Local track | Example systems |
|---|---|---|---|
| Generative video world models | Can we predict future pixels? | `01_video_worldmodel_cosmos` | Cosmos, Genie, Sora-like models |
| Latent world models for control | Can a compact predicted state support action learning? | `02_dreamer_latent_rl` | DreamerV3, R2-Dreamer, V-JEPA-style objectives |
| Vision-Language-Action policies | Can perception plus language directly produce actions? | `03_vla_smolvla` | RT-2, OpenVLA, π0, SmolVLA |
| Robot datasets / imitation | What trajectories are available, and what do they teach? | `04_lerobot_dataset` | LeRobot datasets, Open X-Embodiment |
| Simulation & evaluation | Is the policy useful beyond offline loss? | `05_simulation_benchmarks` | PushT, DMC, Meta-World |

A useful mental model:

- **World model**: predicts consequences (`s', r, done` or future video).
- **Policy**: chooses an action (`a`).
- **VLA**: often a policy, sometimes with an internal world-like representation, but its public interface is action prediction.
- **Dataset**: experience for imitation or model training.
- **Simulator**: ground truth for closed-loop evaluation.

## Lesson 1 — Orientation and vocabulary

**Goal**: distinguish observation, action, reward, done, policy, world model, online RL, offline imitation, and embodiment.

Read `GLOSSARY.md`, then inspect:

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai
find . -maxdepth 3 -type f | sort | less
```

Checkpoint questions:

1. Why is a next-frame predictor not automatically a controller?
2. Why can a low offline action loss still fail in a simulator?
3. What is an embodiment mismatch?

## Lesson 2 — Dataset literacy: LeRobot PushT

**Goal**: understand a robot-learning dataset before training anything.

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/04_lerobot_dataset
source .venv/bin/activate
python scripts/analyze_pusht.py
```

Study `analysis/pusht_summary.json`, the contact sheet, and trajectory plot. Details are in `docs/LEROBOT_DATASET_GUIDE.md`.

Core idea: split by episode. Random frame splitting leaks near-duplicate neighboring frames into validation.

## Lesson 3 — Video world models with Cosmos3-Nano

**Goal**: see future prediction in pixel/video space.

Open the prior generated video:

```text
/mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel/outputs/worldmodel_t2v_20261024_192234.mp4
```

Read `01_video_worldmodel_cosmos/README.md`. Focus on quality versus controllability: a beautiful video is not yet an action policy.

## Lesson 4 — Dreamer-style latent world models

**Goal**: understand recurrent state-space models (RSSMs).

Read `docs/DREAMER_GUIDE.md`, then walk the compact implementation:

```text
02_dreamer_latent_rl/scripts/train_tiny_worldmodel.py
```

Concepts to identify in code:

- posterior encoder;
- prior/transition predictor;
- GRU recurrent state;
- KL/free-nats objective;
- observation, reward, and done decoders;
- open-loop rollout.

The local run is a teaching-sized approximation, not official DreamerV3/R2-Dreamer performance.

## Lesson 5 — Imitation policy and baselines

**Goal**: train a transparent policy and avoid overclaiming.

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/04_lerobot_dataset
source .venv/bin/activate
python scripts/train_tiny_policy.py
```

Compare validation MSE with:

- action equals current state;
- action equals training mean;
- action equals previous action.

A state-only MLP cannot infer the T-block goal unless it is encoded in the observation; this experiment is a baseline, not a serious PushT solution.

## Lesson 6 — Closed-loop evaluation in PushT

**Goal**: test whether offline learning survives environment feedback.

```bash
cd /mnt/models_2296/zmz/workspace/worldmodel_embodied_ai/05_simulation_benchmarks
source ../04_lerobot_dataset/.venv/bin/activate
python scripts/rollout_pusht.py
```

Compare random and tiny-policy success rate, return, coverage, and videos. Closed-loop rollout is the key reality check.

## Lesson 7 — VLA and SmolVLA

**Goal**: understand action chunking and language/image conditioning.

Read `docs/VLA_GUIDE.md`. The local SmolVLA run verifies the full checkpoint/preprocessor/inference path and records GPU latency, but intentionally does **not** claim PushT competence because PushT's 2-D state/action is padded into SmolVLA's 6-D embodiment.

## Lesson 8 — Putting it together

Build a one-page project table:

1. Input observation;
2. Action space;
3. Whether future prediction is explicit;
4. Offline metric;
5. Closed-loop metric;
6. Generalization/embodiment assumptions;
7. Failure mode.

Propose one experiment that combines a world model with a policy, then identify the exact evaluation needed before believing it.

## Reading list

- DreamerV3: [Nature 2025](https://www.nature.com/articles/s41586-025-08744-2), [arXiv](https://arxiv.org/abs/2301.04104), [official repo](https://github.com/danijar/dreamerv3)
- R2-Dreamer: [GitHub](https://github.com/NM512/r2dreamer)
- Cosmos: [arXiv](https://arxiv.org/abs/2501.03575)
- Genie 3: [DeepMind blog](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models)
- V-JEPA 2: [Meta](https://ai.meta.com/blog/v-jepa-2-world-model-benchmarks), [arXiv](https://arxiv.org/abs/2506.09985)
- RT-2: [arXiv](https://arxiv.org/abs/2307.15818)
- OpenVLA: [arXiv](https://arxiv.org/abs/2406.09246)
- π0: [arXiv](https://arxiv.org/abs/2410.24164)
- SmolVLA: [arXiv](https://arxiv.org/abs/2506.01844), [HF blog](https://huggingface.co/blog/smolvla)
- LeRobot: [GitHub](https://github.com/huggingface/lerobot)
- PushT dataset: [Hugging Face](https://huggingface.co/datasets/lerobot/pusht)

## Weekly cadence suggestion

- Day 1: read guide and draw tensors/architecture.
- Day 2: inspect artifacts and logs.
- Day 3: rerun one script with one changed variable.
- Day 4: write a short result note, including what the metric cannot prove.
- Day 5: read one paper and connect it to the local implementation.
