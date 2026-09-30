#!/bin/bash
# 75 分钟 unit 看门狗：防止慢/挂 unit 阻塞串行队列（被杀 unit 由 resume 补）
# 用法: unit_watchdog.sh "<codex 进程匹配串>" [最长秒数, 默认 4500]
PAT="${1:?pattern e.g. codex exec --model gpt-6-astra}"; LIMIT="${2:-4500}"
LOG=/tmp/watchdog-$(echo "$PAT" | md5sum | cut -c1-8).log
while true; do
  pid=$(pgrep -f "vendor/aarch64.*$PAT" | head -1)
  if [ -n "$pid" ] && [ -d "/proc/$pid" ]; then
    age=$(( $(date +%s) - $(stat -c %Y "/proc/$pid") ))
    [ $age -gt "$LIMIT" ] && { echo "$(date -u +%FT%TZ) kill pid=$pid age=${age}s" >> "$LOG"; kill -9 "$pid"; }
  fi
  sleep 60
done
