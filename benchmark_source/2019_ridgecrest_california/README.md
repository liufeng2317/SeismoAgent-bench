# Ridgecrest 2019

本案例资料位于 `benchmark_source/2019_ridgecrest_california/`。

| 路径 | 内容 |
|---|---|
| [analysis/RIDGE2019_analysis.md](analysis/RIDGE2019_analysis.md) | 科学设计、参考目录核验和待办事项 |
| [analysis/processing.yaml](analysis/processing.yaml) | 候选时窗、产品角色和核验输入配置 |
| [analysis/reference_audit.json](analysis/reference_audit.json) | 可复算的目录与震相核验结果 |
| [data/catalogs/](data/catalogs/) | 原始目录、来源说明、各产品统计和图件 |
| `data/waveforms/` | 本地连续波形预留位置；不纳入 Git |
| [references/](references/) | 文献、补充材料、解析与提取记录 |
| [scripts/](scripts/) | 案例级参考核验程序和测试 |

当前仍为 `not_frozen`；结构迁移不改变科学设计或正式评测状态。

在仓库根目录复算：

```bash
python -B benchmark_source/2019_ridgecrest_california/scripts/audit_references.py
python -B -m unittest discover -s benchmark_source/2019_ridgecrest_california/scripts -p 'test_*.py'
```

大目录、波形、论文原件和敏感配置保留本地。文件维护规则见 [资料组织说明](../README.md)。
