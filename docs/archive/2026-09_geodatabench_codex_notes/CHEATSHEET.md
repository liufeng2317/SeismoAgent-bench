# 一页速查（CHEATSHEET）

## 开工五查
```bash
codex --version                                            # CLI
bwrap --ro-bind / / --dev /dev --proc /proc true; echo $?  # 沙箱（本机=封）
test -f /root/.geodatabench/openai_proxy.env && echo ok    # 代理
test -f /root/.cache/dev-platform/codex-home/dev-d/auth.json && echo auth
/chenhao1data/workspace_n/envs/shared311/bin/python -V
```

## 常用命令
```bash
PY=/chenhao1data/workspace_n/envs/shared311/bin/python
cd GeoDataBench

# 干跑矩阵（零调用）
$PY -m geodatabench list <spec.yaml>

# 带代理起跑
source /root/.geodatabench/openai_proxy.env && export HTTP_PROXY HTTPS_PROXY NO_PROXY \
  http_proxy=https_proxy="$HTTPS_PROXY" no_proxy="$NO_PROXY"
$PY -m geodatabench run <spec.yaml> -v

# 断点续跑（跳过 completed）
$PY -m geodatabench run <spec.yaml> --resume-root <output_root> [--task <id>...]

# 官方 wrapper（model-check+退避+manifest）
$PY scripts/run_model_series.py --config <spec> --manifest <m.json> \
  --allow-host-smoke --max-attempts 6 --retry-initial-delay-s 120 --retry-max-delay-s 600

# 旁路重评（不改 unit_result）
PYTHONPATH=<仓库根> $PY scripts/rescore_results.py <output_root> \
  --data-root <runtime视图> --task <id> --summary-name rs.json

# kanban 重建+校验
cd ../1-paper/2-exp/1-kanban && $PY build_case_model_matrix.py && $PY build_case_model_matrix.py --check-only
```

## 关键判断
- capacity("Selected model is at capacity") → 重试循环
- usage limit("hit your usage limit") → 停机留证
- evaluator_internal_error → 先查布局（教程§8表），多数可官方旁路
- frednet 完整输出 → 本机 bwrap fixture 不可验证，如实记 infra

## 黄金规则
1. host 模式 effort 必须 extra_args 钉 `-c`
2. 台账 json+md 两边同步；行带 case_version；旧行 superseded 不删
3. kill 用 [x] 括号 pattern 防自匹配
4. done-count 用 find 不用 Python 递归 glob
5. 新战役独立 output_root；数据根优先用统一 alias 视图
