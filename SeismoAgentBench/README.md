# SeismoAgentBench 代码包

`SeismoAgentBench/` 承载项目后续的专业代码和支撑工具。来源整理是 `utils/` 下的一个子功能，不代表整个 benchmark 架构。Python 导入路径区分大小写，统一使用 `SeismoAgentBench`。

```text
SeismoAgentBench/
├── __init__.py
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
| `SeismoAgentBench/` 下的专业模块 | 后续可复用的领域对象、算法和业务逻辑；随具体功能建立 |
| `utils/source_prepare/` | 来源登记、路径/哈希检查、资料盘点与准备阶段的目录诊断 |
| 根目录 `scripts/` | 下载、转换和批处理入口；逐步调用可复用模块，避免复制实现 |
| `benchmark_source/<case>/scripts/` | 案例专属原生字段解析和来源核验编排 |
| `benchmark_source/` | 资料文件、配置、来源证据及生成的核验结果 |
| 根目录 `tests/` | 共享代码测试；案例专属回归测试继续与案例脚本放在一起 |

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
