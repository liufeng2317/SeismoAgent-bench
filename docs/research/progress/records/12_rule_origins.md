# 规则来源表

本表登记 checker（`seismo_checker/`，1.3）的每一项检查和知识资源（`data/agent_resource/skills/catalog-knowledge/`、`data/agent_resource/skills/catalog-checker/`、`data/agent_resource/magnitude/`）的每一个条目来自哪个案例，供预先登记的分析按"规则来源于该案例 / 不来源于该案例"分开报告 S2c、S3 的结果（登记表 B13，研究计划 B §4.3、§5）。来源的判断依据（2026-11-05）：checker 源码（`checks.py` 的 `DEFAULTS`、`REPORT_ONLY`、`POPULATION` 和各模块的检查编号）、`seismo_checker/README.md` 与 `metadata.json`；设计文档 `docs/research/02_Checker_Design.md` §3–§13；检验记录 `records/00`–`11`，其中 `00` §2 的最初规则表的"证据"列是首批检查的来源；后端审计 `records/backend_audit/`；质控文献综述 `docs/research/reference/seismology_qc/`（2026-11-01 写成，晚于首批检查，所以只在检查明确依文献加入或修改时算作来源）；以及加入或修改检查、知识条目的提交（`git log`、`git show`）。"来源案例"列只写来源明确说明"由该案例的观察得出"或"由该案例的读数定下门槛、类别"的案例；某案例只作为事后检验读数出现时写在"依据"列，不算来源。"通用（文献或通用知识）"表示来源只有文献或常规做法；"未能确定"表示来源文件和提交都没有说明出处。案例名中的 tools、min、backend_checker、backend_knowledge 指该案例的 Agent 运行，r 加数字和"阶段"加数字指该案例 human-in-loop 流程的轮次。

## 表 A：检查

1.3 现行的 40 项检查在前，1.2 删去但代码仍保留（不进入报告）的 8 项在后。

| 阶段 | 检查（id） | 判定或只报告 | 来源案例 | 依据（文件或提交，短） |
|---|---|---|---|---|
| 数据 | `stations_with_data` | 输入说明 | 通用（文献或通用知识） | 设计文档 §3 依据"描述输入"；718dd4e |
| 数据 | `daily_station_count` | 输入说明 | 通用（文献或通用知识） | 设计文档 §3 依据"描述输入"；718dd4e |
| 数据 | `network_geometry` | 输入说明 | 通用（文献或通用知识） | 设计文档 §3 依据"描述输入"；718dd4e |
| 数据 | `channel_sample_rates` | 输入说明 | Maple（分量类型：只有垂直分量的台站）；采样率一致性为通用 | 00 §2 规则表"台站清单"行（通道族、采样率、仅垂直分量台站，证据 Maple r3–r4）；718dd4e |
| 数据 | `data_gaps` | 输入说明 | 通用（文献或通用知识） | 描述输入；≤ 5 % 的门槛未注明出处；Maple 输入 8.6 % 只是检验读数（01 附录 §3） |
| 数据 | `processing_time_shift` | 判定 | 通用（文献或通用知识） | 零相位处理不应产生时移，只有合成验证（0.3 s）；门槛 0.1 s → 2 个采样点按文献复核（03，dea3f2f；文献 data_and_picking D15） |
| 拾取 | `silent_stations` | 判定 | Maple（只有垂直分量的台站）、Magna（近台缺失拾取） | 00 §2"台站清单"行（Maple r3–r4）和"拾取"行（每台站拾取数，Magna r5）；718dd4e；检验读数 Maple tools 30 %、Kīlauea tools 20 %（01 附录 §4） |
| 拾取 | `station_day_gaps` | 判定（安全检查） | 未能确定 | 718dd4e 加入，设计文档和记录只给检验读数（各目录 ≤ 0.6 %，从未触发）；文献综述有对应的常规检查，但晚于该检查 |
| 拾取 | `duplicate_picks` | 判定 | 未能确定 | 718dd4e 加入，设计文档"依据"列只有检验读数 Maple min 11 %；文献 data_and_picking P10 有对应的常规检查，但晚于该检查 |
| 拾取 | `s_to_p_ratio` | 判定 | Magna；上限 1.5 按文献 | 00 §2"拾取"行"P/S 比"（证据 Magna r5、Ridgecrest 主震审查，后者对应初动偏差）；上限见 03、dea3f2f |
| 拾取 | `pick_onset_offset` | 判定（P）；S 只报告 | Prague（Prague min 拾取整体早 2.5 s，PhaseNet blinding 换算错误）、Ridgecrest（主震拾取偏晚）；门槛不收紧按 Kaikōura | 设计文档 §4"针对的是 Prague min 那类错误"；00 §2"拾取"行"大事件上拾取 − 初动偏移"（Ridgecrest 主震审查）；03：收紧到 0.05 s 会在 Kaikōura human-in-loop（0.11 s）上误报；S 只报告据 Magna tools、Maple tools 读数（01 附录 §4） |
| 关联 | `associated_share` | 判定（只抓极端） | 未能确定；门槛按文献 | 718dd4e 加入时未注明出处；门槛 20 % → 10 % 按文献（发表研究 12–19 %，03、dea3f2f） |
| 关联 | `association_busy_hours` | 判定（安全检查，population） | Kaikōura、Kīlauea | 00 §2"关联"行"每小时事件数与拾取率对比"（证据 Kaikōura r3、Kīlauea r2）；718dd4e |
| 关联 | `duplicate_events` | 判定（安全检查，population） | Kaikōura、Kīlauea | 00 §2"关联"行"几秒内的重复发震"（证据同上）；首版 8dc6b6f；共用拾取细节来自文献缺失检查第 7 条，在 Maple min 上验证（03） |
| 关联 | `events_with_few_picks` | 判定 | Kaikōura、Kīlauea；"衡量约束而非对错"的说明来自 Prague | 00 §2"关联"行"每事件拾取数"（证据同上）；首版 8dc6b6f；Prague tools 21 % 报警但真实性合格（01 有效性分类），4f47ae6 写入预期说明 |
| 定位 | `isolated_events` | 判定（population） | Ridgecrest | 00 §2"定位"行"偏离趋势的孤立事件"（证据 Ridgecrest r08、阶段 66）；首版 8dc6b6f；检验读数 Ridgecrest min 12 %、human-in-loop ≤ 9 % |
| 定位 | `events_beyond_stations` | 只报告 | Maple、Ridgecrest、Prague（覆盖外事件的核查）；只报告按 Kīlauea | 07 第 2 条：凸包外 > 10 km 的事件没有一个与序列参考配上（Maple、Ridgecrest、Prague 框外事件分析）；Kīlauea 最终目录 25 % 在覆盖外（0013bda，设计文档 §6） |
| 定位 | `wadati_origin_spread` | 判定 | Ridgecrest、Maple；门槛按 Kīlauea、Maple 读数 | Wadati 法为通用做法（a808c8e 依据"不需要速度模型"）；00 §2"定位"行"发震时刻与深度耦合"（证据 Ridgecrest tools、Maple r2/r5）；0.5 s 取在干净 ≤ 0.46 s 与 Kīlauea min 0.67、Maple min 0.63 之间（01 附录 §6） |
| 定位 | `wadati_origin_offset` | 判定（1.3，\|中位数\| > 1.5 s） | Ridgecrest、Maple；只报告按 Magna、Maple、Ridgecrest、Kaikōura；1.5 s 门槛按 Kīlauea 试水 | 00 §2"定位"行（同上）；a808c8e：human-in-loop Magna −0.89、Maple +0.82、Ridgecrest −0.63、Kaikōura +0.49 s 使它只报告；a9765a8：Kīlauea 试水 backend_checker +2.47 s，改为判定（06） |
| 定位 | `travel_time_intercept` | 只报告 | Ridgecrest、Maple；只报告按 Maple、Kīlauea、Kaikōura | 00 §2"定位"行"发震时刻与深度耦合"；首版 8dc6b6f；a808c8e：Maple、Kīlauea、Kaikōura human-in-loop 截距 0.7–1.0 s |
| 定位 | `depth_single_value` | 判定（population） | Prague（2.00 km 界面）、Ridgecrest（盲轮网格顶部）、Magna（固定 10 km、r8） | 00 §2"定位"行"深度剖面"（证据 Prague、Ridgecrest 盲轮、Magna r8、Agent 运行）；00 §1.2（Magna min 42 % 在 10 km）；首版 8dc6b6f |
| 定位 | `depth_at_edges` | 判定（population） | Prague、Ridgecrest、Magna | 同上；00 §1.2"网格边界设在地表（Ridgecrest 盲轮）16 %" |
| 定位 | `depth_layers` | 判定（population） | Prague（2.0 km 界面条带）、Maple（模型界面堆积） | 718dd4e；00 §1.2（Prague 9–12 % 在 2.00 km）、00 §1.4（Maple 21 % 堆在 2.8→5.2 km/s 界面）；检验读数 Kīlauea min 93 %、Maple min 52 %；"正确台阶模型也成条带、不能比较模型"来自 Prague 区域模型 13.5 %（01，4f47ae6） |
| 定位 | `sp_depth_offset` | 判定 | 通用（近台 S−P 定深）；门槛按 Prague；"门槛以下只报大小"按 Prague、Ridgecrest、Kaikōura、Maple | 首版 8dc6b6f；718dd4e 门槛 1.0 → 1.5 km（Prague human-in-loop +1.08 km）；4f47ae6：门槛以下方向常相反（Prague tools、Ridgecrest tools、Kaikōura tools、Maple min，01 附录 §6）；1.5 km 与文献一致（Gomberg et al. 1990） |
| 定位 | `station_residual_outliers` | 只报告 | Ridgecrest、Maple；只报告按 Kaikōura | 00 §2"定位"行"每台站残差均值"（证据 Ridgecrest tools、Maple r2/r5）；首版 8dc6b6f；Kaikōura human-in-loop 18 个台站超过 0.5 s（a808c8e） |
| 定位 | `station_residual_azimuth` | 只报告 | Ridgecrest、Maple；只报告按 Kaikōura、Magna | 同上；Kaikōura 方位振幅 0.32 s，Magna tools 2.35 km 平移只测得 0.08 s（a808c8e） |
| 定位 | `depth_constraint` | 只报告（归因） | 通用（文献或通用知识） | 文献综述缺失检查第 1 条（Gomberg et al. 1990 的 1.4 倍深度、Bondár et al. 2004 的 GT5 几何）；5692109；03 |
| 定位 | `pile_against_setup` | 只报告（归因） | Prague（台阶界面堆积）；其余依文献 | 文献综述缺失检查第 2 条；02 Prague 堆积成因（网格节点紧邻界面）为直接动机，设计文档 §6 以它为例；5692109 |
| 定位 | `station_delays` | 只报告（归因） | Ridgecrest、Maple（每台站残差）；δS/δP 依文献 | 00 §2"定位"行"每台站残差均值"；δS/δP 为文献综述缺失检查第 3 条（Lin et al. 2008）；5692109 |
| 定位 | `model_ensemble_depth` | 只报告（默认关闭） | 通用（模型敏感性）；只报告按 Maple | 498e198、a808c8e §3.5 依据为通用（整体偏差无法从数据分辨，只测敏感性）；首测 Maple tools，通用模型把干净 Maple 目录判为超出（718dd4e、01 附录 §6）；00 表"定位器间离散"行（Prague 阶段 70）思路相近，但文件未把它记为来源 |
| 定位 | `model_ensemble_time` | 只报告（默认关闭） | 通用（模型敏感性）；只报告按 Maple | 同上 |
| 相对定位 | `relocation_shift` | 判定 | 通用（质心不应移动）；门槛按 Magna | 718dd4e；Magna r6 双差 0.87 km 使门槛 1 → 1.5 km；文献复核加入重定位前不确定度（03、dea3f2f）；合成整体加深 2 km 和 Kīlauea r6 输入误作输出（1.07 km）为检验 |
| 相对定位 | `relocation_large_moves` | 判定 | 通用（文献或通用知识） | 718dd4e；5 % 门槛未注明出处；Magna r6 2.7 % 为检验读数 |
| 相对定位 | `relocation_thinning` | 判定（population） | Ridgecrest | 00 §2"相对定位"行（dt.ct 中用模板推导的到时把检测压到模板上，证据 Ridgecrest 阶段 62）；合成"压到 4 个点"模仿这一错误（01 附录 §7） |
| 相对定位 | `relocated_share` | 只报告（1.2 起） | 通用；改为只报告按 Kīlauea、Magna | 718dd4e；门槛只统计 ≥ 8 个拾取的事件按文献（03）；Kīlauea backend_knowledge 为提高比例把 ngoodmin 4 改为 0、Magna backend_knowledge 经 compare.py 选 ngoodmin 2，离散变差（backend_audit README §3，4b7d014） |
| 震级 | `magnitude_range` | 判定 | 通用（文献或通用知识） | 首版 8dc6b6f，a808c8e 依据"局地台网目录中位数几乎不会低于 −1"；[−1, 5] 未注明出处；首个查出的是 Prague tools 单位错误（检验） |
| 震级 | `magnitude_detection` | 判定 | Kīlauea（Kīlauea min 整体偏 −2.4，magnitude_range 查不出）；距离项依文献 | a808c8e"用来补上 Kīlauea min 这类没被查出的震级偏差"；718dd4e；Hutton & Boore (1987)；门槛下限 −2.3 与 Kīlauea min −2.55 只差 0.25（01 附录 §8） |
| 震级 | `magnitude_recompute` | 判定 | Prague、Kīlauea、Ridgecrest；0.5 门槛按 Magna | 00 §1.4 震级替换（Prague tools −2.60、Kīlauea min −2.29、Ridgecrest tools −1.18）；2c35058；Magna tools +0.19 为区域定标差异、应不报（2c35058）；公式依 IASPEI |
| 震级 | `largest_events_magnitude` | 判定 | Ridgecrest（M7.1、M6.4 记为 5.3、5.2）、Kaikōura（最大事件没有震级） | 01 有效性分类"大事件"(b) 与 4f47ae6；00 §2"质控/完整性"行（阶段 66）思路相同 |
| 震级 | `b_positive` | 只报告（population） | Ridgecrest、Kīlauea（标准 b 值在正确目录上偏低）；方法依文献 | 文献综述缺失检查第 12 条（van der Elst 2021）；01：final 标准 b 值 Ridgecrest 0.49、Kīlauea 0.60；03：Ridgecrest 两个运行 b+ 0.98、1.20；5692109、4b7d014 |
| 定位 | `events_outside_network` | 1.2 删去（代码保留） | 通用；删去按 Kīlauea | 首版 8dc6b6f，a808c8e 依据"台网外定位约束差"；Kīlauea human-in-loop 28 % 是真实事件（4b7d014，设计文档 §10） |
| 定位 | `azimuthal_gap` | 1.2 删去（并入 `depth_constraint`） | Ridgecrest | 00 §2"定位"行"方位间隙"（证据 Ridgecrest r08、阶段 66）；718dd4e；4b7d014 |
| 关联 | `event_travel_time_fit` | 1.2 删去（代码保留） | 未能确定 | 718dd4e 加入时未注明出处；human-in-loop 1.4–18 %、Agent 运行 0.7–8.6 % 分不开（01 附录 §5，4b7d014） |
| 震级 | `rate_after_largest` | 1.2 删去（代码保留） | Ridgecrest | 00 §2"质控/完整性"行"分时段计数"（证据阶段 66：批量质控规则删掉大事件）；a808c8e 依据"大震尾波漏检或被质控规则误删"；从未报警（01） |
| 震级 | `b_value` | 1.2 并入 `b_positive` 细节 | Magna；删去按 Ridgecrest、Kīlauea | 00 §2"震级"行"b 值和 Mc 的合理性"（证据阶段 65、Magna r2–r3）；首版 8dc6b6f；Ridgecrest、Kīlauea final 低于原门槛（01） |
| 定位 | `station_time_steps` | 1.2 删去（代码保留） | 通用（文献）；删去按 Kaikōura | 文献综述缺失检查第 3 条；Kaikōura human-in-loop 也有 1.5 s 台阶（03，4b7d014） |
| 定位 | `wadati_events` | 1.2 删去（代码保留） | 通用（文献或通用知识） | 文献综述缺失检查第 11 条；human-in-loop 0.5–51 % 分不开（03） |
| 震级 | `day_night_ratio` | 1.2 删去（代码保留） | 通用（文献）；≥ 14 天的条件按 Magna | 文献综述缺失检查第 6 条（Tan et al. 2021）；未逐日时 Magna 余震衰减造成假信号 2.69（03）；基准任务最长 8 天 |

`pick_snr`（拾取信噪比）在 1.2 删去，编号已不在代码中，其比例移入 `pick_onset_offset` 的细节（4b7d014）；它与拾取–初动偏差同时加入（718dd4e），针对的同是 Prague min 的整体时移（01 附录 §4）。`b_value` 和三项归因诊断的函数仍在 `checks.py`、`diagnostics.py` 中，但 `run_checks` 不调用它们（`b_value` 只作为 `b_positive` 的细节）。

## 表 B：知识条目

文件路径相对于 `data/agent_resource/`；"skill" 指 `skills/catalog-knowledge/`。

| 文件 | 条目 | 来源案例 | 依据 |
|---|---|---|---|
| `skills/catalog-checker/SKILL.md` | 何时运行（每个阶段之后、提交之前） | 通用（文献或通用知识） | 研究计划 B §2 的设计；f05be28 |
| `skills/catalog-checker/SKILL.md` | 输出契约：最终报告和每个报警的处置（fixed / justified） | 通用（文献或通用知识） | 研究计划 B §2 第 3 条；f05be28 |
| `skills/catalog-checker/SKILL.md` | 规则：不为通过检查而改产品；保留所有报告 | 通用（文献或通用知识） | 研究计划 B §9"表面修复"风险；f05be28（早于 B 层运行） |
| skill `SKILL.md` | 规则 1：症状不是结论 | 通用（文献或通用知识） | b113131；文献综述 README §2 |
| skill `SKILL.md` | 规则 2：小批量准备、全量判定 | Prague、Magna、Maple、Kīlauea、Ridgecrest | 02 小批量重放（六个换模型场景）；b113131 |
| skill `SKILL.md` | 规则 3：先写采纳规则再做实验 | 通用（文献或通用知识） | b113131 |
| skill `SKILL.md` | 规则 4：按区域知识而不是拟合选速度模型 | Kīlauea、Maple、Prague、Magna、Kaikōura | b24b26f；00 §1.4（Kīlauea、Maple 的通用模型拟合更好、偏差更大）；05（按单一量选错，在 Prague、Kīlauea、Magna 三个可选对的案例上）；04（Kaikōura backend_checker 按 S−P、截距、Wadati 选了 iasp91） |
| skill `protocol/pilot_then_full.md` | §1 用 `pilot.py` 选三部分小批量（代表性、最繁忙、最大） | Prague、Magna、Maple、Kīlauea、Ridgecrest | 02（重放场景；windows 模式最繁忙时段在 Prague 上检验）；778b5e1 |
| skill `protocol/pilot_then_full.md` | §1 不用"记录最好的事件"代表全目录 | Magna、Maple | 02：两例移动方向与全量相反 |
| skill `protocol/pilot_then_full.md` | §1 在小批量上查代码和工具用法（单位、基准面、响应、列格式） | Prague、Kīlauea、Ridgecrest | 00 §1.4 的震级单位与响应错误；02 协议 |
| skill `protocol/pilot_then_full.md` | §1 小批量上判定 item 检查、population 只报告；小批量看不出全目录分布 | Prague、Magna、Maple、Kīlauea、Ridgecrest | 02（50 对报告，population 检查常翻转）；778b5e1 |
| skill `protocol/pilot_then_full.md` | §2 第 1–3 步：冻结参数、全量运行、checker 与 compare.py | 通用（文献或通用知识） | 02 协议；b113131 |
| skill `protocol/pilot_then_full.md` | §2 第 4 步：对照小批量预测，被压在边界上的事件移动更多 | Ridgecrest | 02：预测约 +0.1 km，实际 +2.31 km |
| skill `protocol/pilot_then_full.md` | §2 第 5 步：记录各决定在哪一层做出 | 通用（文献或通用知识） | b113131 |
| skill `playbooks/decide_between_candidates.md` | §1 同输入对比、`compare.py`、事先写采纳规则 | 通用（文献或通用知识） | b113131；比较器设计见 02 |
| skill `playbooks/decide_between_candidates.md` | §2 读结论；仍有报警只是少错；所有候选都不合格时找更好的知识 | Kīlauea、Magna、Maple、Prague、Ridgecrest | 01"作为方案比较器"（选对 Kīlauea、Magna、Maple，选错 Prague、Ridgecrest）；02 九个场景 |
| skill `playbooks/decide_between_candidates.md` | §3 层状模型下的堆积或分层：线性梯度和加密网格对照 | Prague、Maple、Magna | 02：Prague 台阶界面堆积；Maple、Magna 线性版本更好，"哪种表示更好因模型而异" |
| skill `playbooks/decide_between_candidates.md` | §3 最浅深度或搜索区顶部的堆积：基准面、搜索起点、近地表太快 | Ridgecrest、Magna、Maple | 00 §1.2（Ridgecrest 盲轮网格顶部）；00 §1.4（Magna、Maple 第一轮通用设置使事件位于基准面之上；Magna 10 % 钉在搜索顶部）；01（Magna 区域模型 19 % 压顶） |
| skill `playbooks/decide_between_candidates.md` | §3 S−P 深度改善但堆积或分层变差 | Maple、Magna | 02：线性版本 S−P 改善但区域顶部出现小堆积 |
| skill `playbooks/decide_between_candidates.md` | §3 换模型后 Wadati 离散变差：比较模型与数据的 Vp/Vs | 未能确定 | b113131 未注明出处 |
| skill `playbooks/decide_between_candidates.md` | §3 不按走时残差（RMS）选模型 | Kīlauea、Maple | 00 §1.4（残差最低的通用模型只在 Prague 偏差也最小）；文献综述 README §1 |
| skill `playbooks/decide_between_candidates.md` | §4 记录 | 通用（文献或通用知识） | b113131 |
| skill `symptoms/README.md` | A/B/C 三层归因 | 通用（文献或通用知识） | 文献综述 README §2；c1b9ee8 |
| skill `symptoms/README.md` | 习惯 1：记录改动 | 通用（文献或通用知识） | 文献综述 README §4 |
| skill `symptoms/README.md` | 习惯 2：不信形式误差和 RMS | 通用（文献或通用知识） | 文献综述 README §1（Yu et al. 2025） |
| skill `symptoms/data_picks_association.md` | `processing_time_shift` | 通用（文献或通用知识） | 文献 data_and_picking D15；c1b9ee8 |
| skill `symptoms/data_picks_association.md` | 四项输入说明 | 通用（文献或通用知识） | c1b9ee8 |
| skill `symptoms/data_picks_association.md` | 单个台站的增益或单位错误（整数倍） | 通用（文献或通用知识） | 文献综述 A 层（量化偏移）；c1b9ee8 |
| skill `symptoms/data_picks_association.md` | `silent_stations` | 通用（文献或通用知识） | 文献 data_and_picking 症状表"Silent station"；c1b9ee8 |
| skill `symptoms/data_picks_association.md` | `duplicate_picks` | 通用（文献或通用知识） | 文献 data_and_picking P10；c1b9ee8 |
| skill `symptoms/data_picks_association.md` | `s_to_p_ratio` 偏低（只有垂直分量的台站只用 P） | 通用（文献或通用知识） | 文献症状表"S/P ratio too low"；c1b9ee8；只有垂直分量的台站见于 Maple（00 表），但该条目未注明来自案例 |
| skill `symptoms/data_picks_association.md` | `s_to_p_ratio` 偏高 | 通用（文献或通用知识） | 文献症状表；33b5e34 |
| skill `symptoms/data_picks_association.md` | `pick_onset_offset`（拾取是概率峰值而非初动、预处理时移；看不到台站时钟误差） | Ridgecrest（概率峰值与初动之差）；其余依文献 | 00 §2"拾取"行原因"概率峰值与初动之差"（Ridgecrest 主震审查）；文献症状表；33b5e34 |
| skill `symptoms/data_picks_association.md` | 台站延迟：δS/δP、残差随时间的台阶、时钟与场地不可分 | 通用（文献或通用知识） | Lin et al. 2008；文献综述 B、C 层；c1b9ee8、33b5e34 |
| skill `symptoms/data_picks_association.md` | `duplicate_events`（共用拾取＝重复录入） | 通用（文献或通用知识） | 文献 association_and_detection；共用拾取在 Maple min 上验证（03） |
| skill `symptoms/data_picks_association.md` | `events_with_few_picks`（衡量约束而非对错；≥ 4 P 且 ≥ 7 个拾取） | Prague（"衡量约束而非对错"）；拾取数建议依文献 | 01 有效性分类（Prague tools 21 % 但真实性合格）；03 文献建议 |
| skill `symptoms/data_picks_association.md` | `associated_share` 偏低 | 通用（文献或通用知识） | 文献 12–19 %（03） |
| skill `symptoms/data_picks_association.md` | `association_busy_hours` | 通用（文献或通用知识） | 文献 association_and_detection"Capacity in dense sequences" |
| skill `symptoms/data_picks_association.md` | 单个事件走时曲线之外的拾取（无检查） | 通用（文献或通用知识） | 文献 location L5；33b5e34 把删去的 `event_travel_time_fit` 改为人工分析 |
| skill `symptoms/data_picks_association.md` | 模板匹配开头段：完整性主要来自模板匹配；只作核对的运行不贡献；门槛的代价 | Prague、Magna、Maple、Kīlauea、Ridgecrest、Kaikōura | 10（六个案例；Ridgecrest tools 只作核对、Magna tools 门槛 16.3）；a33a6c9 |
| skill `symptoms/data_picks_association.md` | 零假设检验；在一组门槛上取通过的最低门槛 | Prague、Magna、Maple、Kīlauea、Ridgecrest、Kaikōura | 00 表"拾取之外的检测"行（Magna、Prague 空运行）；05 与 10 的六案例零假设检验；"取最低通过门槛"来自 Magna、Ridgecrest 的 Agent 门槛（58f4f54） |
| skill `symptoms/data_picks_association.md` | 每个模板的检测数 | Kīlauea | 00 表"拾取之外的检测"行（Kīlauea r5：一个定位错误的模板，160 个检测偏约 6 km）；文献缺失检查第 8 条 |
| skill `symptoms/data_picks_association.md` | 大事件尾波中的幽灵检测 | Ridgecrest | 00 §1.2 与 00 表（阶段 67：629 个幽灵检测） |
| skill `symptoms/data_picks_association.md` | 爆破 | 通用（文献或通用知识） | 文献 Tan et al. 2021、Skoumal et al. 2015 |
| skill `symptoms/location_relocation.md` | 开头：先读 `depth_constraint`（1.4 倍深度内的 S、GT5 几何） | 通用（文献或通用知识） | Gomberg et al. 1990；Bondár et al. 2004；c1b9ee8 |
| skill `symptoms/location_relocation.md` | 堆积表：整数值＝固定或试探深度；不得悄悄固定深度 | Magna | 00 §1.2、§1.3（Magna min 固定 10 km，42 %）；00 表修复"绝不默默固定深度"；03 验证 Kīlauea min 8.00、Kaikōura min 12.00 km |
| skill `symptoms/location_relocation.md` | 堆积表：搜索区上下边界 | Ridgecrest | 00 §1.2（Ridgecrest 盲轮网格顶部 16 %，阶段 66）；03 验证 Ridgecrest tools、Kaikōura tools |
| skill `symptoms/location_relocation.md` | 堆积表：最浅深度且 S−P 更深：近地表太快或基准面错 | Magna、Maple | 00 §1.4（Magna 10 % 钉在搜索顶部、盆地层；Magna、Maple 第一轮基准面设置） |
| skill `symptoms/location_relocation.md` | 堆积表：界面旁、约束差的事件：台阶表示的假象 | Prague | 02 Prague 堆积成因 |
| skill `symptoms/location_relocation.md` | 堆积表：非整数、约束好：模型或真实结构 | 通用（文献或通用知识） | c1b9ee8 |
| skill `symptoms/location_relocation.md` | `depth_layers`：正确分层模型也成条带；约束好、S−P 证实的条带是结构 | Prague | 01（Prague 区域模型 13.5 %）；backend_audit/prague.md（backend_checker 把 2.0 km 附近 725 个真实集中的事件当堆积，改梯度后变差）；7307ed8 |
| skill `symptoms/location_relocation.md` | `sp_depth_offset`：成因与证据（模型、基准面、转换波拾为 S、发震时刻） | 通用（文献或通用知识） | Gomberg et al. 1990；文献 location L 行；c1b9ee8 |
| skill `symptoms/location_relocation.md` | `sp_depth_offset`：门槛以下方向不可靠 | Prague、Ridgecrest、Kaikōura、Maple | 01 附录 §6；4f47ae6 |
| skill `symptoms/location_relocation.md` | `sp_depth_offset`：按海平面以下读深度，HypoInverse CRH 差一个台站高程 | Kīlauea | backend_audit/kilauea.md（backend_checker 的 HypoInverse 小批量与 E5）；7307ed8 |
| skill `symptoms/location_relocation.md` | `sp_depth_offset`：近地表 Vp/Vs 造成偏移；不为消报警去掉台站校正或改 Vp/Vs | Prague、Magna | backend_audit README §3（Prague 沉积区偏 +1 至 +1.5 km；Magna backend_checker 去掉台站校正、Vp/Vs 改为 1.66）；7307ed8 |
| skill `symptoms/location_relocation.md` | `sp_depth_offset`：各台相同的 S−P 偏短可能是模型；不用同号台站延迟吸收 | Kīlauea | 06 试水 backend_checker（−3.7 km 被处置为 S 拾取早 1.7 s）；a8cc755 |
| skill `symptoms/location_relocation.md` | `wadati_origin_spread`：比较模型与数据的 Vp/Vs | 未能确定 | c1b9ee8 未注明出处 |
| skill `symptoms/location_relocation.md` | 整体偏早偏晚、偏深偏浅（C 层，转 `not_visible.md`） | 通用（文献或通用知识） | 文献综述 C 层 |
| skill `symptoms/location_relocation.md` | `isolated_events`；大事件不得被定位质量规则删掉 | Ridgecrest（大事件豁免）；其余依文献 | 00 §1.2 与 00 表（阶段 66：M7.1、M6.4、M5.4 被批量质控规则删掉）；文献 location K 行 |
| skill `symptoms/location_relocation.md` | `events_beyond_stations`：覆盖外 > 10 km 的事件几乎都不属于序列；覆盖外也可有真实地震 | Maple、Ridgecrest、Prague、Kīlauea | 07 第 2 条；0013bda |
| skill `symptoms/location_relocation.md` | `relocation_shift` | 通用（文献或通用知识） | 文献 location R4、G 行；c1b9ee8 |
| skill `symptoms/location_relocation.md` | `relocation_thinning`；模板推导的时差不进 dt.ct | Ridgecrest（模板到时）；其余依文献 | 00 表"相对定位"行（阶段 62）；文献 R3、R5、R10、F 行 |
| skill `symptoms/location_relocation.md` | `relocation_large_moves` | 通用（文献或通用知识） | 文献 location R 行；c1b9ee8 |
| skill `symptoms/location_relocation.md` | `relocated_share`：成因 | 通用（文献或通用知识） | 文献综述门槛复核；33b5e34 |
| skill `symptoms/location_relocation.md` | `relocated_share`：不为提高比例放宽连接门槛 | Kīlauea、Magna | backend_audit README §3（Kīlauea backend_knowledge ngoodmin 4 → 0；Magna backend_knowledge 经 compare.py 选 ngoodmin 2）；7307ed8 |
| skill `symptoms/magnitude_completeness.md` | 复算表：偏移约 ±2.7（mm 配 nm 常数） | Prague、Kīlauea | 00 §1.4（Prague tools、Kīlauea min） |
| skill `symptoms/magnitude_completeness.md` | 复算表：±3 或 ±6（m、µm） | 通用（文献或通用知识） | 单位换算；c1b9ee8 |
| skill `symptoms/magnitude_completeness.md` | 复算表：约 −1 至 −1.5 且随距离变化（单零点 WA 用于位移） | Ridgecrest | 00 §1.4（Ridgecrest tools −1.18）；03（趋势 −1.33） |
| skill `symptoms/magnitude_completeness.md` | 复算表：+0.3（全峰峰值） | 通用（文献或通用知识） | IASPEI 标准 |
| skill `symptoms/magnitude_completeness.md` | 复算表：±0.13（放大倍数 2800 对 2080） | 通用（文献或通用知识） | IASPEI、Uhrhammer & Collins 1990 |
| skill `symptoms/magnitude_completeness.md` | 复算表：0.1–0.4、无单位特征（区域定标，C 层） | Magna | 00 §1.4（Magna tools +0.19：实现无误，差异来自区域定标）；文献综述 C 层 |
| skill `symptoms/magnitude_completeness.md` | 复算表：随震级增大（削波、窗口、饱和） | Ridgecrest | 01（Ridgecrest tools M7.1 记为 5.3）；00 §1.1 阶段 65 大事件直接 ML（Maple、Magna）思路相同 |
| skill `symptoms/magnitude_completeness.md` | 复算表：单个台站项远离其他 | 通用（文献或通用知识） | Hutton et al. 2010；文献综述缺失检查第 4 条 |
| skill `symptoms/magnitude_completeness.md` | `largest_events_magnitude` | Ridgecrest、Kaikōura | 01 有效性分类"大事件"(b) |
| skill `symptoms/magnitude_completeness.md` | 压缩的震级标度（按振幅选记录、过长窗口、定标） | Prague、Maple、Ridgecrest | 05 震级压缩离线检验（三个序列各 300 个事件）；33b5e34 |
| skill `symptoms/magnitude_completeness.md` | `magnitude_range`、`magnitude_detection` | Prague、Kīlauea | 01（Prague tools、Kīlauea min 的单位错误） |
| skill `symptoms/magnitude_completeness.md` | `b_positive` 与标准 b 值 | Ridgecrest、Kīlauea；方法依文献 | 01（final 标准 b 偏低）、03（b+ 读数）；van der Elst 2021 |
| skill `symptoms/magnitude_completeness.md` | 最大事件后的漏检与 Mc(M, t) | Ridgecrest（尾波中漏掉大余震）；Mc(M, t) 依文献 | 01（Ridgecrest tools 漏的 M4+ 大多在主震后 1 小时内）、03；Helmstetter et al. 2006 |
| skill `symptoms/magnitude_completeness.md` | 事件率变化（无检查） | 通用（文献或通用知识） | Habermann 1987；文献 association_and_detection |
| skill `symptoms/magnitude_completeness.md` | 昼夜差异（≥ 14 天才有意义） | Magna（≥ 14 天的条件）；其余依文献 | 03（Magna 未逐日时假信号 2.69）；Tan et al. 2021 |
| skill `symptoms/not_visible.md` | 开头与速度模型总述（C 层，符号随几何） | 通用（文献或通用知识） | 文献综述 README §2 C 层；c1b9ee8 |
| skill `symptoms/not_visible.md` | §1 用区域模型；只用从来源读到的数值，凭记忆重建的模型不得冠原名 | Kīlauea | 06 试水 backend_checker 自拟 Vp = 1.1 + 0.55 z 并标为 Klein (1981)；2bbdbee |
| skill `symptoms/not_visible.md` | §1 基准面 | Kīlauea、Magna、Maple | 04 与 backend_audit（Kīlauea backend_knowledge 顶面放在海平面，−0.40 s）；00 §1.4（Magna、Maple 第一轮基准面设置）；7307ed8 |
| skill `symptoms/not_visible.md` | §1 层或节点 | Maple、Magna | backend_audit README §4（Maple 把最小一维模型按梯度插值）；00 §1.2（Maple、Magna 层顶之间线性渐变，+0.47 s）；7307ed8 |
| skill `symptoms/not_visible.md` | §1 近地表 | Magna、Maple | backend_audit README §1、§7（Magna 采用 CRUST1.0，+0.35 s；Maple 近地表太快，+1.27 s）；7307ed8 |
| skill `symptoms/not_visible.md` | §1 定位程序差异（HypoInverse CRH 与 CRE；hypoDD、GrowClust 台站在深度 0） | Kīlauea、Maple；相对定位部分为合成检验（通用） | 04（Kīlauea backend_checker 换 HypoInverse 后 +0.50 s）；backend_audit/maple.md（HypoInverse 深 1.7 km）；06、778fe2a（CRE 离线检验）；d962b9d（合成） |
| skill `symptoms/not_visible.md` | §2 比较表示方式 | Prague、Maple、Magna | 02 线性梯度对照实验 |
| skill `symptoms/not_visible.md` | §3 不按残差选；其他无参考量也不用来选 | Kīlauea、Maple、Prague、Magna | 00 §1.4；05（选错发生在 Prague、Kīlauea、Magna 三个可选对的案例上）；7307ed8、33b5e34 |
| skill `symptoms/not_visible.md` | §4 报告对模型的敏感程度 | 通用（文献或通用知识） | c1b9ee8；文献综述 B 层"velocity-model sensitivity" |
| skill `symptoms/not_visible.md` | §5 独立信息 | 通用（文献或通用知识） | 文献综述 C 层 |
| skill `symptoms/not_visible.md` | 不用区域模型时约束近地表（第 1–4 条） | Prague、Magna、Maple、Kīlauea、Ridgecrest、Kaikōura | 05 近地表离线检验（六个案例）；33b5e34 |
| skill `symptoms/not_visible.md` | 从数据建最小一维模型（第 1–4 条） | Prague、Magna、Maple、Kīlauea、Ridgecrest、Kaikōura | 08（六个案例；失效例 Magna，内部极小仍错的是 Ridgecrest）；612e765 |
| skill `symptoms/not_visible.md` | 水平框架第 1 条：台站校正 | Kaikōura、Maple | 09；2426cab |
| skill `symptoms/not_visible.md` | 水平框架第 2 条：只在部分台站下存在的层 | Magna | 09（盆地充填层，约 2.5 km 平移）；2426cab |
| skill `symptoms/not_visible.md` | 水平框架：相对定位改变绝对框架（0.3–2.3 km） | Magna、Ridgecrest | 09（Magna 2.29 km、Ridgecrest 0.85 km）；2426cab |
| skill `symptoms/not_visible.md` | 水平框架：独立目录之间的框架差（0.2–2 km） | 未能确定 | e6367f0 改写数值，记录 09 未注明取自哪几个案例的参考目录互比 |
| skill `symptoms/not_visible.md` | 震级标度的绝对水平 | 通用（文献或通用知识） | 文献综述 C 层；c1b9ee8 |
| skill `symptoms/not_visible.md` | 主震尾波中的事件 | Ridgecrest | 01（大事件 (a)）；03 尾波漏检扫描 |
| skill `symptoms/not_visible.md` | 所有台站共有的计时误差、恒定台站延迟 | 通用（文献或通用知识） | 文献综述 C 层；c1b9ee8 |
| `magnitude/README.md` | §1 标准关系式与 Hutton & Boore 形式 | 通用（文献或通用知识） | IASPEI 2013、NMSOP-2 IS 3.3、Hutton & Boore 1987；a6d8973 |
| `magnitude/README.md` | §2 WA 响应；ObsPy 单零点 WOODANDERSON 只能用于速度 | Ridgecrest | 00 §1.4（Ridgecrest tools 把单零点 WA 用于位移，−1.18）；a6d8973 |
| `magnitude/README.md` | §3 单位链 | 通用（文献或通用知识） | IASPEI；a6d8973 |
| `magnitude/README.md` | §3 错误表：mm 振幅配 −2.09 常数（±2.68） | Prague、Kīlauea | 00 §1.4（Prague tools、Kīlauea min） |
| `magnitude/README.md` | §3 错误表：单零点 WA 用于位移 | Ridgecrest | 00 §1.4 |
| `magnitude/README.md` | §3 错误表：m 或 µm（±3、±6） | 通用（文献或通用知识） | 单位换算 |
| `magnitude/README.md` | §3 错误表：全峰峰值（+0.30） | 通用（文献或通用知识） | IASPEI |
| `magnitude/README.md` | §3 错误表：放大倍数 2800 对 2080（±0.13） | 通用（文献或通用知识） | IASPEI；Uhrhammer & Collins 1990 |
| `magnitude/README.md` | §3 错误表：震中距代替震源距 | 通用（文献或通用知识） | IASPEI |
| `magnitude/README.md` | §3 错误表：未去仪器响应或灵敏度用两次 | 通用（文献或通用知识） | a6d8973 |
| `magnitude/README.md` | §3 错误表：速度或加速度记录当作位移 | 通用（文献或通用知识） | a6d8973 |
| `magnitude/README.md` | §3 错误表：两个水平分量取矢量和 | 通用（文献或通用知识） | IASPEI |
| `magnitude/README.md` | §3 错误表：大事件削波、窗口在 S 最大值之前结束 | Ridgecrest | 01（Ridgecrest tools 最大事件偏低）；00 §1.1 阶段 65 思路相同；a6d8973 |
| `magnitude/README.md` | §3 错误表：只保留高信噪比记录 | Prague、Maple、Ridgecrest | 05 震级压缩离线检验；33b5e34 |
| `magnitude/README.md` | §3 错误表：繁忙序列中远超 S 波列的窗口 | Ridgecrest | 05（最密集序列斜率陡 0.07）；33b5e34 |
| `magnitude/README.md` | §4 参考实现 `ml_reference.py` 与读差值的方法 | Prague、Kīlauea、Ridgecrest | 00 §1.4 用它复算各运行（Prague tools、Kīlauea min、Ridgecrest tools 的实现错误；Magna tools +0.19 为定标差异）；a6d8973 |
| `magnitude/README.md` | §5 区域定标库 `calibrations.json` | 通用（文献或通用知识） | NMSOP-2 DS 3.1 表 2、GB 17740-2017；a6d8973；01 把 Magna、Maple min、Ridgecrest min、Kaikōura tools 的区域定标差异交给定标库处理，但条目本身取自文献 |
| `magnitude/README.md` | §5 DS 3.1 表 2 错行说明 | 通用（文献或通用知识） | a6d8973 |

## 汇总

计数规则：一行的"来源案例"列写到某案例（无论是检查的想法、门槛还是判定类别来自它），就算该案例的一条；"通用"指该列只写"通用"或文献、不含任何案例名；"未能确定"单列。00 表引用的"阶段 65"（00 §1.2 标为所有案例）没有逐案计入。

| 案例 | 检查（1.3 现行，共 40） | 检查（1.2 删去，共 8） | 知识条目（共 117） |
|---|---|---|---|
| Prague | 9 | 0 | 25 |
| Magna | 9 | 2 | 26 |
| Maple | 13 | 0 | 26 |
| Kīlauea | 11 | 2 | 25 |
| Ridgecrest | 16 | 3 | 32 |
| Kaikōura | 10 | 1 | 8 |
| 通用（不含案例） | 8 | 1 | 53 |
| 未能确定 | 3 | 1 | 3 |

一行可以有几个来源案例，所以各案例的计数之和大于行数。按案例分开报告时，一个案例的"规则来源于该案例"集合就是上表中写到它的行；"未能确定"的 7 行（检查 `station_day_gaps`、`duplicate_picks`、`associated_share`、`event_travel_time_fit`；知识中比较模型与数据 Vp/Vs 的两处 Wadati 离散条目，以及独立目录之间框架差的数值）在分析中应单独列出，不归入任何一边。Kaikōura 写到的知识条目最少（8 条）；写到它的 10 项现行检查中，4 项的想法来自它（`association_busy_hours`、`duplicate_events`、`events_with_few_picks` 来自 00 表"关联"行的 Kaikōura r3，`largest_events_magnitude` 来自 Kaikōura tools），其余 6 项只是门槛或判定类别以它的读数为依据。
