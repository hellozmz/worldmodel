# Cosmos3-Nano 运行记录

## 环境

- 日期：2026-10-24/25 Asia/Shanghai
- 宿主机：`h200_1727` / `gpu-lg-cmc-h-h200-1727.host.h.pjlab.org.cn`
- 容器：`zmz_dev_v2`
- 工作区：`/mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel`
- GPU：8 × NVIDIA H200 143771 MiB；初始 0–3 卡约 67GB 已用，4–7 空闲
- 存储：`/mnt/models_2296` 挂载 7.0T CFS，初始可用约 3.9T
- 基础环境：Ubuntu 22.04.5，Python 3.12.12，CUDA runtime 12.8，PyTorch 2.9.0+cu128

## 模型下载

- 源：`https://atomgit.com/hf_mirrors/nvidia/Cosmos3-Nano`
- Git clone 地址：`https://atomgit.com/hf_mirrors/nvidia/Cosmos3-Nano.git`
- 下载方式：Git clone + AtomGit LFS API；核心权重通过 `scripts/download_cosmos_lfs.py` 多连接下载并做 SHA256 校验。
- 范围：`transformer/`、`vae/`、`vision_encoder/`、`text_tokenizer/`、`sound_tokenizer/`；示例宣传媒体不作为推理必要权重下载。
- 核心权重约 36GB，其中 transformer 7 个分片约 31.3GB。

## 世界模型推理

- 目标：T2V 世界模型 smoke test：从自然语言场景描述生成一段低分辨率、短时长视频，验证下载、服务、请求、输出落盘全流程。
- 默认参数：448×256、25 帧、12 fps、12 inference steps、guidance 6.0、flow_shift 10.0、seed 20261025。
- 服务：vLLM-Omni，本地模型路径，`--no-guardrails`。

（下方由 `scripts/run_worldmodel_t2v.py` 自动追加具体请求与输出记录。）

## 下载完成与完整性校验

- 2026-10-25 01:24 Asia/Shanghai：核心模型同步完成，`model/` 总计约 36GiB。
- 网络下载先从 AtomGit LFS 拉取了 text tokenizer、sound tokenizer 与部分 transformer 分片；随后发现同机已有完整缓存 `/mnt/nvme1n1/models/Cosmos3-Nano`，为避免长时间占用出口带宽，将其同步到本工作区。
- 所有 11 个核心 LFS 文件均按 AtomGit Git commit `e59a53c25979a090fa8706c9acc0c254a6e89b92` 中的 LFS SHA256 逐一复核，结果全部 `PASS`，并输出 `ALL_SHA256_PASS`。
- `scripts/check_model.py` 当前结果：`RESULT: PASS`。

## 推理环境安装

- 创建独立虚拟环境：`.venv/`
- 目标版本：`vllm==0.22.0`、`vllm-omni==0.22.0`，PyTorch 使用 CUDA 12.8 后端。
- 复现命令见 `scripts/setup_env.sh`。

## GPU 资源记录

- 初始检查时 GPU 0–3 各约 67GiB 已用，GPU 4–7 空闲。
- 模型准备期间，另一用户的 8 卡 GLM-5.3 vLLM 服务占满 GPU 0–7（每卡约 141GiB）。为避免影响他人任务，Cosmos3 服务等待空闲 GPU 后启动。
- 2026-10-25 02:54 Asia/Shanghai：已启动 `scripts/wait_and_run_worldmodel.sh`（容器内 PID 记录于 `logs/wait_and_run.pid`）。该脚本会排队等待任意 GPU 空闲，自动启动 Cosmos3-Nano 服务，执行 T2V 世界模型 smoke test，保存输出与元数据后释放 GPU。

## 成功运行记录

- 推理后端：`vllm-omni 0.22.0` / `vllm 0.22.0` / `torch 2.11.0+cu128` / `diffusers 0.38.0` / `transformers 4.57.6`。
- 环境隔离：`.venv` 关闭 system-site-packages，避免容器内旧 xformers 与新 diffusers 冲突；同时为 vLLM 0.22 wheel 导出 `nvidia/cu13/lib` 中的 `libcudart.so.13` 路径。
- 2026-10-25 03:21 Asia/Shanghai：正常 BF16 服务在 GPU 4、端口 18000 启动成功。日志显示主模型加载 30.237 GiB，AsyncOmni 初始化 32.32s，warmup 总 pipeline 时间 9.44s。
- API 验证：`GET /v1/models` 返回 `cosmos3-nano`。
- 2026-10-25 03:22:36 UTC（本地 03:22 完成请求）：`POST /v1/videos/sync` 成功，HTTP 200，`Content-Type: video/mp4`。
- 请求参数：448×256、25 帧、12 fps、12 inference steps、guidance 6.0、flow_shift 10.0、seed 20261025。
- 输出：`outputs/worldmodel_t2v_20261024_192234.mp4`
- 耗时：1.128s；大小：408109 bytes；SHA256：`a15b2695a263ef956d40a01d0e7c392f3de2c2b77144f8f9e220501ce035b613`。
- ffprobe：H.264，448×256，12 fps，25 帧，duration 2.083333s。
- 结果元数据：`outputs/worldmodel_t2v_20261024_192234.json`；请求快照：`outputs/worldmodel_t2v_20261024_192234_request.json`。
- 成功请求时服务运行于 GPU 4 / 端口 18000，约 34GiB GPU 显存占用。随后 `zmz_dev_v2` 在 2026-10-25 03:26 Asia/Shanghai 收到外部 SIGTERM（exit 143）并停止，服务随之结束；输出与日志已持久化。容器已于 03:40 重启，当前 GPU 又被其他 8 卡服务占用，复跑可执行 `scripts/wait_and_run_worldmodel.sh` 排队。

## 低显存尝试与恢复

- 在其他任务占满 8 卡期间，尝试过 `--enable-layerwise-offload`、FP8、关闭 sound/action 分支与少量源码级 CPU/GPU swap 实验；相关失败日志保留在 `logs/server_lowvram*.log` 和 `logs/server_oneshot_lowvram*.log`。
- 这些实验说明：共享任务仅剩约 2–3GiB HBM 时不足以完成 Cosmos3-Nano 初始化，尤其 VAE、sound tokenizer 和 resident embedding 会先后触发 OOM。
- GPU 释放后已恢复官方模型配置（`sound_gen=true`、`action_gen=true`）并还原 vLLM-Omni 源码；最终成功运行使用未打补丁的正常 BF16 服务。
