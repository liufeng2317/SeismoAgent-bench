# SeismoAgentBench 代码包

`SeismoAgentBench/` 是 benchmark 的可复用代码：任务与输入契约、Agent 运行与记录、评分（含地震目录指标）以及资料准备工具。工作流规范见 [00_Workflow_Specification.md](../docs/framework/00_Workflow_Specification.md)，运行目录与记录见 [01_Run_Layout_and_Records.md](../docs/framework/01_Run_Layout_and_Records.md)，目录指标见 [02_Catalog_Metrics.md](../docs/framework/02_Catalog_Metrics.md)。Python 导入路径区分大小写，统一使用 `SeismoAgentBench`。

```text
SeismoAgentBench/
├── cli.py                  # python -m SeismoAgentBench <command>
├── task/                   # task spec、输入 manifest、输出约定的校验与 Agent prompt 渲染；schemas/ 为 JSON schema
├── agent/                  # Agent 身份与命令契约（tools.py 的工具适配器目前不参与运行）
├── execution/              # 运行目录、子进程执行、Claude/Codex 命令构造、配置校验、运行记录
├── workflow/               # run_agent、evaluate_run、experiment：把执行、记录、评分串起来
├── scoring/                # 评分注册表；artifact-contract@1、catalog-metrics@1
│   └── catalog_metrics/    # 地震目录指标 v2：匹配、L0–L7、可信目录判定、基线、ladder、组件替换、盲审
├── reporting/              # 运行报告、批量汇总、transcript 解析与用量统计
├── configs/                # agents/、environments/（含依赖清单与主机工具安装脚本）、prompts/
└── utils/source_prepare/   # 资料准备：来源登记、文件盘点、来源目录诊断
```

## 职责边界

| 位置 | 职责 |
|---|---|
| `SeismoAgentBench/` | 可跨案例复用的代码；不含具体地震的目录选择、坐标范围、图件布局或专属分析 |
| `workflows/tasks/<case>/` | 任务包（`task_<variant>.json`、`prompt_<variant>.md`、`input.json`、输出约定、`run.sh`）、human-in-loop（expert）流程和评估结果 |
| `workflows/data_preparation/` | 下载、解析、抽取和目录审计的批处理入口 |
| `data/<case>/` | 资料、来源证据、案例专属脚本与生成的核验结果 |
| `seismotools/` | 提供给 Agent 和 expert 流程的专业地震工具 |
| 根目录 `tests/` | 按功能域维护的回归测试，规则见 [tests/AGENTS.md](../tests/AGENTS.md) |

根包和子包的 `__init__.py` 不在导入时加载数据或执行核验；专业逻辑按领域建模块，不预先创建空模块。

## 命令

正式运行通过各案例的 `run.sh` 启动，它调用 `run-claude`（Claude Code × GLM，prompt 经标准输入传入）并把运行放在 `workflows/tasks/<case>/runs/<variant>/<harness>/<model>/<run_id>/`：

```bash
VARIANT=tools bash workflows/tasks/2018_kilauea_hawaii/run.sh       # 后台运行，打印 runner 日志位置
python -m SeismoAgentBench status --run-dir <run>                   # 只读：状态、耗时、已有产物
python -m SeismoAgentBench finalize --run-dir <run>                 # 关闭 runner 已丢失的运行
python -m SeismoAgentBench evaluate --run-dir <run>                 # artifact-contract@1 + catalog-metrics@1
python -m SeismoAgentBench.scoring.catalog_metrics {baseline,run,summary,audit,ladder,swap} --task-dir workflows/tasks/<case> [--run-dir <run>]
```

全部子命令：`run-agent`（任意命令作为 Agent）、`run-claude`、`run-codex`、`evaluate`、`status`、`finalize`、`plan-experiment`、`execute-experiment`。批量运行用 experiment YAML：`plan-experiment` 只展开并校验运行单元，`execute-experiment` 依次执行；它是次要路径，正式运行不用。

Agent 配置（`configs/agents/*.yaml`）只允许 `harness`、`model`、`reasoning_effort`、`executable`、`version_command` 和 `auth`（`mode`、`env_file`、`codex_home`）；凭据放在 git 忽略的 env 文件里，不写进 YAML。环境配置（`configs/environments/*.yaml`）选择 Python 解释器和网络、安装策略，启动时探测并写入运行记录。

资料准备工具的用法：

```bash
python -B -m SeismoAgentBench.utils.source_prepare validate-sources --case-dir data/2019_ridgecrest_california
python -B -m SeismoAgentBench.utils.source_prepare inventory --case-dir data/2019_ridgecrest_california
```

来源契约 v2 目前只有 Ridgecrest 接入；数据组织规则见 [data/README.md](../data/README.md)。

## 测试

```bash
python -B -m unittest discover -s tests -v
```

测试按功能域放在根目录 `tests/`。启动子进程的 runner 和工作流测试在主机负载高时可能因启动慢而报 `execution_timeout`，这类失败与代码改动无关。
