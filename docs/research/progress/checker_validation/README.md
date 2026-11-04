# checker 检验记录

设计文档 [`../../04_Checker_Design.md`](../../04_Checker_Design.md) 只写 checker 现在是什么、为什么这样设计、得到了哪些经验；每一轮检验的方法、数据和读数按主题记在这里，按时间顺序编号。文件写成后只补更正，不改写结论；后来推翻或修改的结论在原处注明。

| 文件 | 时间 | 内容 |
|---|---|---|
| [`01_first_validation.md`](01_first_validation.md) | 2026-10-30 至 10-31 | 1.0 在 human-in-loop 定位轮次和第一轮正式运行上的检验；合成回归测试；有效性分类（有效、部分有效、无效、错误）；对可信标准的覆盖；附录为 1.0 各阶段检查表的原始读数 |
| [`02_replay_compare_pilot.md`](02_replay_compare_pilot.md) | 2026-10-31 | 离线重放（A 层）；`compare.py` 在换速度模型场景上的判定；Prague 台阶界面堆积；小批量能否代表全量；`scope` 和小批量协议 |
| [`03_attribution_and_thresholds.md`](03_attribution_and_thresholds.md) | 2026-11-01 | 依据质控文献的归因诊断及验证；尾波漏检扫描（未采用）；按文献复核门槛 |
| [`04_tier_b_backend.md`](04_tier_b_backend.md) | 2026-11-01 至 11-03 | B 层后端任务六个案例的结果；单因素归因要点（逐运行审计在 [`../backend_audit/`](../backend_audit/README.md)） |
| [`05_near_surface_magnitude_matching.md`](05_near_surface_magnitude_matching.md) | 2026-11-03 | 不给区域模型时能否约束近地表；震级标度压缩的来源；`compare.py` 规则的一项检验；模板匹配阶段的评估 |
| [`06_trial_and_tool_fixes.md`](06_trial_and_tool_fixes.md) | 2026-11-03 至 11-04 | 统一测试试水批次（Kīlauea × 三个后端变体，checker 1.2）；之后的离线修复（Wadati 门槛、NonLinLoc 搜索顶面、HypoInverse CRE、hypoDD 基准面、知识条目） |
| [`07_scoring_questions.md`](07_scoring_questions.md) | 2026-11-04 | 评分口径：震级斜率最少 30 对、`inside_region` 按台站覆盖判定（已定）；偏移门槛与最终目录自身的定位误差（2026-11-05，待定） |
| [`08_velocity_from_data.md`](08_velocity_from_data.md) | 2026-11-03 至 11-04 | 不给区域模型时从数据建最小一维模型（整列缩放加台站校正，按残差选）：四个案例有用、一个无变化、一个出错；阻尼无效；残差附近模型的深度离散是不确定度下限 |
| [`09_horizontal_shift.md`](09_horizontal_shift.md) | 2026-11-05 | 水平偏移的逐项替换：拾取和台站组合几乎不贡献；Kaikōura、Maple 来自台站延迟，Magna、Ridgecrest 来自最终目录的双差框架；只写进知识，不加检查（评分口径问题在 07 第 3 条） |
| [`10_template_threshold.md`](10_template_threshold.md) | 2026-11-05 | 模板匹配的门槛、误检与召回：零假设检验在六个案例都给出 9.5；去掉模板匹配，最终目录只剩 8–56 % 的事件；五个 tools 运行没有把模板匹配检测加进目录 |

检验用到的工具：`workflows/development/tools_case_validation/validate_checker.py`（在 human-in-loop 轮次和正式运行上跑 checker）、`seismotools/checker/examples/smoke/run.sh`（合成回归测试）、`workflows/development/replay/`（离线重放和诊断脚本）、`workflows/development/backend_tier_b/`（B 层后端任务）、`workflows/development/scoring_migrations/`（评分规则改动后对已存分数重判）。输出目录都不纳入版本库。
