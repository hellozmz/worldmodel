# Dreamer / Latent World Models Study Guide

## 1. Problem setting

A control environment repeatedly supplies:

```text
observation o_t, action a_t, reward r_t, done d_t
```

A world model learns a transition distribution:

```text
(o_t, h_t, a_t) -> belief over o_{t+1}, r_t, d_t
```

Dreamer compresses observations into latent states, learns dynamics in that latent space, then trains an actor-critic policy from imagined latent trajectories. This is cheaper and usually more stable than rolling out full pixels.

## 2. RSSM intuition

Dreamer's recurrent state-space model combines:

- **Deterministic recurrent state** `h_t`, commonly a GRU;
- **stochastic latent** `z_t`;
- **posterior** `q(z_t | o_t, h_t)`, used during training when the observation is available;
- **prior** `p(z_t | h_t)`, used during imagination when no future observation exists;
- **decoders** for observation/reward/done.

Training encourages the prior to match the posterior via KL, while decoders make the latent useful.

## 3. Local teaching implementation

File:

```text
02_dreamer_latent_rl/scripts/train_tiny_worldmodel.py
```

It uses PushT state vectors rather than images:

- observation: 2-D agent position;
- action: 2-D target position in pixel space;
- recurrent hidden size: 128;
- Gaussian latent size: 16;
- sequence length: 32;
- observation/reward/done heads.

Important functions/classes:

- `TinyRSSM.forward`: teacher-forced posterior/prior prediction;
- `TinyRSSM.rollout`: open-loop generation from a prior after the first observation;
- `gaussian_kl`: posterior/prior mismatch;
- `make_windows`: episode-safe sequence extraction;
- `evaluate`: held-out teacher-forced loss.

The saved metrics include final train/validation losses and a 64-step open-loop rollout.

## 4. Loss

The local objective is:

```text
L = observation_mse
    + 0.1 * reward_mse
    + done_bce
    + max(KL, free_nats)
```

`free_nats` prevents spending capacity matching an extremely tiny KL at the start of training.

## 5. Why validation must be episode-based

Nearby frames in one episode are highly correlated. If random frames are split, the model can memorize local trajectories. This workspace keeps whole episodes in train or validation.

## 6. Official family and local source

- DreamerV3 paper: <https://www.nature.com/articles/s41586-025-08744-2>
- DreamerV3 preprint: <https://arxiv.org/abs/2301.04104>
- DreamerV3 code: <https://github.com/danijar/dreamerv3>
- R2-Dreamer source downloaded to `02_dreamer_latent_rl/repos/r2dreamer`
- R2-Dreamer repo: <https://github.com/NM512/r2dreamer>

The official R2-Dreamer environment pins Python `<3.12`, while this workspace's system Python is 3.12. The compact local model is therefore deliberately self-contained.

## 7. Common pitfalls

1. Calling a next-state regressor Dreamer: Dreamer also learns a policy from imagined rollouts.
2. Teacher-forced loss only: open-loop compounding error must be checked separately.
3. Latent collapse: decoder/KL balance and free nats matter.
4. Observation leakage: split by episode.
5. Ignoring action space scaling: normalize states/actions before training.
6. Overclaiming from a toy model: this local model teaches mechanics, not benchmark superiority.

## 8. Exercises

1. Change latent size from 16 to 8/32 and compare validation loss.
2. Plot rollout error at horizons 8/16/32/64.
3. Add an image encoder using the PushT video frames.
4. Add an action head and train it from imagined states.
5. Explain which change would be required to call it a full Dreamer agent.
