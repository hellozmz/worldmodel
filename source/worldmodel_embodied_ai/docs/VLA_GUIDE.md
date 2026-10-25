# VLA / SmolVLA Study Guide

## 1. What is a VLA?

A Vision-Language-Action model maps multimodal observations and a language instruction to robot actions:

```text
(images, proprioception, task text) -> action or action chunk
```

Unlike an explicit world model, a VLA's visible output is action. It may inherit world knowledge from a pretrained VLM, but that does not automatically mean it predicts future observations.

## 2. SmolVLA in one page

SmolVLA is a compact open VLA built around a small VLM backbone plus an action expert. Its LeRobot checkpoint is about 450M parameters and outputs an action chunk.

Local checkpoint:

```text
03_vla_smolvla/models/smolvla_base
```

Local tokenizer:

```text
03_vla_smolvla/models/smolvlm2_tokenizer
```

Config highlights:

- state input: 6 dimensions;
- action output chunk: `(batch, 50, 6)`;
- possible cameras: `camera1`, `camera2`, `camera3`;
- flow-matching action expert;
- VLM reference: `HuggingFaceTB/SmolVLM2-500M-Video-Instruct`.

Paper: <https://arxiv.org/abs/2506.01844>; project blog: <https://huggingface.co/blog/smolvla>.

## 3. Local GPU interface test

Script:

```text
03_vla_smolvla/scripts/run_smolvla_gpu.py
```

It performs:

1. load a local PushT frame;
2. pad PushT's 2-D state to SmolVLA's expected 6-D state;
3. use PushT image as `camera1`;
4. load the local SmolVLA checkpoint and tokenizer;
5. load the official preprocessor/postprocessor normalization pipeline;
6. run GPU action-chunk inference;
7. save latency, action statistics, parameter count, and CUDA memory.

This is an **interface and shape test**, not a valid PushT performance evaluation.

## 4. Embodiment mismatch

SmolVLA base expects a 6-D action space from its training embodiment. PushT has a 2-D absolute position action. Padding state gives numerical tensors, but the extra dimensions are meaningless. Executing a 6-D SmolVLA action directly in PushT is invalid.

To do a meaningful SmolVLA robotics evaluation, use:

- an embodiment matching the checkpoint;
- a finetuning dataset with the same state/action format;
- held-out tasks and real or simulated closed-loop evaluation.

## 5. Related systems

- RT-2 showed web-scale VLM knowledge can transfer to robotic action tokens: <https://arxiv.org/abs/2307.15818>
- OpenVLA is a 7B open VLA trained on diverse robot data: <https://arxiv.org/abs/2406.09246>
- π0 uses a VLM plus flow matching for general robot control: <https://arxiv.org/abs/2410.24164>
- SmolVLA targets affordable/efficient robotics: <https://arxiv.org/abs/2506.01844>

## 6. Concepts to master

- proprioceptive state;
- camera coordinate and image normalization;
- action chunking;
- flow matching versus deterministic regression;
- tokenizer/language prompt;
- preprocessor and postprocessor statistics;
- train/eval embodiment consistency;
- offline loss versus closed-loop success.

## 7. Exercises

1. Print every tensor shape before and after preprocessing.
2. Measure first-run and warmed-up latency.
3. Change the task sentence and quantify action sensitivity.
4. Find the exact action normalization statistics in the saved processor state.
5. Explain why a 2-D PushT action cannot be compared with a 6-D SmolVLA action.
