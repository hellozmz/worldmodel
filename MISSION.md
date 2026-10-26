# Mission: World Models & Embodied AI

## Why

我要把已准备好的 Cosmos、Dreamer/RSSM、SmolVLA、LeRobot PushT 和 gym-pusht 实验，整理成一套能真正学会的课程。目标不是“看过论文”，而是能理解世界模型、策略、VLA、数据与评估之间的边界，并能动手跑通、解读、改进一个具身智能实验。最终以 RoboWorld Challenge 2026 的 WorldNav 赛道为默认 challenge 目标，同时维护 workshop paper / technical report 与 benchmark reproduction 两条可切换出口，把学习成果沉淀为可复现研究组合。

## Success looks like

- 能用一套稳定术语讲清：视频世界模型、latent world model、policy、VLA、imitation dataset、simulation benchmark。
- 能独立阅读 PushT 数据结构，设计不泄漏的 train/validation split。
- 能跑通并解释 Cosmos T2V、tiny RSSM、tiny imitation policy、SmolVLA action chunk、gym-pusht rollout。
- 能指出每个实验的证据边界：接口 smoke test、offline metric、closed-loop success 不能混为一谈。
- 能设计一个新的 world model + embodied AI 实验，并写出假设、指标、baseline、失败判据。
- 能把课程能力迁移到 RoboWorld WorldNav：数据审计、baseline、改进组件、seen/unseen 验证、提交包和技术报告。
- 能为一个实验选择更合理的出口：challenge submission、workshop paper / technical report，或 benchmark / reproduction report。

## Constraints

- 课程以中文讲解，术语中英对照。
- 每课必须包含“知识点 + 实践 + 检索练习”。
- 优先使用本工作区和远端 H200 上已有的模型、数据与结果。
- 参赛目标服务于学习；官方排名不是唯一成功标准，可复现证据链和失败分析同样是核心产出。
- 不要求先掌握全部强化学习理论；遇到必要概念时再补。

## Out of scope

- 不追求一次性复现大规模 DreamerV3 或 Cosmos 全量训练。
- 不把 SmolVLA 直接冒充 PushT 策略。
- 不讨论与具身智能无关的通用 LLM 应用。
