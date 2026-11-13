# 07. 用于定位参考的目录

调研日期：2026-11-13。说明：本轮 WebSearch 配额在调研中途用完（会话共享上限），之后只用 WebFetch 打开已知 URL，以及 SeismoAgentBench 仓库中已下载、已解析的 Ridgecrest 论文和目录（`SeismoAgentBench/data/2019_ridgecrest_california/`）。北加州和日本部分因此较简略，日本 JMA 一元化目录的定位精度没有找到可引用的数字。

## 要回答的问题

- 南加州和 2019 Ridgecrest 序列：有哪些高精度目录（Hauksson–Yang–Shearer 重定位目录、Ross et al. 2019 QTM、Shelly 2020、Lin 2020、Atterholt 2025 等、ComCat/SCSN），它们声明的绝对精度和相对精度，以及彼此差多少（已发表的比较）。
- 北加州（如 Waldhauser 的 NCSN 双差目录）和日本（JMA 一元化目录、重定位目录）同样的问题，简要回答。
- 评测机器学习拾取器的论文在没有真实位置时怎样报告定位误差（用目录离散做"真值带"、GT5 地面真值事件、爆破/采石场爆破）。

影响的决定：定位误差怎么报；"真值带"怎么定。

## 结论摘要

- **Ridgecrest 至少有 6 个可用目录，但没有一个是绝对位置真值。** 各目录声明的都是相对精度或形式误差：QTM 名义相对分辨率约 100 m（水平）/350 m（垂直）[1]；Lin 2020 相对误差中位 8 m/16 m（bootstrap 20 次），三维绝对误差中位 75 m/108 m（simul2000 形式误差）[2]；HYS 全目录 90% 绝对误差 <0.75 km（水平）/<1.25 km（垂直），90% 相对误差 <0.1 km [3]；Atterholt 2025 绝对定位 90% 不确定度 <700 m（水平）/<1 km（垂直）[4]；Shelly 2020 不给逐事件不确定度，并明确说大量事件未经人工复核、个别事件可能有大误差 [5]。
- **形式误差普遍低估真实误差。** Ridgecrest 合成实验中，真实位置落在 95% 置信椭球内的比例：Hypoinverse 13.1%，VELEST 80.3%，NonLinLoc 85.0%，HypoSVI 75.0% [6]。因此"目录声明精度"不能直接当真值带宽度。
- **目录之间的实际差异比声明精度大得多。** 上游项目 SeismoAgentBench 对 Ridgecrest 五个目录做的双向唯一配对（1 s / 5 km）中，Shelly–Liu、Shelly–Ross、Shelly–ComCat、Liu–ComCat 的水平距离中位数约 0.25–0.47 km [7]。Mw 7.1 主震深度：SCSN 8.0 km（QTM 页面推荐使用）[8]，Lin 2020 为 4.16 km（相对海平面）[2]，Lomax 2020 约 4 km [9]；QTM 和 Shelly 都声明自己的大震位置不可靠 [1][5]。没有找到一篇系统比较这些 Ridgecrest 目录的已发表论文（未找到）。
- **深度基准不统一，差值与声明的垂直精度同量级。** Shelly 2020 深度相对海拔 0.7 km 的地表面 [5]；Lin 2020 相对平均海平面（约在地表下 1 km）[2]；SCSN 目录深度相对台站平均高程（Hutton 2010）[10]。比较深度前必须先换算基准。
- **大部分目录共享 SCSN 拾取谱系，不独立；两个目录本身来自深度学习拾取。** HYS、Lin 2020、QTM、Shelly 都以 SCSN 分析员拾取或 SCSN 事件为起点 [2][3][5][1]；Liu 2020 用 PhaseNet → REAL → VELEST → hypoDD [7]，Atterholt 2025 用 PhaseNO → GaMMA → HypoSVI → GrowClust [4]。用后两者评价 PhaseNet/PhaseNO 基线有循环问题。
- **北加州**：Waldhauser & Schaff 2008 用 24,438 个重复地震估计 NCSN 网络定位的相对误差（95%）为水平 0.7 km、垂直 2 km；互相关双差相对误差中位约 0.04–0.05 km（区域间 0.04–0.2 km）；在 Parkfield 用一维和三维模型做双差，相对位置差中位 7 m（水平）/20 m（垂直），绝对位置差 51 m（东西）、32 m（南北）、115 m（垂直）[11]。**日本**：JUICE 重定位了 2001–2012 年 Hi-net 目录中 110 多万个 40 km 以浅事件，台站覆盖好时不确定度约 0.37 km（水平）/0.85 km（垂直），且明确是相对位置，绝对位置建议用 JMA 一元化目录 [12]；JMA 目录本身的精度数字未找到。
- **没有真值时的通行做法**：（1）与目录比较并去掉共同偏移；（2）用爆破和采石场爆破检验绝对位置（南加州 36 个已知位置和时刻的爆破，三维模型重定位后震中误差都 <1.5 km、多数 <1.0 km，垂直多数 <2 km）[13]；（3）GT5 网络准则选"地面真值"事件 [14]；（4）重复地震作相对真值 [11]；（5）"波形越相似、两事件应越近"作独立代理（Cianetti et al. 2026：相干 >0.9 的事件对，DL 拾取定位的距离中位数约为人工拾取的一半）[15]；（6）合成实验 [6]。
- **建议**：主指标用"同一定位器、同一模型下，相对分析员拾取定位的位移"；外部目录只用于绝对位置的合理性检查，并先换算深度基准、去掉共同偏移、剔除 M>5 和 M7.1 附近时段；"真值带"用多个目录对同一事件的离散来定，只用与被评方法拾取谱系不同的目录，且水平、深度分开。

## 详细发现

### 1. 南加州和 2019 Ridgecrest

#### 1.1 目录一览

| 目录 | 时间与规模 | 方法链 | 拾取来源 | 声明精度 | 深度基准 | 注意 |
|---|---|---|---|---|---|---|
| ComCat / SCSN | 实时与复核 | Hypoinverse 一维；拾取权重 0–4 级，0 级约一个采样内 [10] | 分析员 + 自动（2019 年复核比例逐日不同，见设计稿） | Hypoinverse 形式误差（ERH/ERZ）；Hutton 2010 称与三维、互相关重定位比较后形式误差"合理" [10] | 台站平均高程 [10]（2019 年是否仍如此，待核） | QTM 页面推荐 M7.1 用 SCSN 震源，深度 8.0 km [8] |
| HYS（Hauksson, Yang & Shearer 2012 及更新版） | 原版 1981–2011.6；SCEDC 另有 1981–2022 版本（2023 年 2 月说明） | 一维 Hypoinverse → 三维 SIMULPS → 互相关差分走时；新版最终用 GrowClust，逐事件标注 1d/3d/gc [3][16] | SCSN 分析员拾取 [3] | 原版：90% 绝对误差 <0.75 km（水平）、<1.25 km（垂直）；90% 相对误差 <0.1 km；绝对误差用 Hauksson 2000 和 Lin 2007 的采石场爆破检验过 [3] | 未确认（待核） | 新版说明：1981–2019 版与以前版本"差别显著"；0.5–2 s 内的近同时事件互相关无法区分，会得到相同位置和时刻 [16] |
| Ross et al. 2019 QTM（Ridgecrest） | 7 月 4–25 日；本地共 111,918 行，其中 `nbranch>1`（成功重定位）46,512 行 [7] | SCSN 模板 → 模板匹配 → 差分时间 → GrowClust 格式重定位 [1][8] | SCSN 事件模板 | 名义相对分辨率约 100 m（水平）、350 m（垂直）[1] | 待核 | M7.1 深度约束差，推荐用 SCSN [8]；未成功重定位的行只有初始位置 [7] |
| Shelly 2020 | 7 月 4–16 日；34,091 事件，由 13,525 个模板检测 [5] | 模板匹配；差分时间上限 P 0.5 s、S 0.85 s；860 万 P、1580 万 S 互相关差分 + 660 万 P、290 万 S 目录差分进 hypoDD；10 层一维模型（近似 SCEC CVM）[5] | SCSN 拾取作模板 | 不给逐事件不确定度；位置是"质心"而非震源；M>~5 事件不可靠；"大量未复核，少数事件可能有大误差，应整体解读" [5] | 海拔 0.7 km 地表面 [5] | 上游项目 SeismoAgentBench 把它作为 Ridgecrest 主参考 [7] |
| Lin 2020 | 2019-01-01 至 07-31；>24,000 事件输入，23,334 个三维定位，21,819 个互相关重定位 [2] | 三维模型（Coso 区，Zhang & Lin 2014）simul2000 → XCORLOC 互相关差分；每事件最多 100 个 2 km 内邻居；排除 101 个 M≥4 事件 [2] | SCSN 到时 | 三维绝对误差中位 75 m（水平）、108 m（垂直）；相对误差中位 8 m、16 m（20 次 bootstrap 的标准差）[2] | 平均海平面（约地表下 1 km）[2] | Mw 6.4、7.1 深度 12.45、4.16 km [2] |
| Liu et al. 2020 | 7 月 4–9 日（研究期）；15,445 事件 [7] | PhaseNet → REAL → VELEST → hypoDD [7] | **PhaseNet** | Table S1 无逐事件不确定度 [7] | 待核 | 漏掉约 884 个常规事件（约 12%）[7]；对 PhaseNet 基线有循环 |
| Atterholt, Wilding & Ross 2025（AWR） | 2019-04 至 2023-05；论文 214,467 事件，v2 数据 222,864 [4][7] | PhaseNO → GaMMA（至少 15 拾取、最大走时误差 2 s）→ HypoSVI（平滑 Hadley–Kanamori + SSST 8 次迭代）→ GrowClust（CC ≥0.65、每对 ≥6 个差分）[4] | **PhaseNO** | 绝对：90% 事件水平 <700 m、垂直 <1 km（HypoSVI 后验，重定位前）[4] | 待核 | v2 修正了相对重定位参数，散布减小 [17]；对 PhaseNO 基线有循环 |
| Lomax 2020 | M≥1.0 事件，序列早期 | NonLinLoc 多速度模型、台站校正、对模型和到时误差稳健的算法 [9] | SCSN 到时（待核） | 摘要未给数字 [9] | 待核 | 唯一以"绝对定位"为目标的 Ridgecrest 目录；M7.1 约 4 km、M6.4 约 12 km [9] |

#### 1.2 目录之间差多少

- **已发表的系统比较：未找到。** 找到的只有定性或局部比较：Lin 2020 称 SCEDC 与三维重定位的主要差别在绝对位置，浅源事件尤其明显，最终目录与 QTM 一样更"锐利" [2]；Atterholt 2025 称在重叠时段其重定位事件数约为 HYS 的三倍 [4]；ADLoc/RANSAC 论文称其 Ridgecrest 结果在空间、时间和震级分布上与 SCSN 和 Shelly 2020"一致"，没有给数字 [18]。
- **上游项目 SeismoAgentBench 的诊断**（不是发表结果）：五个目录双向唯一配对（1 s / 5 km）的水平距离中位数约 0.25–0.47 km [7]。这描述的是产品一致性，不是定位误差。
- **大震**：Mw 7.1 深度在 SCSN（8.0 km）[8] 与 Lin 2020（4.16 km，海平面基准）[2]、Lomax 2020（约 4 km）[9] 之间相差约 4 km；Mw 6.4 在 Lin 2020 为 12.45 km [2]、Lomax 2020 约 12 km [9]。
- **基准差**：Shelly（地表 0.7 km asl）与 Lin（海平面）的基准差约 0.7 km；SCSN 用台站平均高程 [10][5][2]。这与 QTM 的垂直分辨率（350 m）和 HYS 的 90% 垂直误差（1.25 km）同量级，比较深度时不换算会产生假偏差。
- **相关输入的影响**：HYS、QTM、Shelly、Lin 都从 SCSN 拾取或事件出发，彼此的一致性会高估"真实精度"（推断）。Liu 2020 和 AWR 2025 拾取来源不同，但都是深度学习拾取 [7][4]。

#### 1.3 形式误差和真实误差

Yu, Ellsworth & Beroza 2025 在合成 Ridgecrest（1000 个事件，三维 CVM 加小尺度扰动和高程）上比较 8 个程序 [6]：

| 程序 | 平均水平误差（km） | 平均深度误差（km） | 真实位置在 95% 椭球内的比例 |
|---|---|---|---|
| Hypoinverse | 0.824 | 1.118 | 13.1% |
| VELEST | 0.694 | 0.560 | 80.3% |
| NonLinLoc | 0.953 | 0.969 | 85.0% |
| NonLinLoc_SSST | 0.542 | 0.583 | 82.3% |
| HypoSVI | 0.498 | 0.580 | 75.0% |
| HypoDD | 0.315 | 0.571 | （相对：事件对 99.5%） |
| GrowClust | 0.846 | 1.069 | （事件对 84.4%） |

作者结论：多数程序低估误差；差分走时方法精度更高；补偿一维模型偏差（路径/台站校正或差分抵消）很重要 [6]。对本项目的含义：目录给的误差椭圆只能作排序参考，不能直接作为真值带宽度；上游项目 SeismoAgentBench 的记录 15 也发现 NonLinLoc 的 σh 用于给事件排序有效（识别坏事件 AUC 0.62–0.98），但绝对值低估真实误差 [19]。

### 2. 北加州

Waldhauser & Schaff 2008（NCSN 1984–2003，311,273 事件）[11]：

| 量 | 数值 |
|---|---|
| 重复地震数 | 24,438（占 12%） |
| NCSN 网络定位相对误差（由重复地震估计） | 95%：水平 0.7 km、垂直 2 km；中位约 0.11 km（水平）/0.16 km（垂直）；最大误位 8 km、7 km |
| 只用拾取的双差（重复地震） | 95%：水平 0.17 km、垂直 0.7 km |
| 互相关双差相对误差（bootstrap 95% 椭球主轴中位） | 全区约 0.05/0.05 km；区域间约 0.04–0.2 km（MTJ 最大，GGF 最小） |
| 一维 vs 三维双差（Parkfield，4332 事件） | 相对位置差中位 7 m（水平）、20 m（垂直）；绝对位置差中位 51 m（东西）、32 m（南北）、115 m（垂直） |
| 拾取精度 | P 拾取差分时间中位 0.023 s、标准差 0.15 s；互相关中位 0.002 s、标准差 0.01 s |

该目录已延伸到 1984–2021 并在 nocaldd.ldeo.columbia.edu 发布（只看到页面标题，未打开内容）[20]。重复地震方法给出了"相对位置真值"的一种可操作定义：同一重复地震族的真实间距近似为零，族内离散即定位误差 [11]。

### 3. 日本

- **JUICE**（Yano, Takeda, Matsubara & Shiomi 2017, *Tectonophysics* 702）：对 NIED Hi-net 目录 2001–2012 年、40 km 以浅的 110 多万事件做双差重定位（目录差分 + 波形互相关）；台站覆盖好时位置不确定度约 0.37 km（水平）、0.85 km（垂直）；项目页面写明这是"相对"定位，需要绝对位置时请用 JMA 一元化目录 [12]。注意：该文发表在 *Tectonophysics*，不是 *Earth Planets Space*。
- **JMA 一元化目录**：声明的绝对精度、所用速度模型（JMA2001）对深度的影响、与 JUICE 的系统差——本轮未找到可引用数字（检索配额用完前未覆盖到）。JMA 的走时表和台站校正（1997-10 至 2020-09 用 JMA2001，之后陆上台用 JMA2001A、海底台用 JMA2020A/B/C）见同目录 `05_japan_data_and_pickers.md`。建议在方向 5 中补上目录本身的精度。

### 4. 没有真实位置时怎么报定位误差

| 做法 | 例子 | 能回答什么 | 局限 |
|---|---|---|---|
| 与参考目录比较，去掉共同偏移 | 上游项目 SeismoAgentBench 的记录 15：扣除共同偏移后的水平误差、扣除中位数后的深度误差，"坏事件"定义为水平误差 > max(2 km, 3×中位误差) [19] | 相对结构是否一致 | 参考自身有误差，且常与被评方法共享数据 |
| 多目录离散作"真值带" | 设计稿 3.5 节的设想；上游项目 SeismoAgentBench 配对诊断 0.25–0.47 km [7] | 给出"不可区分"的范围 | 目录不独立；大震和基准差会放大离散 |
| 爆破/采石场爆破 | 南加州 36 个爆破（位置和时刻已知）和 19 个采石场（只知位置，用 16,574 个标为 quarry blast 的事件合成）；三维模型重定位后爆破震中误差全部 <1.5 km、多数 <1.0 km，垂直多数 <2.0 km [13]；HYS 用采石场检验绝对误差 [3] | 绝对水平位置 | 源在地表、深度不代表天然地震；只有 P 波（36 个爆破有 1349 个 P、只有 19 个 S）[13]；Ridgecrest 窗口内 ComCat 只有 2 个 quarry blast [7] |
| GT5 地面真值准则 | Bondár et al. 2004：局部网络（0–2.5°）在 ≥10 个台、全部在 250 km 内、次方位空隙 <160°、至少 1 台在 30 km 内时，震中 95% 置信下误差在 5 km 内；主方位空隙阈值（常引为 <110°）待核 [14]；后来 ISC 参考事件表用更严的条件（1 台在 10 km 内、空隙 <160°、网络几何指标 ΔU ≤0.35，Bondár & McLaughlin 2009）[14] | 选出"绝对位置可信到 5 km"的事件 | 5 km 太粗，远大于本项目关心的拾取差异 |
| 重复地震 | Waldhauser & Schaff 2008 [11] | 相对精度的真值 | 只覆盖部分断层段 |
| 波形相干—距离一致性 | Cianetti et al. 2026：相干 >0.9 的事件对，DL 拾取定位的中位和 90 分位距离约为人工拾取的一半；作者称其为独立的、"类真值"信息 [15] | 不依赖速度模型的相对精度代理 | 只对相似事件；与互相关重定位有部分重叠 |
| 合成实验 | Yu et al. 2025 [6] | 绝对与相对误差、不确定度标定 | 合成误差模型决定结论 |
| 结构锐度、偏离断层比例 | Lin 2020 定性比较 [2]；上游项目 SeismoAgentBench 的 checker 的 off-structure 指标 | 定性改善 | 易被平滑或过度聚类"刷"出来 |
| 定位残差、形式误差 | Cianetti 2026 报告 RMS 和标准误差 [15] | 内部一致性 | RMS 与定位好坏不单调（Visso 主震 RMS 人工 0.20 s 对 DL 0.39/0.67 s）[15]；上游项目 SeismoAgentBench 的 RMS 识别坏事件 AUC 6/10 组合 <0.5 [19] |

## 对本项目的影响

1. **定位误差的主指标**：对拾取方法之间的比较，用"同一定位器、同一速度模型、同一台站校正下，相对分析员拾取定位（设计稿 B8）的位移"，水平和深度分开报中位数和 90 分位，另报发震时刻差。速度模型误差在两边共有，差值主要来自拾取。这比任何外部目录都更直接回答"拾取改进是否改善定位"。
2. **外部目录的用法**（绝对位置合理性检查，不作主指标）：
   - 先把所有目录的深度换算到同一基准（Shelly：海拔 0.7 km 地表；Lin：海平面；SCSN：台站平均高程，2019 年的约定需核实）。
   - 去掉共同偏移后再算事件级差值（与上游项目 SeismoAgentBench 的记录 15 一致）。
   - 剔除 M>5 事件，并单独报告 M6.4、M7.1 后第一小时的事件（Shelly 和 QTM 都声明大震位置不可靠，各目录 M7.1 深度相差约 4 km）。
   - QTM 只用 `nbranch>1` 的成功重定位子集。
3. **"真值带"的定义**（建议）：对每个事件，取与被评方法拾取谱系不同的多个目录（对 PhaseNet/PhaseNO 基线，不用 Liu 2020 和 AWR 2025；对分析员拾取，SCSN 系目录也不独立），在基准统一、去掉共同偏移后计算目录间两两距离的中位数，作为该事件的"不可区分距离"。若 agent 定位与参考的差落在带内，只能报告为"与参考不可区分"。按上游项目 SeismoAgentBench 已有诊断，Ridgecrest 的带宽量级是水平几百米 [7]；深度带宽更大且需换算基准后重新计算。
4. **不要用目录声明精度当带宽**：Lin 2020 的 8 m/16 m 和 QTM 的 100 m/350 m 都是相对精度，且形式误差普遍低估真实误差 [6]。设计稿 3.5 节已注明"相对精度不代表绝对位置准确"，建议再加一句"形式误差也低估相对误差"。
5. **对设计稿 3.5 节的核对结果**：QTM 100 m/350 m 和 M7.1 深度约束差——与原文一致 [1][8]；Lin 2020 8 m/16 m——与原文一致，但要注明是 20 次 bootstrap 的中位，另有三维绝对形式误差中位 75 m/108 m [2]；Atterholt 2025——存在（*GJI* 240(3)），但它是 PhaseNO 拾取的目录，应从 PhaseNO 基线的参考中排除 [4]；HYS——SCEDC 现行版本已延伸到 2022 并改用 GrowClust，需记录所用版本 [16]。设计稿没有列 Liu 2020，但上游项目 SeismoAgentBench 已有，且是 PhaseNet 拾取，同样需注意循环。
6. **绝对位置的独立检验**：Ridgecrest 窗口内几乎没有爆破可用（ComCat 窗口快照只有 2 个 quarry blast）[7]。若要检验绝对位置，可在南加州基础 baseline 中加入 SCSN 标为 quarry blast 的事件作小规模检查（仅水平位置），但不能代表天然地震深度。
7. **相对精度的独立检验**：对 Ridgecrest 可以借 Cianetti 2026 的做法 [15]：按波形相干分箱，看事件对距离是否随相干升高而缩小，比较 agent、PhaseNet 和分析员拾取三者。这不依赖任何参考目录，适合放进 H1/H3 的辅助证据。
8. **日本 baseline**：只有 JUICE 的相对精度（0.37/0.85 km）可引；绝对位置参考只能用 JMA 一元化目录，其精度需在方向 5 中补齐后再定报告方式。

## 未解决与待核

- 没有找到已发表的 Ridgecrest 多目录系统比较；建议在上游项目 SeismoAgentBench 现有配对诊断基础上做一次正式比较（统一基准、按震级和时段分层、水平和深度分开），作为"真值带"的依据。
- Lomax 2020 全文未打开：它对其他目录的比较、深度基准和不确定度需核实；它是唯一以绝对定位为目标的 Ridgecrest 目录，值得作为一个参考。
- SCSN/ComCat 2019 年的深度基准（Hutton 2010 写的是台站平均高程）和 HYS 新版的深度基准待核。
- HYS 1981–2022 版在 Ridgecrest 段的事件数、gc 比例、与原版差异；新版说明写"与以前版本差别显著"，具体差异未见文档。
- Bondár et al. 2004 GT5 主方位空隙阈值（<110°）只来自记忆，需读原文。
- JMA 一元化目录的定位精度、JMA2001 模型下的系统深度偏差、与 JUICE 和 Hi-net 目录的比较：未找到，交给方向 5。
- Waldhauser 的北加州双差目录 1984–2021 版本和实时双差（DDRT）系统的精度说明：只看到页面标题。
- 想问 Shelly：Ridgecrest 目录是否有内部的不确定度估计（如 bootstrap）可共享；想问 Hauksson：HYS 新版在 Ridgecrest 段的深度基准和人工复核比例。

## 参考文献

1. Ross, Z. E., Idini, B., Jia, Z., Stephenson, O. L., Zhong, M., Wang, X., Zhan, Z., Simons, M., Fielding, E. J., Yun, S.-H., Hauksson, E., Moore, A. W., Liu, Z., & Jung, J. (2019). Hierarchical interlocked orthogonal faulting in the 2019 Ridgecrest earthquake sequence. *Science*, 366(6463), 346–351. https://doi.org/10.1126/science.aaz0109 [已读原文：上游项目 SeismoAgentBench 论文阅读记录 `data/2019_ridgecrest_california/references/ROSS2019_SCIENCE/`]
2. Lin, G. (2020). Waveform cross-correlation relocation and focal mechanisms for the 2019 Ridgecrest earthquake sequence. *Seismol. Res. Lett.*, 91(4), 2055–2061. https://doi.org/10.1785/0220190277 （NSF PAR：https://par.nsf.gov/servlets/purl/10562086；数据：https://sites.google.com/view/guoqing-lin/products/2019ridgecrest）[已读原文]
3. Hauksson, E., Yang, W., & Shearer, P. M. (2012). Waveform relocated earthquake catalog for southern California (1981 to June 2011). *Bull. Seismol. Soc. Am.*, 102(5), 2239–2244. https://doi.org/10.1785/0120120010 [已读原文]
4. Atterholt, J., Wilding, J. D., & Ross, Z. E. (2025). The evolution of fault orientation in the 2019 Ridgecrest earthquake sequence with a new long-term catalogue of seismicity and moment tensors. *Geophys. J. Int.*, 240(3), 1579–1592. https://doi.org/10.1093/gji/ggaf001 [已读原文]
5. Shelly, D. R. (2020). A high-resolution seismic catalog for the initial 2019 Ridgecrest earthquake sequence: Foreshocks, aftershocks, and faulting complexity. *Seismol. Res. Lett.*, 91(4), 1971–1978. https://doi.org/10.1785/0220190309；数据 https://doi.org/10.5066/P9JN6H0N [已读原文：上游项目 SeismoAgentBench 的 MinerU 解析 `data/2019_ridgecrest_california/references/SHELLY2020_0220190309/`]
6. Yu, Y., Ellsworth, W. L., & Beroza, G. C. (2025). Accuracy and precision of earthquake location programs: Insights from a synthetic controlled experiment. *Seismol. Res. Lett.*, 96(3), 1860–1874. https://doi.org/10.1785/0220240354 [已读原文]
7. 上游项目 SeismoAgentBench 的 Ridgecrest 案例分析与目录说明：`SeismoAgentBench/data/2019_ridgecrest_california/analysis/RIDGE2019_analysis.md`；`docs/data/01_Case_Data_Inventory.md`；Liu et al. (2020) *GRL*（Rapid characterization of the July 2019 Ridgecrest, California, earthquake sequence from raw seismic data using machine-learning phase picker, https://doi.org/10.1029/2019GL086189）的本地阅读记录 [本地记录]
8. SCEDC. Ridgecrest QTM catalog page. https://scedc.caltech.edu/data/qtm-ridgecrest.html [已读原文]
9. Lomax, A. (2020). Absolute location of 2019 Ridgecrest seismicity reveals a shallow Mw 7.1 hypocenter, migrating and pulsing Mw 7.1 foreshocks, and evolving early aftershock structures. *Bull. Seismol. Soc. Am.* https://doi.org/10.1785/0120200006 [只读摘要（经检索摘录）]
10. Hutton, K., Woessner, J., & Hauksson, E. (2010). Earthquake monitoring in southern California for seventy-seven years (1932–2008). *Bull. Seismol. Soc. Am.*, 100(2), 423–446. https://doi.org/10.1785/0120090130 [已读原文：上游项目 SeismoAgentBench 的 `references/AWR2025_CALTECHDATA/supplement/HUTTON2010__paper.pdf`，Location Accuracies 一节]
11. Waldhauser, F., & Schaff, D. P. (2008). Large-scale relocation of two decades of Northern California seismicity using cross-correlation and double-difference methods. *J. Geophys. Res.*, 113, B08311. https://doi.org/10.1029/2007JB005479 [已读原文]
12. Yano, T. E., Takeda, T., Matsubara, M., & Shiomi, K. (2017). Japan unified hIgh-resolution relocated catalog for earthquakes (JUICE): Crustal seismicity beneath the Japanese Islands. *Tectonophysics*, 702, 19–28. https://doi.org/10.1016/j.tecto.2017.02.017；目录页面 https://www.hinet.bosai.go.jp/topics/JUICE/ [只读摘要]
13. Lin, G., Shearer, P. M., Hauksson, E., & Thurber, C. H. (2007). A three-dimensional crustal seismic velocity model for southern California from a composite event method. *J. Geophys. Res.*, 112, B11306. https://doi.org/10.1029/2007JB004977 [已读原文]
14. Bondár, I., Myers, S. C., Engdahl, E. R., & Bergman, E. A. (2004). Epicentre accuracy based on seismic network criteria. *Geophys. J. Int.*, 156, 483–496. https://doi.org/10.1111/j.1365-246X.2004.02070.x [只读摘要和会议幻灯片摘录]；Bondár, I., & McLaughlin, K. L. (2009). A new ground truth data set for seismic studies. *Seismol. Res. Lett.*, 80(3) [未打开原文，经 ISC 参考事件表幻灯片转引]
15. Cianetti, S., Lomax, A., Michelini, A., & Giunchi, C. (2026). Which is better: deep-learning or manual seismic arrival-time picking? *Geophys. J. Int.*, 244(3), ggaf494. https://doi.org/10.1093/gji/ggaf494 [已读原文（前半部分）]
16. Hauksson, E. et al. SCSN relocated catalog notes (February 2023), NOTES_hys_1981_2022_rev_A.pdf. https://service.scedc.caltech.edu/ftp/catalogs/hauksson/Socal_DD/NOTES_hys_1981_2022_rev_A.pdf [已读原文]
17. SCEDC. Atterholt et al. 2025 alternate catalog page；CaltechDATA 2019 Ridgecrest Earthquake Sequence Long-Term Hypocenter and Moment Tensor Catalog (Version 2). https://scedc.caltech.edu/data/alt-2025-atterholt.html ；https://data.caltech.edu/records/5af05-cah73 [已读原文（SCEDC 页面）；CaltechDATA 页面只读检索摘录]
18. Zhu, W., Rong, B., Jie, Y., & Wei, S. S. (2025). Robust earthquake location using Random Sample Consensus (RANSAC). arXiv:2502.10933. https://arxiv.org/abs/2502.10933 [已读原文（HTML，经抓取摘录）]
19. 上游项目 SeismoAgentBench 的记录 `docs/research/progress/records/15_locator_diagnostics.md` [本地记录]
20. Waldhauser, F. Double-difference earthquake catalog for Northern California (1984–2021). https://nocaldd.ldeo.columbia.edu/catalog [只读标题]
