# Prague 2011

| 路径 | 内容 |
|---|---|
| [analysis/PRAGUE2011_analysis.md](analysis/PRAGUE2011_analysis.md) | 案例科学分析、参考角色和待办事项 |
| [analysis/processing.yaml](analysis/processing.yaml) | 产品声明与窗口状态 |
| [data/catalogs/](data/catalogs/) | 各来源目录、说明、处理脚本与分析产物 |
| `data/waveforms/` | 外部波形归档软链接；当前 23 站、552 个 MiniSEED 文件、7,504,932,352 bytes；不纳入 Git |
| [scripts/observations/](scripts/observations/README.md) | 31 站设计集合重建、可用性审计、元数据、下载与波形 inventory |
| [data/models/velocity_models.json](data/models/velocity_models.json) | Keranen et al. (2013) 一维速度模型（Cochran 2020 所用；从 GSA DR 2013191 图 DR1 矢量内容精确提取，脚本 [scripts/models/](scripts/models/digitize_keranen2013_dr1.py)） |
| [references/](references/) | 文献、附件、阅读记录和结构化提取 |

保留主目录、重定位目录、子空间检测和震相产品的区别。

当前 `window_status: not_frozen`。`workflows/data_preparation/` 仅在有案例级执行工具时建立；目录自身的解析脚本保留在 `data/catalogs/<SOURCE_ID>/workflows/data_preparation/`。

当前候选窗为 `2011-11-11` 至 `11-19` UTC；31 站元数据集合中已有 23 站波形，不能把设计台站数当作下载台站数。见 [六案统计](../../docs/data/CASES_SUMMARY.md) 和 [Prague 详细信息](../../docs/data/CASE_DETAILS.md#1-prague-oklahoma-2011)；共享规则见 [资料组织说明](../README.md)。
