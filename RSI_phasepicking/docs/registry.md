# 登记表

按 `design.md` 第 4 节的六个部分和步骤组织。新工作先在这里登记再动手；完成一项改一项状态。状态：未开始 / 进行中 / 完成 / 暂停。

脚本、结果、日志按 design 的六个部分分文件夹（`a_data_labels`、`b_baseline`、`c_pre_experiments`、`d_single_event`、`e_learning`、`f_scale_up`），三处同名；文件名带步骤编号，如 `scripts/a_data_labels/a1_2_candidate_regions.py`，结果在 `results/a_data_labels/a1_events/`。

## 0 准备

| 编号 | 做什么 | 完成标准 | 状态 | 结果在哪里 |
|---|---|---|---|---|
| 0.1 | 调研 16 个方向 | 每个方向一份报告，含参考文献和核实状态 | 完成 | `brain_storm/deep_research/` |
| 0.2 | 建立任务目录、记录运行环境 | 目录符合 research-task-setup；`environment.md` 生成 | 完成（集群一节待用户填写） | `docs/` |
| 0.3 | 定下第 9 节的待决定事项 | 用户回复并记入 `results.md` | 未开始 | `results.md` |

## a 数据与标签

| 编号 | 做什么 | 完成标准 | 状态 | 结果在哪里 |
|---|---|---|---|---|
| a1 | 第 1 轮：下载全部事件列表（南加州全区 2020-01 至今、T1、北加州）；按地震活动和台站密度提出 Ridgecrest/Coso 以外的候选区域。第 3 轮：只下选中事件的波形，第一批几十个事件 | 事件列表齐全；候选区域的分布图和统计交用户选定；第一批事件的波形抽查时间和通道无误 | 未开始 | `results/a_data_labels/a1_events/` |
| a2 | 下载候选区域事件的 QuakeML；统计 manual 比例（按年份 × 震级、按台站距离）、权重码、i/e、S/P、每事件拾取数和方位角空隙；剔除 PhaseNet 来源的参考 | 统计表和图齐全；据此定下震级下限、时间窗和入选门槛；每个事件的参考拾取表 | 未开始 | `results/a_data_labels/a2_labels/` |
| a3 | 生成 T3 半合成集和 E 错误注入集 | 各信噪比档、各注入类型样本数达到 design 5.5、5.6 的要求；真值复核通过 | 未开始 | `results/a_data_labels/a3_synthetic/` |
| a4 | 确认 SCSN 与 NCSN 是否共享人工拾取；扩大分析员间差异的样本 | 有明确结论；样本扩到几百个事件后更新 design 第 3 节的表 | 未开始 | `results/a_data_labels/a4_label_noise/` |

## b 基线流水线

| 编号 | 做什么 | 完成标准 | 状态 | 结果在哪里 |
|---|---|---|---|---|
| b1 | 打通主流水线（design 5.1）：事件窗 → PhaseNet（SCEDC 权重）→ PyOcto → Hypoinverse + HK 一维模型；先用南加州练习池 20–50 个事件 | 每个环节有输出；抽查 20 个事件的拾取图；记录所有固定参数（阈值、窗口、模型、台站框） | 未开始 | `results/b_baseline/b1_pipeline/` |
| b2 | 写评分程序并检验；确定拾取匹配窗口 | 单元测试通过（人工构造的偏差、漏拾、误拾）；B8 定位与目录位置之差的分布合理 | 未开始 | `results/b_baseline/b2_scoring/` |
| b3 | 在各数据集上跑核心基线 B8、B1、B5、R0、R1 | 每个数据集每组都有拾取和定位结果；B1 与 manual 标签的一致性与公开报告的水平同一量级 | 未开始 | `results/b_baseline/b3_core_baselines/` |

## c 预实验

| 编号 | 做什么 | 完成标准 | 状态 | 结果在哪里 |
|---|---|---|---|---|
| c1 | 读图校准：窗口宽度 × 刻度 × 候选线（来自 B1、B5）× 图宽 × 数值摘要，约 5 个模型，每条件约 100 张图（单轮，可走 Batch） | 误差随“每 token 秒数”变化的曲线；定下放大窗口和绘图参数；判断开源模型能否作分级的第一层 | 未开始（启动前问费用） | `results/c_pre_experiments/c1_readout/` |
| c2 | 残差能力边界：练习池 VELEST 冻结速度模型和台站校正；E 集上 R0/R1 的检出率 | 各注入类型 × importance 分层的检出率表 | 未开始 | `results/c_pre_experiments/c2_residual_limits/` |
| c3 | 日本失效地图（若选日本）：原版 / `jma` / `phasenet_sn` 走主流水线，在能登、福岛县冲事件上的误差和召回 | 台网 × 震相 × 震级档的误差表；圈出本地重训模型仍明显差的格子 | 未开始（取决于 0.3） | `results/c_pre_experiments/c3_japan_failure_map/` |

## d 单事件对比

| 编号 | 做什么 | 完成标准 | 状态 | 结果在哪里 |
|---|---|---|---|---|
| d1 | 补全基线：B2–B4b、B6、B7（极性）、R2（用 c2 冻结的台站校正） | 每个数据集每组都有拾取、极性和定位结果 | 未开始 | `results/d_single_event/d1_more_baselines/` |
| d2 | 搭建 harness：工具、图件、宿主机定位、决策记录、泄漏检查；实现 F-fixed | 在 5 个事件上端到端跑通 | 未开始 | `results/d_single_event/d2_harness/` |
| d3 | 基础测试集上跑 A0、F-fixed、A-bestofN、A-expert | 各组结果和成本 | 未开始 | `results/d_single_event/d3_single_event/` |
| d4 | T1 分层 400 个事件 + T3 上跑核心组（每组 3 次重复） | H1、H1b 结果；按事件整群的置信区间 | 未开始（启动前问费用；估计约 4,800 次运行，标准价约 $2.4–3.6k） | `results/d_single_event/d4_h1/` |

## e 跨事件学习

| 编号 | 做什么 | 完成标准 | 状态 | 结果在哪里 |
|---|---|---|---|---|
| e1 | 开源模型上 10–20 条 50 事件短学习流 | 流间标准差估计；定下正式流数 | 未开始 | `results/e_learning/e1_pilot_streams/` |
| e2 | 正式学习流（A-label、A-physics、A-placebo 及次要组） | 每组达到定下的流数；门控统计（提议、接受、拒绝原因） | 未开始 | `results/e_learning/e2_learning/` |
| e3 | 闭源模型方向确认（3 组 × 3 条流） | 与开源模型方向是否一致 | 未开始（启动前问费用；估计约 4,000 次运行，标准价约 $2.0–3.0k） | `results/e_learning/e3_closed_model/` |
| e4 | 选择集上选最终记忆；整理；测试集评估 | H2、H3 结果；H3 恢复比例的置信区间 | 未开始（闭源部分估计约 3,600 次运行，标准价约 $1.8–2.7k） | `results/e_learning/e4_selection_test/` |

## f 扩展

| 编号 | 做什么 | 完成标准 | 状态 | 结果在哪里 |
|---|---|---|---|---|
| f1 | T1 全量分级处理 | 整个序列的 agent 目录；成本–性能曲线 | 未开始 | `results/f_scale_up/f1_tiered/` |
| f2 | 高难场景（日本子场景或火山） | 原版 / 本地重训 / agent / agent+重训初值 四组对比 | 未开始（取决于 0.3） | `results/f_scale_up/f2_hard/` |

## 待用户决定（0.3）

- 高难场景选日本（能登 / S-net / M≥4）还是火山（VCSEIS）；若选日本，谁注册 Hi-net 账号。
- 主力闭源模型和预算上限；gpt-6.1-sol 能否用 Flex（不能的话，上面的费用估计不打折）。
- 集群 GPU 配额，能否部署 Qwen3.8-27B（老师目前部署的是 Gemma）；`environment.md` 的集群一节。
- 老师是否接受 H3 的新写法（“恢复标签反馈收益的比例”，限于粗差）。
- 投稿首选和预印本时间。

费用估计按每事件 $0.50–0.75 的标准价推算（2026-11-13 的价格），详见 `brain_storm/design.md` 第 9.3 节。
