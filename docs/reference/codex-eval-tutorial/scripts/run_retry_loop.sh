#!/bin/bash
# capacity 重试循环模板：每 20 分钟一轮 resume，直到全部 completed
# 用法: run_retry_loop.sh <spec.yaml> <output_root> [max_rounds]
SPEC="${1:?spec}"; ROOT="${2:?output_root}"; MAX="${3:-15}"
cd /chenhao1data/workspace_n/projects/earth_data_agent_bench/GeoDataBench
source /root/.geodatabench/openai_proxy.env
export HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy=https_proxy="$HTTPS_PROXY" no_proxy="$NO_PROXY"
PY=/chenhao1data/workspace_n/envs/shared311/bin/python
LOG="$ROOT/retry.log"
done_count() { find "$ROOT" -name unit_result.json -not -path '*/input/*' \
  -exec grep -l '"status": "completed"' {} + 2>/dev/null | wc -l; }
for i in $(seq 1 "$MAX"); do
  n=$(done_count)
  echo "[retry] round $i completed=$n $(date -u +%FT%TZ)" >> "$LOG"
  $PY -m geodatabench run "$SPEC" --resume-root "$ROOT" >> "$LOG" 2>&1
  echo "[retry] round $i rc=$? completed=$(done_count)" >> "$LOG"
  sleep 1200
done
