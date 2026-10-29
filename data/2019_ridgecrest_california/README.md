# Ridgecrest 2019

本案例资料位于 `data/2019_ridgecrest_california/`。

| 路径 | 内容 |
|---|---|
| [analysis/RIDGE2019_analysis.md](analysis/RIDGE2019_analysis.md) | 科学设计、参考目录核验和待办事项 |
| [analysis/processing.yaml](analysis/processing.yaml) | 来源登记表 v2、既有候选时窗与核验配置 |
| [analysis/reference_audit.json](analysis/reference_audit.json) | 可复算的目录与震相核验结果 |
| [data/catalogs/](data/catalogs/) | 原始目录、来源说明、各产品统计和图件 |
| `data/waveforms/` | 外部统一观测目录软链接；归档共 57 站/3,107 文件/37,839,508,992 bytes，当前 72 小时候选窗为 42 站/360 文件/4,945,348,096 bytes |
| [references/](references/) | 文献、补充材料、解析与提取记录 |
| [scripts/](scripts/README.md) | 按 catalogs / figures / observations 分层的案例脚本与下载入口 |

当前 `window_status: frozen`（2026-10-28 随 metrics v1 冻结）：数据窗为 2019-07-04 00:00 – 07-07 UTC，评测自参考目录共同起点 07-04 15:35:29.4 UTC 起算，掩膜见 `workflows/tasks/2019_ridgecrest_california/expert/00_config/validation.yaml`。

在仓库根目录复算：

```bash
python -B data/2019_ridgecrest_california/scripts/catalogs/audit_references.py
python -B -m unittest discover -s tests/source_prepare
```

区域 StationXML 发现范围是 404 站，不是评测输入；任务输入是整个本地波形目录（时间窗内 42 站有数据），由 Agent 自行选台。见 [案例数据清单](../../docs/data/01_Case_Data_Inventory.md) 和 [Ridgecrest 详细信息](../../docs/data/01_Case_Data_Inventory.md#5-ridgecrest-california-2019)。大目录、波形、论文原件和敏感配置保留本地，文件维护规则见 [资料组织说明](../README.md)。

## Source 整理入口

`processing.yaml` 的 `source_groups` 保存来源关系，`sources` 唯一登记各文件产品的路径、单位、版本、解析器和 SHA-256；`reference_audit` 通过产品键引用它们。当前有 5 个来源组、8 个文件产品，目录子集不重复复制原文件。

```bash
python -B -m SeismoAgentBench.utils.source_prepare inventory --case-dir data/2019_ridgecrest_california
python -B -m SeismoAgentBench.utils.source_prepare validate-sources --case-dir data/2019_ridgecrest_california --verify-files
```

通用代码只处理 source 的登记、完整性和统计诊断；评测将在独立目录实现。来源组织与维护边界见 [资料组织说明](../README.md)。
