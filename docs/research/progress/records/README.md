# 记录

每一轮检验和专题分析的方法、数据和读数，按时间编号；写成后只补更正，不改写结论，后来推翻或修改的结论在原处注明。checker 的现行设计见 [`../../02_Checker_Design.md`](../../02_Checker_Design.md)。

| 文件 | 时间 | 内容 |
|---|---|---|
| [`00_expert_experience_evidence.md`](00_expert_experience_evidence.md) | 2026-10-28 至 10-31 | 专家经验的证据：参数敏感性、错误选择、组件替换、知识替换；checker 最初的规则表 |
| [`01_first_validation.md`](01_first_validation.md) | 2026-10-30 至 10-31 | 1.0 在 human-in-loop 定位轮次和第一轮正式运行上的检验；合成回归测试；有效性分类（有效、部分有效、无效、错误）；对可信标准的覆盖；附录为 1.0 各阶段检查表的原始读数 |
| [`02_replay_compare_pilot.md`](02_replay_compare_pilot.md) | 2026-10-31 | 离线重放（A 层）；`compare.py` 在换速度模型场景上的判定；Prague 台阶界面堆积；小批量能否代表全量；`scope` 和小批量协议 |
| [`03_attribution_and_thresholds.md`](03_attribution_and_thresholds.md) | 2026-11-01 | 依据质控文献的归因诊断及验证；尾波漏检扫描（未采用）；按文献复核门槛 |
| [`04_tier_b_backend.md`](04_tier_b_backend.md) | 2026-11-01 至 11-03 | B 层后端任务六个案例的结果；单因素归因要点（逐运行审计在 [`backend_audit/`](backend_audit/README.md)） |
| [`05_near_surface_magnitude_matching.md`](05_near_surface_magnitude_matching.md) | 2026-11-03 | 不给区域模型时能否约束近地表；震级标度压缩的来源；`compare.py` 规则的一项检验；模板匹配阶段的评估 |
| [`06_trial_and_tool_fixes.md`](06_trial_and_tool_fixes.md) | 2026-11-03 至 11-04 | 统一测试试水批次（Kīlauea × 三个后端变体，checker 1.2）；之后的离线修复（Wadati 门槛、NonLinLoc 搜索顶面、HypoInverse CRE、hypoDD 基准面、知识条目） |
| [`07_scoring_questions.md`](07_scoring_questions.md) | 2026-11-04 | 评分口径：震级斜率最少 30 对、`inside_region` 按台站覆盖判定（已定）；偏移门槛与最终目录自身的定位误差（2026-11-05，待定） |
| [`08_velocity_from_data.md`](08_velocity_from_data.md) | 2026-11-03 至 11-04 | 不给区域模型时从数据建最小一维模型（整列缩放加台站校正，按残差选）：四个案例有用、一个无变化、一个出错；阻尼无效；残差附近模型的深度离散是不确定度下限 |
| [`09_horizontal_shift.md`](09_horizontal_shift.md) | 2026-11-05 | 水平偏移的逐项替换：拾取和台站组合几乎不贡献；Kaikōura、Maple 来自台站延迟，Magna、Ridgecrest 来自最终目录的双差框架；只写进知识，不加检查（评分口径问题在 07 第 3 条） |
| [`10_template_threshold.md`](10_template_threshold.md) | 2026-11-05 | 模板匹配的门槛、误检与召回：零假设检验在六个案例都给出 9.5；去掉模板匹配，最终目录只剩 8–56 % 的事件；五个 tools 运行没有把模板匹配检测加进目录 |
| [`11_hil_relocation.md`](11_hil_relocation.md) | 2026-11-04 | 可达结果的互相关重定位：只在 Kaikōura 采用，其余案例保留原位置并标注网格精度 |
| [`12_rule_origins.md`](12_rule_origins.md) | 2026-11-05 | 规则来源表（注册表 B13）：每项检查（40 项现行、8 项已删）和每条知识条目（117 条）来自哪个案例；用于按规则来源分开报告 |
| [`13_hil_interventions.md`](13_hil_interventions.md) | 2026-11-05 | human-in-loop 干预编码（注册表 B14）：82 项干预分四类；阶梯收益主要来自方法选择，但多数方法选择的触发或取舍依赖参考，S3 可及的份额是一个范围（召回 42–98 %，位置离散 29–99 %） |
| [`14_e1_reliability.md`](14_e1_reliability.md) | 2026-11-05 | E1（注册表 B5）：checker 1.3 在 6 个 human-in-loop 目录和 31 次运行上的误报与检出；震级单位或响应错误 6/6、深度堆积 7/7 报出，发震时刻偏差 1/15、水平偏移 0/7 |
| [`15_locator_diagnostics.md`](15_locator_diagnostics.md) | 2026-11-05 | 定位程序的残差和不确定度（导师建议）：事件水平不确定度识别坏事件的 AUC 0.62–0.98，去掉最不确定的 10 % 后坏事件比例多数减半；RMS 无用；按台站残差离散筛选台站作用小且因案例而异；据此加入 checker 1.4（两项只报告） |
| [`16_maple_s3_vertical_only_picks.md`](16_maple_s3_vertical_only_picks.md) | 2026-11-07 | Maple 第一次 S3 运行四分之一定位偏差超过 5 km 的原因：为回应 `silent_stations` 报警加入了 8 个只有垂直分量台站的 DPPPicker 拾取（阈值 0.3，46 % 残差超过 0.5 s）；去掉它们后超过 5 km 的比例从 30 % 降到 5.9 %。速度模型的改动本身是对的 |
| [`17_dev_round1.md`](17_dev_round1.md) | 2026-11-07 | 开发循环第一轮（1.4，主震前后一天）：Prague 2、Magna 4、Maple 6、Kīlauea 0、Ridgecrest 2、Kaikōura 5 项不通过；两次运行因 checker skill 的路径写法把产品写进 `work/work/`（已修复）；正确的报警被残差拟合否定（Magna）、可以修复的深度堆积被说成调参（Kaikōura）；1.5 的候选改动 |
| [`backend_audit/`](backend_audit/README.md) | 2026-11-02 | 后端消融的逐运行决策审计（04 的细节） |

检验用到的工具：`workflows/development/tools_case_validation/validate_checker.py`（在 human-in-loop 轮次和正式运行上跑 checker）、`seismo_checker/examples/smoke/run.sh`（合成回归测试）、`workflows/development/replay/`（离线重放和诊断脚本）、`workflows/development/backend_tier_b/`（B 层后端任务）、`workflows/development/scoring_migrations/`（评分规则改动后对已存分数重判）。输出目录都不纳入版本库。
