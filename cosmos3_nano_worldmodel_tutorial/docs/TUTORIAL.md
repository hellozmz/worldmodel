# Cosmos3-Nano 世界模型学习教程

> 面向目标：理解“世界模型是什么、Cosmos3 怎么做、一次推理流程发生了什么、如何设计自己的实验”，并能在当前 H200 环境中复现和扩展。

> 当前工作区已经跑通一次 T2V 世界模型 smoke test：`outputs/worldmodel_t2v_20261024_192234.mp4`（448×256、25 帧、12 fps）。详细耗时、显存与哈希见 `docs/RUN_LOG.md`。

## 0. 术语速查

| 术语 | 一句话解释 |
|---|---|
| Observation / 观测 | 传感器看到的画面、音频或状态，例如一帧相机图像 |
| Action / 动作 | 机器人或车辆的控制量，例如关节角、夹爪开合、线速度/角速度 |
| Dynamics / 动力学 | 环境从当前状态到下一状态的转移规律 |
| Latent space / 隐空间 | 模型内部压缩后的连续表示，比像素更高效 |
| DiT | Diffusion Transformer，用 Transformer 预测去噪方向，生成连续模态 |
| Tokenizer | 把文本/图像/音频/动作转换成模型可处理 token 的组件 |
| T2V / I2V / V2V | 文本到视频 / 图像到视频 / 视频到视频 |
| Forward dynamics | 给定当前状态和动作，预测未来观测 |
| Policy | 给定目标和观测，输出动作 |
| Inverse dynamics | 给定相邻帧或视频，反推动作 |

## 1. 先建立直觉：世界模型解决什么问题

世界模型（World Model）学习环境的状态转移规律：

```text
当前观测 x_t，历史 H，动作/控制 a_t  →  预测未来观测 x_(t+1)...x_(t+k)
```

与普通视频生成相比，世界模型更关心：

1. **时间一致性**：同一物体不能无故消失、变形或瞬移。
2. **空间一致性**：遮挡、视差、阴影、反射应与三维场景一致。
3. **物理合理性**：惯性、碰撞、重力、接触和运动轨迹不能明显违反常识。
4. **动作条件化**：给定机器人或车辆动作后，未来画面应随动作变化。
5. **可交互性**：不仅能“生成好看视频”，还能用于策略评估、规划和机器人控制。

一个有用的理解方式：

- 视频生成模型 = 学会“观测分布”的生成器。
- 世界模型 = 学会“环境动力学”的生成器，最好能接受动作并预测后果。

## 2. Cosmos3-Nano 是什么

Cosmos3-Nano 是 NVIDIA Cosmos3 系列的 16B 参数全模态世界模型。官方描述它的输入可包括文本、图像、视频、音频和动作轨迹，输出可包括文本、图像、视频、音频和动作，用于 Physical AI、机器人、自动驾驶和仿真。

核心架构是 **Mixture-of-Transformers（MoT）**：

1. **自回归 Transformer 塔**：适合离散 token，例如文本、动作序列、推理。
2. **扩散 Transformer 塔**：适合连续信号，例如图像、视频帧 latent 和音频，通过迭代去噪生成。
3. **模态编码/解码器**：
   - 文本 tokenizer 负责语言条件；
   - vision encoder 提取视觉输入特征；
   - VAE 将视频压缩到 latent 空间；
   - sound tokenizer 处理音频 latent；
   - 生成后再解码回 MP4 / AAC / JSON 等用户可读格式。

从本地 `model/model_index.json` 可以看到实际组件：

```text
Cosmos3OmniDiffusersPipeline
├── UniPCMultistepScheduler        # 扩散/flow 调度
├── Qwen2TokenizerFast             # 文本 tokenizer
├── Cosmos3OmniTransformer         # 主干 DiT/MoT
├── AutoencoderKLWan               # 视频 VAE
├── Qwen3VLVisionModel             # 视觉编码
└── Cosmos3AVAEAudioTokenizer      # 音频 tokenizer
```

这使同一个基础模型能同时做：

- 文本生成视频（T2V）：想象一个世界；
- 图像生成视频（I2V）：给定当前观测，预测未来；
- 视频 + 音频生成：生成可听可见的环境；
- forward dynamics：给定动作，预测未来画面；
- policy：给定目标和当前画面，预测动作；
- inverse dynamics：由视频反推动作；
- reasoner：看图/视频回答规划与空间推理问题。

对你学习世界模型来说，最核心的是 **I2V + action conditioning**：`当前画面 + 动作序列 → 未来画面`。这就是机器人仿真中的环境模型。

## 3. 一次文本到视频推理的数据流

当前工作区的 smoke test 采用 T2V，流程如下：

```text
用户 prompt
   ↓
文本 tokenizer / 结构化 prompt
   ↓
扩散 Transformer 在 latent 空间迭代去噪
   ↓
视频 VAE decoder
   ↓
MP4 封装
   ↓
outputs/worldmodel_t2v_*.mp4
```

具体参数：

| 参数 | 当前值 | 含义 |
|---|---:|---|
| `size` | `448x256` | 256p、16:9，降低显存与耗时 |
| `num_frames` | `25` | 约 2 秒短视频，用于验证流程 |
| `fps` | `12` | 输出帧率 |
| `num_inference_steps` | `12` | 扩散步数；官方高质量示例为 35 |
| `guidance_scale` | `6.0` | prompt 引导强度 |
| `flow_shift` | `10.0` | flow matching 调度参数 |
| `seed` | `20261025` | 固定随机种子，便于复现 |

质量优先时可逐步改成官方 `1280x720`、189 帧、35 步、24 fps，但耗时和显存都会显著增加。

## 4. 环境与目录

### 宿主机与容器

- 宿主机：`h200_1727`
- 容器：`zmz_dev_v2`
- GPU：8 张 NVIDIA H200 141GB
- 工作区：`/mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel`
- 模型来源：AtomGit `https://atomgit.com/hf_mirrors/nvidia/Cosmos3-Nano`

### 关键文件

```text
model/
  model_index.json                     # pipeline 与组件索引
  transformer/                         # 16B 主干权重，7 个 safetensors 分片
  vae/                                 # 视频 latent 编解码
  vision_encoder/                      # 视觉输入编码
  text_tokenizer/                      # 文本 tokenizer
  sound_tokenizer/                     # 音频生成/编码组件
scripts/
  download_cosmos_lfs.py               # 从 AtomGit LFS 下载并校验核心权重
  check_model.py                       # 检查文件是否仍是 LFS pointer
  start_server.sh                      # 启动 vLLM-Omni 服务
  run_worldmodel_t2v.py                # 提交 T2V 世界模型请求
  status.sh                            # 查看进程、API 和 GPU
```

## 5. 复现实验

### 5.1 校验模型

```bash
cd /mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel
source .venv/bin/activate
python scripts/check_model.py
```

如果输出 `POINTER`，表示文件只有 Git LFS 指针，尚未下载真实权重。

### 5.2 启动服务

默认使用 GPU 4 和端口 18000：

```bash
scripts/start_server.sh
```

如果所有 GPU 都被其他任务占用，可以让脚本自动排队：

```bash
scripts/wait_and_run_worldmodel.sh
```

它会等待任一 GPU 显存低于 10GB，自动启动服务、提交 256p/25 帧请求、保存输出后停止服务释放 GPU。

如需换 GPU 或端口：

```bash
CUDA_VISIBLE_DEVICES=5 PORT=18001 scripts/start_server.sh
```

等待日志出现 API ready 后，另开 shell 检查：

```bash
curl --noproxy "*" http://127.0.0.1:18000/v1/models
```

### 5.3 跑一次世界模型视频推演

```bash
source .venv/bin/activate
python scripts/run_worldmodel_t2v.py
```

脚本会保存：

1. 请求参数 JSON；
2. 生成 MP4；
3. 耗时、字节数、SHA256；
4. ffprobe 的分辨率、帧率、帧数等元数据；
5. 追加写入 `docs/RUN_LOG.md`。

## 6. 建议的 7 天学习路线

### Day 1：概念与接口

- 通读 `model/README.md` 的 Description、Architecture、Input/Output。
- 运行 T2V smoke test。
- 手工改 prompt，观察物体运动、遮挡、阴影和相机运动。

练习题：

1. 同一 seed 下，把“机器人左转”改成“机器人右转”，哪些区域变化？
2. 去掉“shadow moves consistently”后，物理一致性是否变差？
3. 固定 prompt，改 seed，哪些细节不稳定？

### Day 2：视频 latent 与 DiT

学习三个概念：

- VAE：像素空间 ↔ latent 空间；
- Flow matching / diffusion：从噪声逐步去噪；
- Diffusion Transformer：用注意力建模时空依赖。

观察配置：

```bash
cat model/model_index.json
find model/vae -maxdepth 2 -type f -name '*.json' -print -exec cat {} \;
```

### Day 3：条件生成与 action conditioning

阅读官方模型卡中 action generation 示例，理解三种任务：

```text
forward dynamics: 当前帧 + 动作 → 未来视频
policy:          当前帧 + 任务 → 动作
inverse dynamics: 视频         → 动作
```

这三种任务构成机器人学习闭环。

### Day 4：从 API 到源码

- 请求层：`scripts/run_worldmodel_t2v.py`
- 服务层：vLLM-Omni recipe
- 模型层：`vllm_omni/diffusion/models/cosmos3/pipeline_cosmos3.py`

重点找三个函数：文本编码、denoise loop、video decode。

### Day 5：控制变量实验

一次只改一个参数：

| 实验 | 变量 | 观察指标 |
|---|---|---|
| 分辨率 | 256p / 480p / 720p | 细节、显存、耗时 |
| 长度 | 25 / 49 / 97 / 189 帧 | 时间一致性 |
| 步数 | 8 / 12 / 20 / 35 | 收敛质量 |
| guidance | 3 / 6 / 9 | prompt 遵循 vs 过饱和 |
| seed | 多组 | 稳定性 |

### Day 6：评估世界模型

不要只看“像不像”，建议建立四类指标：

1. 视觉质量：清晰度、压缩伪影、色彩；
2. 时间一致性：物体轨迹、闪烁、形态漂移；
3. 物理一致性：碰撞、重力、遮挡、阴影；
4. 任务有效性：动作后未来是否符合控制目标。

人工评估表可为每项打 1–5 分，并保留 seed 与 request JSON。

### Day 7：扩展阅读与方向

- World model / model-based RL；
- Video prediction 与 latent dynamics；
- Action tokenizer / inverse dynamics；
- 机器人策略学习与仿真数据生成；
- 安全 guardrails 与模型许可约束。

## 7. 常见问题

### Q1：为什么 GPU 4？

当前 0–3 卡已有任务占用，4–7 空闲。可通过 `nvidia-smi` 重新选择。

### Q2：为什么用 `--no-guardrails`？

官方 guardrail 需要额外的 gated 模型和 token。为避免依赖，本学习环境关闭 guardrail；使用时你必须自行遵守 OpenMDW1.1 许可和内容安全要求。

### Q3：文件只有 100 多字节？

这是 Git LFS pointer，不是权重。运行：

```bash
python scripts/download_cosmos_lfs.py
```

### Q4：服务启动很慢？

16B 模型需要加载约 36GB 权重。首次加载受 NFS 和页缓存影响，可能需要数分钟。

### Q5：请求超时或 OOM？

- 换空闲 H200；
- 保持 256p 和 25 帧；
- 降低 `num_inference_steps`；
- 官方支持 `--enable-layerwise-offload` 降低显存；
- 高质量 720p/189 帧应单独规划资源。

## 8. 学习成果检查清单

完成本教程后，你应该能回答：

1. 世界模型和视频生成器的差别是什么？
2. Cosmos3-Nano 的 MoT 架构为什么要同时有自回归塔和扩散塔？
3. 一次 T2V 请求经过哪些模块？
4. 如何把模型从“生成视频”扩展到“动作条件化预测未来”？
5. 如何设计控制变量实验评估时间一致性和物理合理性？
6. 如何根据日志和输出元数据复现一次实验？

## 9. 参考资料与本地阅读

- 官方模型卡：`model/README.md`
- vLLM-Omni Cosmos3 recipe：`https://github.com/vllm-project/vllm-omni/blob/main/recipes/cosmos3/Cosmos3-Nano.md`
- NVIDIA Cosmos：`https://github.com/nvidia/cosmos`
- vLLM-Omni 文档：`https://docs.vllm.ai/projects/vllm-omni/en/latest/`
