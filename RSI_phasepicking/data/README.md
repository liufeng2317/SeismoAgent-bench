# 输入数据

只放输入：外部获取的数据和上游任务的交接产出。本任务算出的东西放 `results/`。大数据只放符号链接（绝对路径），链接只读。

## 已有

| 路径 | 内容 | 来源与版本 | 大小 | 链接指向或 git 状态 |
|---|---|---|---|---|
| `waveforms/raw/ridgecrest_2019` | 2019 Ridgecrest 连续波形、台站元数据、波形清单（T1 用） | 上游项目 SeismoAgentBench，提交 367f80a 时的本地波形（2026-11-13 建立链接） | 约 36 GB | `/ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/data/2019_ridgecrest_california/waveforms` |
| `catalogs/raw/scedc_events/` | SCEDC 事件列表（全震级，FDSN text），2020-01 至 2026-11-12 按月一个文件，另有 T1 窗口 2019-07-04..07；共 153,756 个事件 | SCEDC FDSN event 服务，2026-11-13 获取；`scripts/a_data_labels/a1_1_download_events.py` | 30 MB | 不进 git |
| `catalogs/raw/ncedc_events/` | NCEDC 事件列表（全震级，含南加州事件），2020-01 至 2026-11 按月一个文件；共 206,500 个事件 | NCEDC FDSN event 服务，2026-11-13 获取；同上 | 23 MB | 不进 git |
| `catalogs/raw/scedc_quakeml/` | 候选区 R1–R4 内 M≥2.5 事件（582 个）的 QuakeML，含拾取和到时 | SCEDC FDSN event 服务（`includearrivals=true`），2026-11-13 获取；`scripts/a_data_labels/a2_1_download_quakeml.py` | 454 MB | 不进 git |
| `stations/raw/scedc_{CI,AZ}_stations.txt` | 2020 年以来运行过的 CI、AZ 台站（台站级） | SCEDC FDSN station 服务，2026-11-13 获取；`a1_1_download_events.py` | 72 KB | 进 git |

## 计划获取（获取后移到上表）

| 路径 | 内容 | 来源 |
|---|---|---|
| `waveforms/raw/socal/` | 南加州练习池和基础测试集的事件窗波形 | SCEDC S3（`s3://scedc-pds`） |
| `waveforms/raw/norcal/` | 北加州事件窗波形 | NCEDC S3（`s3://ncedc-pds`） |
| `catalogs/raw/ncedc_quakeml/` | 北加州事件 QuakeML | NCEDC FDSN event 服务 |
| `catalogs/raw/ridgecrest_references/` | Ridgecrest 高精度目录（QTM、Shelly 2020、Lin 2020、HYS） | 链接到上游项目 `data/2019_ridgecrest_california/data/catalogs/` 的固定版本 |
| `stations/` | 各数据集的 StationXML（含仪器响应） | SCEDC / NCEDC / NIED |
| `models/` | 一维速度模型初值 | 上游 seismotools 和 seismo_checker 的速度模型库 |
| `waveforms/raw/japan/`、`catalogs/raw/jma/` | 日本子场景的波形和 JMA 检测值（若选日本） | NIED（HinetPy）、JMA；**禁止再分发** |

换机器时照本表重建链接；跟进上游新版本时只改链接，并在 `docs/changelog.md` 记一行。
