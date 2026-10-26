# Research & Competition Portfolio Plan

更新日期：2026-10-26

## 目标

把课程中的 Cosmos、PushT、RSSM、SmolVLA 和闭环评估实验，组织成一个可并行退出的研究组合，而不是只依赖单一比赛窗口。

```text
Research & Competition Portfolio
├── Challenge Track              # RoboWorld WorldNav 默认路线，也可替换为其他当届开放活动
├── Paper / Report Track         # workshop paper、technical report、负结果报告
└── Benchmark / Reproduction     # 公开协议、baseline、复现命令、结果表
```

## 三条产出线

| Track | 核心问题 | 最小交付物 | 当前状态 |
|---|---|---|---|
| Challenge | 官方指标是否提高？提交是否合法？ | 规则记录、baseline、validation、submission log、报告 | RoboWorld WorldNav 是默认路线 |
| Paper / report | claim 是否清楚，证据是否足够？ | 问题定义、协议、baseline、seed、ablation、failure analysis | 先从 R1–R4 中选择一个问题 |
| Benchmark / reproduction | 别人能否复现？误差来自哪里？ | 协议、环境、配置、命令、结果表、敏感性分析 | PushT/RSSM/SmolVLA 证据链已具备雏形 |

## 推荐研究问题

### R1 · Offline / closed-loop mismatch

问题：为什么 offline action MSE 或 rollout MSE 改善，闭环 success 仍然可能不改善？

现有证据：tiny imitation policy 在 offline 验证集上优于 random，但 10 次 PushT 闭环 success 均为 0。

最小扩展：

- random / previous action / tiny policy / stronger baseline
- 3 seeds
- rollout horizon 曲线
- seen / unseen split
- distribution shift 与 failure taxonomy

候选题目：`When Offline Prediction Improves but Closed-Loop Control Fails: An Evidence-Hierarchy Study for Embodied World Models`

### R2 · Action controllability

问题：world model 是否真正根据动作改变预测未来，还是只学习轨迹平滑性？

最小扩展：

- 固定初始状态，改变动作序列
- 比较 future latent / image / state divergence
- action-conditioned vs unconditional predictor
- divergence vs horizon 曲线

候选题目：`Measuring Action Controllability in Video and Latent World Models`

### R3 · VLA embodiment mismatch

问题：接口形状匹配是否等于机器人形态、传感器和动作语义匹配？

现有证据：SmolVLA 输出 `(1, 50, 6)`，PushT action 是 2-D；本地结果只能作为 interface smoke test。

最小扩展：

- action-space audit：维度、单位、坐标系、频率、Stop 语义
- zero-shot / adapter / finetune 对照
- closed-loop 指标
- latency、显存和吞吐

候选题目：`Interface Success Is Not Embodiment Success: Evaluating VLA Transfer Under Action-Space Mismatch`

### R4 · World-model-assisted planning

问题：RSSM 想象未来能否帮助选择更好的动作？

路线：

```text
state/image
  ↓
RSSM latent rollout
  ↓
candidate action sequences
  ↓
imagined future scoring
  ↓
choose action
  ↓
gym-pusht closed-loop evaluation
```

这是最贴近世界模型主线、也最适合升级成 challenge / paper 双出口的方向。

## 里程碑

### Week 0–2：证据整理

- 固化当前 PushT、RSSM、SmolVLA 的配置、命令、seed 和 JSON 指标。
- 补齐 random / previous action / tiny policy 对照表。
- 建立失败案例库：成功、失败、崩溃、shape mismatch、distribution shift。
- 产出 `research_portfolio/README.md` 与 `decision.md`。

### Week 3–6：单问题深化

- 从 R1–R4 中只选一个问题。
- 增加 stronger baseline 和 3 seeds。
- 完成一个关键 ablation。
- 报告 offline、closed-loop、latency、显存和训练时长。
- Challenge 线继续执行 RoboWorld P0–P5，但共享数据审计和失败分析。

### Week 7–12：外部出口

- 若官方 challenge 窗口可用：提交并记录分数变化。
- 若窗口不可用或数据不匹配：整理 workshop paper / technical report。
- 无论是否提交比赛：完成 benchmark reproduction report。
- 公开图表、表格、复现命令和 limitations。

## Portfolio 目录

```text
research_portfolio/
├── README.md
├── decision.md
├── challenge_track/
│   ├── roboworld/
│   ├── other_challenge/
│   └── submission_log.md
├── paper_track/
│   ├── main.md
│   ├── figures/
│   ├── tables/
│   ├── experiments.json
│   ├── reproduction.md
│   └── limitations.md
├── benchmark_track/
│   ├── protocol.md
│   ├── baselines.md
│   ├── results.json
│   └── report.md
└── archive/
    ├── rejected_ideas.md
    └── negative_results.md
```

## 最低实验标准

- 至少 3 个 baseline
- 至少 3 个正式 seed
- episode-safe train / validation / test split
- seen 与 unseen 结果分列
- offline 与 closed-loop 指标分列
- 关键组件 ablation
- latency、显存、训练时长
- 失败案例分类
- 精确命令、配置、环境版本和随机种子

## 停止或切换条件

- 数据下载、授权或存储不可承受：转公开小规模 benchmark。
- baseline 无法在合理时间复现：先转 reproduction report，不做方法创新。
- 闭环环境不可用：只报告 offline 证据，并明确不能声称控制成功。
- 指标不随核心组件变化：保留负结果，写 failure analysis。
- deadline 不够三轮实验：转下一届或 technical report。
- 同时出现两个吸引人的新想法：归档到 `rejected_ideas.md`，当前周期不并行。

## 机会发现渠道

- RoboWorld Challenge：<https://roboworld2026.github.io>
- AGIBOT WORLD Challenge：<https://agibot-world.com/challenge2026>
- RoboChallenge：<https://robochallenge.ai>
- GigaBrain Challenge：<https://gigaai-research.github.io/GigaBrain-Challenge-2026>
- Embodied AI Workshop：<https://embodied-ai.org>
- WorldModelBench：<https://worldmodelbench.github.io>
- WorldArena：<https://world-arena.ai>
- CoRL workshops：<https://www.corl.org/program/workshops>
- OpenReview：<https://openreview.net>
- CodaBench：<https://www.codabench.org>
- EvalAI：<https://eval.ai>
- arXiv：<https://arxiv.org>
- Papers with Code：<https://paperswithcode.com>

> 截至 2026-10-26，部分 2026 会议、workshop 或 ICRA/CVPR 周期可能已经结束。本文件不维护实时 deadline；报名或投稿前必须核对官方页面。

## 与 RoboWorld 的关系

RoboWorld WorldNav 仍是默认 challenge 出口，因为它与课程的 vision + language + future trajectory 主线最贴近。Portfolio 的作用不是削弱这个目标，而是确保：

1. 官方窗口、数据或规则变化时，成果仍有报告出口；
2. 实验证据能沉淀为可复用 benchmark 结论；
3. 研究问题、比赛提交和技术报告共享同一套代码和失败分析。
