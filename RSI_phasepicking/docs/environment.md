# 运行环境

记录时间：2026-11-13 09:13；主机：earthquake-agent-cpu2-worker-0；用户：liufeng1

由 collect_env.sh 自动生成；“可访问的集群”一节需要手动补充。环境有变化时重新生成，并在 changelog 记一行。

## 本机

- 系统：Ubuntu 22.04.5 LTS（内核 5.15.0-25-generic）
- CPU：Kunpeng-920；本进程可用 64 核，机器共 192 核
- 内存：2.0Ti 总量，1.9Ti 可用（登录节点等有每人限额时，以限额为准，手动注明）
- 当前目录所在磁盘：/pvc-c09b7260-9cae-4bc7-be3f-4455bfb168a2，1.0T 总量，33G 可用

## GPU

未找到 nvidia-smi，本机没有可用的 NVIDIA GPU。

## Python 和 conda

- conda：conda 26.1.1，安装在 /liufeng1afs/software/miniconda3
- 本任务使用的环境：`seismoagent_eval`（Python 3.9.25）
- 完整依赖：`conda env export -n seismoagent_eval --no-builds > docs/conda_env.yml`

全部环境：

```

# conda environments:
#
# * -> active
# + -> frozen
base                     /liufeng1afs/software/miniconda3
InternAgent              /liufeng1afs/software/miniconda3/envs/InternAgent
adfwi                    /liufeng1afs/software/miniconda3/envs/adfwi
autoresearch             /liufeng1afs/software/miniconda3/envs/autoresearch
bvalue                   /liufeng1afs/software/miniconda3/envs/bvalue
earthagent               /liufeng1afs/software/miniconda3/envs/earthagent
inversionagent           /liufeng1afs/software/miniconda3/envs/inversionagent
rsync-tool               /liufeng1afs/software/miniconda3/envs/rsync-tool
seismoagent              /liufeng1afs/software/miniconda3/envs/seismoagent
seismoagent_eval         /liufeng1afs/software/miniconda3/envs/seismoagent_eval
trace                    /liufeng1afs/software/miniconda3/envs/trace

```

## 可访问的集群

本机未检测到 Slurm。

<!-- 若还可访问其他集群，按下表手动填写；没有就删掉此表并写“无”。 -->

| 集群 | 登录方式 | 分区 / 队列 | 账户 | 每人限额（登录节点、作业） | 存储路径 | 备注 |
|---|---|---|---|---|---|---|
| 待填写 |  |  |  |  |  |  |
