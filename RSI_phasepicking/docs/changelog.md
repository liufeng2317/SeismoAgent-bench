# 修订记录

- 2026-11-13：b2 完成：共享评分模块 `scripts/scoring.py`、四张评分图；拾取检测、AIC 精修、网络触发和波形图全部改用因果滤波（零相位滤波使 M4 事件的 P 早约 1 s），B0 的 P 平均绝对误差从 0.076 s 降到 0.026 s，三种方法在新流水线上重跑。
- 2026-11-13：b1 完成：共享模块 `scripts/pipeline.py`、`pickers.py`、`viz.py` 和 `b_baseline/b1_pipeline.py`；B0、B1、B8 在第一批 40 个事件上走通；design 5.1 更新事件窗规则、B0 的 S 拾取方法（弃用 `ar_pick`）和关联门槛。
- 2026-11-13：研究问题改为递进的 Q1–Q4（持续提升 → RSI 可行 → 上限对比 DL → OOD 专家），原 H1c、H4 降为辅助问题 S1、S2；design 和 registry 中的引用同步替换。
- 2026-11-13：基线改为三层（基础 STA/LTA + AIC、DL 强基线、agent + 强基线）；H1 改为“只用经典工具的 agent 离 DL 天花板多近”，新增 H1b（agent + 强基线在 OOD 上的改进），原 H1b 改为 H1c；design 5.1、5.2、5.3、5.10 和第 4 节、registry 的 b、c、d 同步修改；新增强基线 B-ens（DL 集成），原 B6 改为 B0。
- 2026-11-13：权重改为链接 TRACE-2.0 的 SeisBench 预训练权重库（`data/models/seisbench/models`，离线加载），删除单独下载的副本（两者逐字节相同）。
- 2026-11-13：下载 PhaseNet SCEDC 权重到 `data/models/phasenet/`；design 5.1 写明阈值和短周期台的通道组合（EHZ + HNE + HNN）。
- 2026-11-13：a1 第 3 轮完成：选定 R2，第一批 40 个事件、30 个台站，下载事件窗波形和仪器响应；a2 生成第一批参考拾取表并抽查波形。
- 2026-11-13：a1、a2 第 1 轮完成：下载全部事件列表，提出候选区 R1–R4，统计 582 个 M≥2.5 事件的人工拾取比例等（`results.md`）。
- 2026-11-13：scripts、results、logs 改为按 design 的部分分文件夹（当前只有 `a_data_labels/`）；`paths.py` 增加各部分的结果目录；整理脚本和移动清单在 `logs/reorganize/`；移动后重跑 a1_2，结果与移动前一致。
- 2026-11-13：基础 baseline 区域改为 Ridgecrest/Coso 以外（由 a1 选定）；测试候选按人工拾取比例而不是模型训练截止划分；第一批波形只取几十个事件；registry a1、a2 细化。
- 2026-11-13：基线定位模型改为 SCSN 版 Hadley–Kanamori 模型（Hutton et al. 2010 表 5），不用上游的 `UCVM_HK_1D`（CVM-S 版本，层值不同）。
- 2026-11-13：基线流水线移到预实验之前（a 数据与标签 → b 基线流水线 → c 预实验 → d 单事件对比）；design 新增 5.1“基线流水线”（每个环节的固定选择和理由、第一轮核心基线、打通标准），5.2 补充固定流程 F-fixed 的步骤；registry 同步重排。
- 2026-11-13：按 research-task-setup 建立任务目录（docs/data/scripts/results/logs）；生成 `environment.md`（环境 `seismoagent_eval`，本机无 GPU）；`docs/design.md` 按 skill 结构重写，讨论稿保留在 `brain_storm/design.md`；新建 `registry.md`、`results.md`；`data/` 链接上游 Ridgecrest 波形（上游提交 367f80a）。
- 2026-11-13：依据 deep research 修订讨论稿 `brain_storm/design.md`（上一版在 `weekly_highlight/20261111/design.md`）。
- 2026-11-13：完成 16 个方向的 deep research（`brain_storm/deep_research/`）。
- 2026-11-13：整理 Advikar 试点报告（`brain_storm/advikar_pilot_summary.md`）。
