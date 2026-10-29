# Kaikōura 2016

| 路径 | 内容 |
|---|---|
| [analysis/KAIKOURA2016_analysis.md](analysis/KAIKOURA2016_analysis.md) | 案例科学分析、参考角色和待办事项 |
| [analysis/processing.yaml](analysis/processing.yaml) | 产品声明与窗口状态 |
| [data/catalogs/](data/catalogs/) | 各来源目录、说明、处理脚本与分析产物 |
| `data/waveforms/` | 外部波形归档软链接；当前 53 站、1,359 个 MiniSEED 文件、12,313,116,160 bytes；不纳入 Git |
| [scripts/observations/](scripts/observations/README.md) | 案例级观测数据准备：Table S1 台站清单、双 provider 可用性审计、元数据获取、波形清单与下载 |
| [references/](references/) | 文献、附件、阅读记录和结构化提取 |

保留 GrowClust 版本、SUGAR S10/S11、关联震相和机制解之间的区别；补充材料中的同源表通过软链接引用。

当前 `window_status: frozen`（2026-10-28 随 metrics v1 冻结；评测时间、区域和深度掩膜见 `workflows/tasks/2016_kaikoura_new_zealand/expert/00_config/validation.yaml`）。`workflows/data_preparation/` 仅在有案例级执行工具时建立；目录自身的解析脚本保留在 `data/catalogs/<SOURCE_ID>/workflows/data_preparation/`。

评测时间窗（已冻结）为 `2016-12-01` 至 `12-09` UTC；81 站 Table S1/元数据集合中已有 53 站适用波形，strong-motion-only 等站不应计为已下载速度波形。见 [案例数据清单](../../docs/data/01_Case_Data_Inventory.md) 和 [Kaikōura 详细信息](../../docs/data/01_Case_Data_Inventory.md#2-kaikōura-new-zealand-2016)；共享规则见 [资料组织说明](../README.md)。
