# SeismoAgentBench 代码包

整体 benchmark 的控制流程见 [BENCHMARK_WORKFLOW_PLAN.md](BENCHMARK_WORKFLOW_PLAN.md)。该计划定义任务、输入 manifest、执行后端、agent、工具适配器、scorer 和 provenance 的边界。`SeismoAgentBench/` 承载项目的稳定控制代码和支撑工具；来源整理是 `utils/` 下的一个子功能，不代表整个 benchmark 架构。Python 导入路径区分大小写，统一使用 `SeismoAgentBench`。

```text
SeismoAgentBench/
├── __init__.py
├── task/                   # task and input-manifest contracts
├── execution/              # trusted-development run control
├── scoring/                # artifact validation and scoring interfaces
└── utils/
    ├── __init__.py
    └── source_prepare/
        ├── __init__.py
        ├── __main__.py     # source 专属命令行入口
        ├── sources.py      # 来源契约、文件盘点、完整性检查和声明式筛选
        └── catalog.py      # 来源目录的基础解析、统计与对应诊断
```

## 职责边界

| 位置 | 职责 |
|---|---|
| `SeismoAgentBench/task/` | 任务、输入 manifest 及其契约校验 |
| `SeismoAgentBench/execution/` | 运行目录、命令执行和运行记录 |
| `SeismoAgentBench/scoring/` | 输出产物校验及后续科学评分接口 |
| `utils/source_prepare/` | 来源登记、路径/哈希检查、资料盘点与准备阶段的目录诊断 |
| 根目录 `scripts/` | 下载、转换和批处理入口；逐步调用可复用模块，避免复制实现 |
| `benchmark_source/<case>/scripts/` | 案例专属原生字段解析、来源核验编排、分析与绘图脚本 |
| `benchmark_source/` | 资料文件、配置、来源证据及生成的核验结果 |
| 根目录 `tests/` | 按功能域集中维护回归测试；不在案例目录复制共用测试 |

`SeismoAgentBench/` 只接收可跨案例复用的代码，不包含具体地震的目录选择、科学阶段、坐标范围、图件布局或专属分析内容。这类逻辑保留在 `benchmark_source/<case>/scripts/`；仅服务单个案例的辅助函数先在案例内维护，出现明确复用需求后再提取公共接口。原始资料、配置和生成图件仍分别保存在案例的 `data/`、`analysis/` 等相应目录。

专业逻辑应按领域命名并形成明确模块，而不是全部堆入 `utils/`。例如后续实际实现波形处理或目录操作时，再建立对应专业模块；不提前创建没有实现的 `core/`、`models/` 或 `pipelines/`。目前 `source_prepare/catalog.py` 中的函数服务于来源核验；当专业模块确实需要复用时，再抽取相应领域基础能力，避免反向依赖整个资料准备流程。

根包及 `utils` 的 `__init__.py` 只说明职责，不批量导入子模块，不在导入时加载数据或执行核验。source 命令保留在子包入口，不把它设置为整个项目的默认 CLI。评测后续独立组织，不放进 `source_prepare/`。

## 使用

从仓库根目录运行，使用 Python 3.10+ 和 PyYAML：

```bash
python -B -m SeismoAgentBench.utils.source_prepare validate-sources --case-dir benchmark_source/2019_ridgecrest_california
python -B -m SeismoAgentBench.utils.source_prepare inventory --case-dir benchmark_source/2019_ridgecrest_california
python -B -m SeismoAgentBench.utils.source_prepare validate-sources --case-dir benchmark_source/2019_ridgecrest_california --verify-files
python -B -m unittest discover -s tests -v
```

库调用使用明确的子模块路径，例如：

```python
from SeismoAgentBench.utils.source_prepare.sources import load_case, inventory
```

旧的 `seismoagentbench` 导入与 `python -m seismoagentbench` 命令已替换，不保留第二份实现。来源契约及数据组织规则见 [benchmark_source/README.md](../benchmark_source/README.md)。当前只有 Ridgecrest 接入来源契约 v2，其余案例的迁移范围没有因包路径调整而改变。

## 测试边界

自动化测试统一放在根目录 `tests/`，按功能域组织。当前 source 工具只保留 `tests/source_prepare/test_registry.py` 与 `test_catalogs.py` 两个测试模块，同类输入差异使用参数表；不为每个新 case 复制一套。完整来源文件核验仍通过工具命令显式执行。新增或修改测试遵守 [测试维护规则](../tests/AGENTS.md)。
