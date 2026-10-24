# Kīlauea 2018

| 路径 | 内容 |
|---|---|
| [analysis/KILAUEA2018_analysis.md](analysis/KILAUEA2018_analysis.md) | 案例科学分析、参考角色和待办事项 |
| [analysis/processing.yaml](analysis/processing.yaml) | 产品声明与窗口状态 |
| [data/catalogs/](data/catalogs/) | 各来源目录、说明、处理脚本与分析产物 |
| `data/waveforms/` | 外部波形归档软链接；当前 25 站、520 个 MiniSEED 文件、6,946,877,952 bytes；不纳入 Git |
| [scripts/observations/](scripts/observations/README.md) | 案例级观测数据准备：台站清单提取、逐日可用性审计、元数据获取、波形清单与下载 |
| [references/](references/) | 文献、附件、阅读记录和结构化提取 |

区分地震、LP 事件、相对坐标和近似绝对坐标；不同观测定义不合并为一个目录。

当前 `window_status: not_frozen`。`workflows/data_preparation/` 仅在有案例级执行工具时建立；目录自身的解析脚本保留在 `data/catalogs/<SOURCE_ID>/workflows/data_preparation/`。

当前候选窗为 `2018-05-01` 至 `05-09` UTC，25 个 phase-manifest 台站均有波形；逐日探针全部存在，但采样时刻存在不等于无微小缺口。见 [六案统计](../../docs/data/CASES_SUMMARY.md) 和 [Kīlauea 详细信息](../../docs/data/CASE_DETAILS.md#4-kīlauea-hawaiʻi-2018)；共享规则见 [资料组织说明](../README.md)。
