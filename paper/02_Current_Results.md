# 当前结果（2026-11-05）

论文结构见 [01_Outline.md](01_Outline.md)。所有 Agent 运行为 Claude Code × GLM-5.3，每个配置一次运行，按指标 v2（含 2026-11-04 两项口径修正）相对 human-in-loop 最终目录评分。运行数少，结论都是初步的。逐项数值见 [SCORE_TABLE.md](../docs/research/progress/SCORE_TABLE.md)，checker 检验的每一轮见 [checker_validation/](../docs/research/progress/checker_validation/README.md)。

## 1. 一览

| 论点 | 当前结论 | 依据 |
|---|---|---|
| 1 动机 | 专家目录靠诊断和上游修复的经验；S1 有工具仍没有一个运行可信，只找回 22–51 % 的事件；错误出在后端选择和没有用模板匹配 | §2 |
| 2 checker 可靠 | A 层错误（震级实现、定位设置造成的堆积、拾取时移、发震时刻离散）能可靠查出；8 项不能区分对错的检查已删去 | §3 |
| 3 Agent 使用 checker | 震级单位和响应错误：不带 checker 3/6，带 checker 0/12；单案例试水中 checker + 知识只剩 1 项不通过；报警也会诱导表面修复 | §4 |
| 4 边界 | 时间、深度整体偏差来自速度模型，checker 和知识都没有修好；数据只给方向不给水平；至今没有运行可信 | §5 |

## 2. 动机：有工具的 Agent 也做不出可信目录（论点 1）

### 2.1 专家目录靠经验

专家阶梯（每一轮只改一处，指标 v1）：

- **在专家会考虑的范围内**，检测参数（拾取门槛、关联窗口）只改变归一化召回 ≤ 0.07；换一种方法——模板匹配——在每个案例上改变 0.2–0.6（Prague 1.17 → 1.81、Magna 0.79 → 1.16、Kīlauea 0.93 → 1.15、Kaikōura 0.88 → 1.17、Ridgecrest 1.20 → 1.40）。定位和震级的选择改变精度 20–50 %。
- **超出这个范围**，单个选择造成的误差是专家的 5–10 倍，而且在召回数字里看不出来：自选速度模型使深度偏 +8 至 +9 km；固定深度 10 km 使 42 % 的事件堆在一个深度；网格顶面放在地表使 16 % 的事件（包括主震）堆在网格顶部；震级单位用错使整体偏 −2.4 至 −2.8；对大事件套用批量质控规则丢掉了 M7.1、M6.4、M5.4。
- 专家是在中间结果里发现这些问题、回到上游修复才得到最终目录的；其中几处修复只因为看了合适的诊断（深度剖面、按震级分档的偏差、大事件列表）才被发现。这些诊断就是 checker 的来源。

### 2.2 S0 对 S1

| 案例（分级） | S0 不通过 | S0 召回 | S1 不通过 | S1 不通过的判据 | S1 召回 |
|---|---|---:|---|---|---:|
| Prague（基础） | 无有效目录 | — | 2 | 深度偏差、震级偏差 | 46 % |
| Magna（基础） | 无有效目录 | — | 3 | 深度偏差、水平偏移、震级偏差 | 51 % |
| Maple Creek（中等） | 12 | 13 % | 5 | 时间偏差、深度偏差、水平离散、偏离构造、震级标度 | 22 % |
| Kīlauea（中等） | 5 | 42 % | 1 | 时间偏差（−0.36 s，门槛 0.3 s） | 37 % |
| Ridgecrest（困难） | 6 | 30 % | 5 | 深度偏差、深度堆积、大事件、偏离构造、震级偏差 | 39 % |
| Kaikōura（困难） | 8 | 4 % | 7 | 时间偏差与离散、水平偏移与离散、深度堆积、大事件、震级偏差 | 43 % |

召回 = 找回最终目录事件的比例。Ridgecrest 的最终目录本身也漏了主震尾波中的几个 M ≥ 4 事件，所以"大事件"一项所有目录都不通过。

**判据热图**（每格 = 判据数值 ÷ 门槛；蓝色通过，红色超出）：

![判据热图](../docs/research/assets/results_overview/criteria_heatmap.png)

- S1 的不通过项集中在时间偏差（Maple、Kīlauea、Kaikōura）、深度偏差（Prague、Magna、Maple、Ridgecrest）、深度堆积（Ridgecrest、Kaikōura）和震级偏差（Prague、Magna、Ridgecrest、Kaikōura）；水平偏移在 Magna、Kaikōura 不通过。
- 判据门槛不宽松：参考目录相对最终目录也有不通过的判据（如 Kaikōura GeoNet 的深度偏差和水平离散、Kīlauea ComCat 的深度偏差）。
- 各案例的空间分布和检测对比图见附录 A。

### 2.3 错误出在哪里

1. **检测：没有用模板匹配。** 去掉模板匹配事件后，最终目录只剩 8–56 % 的事件，归一化召回从 0.99–1.85 降到 0.72–0.98。六个 S1 运行中五个没把模板匹配检测加进目录：三个没有运行，Maple 只做了一天的试验，Ridgecrest 跑了全量却只用来核对完整性。门槛本身只在 Magna 造成明显损失（Agent 用 16.3，保留最终目录事件 55 %；门槛 10 时为 80 %）。工具在手，Agent 没有把它用到产品里。
2. **定位和震级：后端选择。** 组件替换（Agent 拾取 + 专家定位）后误差大部分消失：Maple S1 深度偏差 −2.18 → −0.31 km、时间偏差 1.01 → 0.20 s；Prague S1 深度偏差 +1.10 → 0.00 km；Magna S1 深度偏差 −1.94 → −0.96 km、水平偏移 2.50 → 1.61 km；Kīlauea S0 深度偏差 +1.29 → −0.03 km、时间偏差 0.90 → 0.19 s。
3. **震级：实现错误。** 用 IASPEI 标准 ML 复算 30 个事件：Prague S1 和 Kīlauea S0 把以 mm 为单位的 Wood-Anderson 振幅配上了 nm 的常数（−2.6、−2.3）；Ridgecrest S1 把速度输入的一零点 WA 响应用在位移上（−1.2）；Magna S1 实现正确，剩下的 +0.2 是区域定标。
4. **Agent 不认为自己错了。** 明显的错误会被合理化，例如 Prague 把 ML −8 解释为"极安静台阵下的微震"。这正是需要确定性报警、并要求逐条处置的原因。

## 3. checker 本身（论点 2）

**检验方法。** 在 human-in-loop 定位轮次（应当基本干净，衡量误报）和正式 Agent 运行（相对最终目录的误差已知，衡量检出）上运行 checker；14 个场景的合成回归测试（干净输入不报警，每种植入错误由预期的检查报警）；离线重放（同一批拾取只换一个因素）。

**能查出什么：**

| 层级 | 内容 | 例子 |
|---|---|---|
| A 层：能可靠查出 | 错误有结构，数据冗余足以判断 | 震级单位、常数和仪器响应错误；定位设置造成的深度堆积（网格顶部、固定深度、台阶界面）和分层条带；拾取整体时移、重复拾取、没用上的台站；发震时刻离散和严重的整体时间错误（Wadati 偏差 > 1.5 s）；相对定位的整体平移、过度收缩和大位移 |
| B 层：部分能查出 | 需要对照实验区分原因 | 深度整体偏差（S−P 深度在超过 1.5 km 时方向可靠）；分层条带可能是模型错，也可能是正确台阶模型的界面；孤立事件 |
| C 层：看不到 | 所有台站或事件共有的误差，被发震时刻、台站校正、震级常数吸收 | 速度模型整体快慢、近地表和基准面造成的整体时间与深度偏差（0.3–1.5 s 量级）；震级定标的绝对水平（0.1–0.4 级）；主震尾波中的漏检；模板匹配门槛过高造成的漏检 |

**对可信标准的覆盖。** 深度堆积全部查出；震级实现错误全部查出，区域定标差异查不出；发震时刻离散查出，整体偏差只查出严重的；深度偏差部分查出；水平偏移、水平离散、偏离构造基本查不出；大事件漏检查不出，大事件震级偏低查出。

**只保留可靠的报警。** 8 项检查在干净目录上也会报警、分不开对错，已删去或并入其他检查（例如干净目录也有 30–64 % 的低信噪比拾取；Kīlauea human-in-loop 有 28 % 的真实事件在台网外）。走时截距、台站残差、模型组等测得准但单独说明不了对错的量只报告数值、不报警，以免诱导 Agent 去"修"。

**检查不是选择标准。** 按最小的 Wadati 偏差、RMS、最浅深度比例、截距或 S−P 深度偏差挑速度模型，每一种都至少在一个案例上选错。

## 4. Agent 使用 checker（论点 3，初步）

正式的 S2c、S3 尚未运行。现有证据来自后端消融：三个变体共用 S1 运行的拾取和关联，只做定位、相对定位和震级——`backend`（只有工具）、`backend_checker`（加 checker）、`backend_knowledge`（加 checker 和知识）。

| 案例 | S1 | backend | backend_checker | backend_knowledge |
|---|---:|---:|---:|---:|
| Prague | 2 | 4 | 1 | 1 |
| Magna | 3 | 4 | 4 | 4 |
| Maple Creek | 5 | 6 | 4 | 5 |
| Kīlauea | 1 | 1 | 3 | 2 |
| Ridgecrest | 5 | 5 | 3 | 3 |
| Kaikōura | 7 | 4 | 4 | 6 |
| **合计** | 23 | 24 | **19** | 21 |

表中为不通过的可信标准数。统一后的试水（Kīlauea，更新后的 checker 和知识）：`backend` 3 项、`backend_checker` 4 项、`backend_knowledge` **1 项**（时间偏差 +0.08 s、深度偏差 −0.07 km 都通过，只剩深度堆积；该项随后由 NonLinLoc 接口修正离线消除）。

1. **A 层错误被稳定挡住。** 不带 checker 的后端变体 6 个案例中 3 个犯了震级响应或单位错误，带 checker 的 12 次运行 0 次。起作用的主要是 checker 和知识里正确的参考计算，Agent 照用了它，而不是被报警纠正：正确的参考实现本身就是有效的经验载体。
2. **checker 单独使用不如和知识结合。** 试水中知识变体从原图数字化已发表的速度模型、查明基准面，时间和深度都通过；只有 checker 的变体没取到模型数值，自拟了一个过慢的模型，结果最差。
3. **报警会诱导表面修复，处置完整不等于处置正确。** 4 次由报警驱动的改动使结果变差：深度分层报警后把台阶模型改成梯度；S−P 深度报警后去掉台站校正、改 Vp/Vs；为提高移动比例放宽连接；比较工具选中了离散更大的参数。试水中只有 checker 的 Agent 把正确的 S−P 深度报警解释为"拾取提前 1.7 s"，用同号的台站延迟吸收。对策是在症状手册里写明哪些改动不该做，并把只会诱导修改的检查降为只报告。

## 5. 边界（论点 4）

1. **时间和深度的整体偏差来自速度模型的近地表和基准面。** 单因素重定位复现了后端运行的主要偏差：模型顶面放在海平面（Kīlauea −0.37 s）、采用通用模型（Magna +0.35 s）、近地表太快的已发表模型（Maple +1.27 s）。不给区域模型时，数据只给方向不给水平：表层越慢越厚，Wadati 偏差越正（相关 −0.87 至 −1.00），但正确模型处的值因案例而异。
2. **从数据建模型有用，但会失效，且失效时数据不报警。** 整列缩放加台站校正、按残差选：在 Kīlauea、Kaikōura、Maple、Prague 改善了时间或深度，在 Ridgecrest 没变化，在 Magna 使深度偏深 1.9–6.6 km。只写进知识，带保护条件。
3. **水平偏移来自台站延迟和最终目录的框架。** 10 个一维候选模型的水平偏移都在 1.1–2.9 km（门槛 1 km）；换成专家拾取最多改变 0.26 km；加上专家的台站延迟后，Kaikōura、Maple 降到 0.2–0.5 km；Magna、Ridgecrest 的最终目录框架来自双差重定位，绝对定位复现不了。整批平移在没有参考时看不出来。
4. **工具的约定本身是隐蔽的误差源，修工具比教 Agent 可靠。** HypoInverse CRH 模型忽略台站高程（Maple +0.56 s）、NonLinLoc 深度搜索从参考高程开始、hypoDD 和 GrowClust 把台站放在模型深度 0；前两项已改接口默认值。
5. **最终目录有一部分依赖参考。** 例如 Ridgecrest 的分层框架来自 Shelly 的模型，Magna 的 ML 对 UUSS 重新定标。这部分任何 Agent 不借助参考都到不了；按干预编码分出来（未开始）。
6. **至今没有运行达到可信标准。** 最接近的两个：Kīlauea S1（只有时间偏差 −0.36 s 不通过）和 Kīlauea checker + 知识后端试水（只有深度堆积，已由工具修正离线消除）。

## 6. 尚缺的结果

| 内容 | 对应论点 | 状态 |
|---|---|---|
| 完整流程的 S2c、S3 任务包与正式运行 | 3 | 后端版本已有，完整流程未搭建 |
| 误报与检出整理成论文用的表和图 | 2 | 数据在检验记录 01、03 中，未整理 |
| 差距弥合计算与瀑布图 | 3c | 未开始 |
| 处置审计（真修复与表面修复） | 3d | 后端消融已有个例，未系统统计 |
| human-in-loop 干预编码 | 4b | 未开始 |
| 重复运行、第二个模型、保留案例 | 全部 | 未开始 |
| 分级特征表 | 实验设置 | 未开始 |

## 附录 A. 各案例图

每个案例比较五个目录：最强参考目录、官方目录、S0、S1、human-in-loop 最终目录，都按评分区域裁剪；颜色在所有图中固定对应目录。最强参考 / 官方目录：Prague 为 Cochran / ComCat，Magna 为 Pang / UUSS，Maple Creek 为 Shelly（只有发震时刻，空间图不画）/ ComCat，Kīlauea 为 Shelly / ComCat，Ridgecrest 为 Shelly / SCSN，Kaikōura 为 Chamberlain / GeoNet。空间图：上排震中，下排沿最终目录震中主轴的深度剖面。检测图：左侧时间—震级，右侧累计事件数、震级—频度分布（圆点为 Mc）、深度分布。

| 案例 | 事件数（最强参考 / 官方 / S0 / S1 / 最终） | Mc（同上） |
|---|---|---|
| Prague | 2,078 / 11 / — / 3,391 / 6,767 | 0.4 / – / – / −2.5* / −0.3 |
| Magna | 4,169 / 1,432 / — / 3,109 / 5,412 | 0.7 / 0.7 / – / 1.5 / 0.7 |
| Maple Creek | 18,062 / 626 / 6,824 / 3,411 / 12,422 | −0.7 / 0.7 / 1.1 / 0.7 / −0.2 |
| Kīlauea | 1,902 / 496 / 3,131 / 2,136 / 5,198 | 1.3 / 2.4 / −0.4* / 2.4 / 1.0 |
| Ridgecrest | 7,716 / 6,564 / 7,748 / 12,239 / 17,902 | 1.3 / 2.0 / 2.0 / 0.4* / 1.0 |
| Kaikōura | 2,260 / 1,507 / 1,384 / 8,817 / 12,924 | 1.6 / 2.4 / 2.0 / 1.5 / 0.8 |

\* 震级整体偏低（单位或响应错误），Mc 不可比。

读图要点：

- S0 的错误一眼可见：Maple 的震中散满整个区域，Kaikōura 大量事件压在 12 km 固定深度。
- S1 的空间分布集中得多，但有定位假象：Ridgecrest 在网格顶部和速度分层界面上的水平条带，Maple 的震中落在定位网格上。这类假象正是 checker 的深度堆积和分层条带检查要报的。
- 最终目录看起来也是网格状的：模板匹配事件落在模板周围 0.25 km（水平）× 0.5 km（深度）的网格上，没有再精细定位。网格误差远小于评分门限，不影响绝对定位判定，但相对位置精度不如互相关重定位目录；互相关重定位只在 Kaikōura 改善了相对位置（2 km 内事件对的相对误差 1.53 → 0.69 km），已采用。

**Prague 2011**

![Prague 空间](../docs/research/assets/results_overview/2011_prague_oklahoma_space.png)
![Prague 检测](../docs/research/assets/results_overview/2011_prague_oklahoma_detection.png)

**Magna 2020**

![Magna 空间](../docs/research/assets/results_overview/2020_magna_utah_space.png)
![Magna 检测](../docs/research/assets/results_overview/2020_magna_utah_detection.png)

**Maple Creek 2017**

![Maple Creek 空间](../docs/research/assets/results_overview/2017_maple_creek_yellowstone_space.png)
![Maple Creek 检测](../docs/research/assets/results_overview/2017_maple_creek_yellowstone_detection.png)

**Kīlauea 2018**

![Kīlauea 空间](../docs/research/assets/results_overview/2018_kilauea_hawaii_space.png)
![Kīlauea 检测](../docs/research/assets/results_overview/2018_kilauea_hawaii_detection.png)

**Ridgecrest 2019**

![Ridgecrest 空间](../docs/research/assets/results_overview/2019_ridgecrest_california_space.png)
![Ridgecrest 检测](../docs/research/assets/results_overview/2019_ridgecrest_california_detection.png)

**Kaikōura 2016**

![Kaikōura 空间](../docs/research/assets/results_overview/2016_kaikoura_new_zealand_space.png)
![Kaikōura 检测](../docs/research/assets/results_overview/2016_kaikoura_new_zealand_detection.png)
