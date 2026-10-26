# World Models & Embodied AI Course Outline

目标：把本地/远端已准备好的实验，组织成一门“知识点 + 实践”的课程。每课 15–30 分钟，包含概念、动手任务、自动反馈 quiz、证据解读和下一步。

入口：`lessons/index.html` 是课程总目录，包含课程主线、16 课学习路线和全部参考手册。

整体结构是「总—分—总—延伸」：

1. 0001 建立总框架；
2. 0002–0011 分学数据、想象、行动、VLA；
3. 0012–0014 收束为 capstone / challenge / research portfolio；
4. 0015–0016 补充最新前沿与无真机仿真实验流程。

## Module A — Orientation

### Lesson 0001 — Build the mental map
- 世界模型、策略、VLA、数据集、仿真器的边界
- benchmark、leaderboard、challenge 的区别
- 输入/输出张量视角
- 实践：把 Cosmos、RSSM、SmolVLA、PushT 分类

## Module B — Data

### Lesson 0002 — Read a robot dataset
- LeRobot PushT schema
- observation/action/reward/done
- 实践：解读 25,650 帧、206 episode、图像/状态/动作

### Lesson 0003 — Design non-leaking baselines
- episode-safe split
- action persistence / state / mean baseline
- 实践：解释 tiny policy 指标与 baseline 差距

## Module C — Video world models

### Lesson 0004 — Predict future video
- Cosmos T2V / I2V / action conditioning
- 实践：观察本地 2 秒生成视频与请求参数

### Lesson 0005 — From pixels to latent video
- VAE、diffusion/flow、DiT
- 实践：把视频生成流程拆成组件卡片

## Module D — Latent world models

### Lesson 0006 — Learn an RSSM
- posterior、prior、GRU、decoder、KL/free nats
- 实践：对应 tiny RSSM 训练指标

### Lesson 0007 — Diagnose open-loop rollouts
- teacher forcing vs imagination
- compounding error
- 实践：读 rollout 曲线和 64 步误差

## Module E — Policies

### Lesson 0008 — Train an imitation policy
- state→action MLP
- normalization、优化、验证
- 实践：解读 67,074 参数模型与 19.29px RMSE

### Lesson 0009 — Evaluate in closed loop
- gym-pusht、return、coverage、success
- 实践：比较 random 与 tiny policy 视频/指标
- 实践：套用 interface / offline / closed-loop 三级评价体系

## Module F — VLA

### Lesson 0010 — Inspect a VLA interface
- SmolVLA、action chunk、flow matching
- 实践：解读 `(1, 50, 6)` 输出与延迟/显存

### Lesson 0011 — Detect embodiment mismatch
- 6-D SmolVLA vs 2-D PushT
- adapter、finetune、真实评估
- 实践：判断哪些结论不能外推

## Module G — Integration

### Lesson 0012 — Design your capstone
- world model + policy + benchmark
- hypothesis、baseline、metric、failure criterion
- 实践：写出一页实验设计
- 实践：从外部比赛和 benchmark 中选择下一步验证平台

## Module H — Challenge Output

### Lesson 0013 — Turn the course into a RoboWorld 2026 output
- RoboWorld Challenge 2026 与 RoboPAD @ NeurIPS 2026 的关系
- WorldNav / HA-VLN 2.0 / SafeDrive-VLA 赛道取舍
- 推荐 WorldNav 作为主目标：initial RGB + language → future trajectory
- P0 Decision → P1 Reproduce → P2 Improve → P3 Validate → P4 Submit → P5 Archive
- 实践：建立 `roboworld_2026/` 项目包、立项页和提交计划

## Module I — Research Portfolio

### Lesson 0014 — Build a research and competition portfolio
- Challenge / workshop paper / benchmark reproduction 三条产出线
- RoboWorld WorldNav 是默认 challenge 路线，但不是唯一出口
- R1 offline vs closed-loop mismatch、R2 action controllability、R3 VLA embodiment mismatch、R4 world-model-assisted planning、R5 differentiable / action-conditioned world models
- 最低实验标准：baseline、seed、split、offline/closed-loop、ablation、cost、failure analysis、reproduction
- 实践：建立机会雷达和 `research_portfolio/decision.md`

## Module J — VLA / WAM Frontier

### Lesson 0015 — VLA, WAM, and SuperMimic
- VLA / world model / WAM / SuperMimic / action controllability 的接口边界
- SuperMimic：learned differentiable dynamics、BPTT、短 imagined rollout、motion coverage / training efficiency
- DreamZero：video diffusion WAM、联合未来视频与动作、7Hz closed-loop
- 证据边界：training motions 上的 coverage/scaling 不等于 unseen-task generalization
- 实践：固定 initial state，比较 K 组动作序列的 latent/image/state divergence 与 horizon 曲线

## Module K — Simulation Without Hardware

### Lesson 0016 — Run embodied AI experiments without hardware
- 仿真能提供 environment / action space / reward / success，但不能直接证明真机成功
- CPU 路线：gym-pusht → LeRobot
- GPU 路线：MuJoCo Playground、ManiSkill、Isaac Lab
- 扩展路线：Habitat、CALVIN、LIBERO、BEHAVIOR
- P0 Choose → P1 Install → P2 Smoke → P3 Schema → P4 Split → P5 Baselines → P6 Offline → P7 Closed-loop → P8 Model → P9 Cost/Failure → P10 Report
- 实践：产出 lock 文件、smoke 视频、schema 文档、split JSON、baseline 表、闭环 JSON、成本与失败案例

## Reference Pages

### 基本介绍
- 一句话定义 world model、embodied AI、policy、VLA、benchmark、challenge
- perception → world model → planning/policy → action → environment 闭环
- video world model、latent world model、VLA policy 三条路线

### 评价体系
- interface smoke test / offline metric / closed-loop evaluation
- PSNR、SSIM、LPIPS、FVD、rollout error、temporal consistency
- success、return、coverage、SPL、action MSE、latency、safety
- episode-safe split、seed、baseline、泛化、算力与失败判据

### 比赛与 Benchmark 地图
- 导航与通用具身智能：Embodied AI Workshop、AI Habitat、BEHAVIOR
- 机械臂操作：CALVIN、LIBERO、Meta-World、PushT/LeRobot
- 无真机仿真：gym-pusht、LeRobot、MuJoCo Playground、ManiSkill、Isaac Lab
- 世界模型：WorldModelBench、WorldArena、DeepMind Control Suite
- 真机与平台：RoboChallenge、RoboVerse、LeRobot

### RoboWorld Challenge 2026
- 课程默认目标产出活动
- WorldNav 主目标：SR、ATE、RPE、full-route fidelity、heading / turn fidelity
- HA-VLN 2.0 进阶目标：closed-loop RGB-D、动态行人、social compliance
- SafeDrive-VLA 观察目标：CARLA 安全指令与 instruction-scene conflict
- 项目模板见 `ROBOWORLD_2026_PLAN.md`

### Research & Competition Portfolio
- Challenge、paper/report、benchmark/reproduction 三线并行与切换策略
- AGIBOT WORLD、RoboChallenge、GigaBrain、Embodied AI Workshop、WorldModelBench、WorldArena 等入口
- OpenReview、CodaBench、EvalAI、arXiv、Papers with Code 等发现渠道
- 项目模板见 `RESEARCH_PORTFOLIO_PLAN.md`
