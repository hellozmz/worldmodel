# RoboWorld Challenge 2026 学习与产出计划

## 目标

把本课程从“学习 world model / VLA / embodied policy”升级为一个明确产出：

> 形成一个可复现的 RoboWorld 2026 WorldNav 项目包，包含数据审计、baseline、改进实验、验证结果、失败分析和官方提交记录。

主目标：**WorldNav**

进阶目标：**HA-VLN 2.0**

观察目标：**SafeDrive-VLA**

> 这份计划是研究组合中的默认 Challenge Track，不是唯一出口。若官方窗口、数据或规则不匹配，实验证据可切换到 workshop paper / technical report 或 benchmark reproduction；见 `RESEARCH_PORTFOLIO_PLAN.md`。

选择理由：

1. WorldNav 的任务形式是“初始 RGB + 语言指令 → 未来轨迹”，与课程的 perception / world model / policy 主线最一致。
2. 官方允许 world model、VLA 和 policy-only 方法，适合从简单 baseline 逐步升级。
3. HA-VLN 2.0 更贴近闭环与社会性导航，可作为第二阶段挑战。
4. SafeDrive-VLA 数据体量大、领域差异明显，不建议作为第一参赛目标。

## 官方入口

- 主页：<https://roboworld2026.github.io>
- 注册：<https://forms.gle/P2jH3c2VoGsNNWXG8>
- WorldNav：<https://roboworld2026.github.io/track1.html>
- WorldNav GitHub：<https://github.com/roboworld2026/track1>
- WorldNav CodaBench：<https://www.codabench.org/competitions/18135/>
- HA-VLN 2.0：<https://roboworld2026.github.io/track2.html>
- HA-VLN 2.0 GitHub：<https://github.com/roboworld2026/track2>
- HA-VLN 2.0 CodaBench：<https://www.codabench.org/competitions/18185/>
- SafeDrive-VLA：<https://roboworld2026.github.io/track3.html>
- SafeDrive-VLA GitHub：<https://github.com/ASGuard-UCI/safedrive-vla>
- SafeDrive-VLA CodaBench：<https://www.codabench.org/competitions/18333/>

> 官方时间线页面目前按阶段描述，不在此处猜测具体日期。所有报名、数据、提交和截止信息以官网为准。

## 学习路线

### Stage 0 — 课程基础

目标：建立概念与评价纪律。

- Lesson 0001：world model / policy / VLA / benchmark / challenge 边界
- Reference：basic-introduction
- Reference：evaluation-system

产出：

- 一页概念图
- 明确“我准备采用 world model、VLA 还是 policy-only 路线”

### Stage 1 — 数据与 baseline

目标：先跑通，不急于创新。

- Lesson 0002：数据 schema
- Lesson 0003：episode-safe split 与 baseline
- Lesson 0008：imitation policy

迁移到 WorldNav：

- 审计 LCVN 字段、轨迹长度、动作单位、语言类型
- 确认 training / seen validation / unseen validation split
- 复现官方或最小 vision-language → trajectory baseline

产出：

```text
data/schema_audit.md
baselines/reproduce.md
baselines/metrics.json
```

### Stage 2 — World model 组件

目标：让“想象未来”变成可检验组件，而不是口号。

- Lesson 0004：Cosmos 视频生成
- Lesson 0005：VAE / diffusion / attention
- Lesson 0006：RSSM
- Lesson 0007：open-loop rollout 误差

可选实验：

1. 用 latent predictor 预测 future representation。
2. 对比有/无 future prediction 的轨迹模型。
3. 分析 rollout 误差随 horizon 的变化。

产出：

```text
experiments/hypothesis.md
experiments/rollout_analysis.md
```

### Stage 3 — VLA 与动作空间

目标：检查接口与语义是否真正匹配。

- Lesson 0010：SmolVLA action chunk
- Lesson 0011：embodiment mismatch

检查项：

- action 维度
- 位移与角度单位
- 坐标系
- 控制频率
- Stop / null action 定义
- 训练数据 embodiment 与 WorldNav 是否一致

产出：

```text
experiments/action_space_audit.md
```

### Stage 4 — 验证与失败分析

目标：用官方指标反推方法缺陷。

- Lesson 0009：closed-loop vs offline
- Reference：evaluation-system

WorldNav 指标：

- Success Rate
- Absolute Trajectory Error
- Relative Pose Error
- Full-route fidelity
- Heading / turn fidelity

至少分析：

1. 成功与失败案例各 10 个
2. 短指令 vs 长指令
3. seen vs unseen 环境
4. 转向错误与位移错误
5. Stop 过早 / 过晚

产出：

```text
experiments/ablation.md
experiments/failure_analysis.md
report/RoboWorld_Report.md
```

### Stage 5 — 提交与复现包

目标：让结果可复现、可比较、可继续迭代。

- Lesson 0012：capstone 设计
- Lesson 0013：RoboWorld 产出

产出：

```text
submission/run.sh
submission/predictions/
submission/submission_log.md
report/slides.md
```

## 最小可行项目

如果时间不足，不要同时追三个赛道。只做 WorldNav 的 MVP：

1. 注册团队，阅读规则。
2. 下载最小可训练子集。
3. 复现一个 baseline。
4. 增加一个明确改进。
5. 报告 seen / unseen validation。
6. 生成提交文件。
7. 写 5 页技术报告。

## 成功标准

学习成功不等于排行榜第一。以下任一达成即可视为有效产出：

- 完整提交一次官方结果；
- 完成可复现项目包并通过队友复现；
- 在 unseen validation 上做出有消融支撑的改进；
- 形成高质量失败分析，明确下一版方法；
- 输出公开技术报告或课程项目展示。

## 红线

- 不把 PushT 成绩外推为 RoboWorld 成绩。
- 不把 offline 指标说成闭环任务成功。
- 不把 SmolVLA 接口跑通说成学会 RoboWorld。
- 不使用规则禁止的外部数据或测试标签。
- 不只保存最好分数，必须保留失败实验记录。
