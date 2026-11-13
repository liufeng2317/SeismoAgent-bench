# 脚本

按 `docs/design.md` 第 4 节的六个部分分文件夹，`results/`、`logs/` 用同样的文件夹名；文件名带部分和步骤编号：

| 部分 | 文件夹 | 例子 |
|---|---|---|
| a 数据与标签 | `a_data_labels/` | `a1_1_download_events.py`、`a1_2_candidate_regions.py`、`a2_2_label_stats.py` |
| b 基线流水线 | `b_baseline/` | `b1_pipeline.py`、`b2_scoring.py`、`b3_core_baselines.py` |
| c 预实验 | `c_pre_experiments/` | `c1_readout.py`、`c2_residual_limits.py` |
| d 单事件对比 | `d_single_event/` | `d1_more_baselines.py`、`d2_harness.py`、`d4_h1.py` |
| e 跨事件学习 | `e_learning/` | `e2_learning.py` |
| f 扩展 | `f_scale_up/` | `f1_tiered.py` |

文件夹在用到时再建。

- 共用代码放在 `scripts/` 顶层（`paths.py`，以后的 `common.py`；不要再建同名文件夹）。各部分的脚本启动时把 `scripts/` 加进导入路径，`data/` 和 `results/` 下的路径只经由 `paths.py` 读取，不写死。
- 默认参数就是最终运行的参数；每次运行用独立的输出目录，目录已存在时拒绝写入。
- 调研阶段的临时分析脚本留在 `docs/brain_storm/deep_research/scripts/`，不在这里。
