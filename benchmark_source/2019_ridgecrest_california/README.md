# Ridgecrest 2019

本案例资料位于 `benchmark_source/2019_ridgecrest_california/`。

| 路径 | 内容 |
|---|---|
| [analysis/RIDGE2019_analysis.md](analysis/RIDGE2019_analysis.md) | 科学设计、参考目录核验和待办事项 |
| [analysis/processing.yaml](analysis/processing.yaml) | 来源登记表 v2、既有候选时窗与核验配置 |
| [analysis/reference_audit.json](analysis/reference_audit.json) | 可复算的目录与震相核验结果 |
| [data/catalogs/](data/catalogs/) | 原始目录、来源说明、各产品统计和图件 |
| `data/waveforms/` | 外部统一观测目录的软链接，包含波形、台站和清单；不纳入 Git |
| [references/](references/) | 文献、补充材料、解析与提取记录 |
| [scripts/README.md](scripts/README.md) | 按 catalogs / figures / observations 分层的案例脚本与下载入口 |

当前仍为 `not_frozen`；结构迁移不改变科学设计或正式评测状态。

在仓库根目录复算：

```bash
python -B benchmark_source/2019_ridgecrest_california/scripts/catalogs/audit_references.py
python -B -m unittest discover -s tests/source_prepare
```

大目录、波形、论文原件和敏感配置保留本地。文件维护规则见 [资料组织说明](../README.md)。

## Source 整理入口

`processing.yaml` 的 `source_groups` 保存来源关系，`sources` 唯一登记各文件产品的路径、单位、版本、解析器和 SHA-256；`reference_audit` 通过产品键引用它们。当前有 5 个来源组、8 个文件产品，目录子集不重复复制原文件。

```bash
python -B -m SeismoAgentBench.utils.source_prepare inventory --case-dir benchmark_source/2019_ridgecrest_california
python -B -m SeismoAgentBench.utils.source_prepare validate-sources --case-dir benchmark_source/2019_ridgecrest_california --verify-files
```

通用代码只处理 source 的登记、完整性和统计诊断；评测将在独立目录实现。来源规范与迁移边界见 [通用 source 架构](../README.md#通用-source-架构ridgecrest-试点)。
