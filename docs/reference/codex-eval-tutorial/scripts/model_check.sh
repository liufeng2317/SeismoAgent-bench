#!/bin/bash
# 模型可用性小探针：一次 "Reply OK" 调用，验证 slug/认证/代理
MODEL="${1:?usage: model_check.sh <model-slug>}"
source /root/.geodatabench/openai_proxy.env
export HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy=https_proxy="$HTTPS_PROXY" no_proxy="$NO_PROXY"
OUT=$(mktemp -d)
timeout 120 codex exec --model "$MODEL" --json --skip-git-repo-check --ephemeral \
  --ignore-user-config --ignore-rules -c 'model_reasoning_effort="low"' \
  >"$OUT/t.jsonl" 2>"$OUT/e.log" <<< "Reply with exactly OK" || true
grep -q '"text":"OK"' "$OUT/t.jsonl" && echo "MODEL_OK $MODEL" || {
  echo "MODEL_FAIL $MODEL"; tail -3 "$OUT/t.jsonl" "$OUT/e.log"; }
echo "evidence: $OUT"
