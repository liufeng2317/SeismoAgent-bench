#!/usr/bin/env bash
# 收集当前机器的运行环境，以 Markdown 输出到标准输出。
# 用法：bash collect_env.sh [conda 环境名] > docs/environment.md
# 不给环境名时用当前激活的环境；没有的命令（nvidia-smi、conda、sinfo）跳过并注明。
set -u

env_name="${1:-${CONDA_DEFAULT_ENV:-}}"
has() { command -v "$1" >/dev/null 2>&1; }
fence() { printf '```\n'; "$@" 2>&1; printf '```\n'; }

echo "# 运行环境"
echo
echo "记录时间：$(date '+%Y-%m-%d %H:%M')；主机：$(hostname)；用户：${USER:-$(id -un)}"
echo
echo "由 collect_env.sh 自动生成；“可访问的集群”一节需要手动补充。环境有变化时重新生成，并在 changelog 记一行。"

echo
echo "## 本机"
echo
os_name="$( . /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-}")"
cpu_model="$(lscpu 2>/dev/null | sed -n 's/^Model name: *//p' | head -1)"
echo "- 系统：${os_name:-未知}（内核 $(uname -r)）"
echo "- CPU：${cpu_model:-未知}；本进程可用 $(nproc) 核，机器共 $(nproc --all) 核"
echo "- 内存：$(free -h | awk '/^Mem:/{print $2 " 总量，" $7 " 可用"}')（登录节点等有每人限额时，以限额为准，手动注明）"
echo "- 当前目录所在磁盘：$(df -h . | awk 'NR==2{print $1 "，" $2 " 总量，" $4 " 可用"}')"

echo
echo "## GPU"
echo
if has nvidia-smi; then
  cuda="$(nvidia-smi 2>/dev/null | sed -n 's/.*CUDA Version: *\([0-9.]*\).*/\1/p' | head -1)"
  echo "驱动支持的 CUDA 版本：${cuda:-未知}"
  echo
  fence nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader
else
  echo "未找到 nvidia-smi，本机没有可用的 NVIDIA GPU。"
fi

echo
echo "## Python 和 conda"
echo
if has conda; then
  echo "- conda：$(conda --version 2>&1)，安装在 $(conda info --base 2>/dev/null)"
  if [ -n "$env_name" ]; then
    py="$(conda run -n "$env_name" python --version 2>&1 | tail -1)"
    echo "- 本任务使用的环境：\`$env_name\`（$py）"
    echo "- 完整依赖：\`conda env export -n $env_name --no-builds > docs/conda_env.yml\`"
  else
    echo "- 本任务使用的环境：未指定（运行时给出环境名，或先激活环境再运行）"
  fi
  echo
  echo "全部环境："
  echo
  fence conda env list
else
  echo "未找到 conda。系统 Python：$(python3 --version 2>&1)"
fi

echo
echo "## 可访问的集群"
echo
if has sinfo; then
  echo "本机可以提交 Slurm 作业（集群：$(scontrol show config 2>/dev/null | sed -n 's/^ClusterName *= *//p')）。分区概况："
  echo
  fence sinfo -s
  echo
  echo "账户和 FairShare："
  echo
  fence sshare -U
else
  echo "本机未检测到 Slurm。"
fi
echo
echo "<!-- 若还可访问其他集群，按下表手动填写；没有就删掉此表并写“无”。 -->"
echo
echo "| 集群 | 登录方式 | 分区 / 队列 | 账户 | 每人限额（登录节点、作业） | 存储路径 | 备注 |"
echo "|---|---|---|---|---|---|---|"
echo "| 待填写 |  |  |  |  |  |  |"
