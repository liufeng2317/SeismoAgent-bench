# 后端任务（B 层）结果（2026-11-01 至 11-03，6 个案例）

从设计文档 [`../../04_Checker_Design.md`](../../04_Checker_Design.md) 迁出（2026-11-04）。逐运行的决策审计和单因素归因在 [`../backend_audit/`](../backend_audit/README.md)。


设计见 [`workflows/development/backend_tier_b/README.md`](../../../../workflows/development/backend_tier_b/README.md)：三个变体共用正式 tools 运行的拾取和关联，只做定位、相对定位和震级；`backend` 只有工具（看不到 checker），`backend_checker` 加 checker skill 和处置合同，`backend_knowledge` 再加知识 skill 和震级资源。每个变体每个案例只跑一次，结论是初步的。Ridgecrest、Kaikōura 在后台继续。

| 案例 | 正式 tools | backend | backend_checker | backend_knowledge |
|---|---|---|---|---|
| Prague | 2 项未通过（深度 +1.10，震级 −2.77） | 4 项（深度 +1.11，震级 −1.43） | **1 项**（深度 −0.02，震级 −0.07） | **1 项**（深度 +0.26，震级 −0.11），用时减半 |
| Kīlauea | 1 项（时间 −0.36） | 1 项（震级 −0.99） | 3 项（时间 +0.50、水平离散、大事件） | 2 项（时间 −0.40、水平离散） |
| Magna | 3 项（深度 −1.94、水平 2.35、震级 +0.67） | 4 项 | 5 项（深度 +0.56，时间 +0.34） | 4 项（深度 −0.51，时间 +0.38） |
| Maple | 6 项（时间 +1.15，深度 −2.18） | 7 项（含深度堆积） | **5 项**（时间 −0.05，深度 +0.44，水平 0.26） | 6 项（时间 +1.18，深度 −2.50） |
| Ridgecrest | 6 项（深度 −2.31，震级 −1.21） | 6 项（深度 +1.31，震级 −0.98） | **4 项**（深度 +0.82，震级 +0.06） | **4 项**（深度 +1.10，震级 −0.08） |
| Kaikōura | 7 项（时间 +0.63，水平 3.70，震级 −0.60） | 4 项（时间 +0.81，深度 −1.30，水平 1.94） | 4 项（时间 +0.60，**深度 +3.22**，水平 3.35） | 6 项（时间 +0.50，深度 +1.61，水平 3.53） |
| **合计未通过** | 25 | 26 | **22** | 23 |

相对 `backend`：`backend_checker` 3 个案例更好（Prague、Maple、Ridgecrest）、2 个更差（Kīlauea、Magna）、1 个持平（Kaikōura）；`backend_knowledge` 3 个更好、1 个持平、2 个更差。Kaikōura `backend_checker` 把唯一剩下的报警（hypoDD 后 36 % 事件移动超过 5 km）处置为 justified（"差分走时要求的、迭代收敛"），深度偏差为 +3.22 km（正式 tools 前端 +0.54）。更正（2026-11-03）：偏差在 hypoDD 之前已是 +3.00 km（`run/final/located.csv`），hypoDD 只加 0.22 km，大位移事件的深度变化上下各半，这条 justified 有数据支持。偏差来自绝对定位的模型选择：Agent 在 checker 的五个通用模型中按 `sp_depth_offset`、走时截距和 Wadati 偏差选了 iasp91（CRUST1.0 因 S−P 深度 +3.9 km 被否），正是 [05_near_surface_magnitude_matching.md](05_near_surface_magnitude_matching.md) 显示不可靠的做法。为此 checker README 增加一段：检查和测量值不是选择速度模型的标准。核对模块只查处置是否完整，不查是否正确，这一点仍然成立，但这个例子不能作为"处置错误"的证据。

1. **A 层错误被稳定挡住。** 不带 checker 的 `backend` 在 Prague（−1.43）和 Kīlauea（−0.99）都犯了震级响应/单位错误；两个带 checker 的变体在这两个案例上都没有。checker 运行 6–15 次，过程中出现的报警有修复（Prague 3 个，均对照旧报告核实）也有给证据的 justified。
2. **C 层偏差没有改善，有时变差。** 带 checker 的 Agent 常会换速度模型或定位方法：Magna 深度修好了，时间偏差却变成不通过；Kīlauea 换成 HypoInverse 后时间偏差和水平离散变差。这是速度模型整体偏差在深度和发震时刻之间的权衡，checker 看不到（[03_attribution_and_thresholds.md](03_attribution_and_thresholds.md)、文献 C 层）。
3. **知识 skill 的流程被认真执行，但修不了先验模型。** Maple 知识变体：小批量发现台阶界面堆积后改用梯度、对堆积做 0.5/0.25/0.1 km 网格对照实验并改用 0.1 km、采纳前写下规则并用 `compare.py` 确认、HypoInverse 独立交叉验证并正确识别 +1.7 km 是基准面差异、无法约束的 10 个事件不发坐标并用 Wadati 估计发震时刻。但速度模型是它凭已有知识选的已发表黄石最小一维模型，结果深度 −2.50 km、时间 +1.18 s，与正式运行相同。改进方向：知识资源需要提供区域速度模型（像震级定标库一样，附基准面、层的表示方式和适用范围），知识替换实验已显示区域模型的梯度版本可把 Maple 深度偏差降到 −1.28 km（[02_replay_compare_pilot.md](02_replay_compare_pilot.md)）。
4. **合成恢复测试不适合作误差上界（已从 1.1 中去掉，代码留在 `checker-1.1` 分支历史中）。** 以目录位置为真值、在一维备选模型（速度 ±5 %、Vp/Vs ±0.05、台阶/梯度互换、层顶 ±0.5 km、浅部 2 km ±20 %、低速表层、CRUST1.0、LITHO1.0）中正演再用原模型定位：Prague（实际 0.00 km）、Kīlauea（−0.06）落在给出的范围内，但 Magna（−1.59、−0.88、−3.05）和 Maple（−3.25、−1.28）都在范围之外。实际大偏差来自三维结构、台站项、系统性拾取误差和定位假象，一维扰动模拟不出。连"同一模型、仅拾取噪声"一项也没有合并，以免被当作误差估计。

**决策审计与单因素归因（[`progress/backend_audit/`](../backend_audit/README.md)）。** 逐个运行审计决定、重新评分中间目录、正演合成走时，并用同一批拾取只换一个因素重定位：

- 时间和深度偏差几乎完全由近地表速度和基准面决定：Kīlauea knowledge 把区域模型顶面放在海平面（只改这一项复现 −0.37 s）；Magna 两个 checker 变体采用 checker 自带的 CRUST1.0（复现 +0.35 s）；Maple knowledge 用的已发表模型近地表太快（复现 +1.27 s）。Maple、Magna 单靠换模型无法同时通过时间和深度判据。
- 不带 checker 的 `backend` 在 6 个案例中有 3 个犯了震级响应/单位错误（−1.43、−0.99、−0.98），带 checker 的两个变体 12 次运行 0 次——起作用的是 checker 与知识资源中的正确参考计算链，Agent 照用了它。
- 几个"好结果"是碰巧（Prague checker 的 hypoDD 中心漂移、Maple checker 的基准面误设与 Vp/Vs 抵消）；4 次报警驱动的改动使结果变差（台阶改梯度、去掉台站校正和改 Vp/Vs、为提高 `relocated_share` 放宽连接、`compare.py` 选中离散更大的参数）。
- checker 自带的通用模型和 IASPEI 复算被 Agent 当作推荐采用；`sp_depth_offset` 在 Prague 偏约 +1 至 +1.5 km，且对 HypoInverse 输出差一个台站高程；`wadati_origin_offset` 在三个案例与时间偏差一致、在 Maple 方向相反，保持只报告。
- 工具 bug：HypoInverse 接口的 CRH 层深字段宽度错误，界面被截断（2afcdc8 修复；此前所有 HypoInverse 运行受影响）。有效性：一个运行向共享环境安装了包；一个运行访问了覆盖 Prague 的区域重定位目录论文（未读出、未使用）；Maple 专家的区域模型出自目标论文，不能作为知识资源。

**下一步：** README 和 skill 修改已合并（checker 1.1）；速度模型资源的做法已改为不提供任何具体模型，只给用法知识和约束近地表的方法（2026-11-03 决定，[05_near_surface_magnitude_matching.md](05_near_surface_magnitude_matching.md)）；之后在 Kīlauea、Maple 上每个变体重复 2–3 次（等所有问题解决后统一跑）。

**循环性：** 检查规则和门槛都是在这六个案例上总结和校准的。报告 S2c、S3 结果时，按"规则来源于该案例 / 不来源于该案例"分开统计（[`00_B_Research_Plan_Checker.md`](../../00_B_Research_Plan_Checker.md) §4），并在冻结前固定所有门槛。
