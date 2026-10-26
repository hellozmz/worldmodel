# World Models & Embodied AI Glossary

本课程统一使用的核心语言。随着学习推进，术语会逐步扩充和收紧。

## Terms

**World model**:
学习环境状态、动作与未来观测/奖励之间关系的模型。
_Avoid_: 环境模拟器、万能预测器

**Policy**:
从观测或历史映射到动作的决策函数。
_Avoid_: 模型、控制器混用

**VLA**:
Vision-Language-Action model，把图像、语言和机器人状态映射为动作或动作块。
_Avoid_: 视觉语言模型、通用机器人大脑

**Embodied AI**:
智能体通过感知、决策、动作与物理或仿真环境交互，并把环境反馈作为下一轮输入。
_Avoid_: 有摄像头的聊天机器人

**Benchmark**:
固定任务、数据划分、指标和比较规则的实验协议。
_Avoid_: 数据集、比赛混称

**Challenge / Competition**:
在规定时间内提交结果，并按官方指标排名的活动；任务和规则可能每届变化。
_Avoid_: 与永久 benchmark 混称

**RSSM**:
Recurrent State-Space Model，用确定性格点与随机 latent 组合表示状态并学习动态。
_Avoid_: RNN、世界模型混称

**Action chunk**:
一次推理输出的连续多步动作。
_Avoid_: 动作序列、轨迹混用

**Embodiment mismatch**:
模型训练时的机器人形态、传感器或动作空间与部署环境不一致。
_Avoid_: 域差距泛化成一切问题

**Episode-safe split**:
按 episode 划分训练/验证，避免相邻高度相关帧同时出现在两边。
_Avoid_: 随机切分、IID 假设

**Closed-loop evaluation**:
策略自己产生的动作影响后续观测，并在环境中连续评估。
_Avoid_: 离线指标外推

**Interface smoke test**:
只验证依赖、输入输出形状、设备和推理流程是否跑通，不证明任务性能。
_Avoid_: 证明模型已学会任务

**Offline metric**:
在留出数据上计算的预测误差或感知指标，例如 MSE、PSNR、SSIM、LPIPS、FVD。
_Avoid_: 用它直接等同闭环成功

**Rollout error vs horizon**:
预测步数增加时误差如何累积；比单步 teacher-forced loss 更能反映 world model 可用性。
_Avoid_: 只报告一个 validation loss

**Research portfolio**:
把同一套实验能力组织成 challenge、paper/report 和 benchmark reproduction 三个可切换出口。
_Avoid_: 把学习目标绑定在单一比赛截止日期上

**Technical report**:
面向可复现证据链的技术报告，可包含协议、baseline、消融、失败分析和 limitations，不必须是完整会议论文。
_Avoid_: 与宣传材料混称

**Benchmark / reproduction report**:
说明固定协议、环境、配置、命令、baseline 和误差来源的报告，目标是让别人复现并判断结果边界。
_Avoid_: 只贴一个最好分数

**Negative result**:
在清晰协议下没有得到预期改进，但能排除一种解释或揭示评估陷阱的结果。
_Avoid_: 等同于失败或没有价值
