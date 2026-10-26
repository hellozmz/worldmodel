# World Models & Embodied AI Resources

## Knowledge

- [Paper: DreamerV3 — Mastering diverse control tasks through world models](https://www.nature.com/articles/s41586-025-08744-2)
  DreamerV3 的正式论文，用于理解 latent world model + actor-critic 的完整闭环。
- [Repo: danijar/dreamerv3](https://github.com/danijar/dreamerv3)
  官方实现，适合把论文概念落到代码结构。
- [Repo: NM512/r2dreamer](https://github.com/NM512/r2dreamer)
  R2-Dreamer 实现，用于进阶比较 decoder-free / redundancy-reduced world model。
- [Paper: NVIDIA Cosmos](https://arxiv.org/abs/2501.03575)
  理解视频世界模型、生成式仿真与物理 AI 的关系。
- [Blog: Genie 3](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models)
  交互式生成环境的最新视角，用于对比“可玩世界”与“机器人可执行世界”。
- [Paper: V-JEPA 2](https://arxiv.org/abs/2506.09985)
  自监督视频表征与 action-conditioned world model 的代表工作。
- [Paper: RT-2](https://arxiv.org/abs/2307.15818)
  VLA 从互联网级 VLM 知识迁移到机器人动作的早期关键工作。
- [Paper: OpenVLA](https://arxiv.org/abs/2406.09246)
  开源 7B VLA 与大规模机器人数据训练范式。
- [Paper: π0](https://arxiv.org/abs/2410.24164)
  Flow matching 与通用机器人控制的结合。
- [Paper: SmolVLA](https://arxiv.org/abs/2506.01844)
  小型、可负担 VLA 的代表，直接对应本地实验。
- [Project / Paper: SuperMimic](https://supermimic.github.io) / [arXiv:2610.28480](https://arxiv.org/abs/2610.28480)
  一个 learned differentiable world model 用于 humanoid whole-body control；注意官方结果主要证明 motion coverage、scaling 与训练效率，不等价于 unseen-task generalization。
- [Paper: World-Action Models for Robot Learning and Control](https://arxiv.org/abs/2609.16074)
  WAM 综述：future world prediction 与 executable action generation 的耦合、分类、应用和挑战。
- [Paper: World Action Models are Zero-shot Policies / DreamZero](https://arxiv.org/abs/2602.15922)
  video diffusion backbone 联合建模未来视频与动作的 WAM 代表。
- [Paper: Do Robotic World Models Really Follow Actions?](https://arxiv.org/abs/2608.24885)
  action-conditioned world model 在 expert 与 off-expert 动作分布上的可控性诊断。
- [Repo: Hugging Face LeRobot](https://github.com/huggingface/lerobot)
  机器人学习代码库与数据集生态，本地 PushT 实验直接基于它。
- [Dataset: lerobot/pusht](https://huggingface.co/datasets/lerobot/pusht)
  本课程的数据与闭环任务来源。

## Simulation Without Hardware

- [gym-pusht](https://github.com/huggingface/gym-pusht)
  CPU 友好的 PushT Gymnasium 环境；2D action、state observation、coverage reward、95% success 阈值。
- [LeRobot installation](https://huggingface.co/docs/lerobot/en/installation)
  官方安装路线，包含 Python 3.12、可选 extras、PushT simulation extra 和平台注意事项。
- [MuJoCo Playground](https://github.com/google-deepmind/mujoco_playground)
  基于 MuJoCo MJX 的 GPU 加速 robot learning 与 sim-to-real 环境。
- [ManiSkill](https://github.com/mani-skill/ManiSkill)
  GPU-parallel manipulation 框架；Linux + NVIDIA 支持最完整，并提供 Colab 入口。
- [Isaac Lab](https://isaac-sim.github.io/IsaacLab)
  NVIDIA Isaac Sim 上的模块化 robot learning 框架，覆盖 RL、learning from demonstrations、motion planning、domain randomization 与 cloud workflows。
- [Habitat-Lab](https://github.com/facebookresearch/habitat-lab)
  3D 导航与具身智能仿真实验框架。
- [CALVIN](https://github.com/mees/calvin)
  language-conditioned long-horizon manipulation benchmark。
- [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO)
  lifelong robot learning benchmark。
- [BEHAVIOR-1K](https://github.com/StanfordVL/BEHAVIOR-1K)
  长时序家庭活动与日常任务仿真 benchmark。

## Wisdom (Communities)

- [LeRobot GitHub Discussions](https://github.com/huggingface/lerobot/discussions)
  适合讨论数据格式、policy 复现、训练配置和硬件接入。
- [Hugging Face Forums](https://discuss.huggingface.co/)
  适合追问模型卡、Transformers/LeRobot 集成和训练细节。
- Local lab: `h200_1727` / `zmz_dev_v2` workspace
  适合把课程中的假设放进真实 GPU 与仿真实验中验证。

## Evaluation & Benchmarks

- [RoboWorld Challenge 2026](https://roboworld2026.github.io)
  课程默认目标产出活动；推荐 WorldNav 主目标、HA-VLN 2.0 进阶目标。
- [WorldNav Track](https://roboworld2026.github.io/track1.html)
  initial RGB + language → future trajectory；官方指标 SR、ATE、RPE、full-route fidelity、heading / turn fidelity。
- [WorldNav GitHub](https://github.com/roboworld2026/track1)
  WorldNav 官方代码库入口。
- [WorldNav CodaBench](https://www.codabench.org/competitions/18135/)
  WorldNav 提交入口；使用前核对当届规则。
- [HA-VLN 2.0 Track](https://roboworld2026.github.io/track2.html)
  closed-loop RGB-D 社会导航；关注动态行人、碰撞率和 social compliance。
- [SafeDrive-VLA Track](https://roboworld2026.github.io/track3.html)
  CARLA 安全驾驶与 instruction-scene conflict；适合作为观察和进阶方向。
- [Course reference: RoboWorld 2026](reference/roboworld-2026.html)
  课程内目标产出、赛道取舍、项目包模板和五阶段里程碑。
- [Course plan: ROBOWORLD_2026_PLAN.md](ROBOWORLD_2026_PLAN.md)
  从课程学习到参赛提交的详细执行计划。
- [Course reference: Research & Competition Portfolio](reference/research-competition-portfolio.html)
  Challenge、workshop paper / technical report、benchmark / reproduction 三条产出线与机会筛选表。
- [Course plan: RESEARCH_PORTFOLIO_PLAN.md](RESEARCH_PORTFOLIO_PLAN.md)
  5 个研究问题、2/6/12 周里程碑、最低实验标准和停止/切换条件。

- [Course reference: evaluation-system](reference/evaluation-system.html)
  课程内的评价体系速查：interface / offline / closed-loop、world model 指标、policy 指标和实验检查表。
- [Course reference: benchmark-map](reference/benchmark-map.html)
  课程内的比赛与 benchmark 地图：导航、操作、世界模型、真机平台和参赛检查表。
- [Embodied AI Workshop](https://embodied-ai.org)
  具身智能方向的主流 workshop 与 challenge 入口。
- [AI Habitat](https://aihabitat.org)
  3D 室内导航仿真与相关 challenge。
- [BEHAVIOR](https://behavior.stanford.edu/index.html)
  长时序家庭活动 benchmark；[Challenge 页面](https://behavior.stanford.edu/challenge/index.html)。
- [CALVIN](http://calvin.cs.uni-freiburg.de)
  language-conditioned long-horizon manipulation；[GitHub](https://github.com/mees/calvin)。
- [LIBERO](https://libero-project.github.io)
  lifelong robot learning 与知识迁移 benchmark。
- [Meta-World](https://meta-world.github.io)
  multi-task / meta-RL manipulation；[GitHub](https://github.com/Farama-Foundation/Metaworld)。
- [WorldModelBench](https://worldmodelbench.github.io)
  world model 评估相关 workshop / benchmark。
- [WorldArena](https://world-arena.ai)
  embodied world model 评估；[GitHub](https://github.com/tsinghua-fib-lab/WorldArena)。
- [RoboChallenge](https://robochallenge.ai)
  real-robot benchmark 与 policy evaluation。
- [RoboVerse](https://roboverseorg.github.io)
  统一机器人学习平台 / benchmark。

## Research & Competition Discovery

- [AGIBOT WORLD Challenge 2026](https://agibot-world.com/challenge2026)
  open-world understanding、manipulation、world modeling 与 Sim2Real；核对当届阶段是否仍开放。
- [RoboChallenge](https://robochallenge.ai)
  robot foundation models、VLA、policy evaluation 与 long-horizon robot tasks。
- [GigaBrain Challenge 2026](https://gigaai-research.github.io/GigaBrain-Challenge-2026)
  world model empowered VLA、simulation、real-world evaluation 与 agentic embodied demos。
- [CoRL Workshops](https://www.corl.org/program/workshops)
  robot learning、world models、manipulation 与 learned simulation 的 workshop / challenge 入口。
- [OpenReview](https://openreview.net)
  查 workshop CFP、审稿标准、接收论文和常见问题定义。
- [CodaBench](https://www.codabench.org) / [EvalAI](https://eval.ai)
  按 robotics、embodied AI、world model 等关键词追踪公开比赛。
- [arXiv](https://arxiv.org) / [Papers with Code](https://paperswithcode.com)
  追踪新方法、代码、数据集和 baseline；优先回到官方论文和官方实现。

## Gaps

- 课程已经建立三级评价体系、benchmark 地图和研究组合；仍需要随着活动更新，定期核对官方 challenge / workshop 的当届任务、指标和截止日期。
