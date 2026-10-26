# Cosmos3-Nano 世界模型学习与推理工作区

本目录部署在 `h200_1727` 的 `zmz_dev_v2` 容器中：

```text
/mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel
```

包含：

- `model/`：从 AtomGit `hf_mirrors/nvidia/Cosmos3-Nano` 下载的模型仓库与核心权重。
- `.venv/`：独立 Python 推理环境。
- `scripts/`：模型校验、服务启动、状态检查、文本到视频请求脚本。
- `outputs/`：世界模型生成的视频、请求与元数据。
- `logs/`：下载和服务日志。
- `docs/TUTORIAL.md`：世界模型学习教程。
- `docs/RUN_LOG.md`：环境、下载、运行与结果记录。

## 快速开始

```bash
cd /mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel
source .venv/bin/activate
python scripts/check_model.py
scripts/start_server.sh          # 默认 GPU 4、端口 18000
# 另开一个 shell：
python scripts/run_worldmodel_t2v.py

# 或者等待任意一张 GPU 空闲后自动启动、推理、落盘并释放 GPU：
scripts/wait_and_run_worldmodel.sh
```

生成结果保存在 `outputs/`，每次请求都会落盘 request JSON、MP4、耗时、大小、SHA256 和 ffprobe 元数据。

## 已跑通的 smoke test

- 输出视频：`outputs/worldmodel_t2v_20261024_192234.mp4`
- 元数据：`outputs/worldmodel_t2v_20261024_192234.json`
- 结果：448×256，25 帧，12 fps，H.264，请求耗时 1.128s，SHA256 已记录。
- 详细过程见 `docs/RUN_LOG.md`，学习路线见 `docs/TUTORIAL.md`。
