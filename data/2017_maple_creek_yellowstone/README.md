# Maple Creek 2017

| 路径 | 内容 |
|---|---|
| [analysis/MAPLE2017_analysis.md](analysis/MAPLE2017_analysis.md) | 案例科学分析、参考角色和待办事项 |
| [analysis/processing.yaml](analysis/processing.yaml) | 产品声明与窗口状态 |
| [data/catalogs/](data/catalogs/) | 各来源目录、说明、处理脚本与分析产物 |
| `data/waveforms/` | 外部波形归档软链接；当前 27 站、560 个 MiniSEED 文件、4,414,311,936 bytes；不纳入 Git |
| [scripts/observations/](scripts/observations/README.md) | 案例级观测数据准备：台站清单提取、元数据获取、波形清单与下载 |
| [references/](references/) | 文献、附件、阅读记录和结构化提取 |

区分已获得的事件目录、震相辅助资料和缺失产品；目录存在不代表事件产品已就绪。

当前 `window_status: frozen`（2026-10-28 随 metrics v1 冻结；评测时间、区域和深度掩膜见 `workflows/tasks/2017_maple_creek_yellowstone/expert/00_config/validation.yaml`）。`workflows/data_preparation/` 仅在有案例级执行工具时建立；目录自身的解析脚本保留在 `data/catalogs/<SOURCE_ID>/workflows/data_preparation/`。

评测时间窗（已冻结）为 `2017-06-11` 至 `06-19` UTC，27 个 phase-manifest 台站均有波形。研究侧有 Shelly 的 phase 产品和由其派生的检测事件表（时间窗内 18,062 个，仅有时间）；Pang 2019 的事件表仍缺。official baseline（UUSS ComCat）的空间框已于 2026-10-22 修正，覆盖 Mw 4.4 锚点（全量 2,447 个、时间窗内 626 个），是主检测和主定位参考。见 [案例数据清单](../../docs/data/01_Case_Data_Inventory.md) 和 [Maple Creek 详细信息](../../docs/data/01_Case_Data_Inventory.md#3-maple-creek-yellowstone-2017)。
