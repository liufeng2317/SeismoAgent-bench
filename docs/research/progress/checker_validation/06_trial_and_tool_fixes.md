# 统一测试试水批次与之后的离线修复（2026-11-03 至 11-04）

从设计文档 [`../../02_Checker_Design.md`](../../02_Checker_Design.md) 迁出（2026-11-04）。Kīlauea 三个后端变体（checker 1.2）的结果，以及试水之后不跑 Agent、只做离线检验的修改。


改动后先只跑一批（Kīlauea × 三个后端变体，各 1 次），检验新的环境策略（`run_local`）、checker 1.2 和更新后的知识 skill。三个运行都没有修改共享环境（`environment_integrity` 未变），扣留模式无命中；待审清单记录了查找速度模型时的访问（Klein 1981、Lin & Amelung 2014、Lin & Shearer 2021 等），人工核对未使用其中的地震位置。

| 变体 | 不通过（1.0 → 1.2） | 时间偏差 | 深度偏差 | 用时 | 速度模型与基准面 |
|---|---|---|---|---|---|
| `backend` | 1 → 3（时间、深度、水平离散） | +0.59 s | +1.11 km | 6.8 h | Klein (1981) 的近似（地表 1.9、4 km 处 4.8 km/s），顶面放在海平面；这次没有震级单位错误（1.0 为 −0.99） |
| `backend_checker` | 3 → 5（时间、深度、水平离散、震级标度、大事件；震级标度按 [07_scoring_questions.md](07_scoring_questions.md) 改为样本不足后为 4） | +1.73 s | +1.62 km | 2.2 h | 未能取到 Klein 模型的数值，自拟"Vp = 1.1 + 0.55 z"并注明为 Klein (1981)；参考高程 0 |
| `backend_knowledge` | 2 → **1**（深度堆积 9.0 %，门槛 8.0 %） | **+0.08 s** | **−0.07 km** | 4.0 h | 从原图数字化 Klein (1981)，用原文确认"深度以地表为基准、山顶约在海平面以上 1 km"，模型整体上移；Vp/Vs 1.78 与 Wadati 1.77 吻合 |

1. **知识 skill 起作用。** 1.0 中同一变体栽在基准面（−0.40 s），这次按 `not_visible.md` 查明并处理了基准面，时间和深度都通过；剩下的深度堆积是 7 % 事件压在海平面下第一个网格格点，深度搜索从海平面开始而台站在其上约 1.1 km（知识 skill 的"深度搜索起点不对"），Agent 以"真实浅部事件"处置，其 HypoInverse 交叉验证并不支持。
2. **checker 单独使用、又不提供模型时，结果反而最差。** `sp_depth_offset` 正确报出 −3.7 km；Agent 处置为 justified："给定的 S 拾取比真实 S 波早约 1.7 s"，并用每个台站约 −1.7 s 的 S 延迟吸收。同一批拾取在 1.0 中配正确模型时没有这种超前；原因是自拟的模型太慢。这是"处置完整但不正确"的确切例子（替代 [04_tier_b_backend.md](04_tier_b_backend.md) 中已更正的 Kaikōura 例子）。已在知识 skill 的 `sp_depth_offset` 条目补充：各台站相同的 S−P 偏短也可能是模型；不要用同号、同量级的台站延迟吸收共同偏移（a8cc755）。S2c 看不到这条。
3. **震级：** 三个变体都没有单位或响应错误。`backend_checker` 的震级标度不通过（斜率 −0.70）不是震级问题，也不是深度的连带结果：它的发震时刻整体偏差 1.7 s，在评分器 2 s 的时间门槛下只有 12 个事件与 ComCat 震级参考配上对（与最终目录 100 个），斜率只来自这 12 对；它的震级就是 checker 的标准复算（与 knowledge 运行同法，后者斜率 −0.08）。评分器的震级三项都只要求 ≥ 5 对（`dimensions.py` `BIAS_MIN_PAIRS`），斜率需要更多配对才可靠，是否提高（例如 30）待定（预先登记的评分规则）。诊断脚本 `workflows/development/replay/magnitude_location.py`（用运行自己的位置和最终目录的位置分别计算震源距与 ML）。
4. 单次运行，结论是初步的；变体间差异主要来自速度模型的来源（文献检索、数字化或自拟），与 [04_tier_b_backend.md](04_tier_b_backend.md)、[05_near_surface_magnitude_matching.md](05_near_surface_magnitude_matching.md) 一致。

**试水之后的离线修改（不跑 Agent，攒到下一轮统一测试）：**
- `wadati_origin_offset` 判定，门槛 1.5 s（设计文档 §13 版本记录，1.3 开发版）：试水 `backend_checker` 运行 +2.47 s 报警，human-in-loop 目录都不报警。
- NonLinLoc 接口（`seismotools/nonlinloc`，9f0d6d7）：不设 `region` 时，深度搜索原从参考高程开始（`grid_depth_km` 只管走时网格），参考高程在海平面而台站高出约 1 km 时浅部事件被压在搜索顶面；改为从台站平均高程（或 0，取较浅者）开始。用各运行自己的输入离线重定位全部事件：Kīlauea knowledge 众数深度占比 0.106 → 0.031（评分门槛 0.08），时间偏差不变，与最终目录的深度差中位数 0.258 → 0.253 km，顶面上的 79 个事件在最终目录中位于海平面以上 0.73 km；Maple checker、Magna backend 基本不变（0.052 → 0.039、0.054 → 0.056；深度差中位数 +0.01 km 以内）。改为从最高台站开始会把堆积移到空中（Kīlauea 深度差 0.270 km），未采用。参考高程设在台站高程时结果不变。
- 知识 skill：只用从来源读到的模型数值，凭记忆或文字描述重建的模型不能冠以原名（2bbdbee）；S−P 共同偏短可能是模型，不要用同号台站延迟吸收（a8cc755）。
- HypoInverse 接口 v2（`seismotools/hypoinverse`，778fe2a）：v1 写 CRH 模型，所有台站被放在模型顶面、忽略高程（B 层 Kīlauea `backend_checker` 换用 HypoInverse 后时间偏差 +0.50 s）；v2 默认写 CRE 模型（`CRE n file top T`，hyp1.40 自带）：台站按高程放置，模型深度 0 在 `reference_elevation_km`（与 NonLinLoc 接口同义），必要时顶面抬到最高台站、第一层向上延伸，输出深度为参考高程以下；`model_type: CRH` 保留 v1。验证：上游 testone 结果逐字一致，原合成测试不变；新增的已知答案测试（台站高 0–2 km、均匀半空间）CRE 深度误差 ≤ 0.05 km、时间 0.01 s，CRH 深度中位偏差 +1.45 km。用运行自己的拾取离线比较：Maple（模型以海平面为基准，台站在 2.4 km）时间偏差 +0.56 → −0.08 s，深度偏差 +1.83 → +1.34 km，水平偏移 0.88 → 0.33 km；Kīlauea（Klein 模型，基准面 1.1 km）水平偏移 0.39 → 0.07 km，与最终目录的深度差中位数 0.51 → 0.40 km（NonLinLoc 为 0.26 km）。
- hypoDD / GrowClust 的深度基准（d962b9d，文档和知识，不改代码）：两者都不读台站高程，所有台站在模型深度 0。合成精确数据（60 个事件、15 个台站高 1.6–2.8 km、均匀半空间、初始位置加扰动）：直接用海平面基准时重定位后簇中心多偏深约 0.2 km，相对位置误差中位数 0.14 km；深度和模型先换算到台站平均高程（`dep_corr`）再换回时为 0.02 km（台站都在海平面的对照为 0.03 km）。Agent 自己写这两个程序的原生输入，所以规则写进 hypoDD README、GrowClust 接口 README 和知识 skill 的定位程序差异条目。审计中 0.5–0.7 km 的整体平移比这大，应还叠加了模型不一致。
