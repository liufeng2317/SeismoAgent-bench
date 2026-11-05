#!/usr/bin/env bash
# End-to-end smoke test of the run package, the checker and the scorer, without a model (checker freeze, 2026-11-05).
# The runner starts scripted_agent.py in place of the Agent on a back-end arm; the scorer then scores the run with
# its checker audit. Runs go to workflows/tasks/<case>/runs_smoke/ (scorable, never in the summary).
# Usage: run.sh [CASE] [VARIANT] [SOURCE_RUN]  (defaults: Kilauea, backend_knowledge, its 2026-11-03 run); VARIANT may be a
# full-pipeline arm (task_<variant>.json in the case folder) or a back-end arm (in backend/)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CASE="${1:-2018_kilauea_hawaii}"
VARIANT="${2:-backend_knowledge}"
TASK="$ROOT/workflows/tasks/$CASE"
SOURCE="${3:-$TASK/runs/backend_knowledge/claude/glm-5.3/20261103T010127Z}"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
SCORE_PYTHON="${SCORE_PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
RUN_ROOT="$TASK/runs_smoke/$VARIANT/scripted/none"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
cd "$ROOT"
SPEC_DIR="$TASK"; if [ ! -f "$SPEC_DIR/task_$VARIANT.json" ]; then SPEC_DIR="$TASK/backend"; fi  # full-pipeline or back-end arm
"$PYTHON" -m SeismoAgentBench run-agent --task "$SPEC_DIR/task_$VARIANT.json" --input "$SPEC_DIR/input_$VARIANT.json" \
  --agent-name "scripted-smoke" --agent-version 1 --run-root "$RUN_ROOT" --run-id "$RUN_ID" --timeout 7200 \
  -- "$PYTHON" -I "$ROOT/workflows/development/smoke_end_to_end/scripted_agent.py" \
     --source-run "$SOURCE" --checker "$ROOT/seismo_checker"
"$SCORE_PYTHON" -m SeismoAgentBench.scoring.catalog_metrics run --task-dir "$TASK" --run-dir "$RUN_ROOT/$RUN_ID"
echo "run: $RUN_ROOT/$RUN_ID"
