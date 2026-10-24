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

当前 `window_status: not_frozen`。`workflows/data_preparation/` 仅在有案例级执行工具时建立；目录自身的解析脚本保留在 `data/catalogs/<SOURCE_ID>/workflows/data_preparation/`。

当前候选窗为 `2017-06-11` 至 `06-19` UTC，27 个 phase-manifest 台站均有波形。研究侧当前只有 phase 产品，event-level 表仍缺；official baseline 的旧空间窗不覆盖 Mw 4.4 锚点，不能作为已冻结基线。见 [六案统计](../../docs/data/CASES_SUMMARY.md) 和 [Maple Creek 详细信息](../../docs/data/CASE_DETAILS.md#3-maple-creek-yellowstone-2017)。
