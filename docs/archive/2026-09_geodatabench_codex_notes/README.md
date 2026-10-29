# 本机 Codex CLI 沙箱评测教程（earth_data_agent_bench / dev-d 宿主）

> 基于本项目 2026-09-20 ~ 09-24 的实跑经验整理（gpt-5.6-sol / gpt-6-astra / gpt-6-luna 三模型 × 40 Case × Base/Open 全量矩阵 + 多轮 capacity 重试）。
> 所有命令均在 `/chenhao1data/workspace_n/projects/earth_data_agent_bench` 下验证过。

---

## 0. 一图流：评测链路

```
experiment YAML ──> geodatabench run ──> 每个 (agent, task, variant) 一个 unit：
                                          1. runs/<root>/<task>/<variant>/<agent>/<run_id>/
                                          2. symlink 公共 input（data_root/<task>/input）
                                          3. codex exec --model <slug> --json < prompt
                                          4. agent 写 output/
                                          5. agent 退出后：task/main.py evaluate(output, 私有 reference)
                                          6. unit_result.json + _batches/<run_id>/summary.json
```

- Agent **看不到** reference/expert_product（评分在 agent 退出后由宿主进行）
- transcript.jsonl 是完整事件流（含 usage tokens）；评分、资源、证据都在 unit 目录里

---

## 1. 前置检查（每次开工先跑）

```bash
cd /chenhao1data/workspace_n/projects/earth_data_agent_bench

# 1) codex CLI
codex --version                      # 当前 0.156.0

# 2) 沙箱能力（决定你用哪种隔离模式，见 §2）
bwrap --ro-bind / / --dev /dev --proc /proc true && echo OK || echo BLOCKED
# 本机现状：BLOCKED（Creating new namespace failed: Operation not permitted）
# → 只能 host-direct 模式；bubblewrap 正式模式需换有 unprivileged userns 的宿主

# 3) 网络代理（直连 chatgpt.com/api.openai.com 会被 reset，必须走平台 closeai 代理）
test -f /root/.geodatabench/openai_proxy.env && echo proxy_OK
# 不存在就跑 scripts/setup_proxy_env.sh 重新生成（宿主 /root 会被定期清，重生成是常规操作）

# 4) 评测 Python
/chenhao1data/workspace_n/envs/shared311/bin/python --version   # 3.11.x

# 5) 认证（平台注入，不要动）
test -f /root/.cache/dev-platform/codex-home/dev-d/auth.json && echo auth_OK
```

---

## 2. 两种隔离模式

| | bubblewrap 沙箱（正式） | host-direct（本机现实） |
|---|---|---|
| 配置 | `isolation: bubblewrap` | `isolation: none` + `use_host_home: true` |
| 输入 | 只读挂载 `/work/input`，输出 bind `/work/output`，工具网络可禁 | 工作目录内自由访问（Agent 靠任务合同约束） |
| 本机可用性 | ❌ namespace 被封 | ✅ 本次全部战役都用它 |
| effort 传递 | YAML `reasoning_effort` 会自动转成 `-c` 参数 | ⚠️ **不会**！必须手动 `extra_args` 钉定（见 §4 大坑） |

模板见 `templates/agent_config_bubblewrap.yaml`（换宿主后直接可用）与 `templates/agent_config_host.yaml`（本机用）。

---

## 3. 最小可运行示例（5 分钟）

```bash
cd GeoDataBench

# 干跑：只列 unit 矩阵，零模型调用
/chenhao1data/workspace_n/envs/shared311/bin/python -m geodatabench list configs/example.yaml

# 单 unit 冒烟（会真实调用模型）
source /root/.geodatabench/openai_proxy.env && export HTTP_PROXY HTTPS_PROXY NO_PROXY \
  http_proxy=https_proxy="$HTTPS_PROXY" no_proxy="$NO_PROXY"
/chenhao1data/workspace_n/envs/shared311/bin/python -m geodatabench run <你的spec.yaml> -v
```

---

## 4. Agent 配置详解（含本机三大坑）

`templates/agent_config_host.yaml` 逐行注释版：

```yaml
harness: codex
model: gpt-6-astra            # slug 见 §7；gpt-6 裸名会被 ChatGPT 账号 400 拒绝
provider: direct              # 走平台认证；GLM 系用 base_url: https://api.z.ai/api/v1
base_url: null
api_key: null                 # direct 模式不要填 key
config:
  use_host_home: true         # 继承平台 CODEX_HOME 认证（/root 被清后依然有效）
  env_file: /root/.geodatabench/openai_proxy.env   # 只注入 proxy 变量，不挂进 Agent
  yolo: true
  sandbox_mode: danger-full-access
  isolation: none             # 本机 bwrap 不可用；见 §2
  reasoning_effort: medium    # ⚠️ host 模式下这行不会传给 CLI！
  disable_python_bytecode: true
  extra_args:
    - "-c"
    - 'model_reasoning_effort="medium"'   # ✅ 必须显式钉定；transcript 不记录 effort
```

**本机三大坑：**
1. **effort 不传递**：`_build_argv` 只在 bubblewrap 分支加 `-c model_reasoning_effort`；host 模式必须 `extra_args`，并在 run.log 里留 argv 证据
2. **直连被墙**：不开 closeai 代理时 codex 反复 `Connection reset by peer`
3. **`~/.codex` 不存在**：认证在平台 CODEX_HOME；`use_host_home: true` 继承即可

---

## 5. Experiment Spec 详解

```yaml
output_root: runs/my_campaign/<agent-id>       # 独立 root，别和历史混
data_root: <绝对路径>                            # <data_root>/<task>/input 会被 symlink
prompt_prefix: ""
prompt_suffix: "\nHost runtime: execute Python with /chenhao1data/workspace_n/envs/shared311/bin/python, not plain python3.\n"
concurrency: 1                                  # capacity 敏感期保持 1
agents:
  - id: <agent-id>
    config: <相对 GeoDataBench 或绝对路径>/agent.yaml
tasks:
  - path: cryosphere/some_case_v07              # = GeoDataBench/tasks/<path>
    variants: [base]                            # base 用 taskPromptBase，open 用 taskPromptOpen
```

**data_root 选择（重要，版本对齐）**：
- 常规 35 Case：`data/geodatabench/1-用于大规模评测的cases`
- solid_earth 4 Case 当前候选：必须用 successor runtime 视图（factory v0.15/v0.9/v0.12/v0.25），否则跑在旧数据上（09-22 版本错位事故）
- glass：`runs/hydrology_glm53_flash_ladder_20260917_r2/_data_aliases`
- id68/id72：共享根没有，会回退 task 目录本地数据（可用）
- **偷懒做法（推荐）**：直接复用统一 alias 根 `runs/gpt6_luna_registry_base_20260923/_data_aliases`（已把 40 Case 全部指对）

---

## 6. 运行、断点续跑与容量策略

### 6.1 单次运行
```bash
cd GeoDataBench
source /root/.geodatabench/openai_proxy.env && export HTTP_PROXY HTTPS_PROXY NO_PROXY \
  http_proxy=https_proxy="$HTTPS_PROXY" no_proxy="$NO_PROXY"
/chenhao1data/workspace_n/envs/shared311/bin/python -m geodatabench run <spec.yaml> -v
```

### 6.2 断点续跑（跳过已 completed 的 unit）
```bash
... run <spec.yaml> --resume-root <output_root 绝对路径> [--task <task_id> ...]
```

### 6.3 官方 wrapper（model-check + capacity 指数退避 + manifest）
```bash
scripts/run_model_series.py --config <spec> --manifest <manifest.json> --allow-host-smoke \
  --max-attempts 6 --retry-initial-delay-s 120 --retry-max-delay-s 600
```
⚠️ wrapper 的坑：出现**非 capacity** 失败（如 host 策略拒绝 rm、git init 超时）会停止整轮重试 → 之后用 6.2 手动补。

### 6.4 capacity 重试循环（实战模板 = `scripts/run_retry_loop.sh`）
- "Selected model is at capacity" 是间歇波动的（窗口 1-2 小时），每 20-30 分钟试一轮即可
- **usage limit**（"You've hit your usage limit... try again at <日期>"）是另一回事：立即停机留证，不要重试
- 慢单元加 **75 分钟看门狗**（`scripts/unit_watchdog.sh`）：杀掉当前 unit 让串行队列继续流动，之后 resume 补

### 6.5 后台常驻的坑
- 外层环境会**周期性收割 detached 进程**：循环脚本要能被重新拉起；done-count 用 `find`（Python glob 递归会跟进 input 符号链接卡死）
- kill 进程时 pattern 加 `[x]` 防止 pkill/pgrep 自匹配把自己的 shell 杀掉（教训 ×2）

---

## 7. 模型 slug 速查（direct 后端，2026-09 实测）

| slug | 状态 |
|---|---|
| `gpt-5.6-sol` / `gpt-5.6-terra` / `gpt-5.6-luna` | ✅ |
| `gpt-6-astra` | ✅（gpt-6 系实际可用名） |
| `gpt-6-luna` | ✅ |
| `gpt-6`（裸名） | ❌ 400: not supported with ChatGPT account |
| GLM 系 | 走 `base_url: https://api.z.ai/api/v1` + `${env:GLM2_API_KEY}`，认证后端不同 |

跑前用 wrapper 的 model-check（"Reply OK" 小调用）验证 slug。

---

## 8. 评分与"旁路 rescore"（evaluator 布局问题清单）

部分 Case 的 in-run 评估会因**数据布局**报 `evaluator_internal_error`（不是模型错！），用官方冻结 evaluator 旁路评分，**不改写原始 unit_result**：

| Case | 方案 |
|---|---|
| ft_hidfa_v11 | `rescore_results.py --data-root .../essd-17-6273-2025/case_factory/v0.11/runtime_v0.11` |
| REA | `--data-root .../essd-17-4005-2025/case_factory/v0.8/runtime_v0.8` |
| barium / gobai | `--data-root GeoDataBench/runs/ocean_glm53flash_ladder_20260916/runtime` |
| glass | `--data-root .../_data_aliases` **且加 `PYTHONPATH=<仓库根>`**（evaluator import 外层 others 包） |
| soil_doc | 直接调冻结 `task/evaluator/verify.py`（同 Case input+reference） |
| sea_ice_age | 组装合并私有视图：verify.py + reference/b_projection + expert_product/c_projection 放同一目录 |
| frednet | ⚠️ 完整输出会触发 bwrap fixture 校验 → 本机无法全量验证（评估器自声明 infra fault）；不伪造分数 |

---

## 9. 台账登记规范（跑完必做）

1. 七圈层 `1-paper/2-exp/<domain>/experiments.{md,json}` 同步更新（**不能只改一边**）
2. 行内带**显式 `case_version`/`successor_version`**（否则 kanban latest-only 选择器会按 case-id 后缀误判为历史版本整行丢弃——09-24 实际踩过）
3. 被重跑取代的旧行标 `superseded_by_*`（保留证据，不删除）
4. `INDEX.{md,json}` 刷新时间戳与描述
5. 重建 kanban：`cd 1-paper/2-exp/1-kanban && python build_case_model_matrix.py && python build_case_model_matrix.py --check-only`
6. capacity/infra 失败保留 raw fallback 证据，不混入正式分数

---

## 10. 故障速查表

| 症状 | 处置 |
|---|---|
| `Selected model is at capacity` | 正常波动：resume 重试循环（20-30 分钟间隔） |
| `You've hit your usage limit` | 配额硬停：立即停机留证，等窗口 |
| `Connection reset by peer`（wss/https） | 代理没开：source proxy dotenv 并 export |
| codex 起不来 rc=-7/135 | CODEX_HOME 在网络 FS 上：host 模式配 use_host_home 或本地 home |
| `git init` TimeoutExpired | 负载抖动，重试即可 |
| agent 用 rm -f 被拒后崩溃 | host 安全策略；重跑通常会换写法 |
| unit 跑 >2h | 看门狗杀掉换路；transcript 先确认是否在慢读 afs |
| kanban 行数 < 预期 | 检查 case_version 标注（§9.2） |

---

## 附：本机速查

- 评测 Python：`/chenhao1data/workspace_n/envs/shared311/bin/python`
- 代理 dotenv：`/root/.geodatabench/openai_proxy.env`（源：`dev-platform/machines/dev-d/state/proxy.env`）
- 统一 40-Case alias 数据根：`GeoDataBench/runs/gpt6_luna_registry_base_20260923/_data_aliases`
- registry：`data/geodatabench/1-用于大规模评测的cases/registry/current_case_index.json`（40 Case）
- 历史权威 run 参考：`runs/gpt6_medium_registry_{base,open}_20260920/`、`runs/gpt6_luna_registry_base_20260923/`
