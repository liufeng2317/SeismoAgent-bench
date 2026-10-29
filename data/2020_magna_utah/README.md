# Magna 2020

| 路径 | 内容 |
|---|---|
| [analysis/MAGNA2020_analysis.md](analysis/MAGNA2020_analysis.md) | 案例科学分析、参考角色和待办事项 |
| [analysis/processing.yaml](analysis/processing.yaml) | 产品声明与窗口状态 |
| [data/catalogs/](data/catalogs/) | 各来源目录、说明、处理脚本与分析产物 |
| `data/waveforms/` | 外部波形归档软链接；当前 47 站、1,184 个 MiniSEED 文件、10,859,513,344 bytes；不纳入 Git |
| [scripts/observations/](scripts/observations/README.md) | 案例级观测数据准备：可用性探针审计、台站清单提取、元数据获取、波形清单与下载 |
| [references/](references/) | 文献、附件、阅读记录和结构化提取 |

区分拾取记录、重定位事件、ISC 对比档案和官方快照。

当前 `window_status: frozen`（2026-10-28 随 metrics v1 冻结；评测时间、区域和深度掩膜见 `workflows/tasks/2020_magna_utah/expert/00_config/validation.yaml`）。`workflows/data_preparation/` 仅在有案例级执行工具时建立；目录自身的解析脚本保留在 `data/catalogs/<SOURCE_ID>/workflows/data_preparation/`。

当前候选窗为 `2020-03-18` 至 `03-26` UTC；47 站是可用性下载 superset，不等同于 Pang 论文的 39 站条件。见 [六案统计](../../docs/data/CASES_SUMMARY.md) 和 [Magna 详细信息](../../docs/data/CASE_DETAILS.md#6-magna-utah-2020)；共享规则见 [资料组织说明](../README.md)。
