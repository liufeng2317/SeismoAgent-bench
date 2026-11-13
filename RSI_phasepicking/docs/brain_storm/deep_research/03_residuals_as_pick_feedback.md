# 03. 定位残差能发现多大的拾取误差

调研日期：2026-11-13。说明：本轮 WebSearch 配额在调研中途用完（会话共享上限），之后只用 WebFetch 打开已知 URL 和本地文件；部分条目因此只读到摘要或未打开，均已标注。第 3.3 节的 Monte Carlo 是本次调研自己做的简化模拟，不是文献结果，标为"自做模拟"。

## 要回答的问题

- 走时残差的分解：拾取误差、一维速度模型误差、台站项、定位与发震时刻的权衡各占多少。一维局部定位（南加州及其他地区）的典型残差离散有多大，其中拾取误差占多少。Lin & Shearer 的源特定台站校正（SSST）、shrinking-box SSST、Richards-Dinger & Shearer 2000、Hauksson & Shearer、VELEST 台站校正、三维模型。
- 留一台站（jackknife）残差和离群检测：识别错误拾取的能力如何，在多大拾取误差下有效（如 0.05、0.1、0.3、1 s；震相识别错误；跳周）。有没有发表过的可检测性/敏感性分析，或拾取误差传播到定位的 Monte Carlo 研究。
- 已有的用定位残差重拾或迭代改进拾取的方法，以及拾取—定位、拾取—关联的联合优化：自动系统中的迭代重拾（Diehl et al. 2009 MPX、Nippress、Kissling 最小一维模型流程）、贝叶斯联合拾取—定位、PhaseNO/GaMMA 基于残差的剔除、"定位驱动的重拾"、差分走时/互相关精修（波形互相关精修拾取，如 Shelly；Rowe 2002 自适应拾取）、HypoDD 残差加权、稳健定位（L1、NonLinLoc 的 EDT）。哪些可以作为"残差驱动重拾"的非 LLM 基线？
- 基于残差的分数可以怎样被刷（丢掉难拾取、把拾取挪向预测时刻、速度模型过拟合），用什么约束防止？

影响的决定：残差反馈能纠正哪类错误（粗差还是细调）；反馈信号怎么设计；和哪个非 LLM 基线比较。

## 结论摘要

- **一维模型下，残差主要是模型误差，不是拾取误差。** 南加州分析员拾取的随机误差约 0.02 s（P）和 0.03 s（S）（由相邻事件差分残差在间距趋零时的极限估计）[1]；同一批数据用一维模型时 composite event 的残差 MAD 为 0.173 s，三维层析后降到 0.076 s [1]。Ridgecrest 合成实验中，一维近似本身造成的走时误差中位数 79 ms，Hypoinverse 输出残差中位数 130 ms，而设定的 P 拾取误差（Laplace 尺度 20 ms）明显更小 [5]。北加州重复地震的 P 拾取差分时间中位数 0.023 s，但标准差 0.15 s，说明分析员拾取的误差分布是"窄中心 + 长尾" [6]。
- **单事件留一残差只能抓粗差。** 定位会吸收一部分拾取误差：每个拾取被吸收的比例就是它的"importance"（帽子矩阵对角元），全部拾取的 importance 之和等于未知数个数 4 [7]。自做模拟（3.3 节）：在 5% 误报率下，20 台站网络、一维模型残余误差 0.10 s 时，0.1 s 的单个拾取误差检出率约 1%，0.3 s 约 15%，1 s 约 96%；7 台站稀疏网络中 1 s 误差也只有约 33% 被检出（大误差把定位拉偏后自身残差反而变小）。0.05–0.1 s 的误差几乎不可能靠单事件残差发现，但它们对定位的影响也很小（密集网络水平中位 17–34 m）。
- **系统性拾取偏差对残差不可见。** 所有台站一致的延迟会被发震时刻完全吸收；某台站一致的偏差会被台站项吸收（推断，源于定位方程结构；与 [1][2] 中台站项的作用一致）。因此"PhaseNet 在缓起震相上系统性偏晚 0.02–0.05 s"这类试点中 agent 的优势，不能通过物理残差反馈学到。Cianetti et al. 2026 也发现两个 PhaseNet 模型各有系统偏差（一个偏早一个偏晚），只用数据无法判断哪个速度模型对 [18]。
- **台站项和 SSST 能把可检测门槛降下来，但有限度。** SSST/三维模型把背景离散从约 0.15 s 降到接近拾取噪声水平 [1][2]；Ridgecrest 合成实验中，把 VELEST 台站校正输入 Hypoinverse 后，水平误差均值从 0.824 降到 0.534 km、深度误差从 1.118 降到 0.650 km [5]。模拟中残余模型误差 0.05 s 时 0.3 s 误差检出率约 46%。0.1 s 级误差要靠多事件信息（差分走时、波形互相关）：互相关差分时间比拾取精确约 14 倍（中位 0.002 s 对 0.023 s）[6]。
- **已有的"残差驱动"做法几乎都是剔除或降权，而不是重拾。** Hypoinverse 默认对残差超过约 1.5–3 倍 RMS 的拾取余弦降权，并专门设 RMSCUT 防止"丢大残差 → RMS 降低 → 再丢更多"的向内螺旋 [7]；Alpine 层析流程用 VELEST 联合反演后剔除残差 ≥0.6 s 的拾取 [14]；GaMMA 关联设最大走时误差（Atterholt 2025 用 2 s）[20]；ADLoc 用 RANSAC 加台站项剔除离群拾取，在 Ridgecrest 合成数据（Yu 2025 基准）上平均定位误差从 0.680 km（只加台站项）降到 0.456 km（内点阈值 0.2 s）（抓取到的表格列名不清，具体是水平还是三维误差待核）[9]；BayesLoc 联合估计拾取精度和震相标签，能找回人为交换的 Pn/Pg 标签 [11]。真正"定位后在预测时刻附近重拾再定位"的闭环，见于 AlpArray 的 ADAPT–VELEST 流程（迭代检测、定位与高质量重拾）[15]，以及模板匹配/互相关精修（Rowe 2002、Shelly 2020）[16][17]，但没有找到它们对重拾效果的定量拆分。
- **残差分数很容易刷，而且上游项目 SeismoAgentBench 的运行中已经出现过。** RMS 不是定位质量的好指标：在上游项目 SeismoAgentBench 的 10 个案例—模型组合中，6 个 RMS 识别坏事件的 AUC 低于 0.5 [26a]；Cianetti 2026 中 DL 拾取在多数指标上更好，但 Visso 主震的 RMS 却是人工 0.20 s 对 DL 0.39/0.67 s [18]。上游项目 SeismoAgentBench 开发轮中，agent 用单侧台站 S 延迟（东侧 −0.5 至 −1.6 s、西侧 +0.9 至 +1.5 s）吸收了一个真实的深度偏差，并以"残差变差"为由否定了正确的深度报警 [26c]；为消除"静默台站"报警加入的低质量拾取（46% 残差 >0.5 s）把 30% 的事件拉偏 5 km 以上 [26b]。
- **建议：** 残差反馈只承担"粗差"（≥0.3–0.5 s、震相识别错误、漏拾/误拾、S 拾取在错误波列上）的发现；细调（<0.1 s）的评价只能来自分析员标签、半合成数据或多事件互相关。反馈信号用"交叉验证残差"（定位时留出的拾取的预测误差）和"相对同模型分析员拾取定位的位移"，不用 RMS。非 LLM 基线首选"预测时刻窗口内重拾 + 稳健定位"的固定流程（PhaseNet/AIC 重拾 + ADLoc RANSAC 或 Hypoinverse 残差降权），再加一个只剔除不重拾的对照。

## 详细发现

### 1. 走时残差的分解

#### 1.1 南加州的定量证据

| 来源 | 数据 | 关键数字 | 含义 |
|---|---|---|---|
| Lin et al. 2007（三维层析）[1] | SCSN 1981–2005，约 43 万事件，一维 shrinking-box SSST 定位 | 相邻事件同台差分残差的 MAD 随间距趋零时，与随机拾取误差 **0.02 s（P）、0.03 s（S）** 一致；台站项加回后残差随间距明显增大 | 分析员拾取的随机误差远小于路径效应 |
| 同上 [1] | 2597 个 composite events | 残差 MAD **0.173 s（一维初始模型）→ 0.076 s（三维层析加重定位后）** | 一维模型误差是残差主体；三维模型去掉一半以上 |
| 同上 [1] | composite event 平均 18 个拾取 | 随机拾取误差降低 76%（高斯假设） | 用多事件平均可以估计、也可以压低拾取误差 |
| Richards-Dinger & Shearer 2000 [3] | SCSN 1975–1998，SSST 网格搜索、L1 | 最终定位标准误差中位 328 m（水平）、741 m（深度） | SSST 是南加州重定位的基础方法 |
| Yu, Ellsworth & Beroza 2025 [5] | Ridgecrest 合成，1000 事件，27 台 | P 拾取误差 Laplace 尺度 20 ms，S 40 ms；1% P、4% S 离群（0.4–1.0 s / 0.4–1.4 s）；一维近似造成的走时误差中位 **79 ms**；Hypoinverse 残差中位 **130 ms** | 作者明确写道：简化速度模型对总残差的贡献远大于设定的拾取误差 |
| 同上 [5] | 拟合 QTM 目录的差分残差 | Laplace 尺度约 22 ms（P）、20 ms（S） | Ridgecrest 实际差分残差的量级 |

补充：Lin & Shearer 2005 的合成测试中，台站项设为 0.3 s 标准差、随机拾取误差设为 0.01 s（P）/0.02 s（S），作者特意把拾取误差设得很小，以突出台站项校正的效果 [2]。这说明在他们的模型里，"台站项 ≫ 拾取误差"是默认前提。

#### 1.2 北加州

Waldhauser & Schaff 2008 用 24,438 个重复地震（真实相对位置近似为零）检验 NCSN：互相关差分时间中位 0.002 s、标准差 0.01 s；用 NCSN P 拾取算出的差分时间中位 0.023 s、标准差 0.15 s，精度差约 14 倍 [6]。中位 0.023 s 对应单个拾取误差约 0.016 s（差分包含两个拾取，按 √2 换算，推断）；标准差 0.15 s 远大于中位，说明误差有长尾（少数大误差拾取）。同一分析给出 NCSN 网络定位的相对误差 95% 置信水平为水平 0.7 km、垂直 2 km，最大误位 8 km 和 7 km [6]。

#### 1.3 各分量的作用方式（综合 [1][2][5][7]，部分为推断）

| 分量 | 在残差里的样子 | 能否被单事件残差看到 |
|---|---|---|
| 随机拾取误差（分析员约 0.02–0.03 s [1]） | 各拾取独立，量级小 | 被淹没在模型误差中 |
| 拾取长尾/粗差（离群、错相、跳周） | 个别拾取残差大 | 能看到，但要大于背景 3–5 倍，且不能是高 importance 拾取 |
| 一维模型误差 | 随台站和方位缓变，同一地区事件间高度相关 [1] | 看起来像"台站问题"，单事件内无法与拾取误差区分 |
| 台站项（近地表） | 每台站常数 | 被台站项/SSST 吸收；也会吸收该台站的系统拾取偏差（推断） |
| 定位—发震时刻权衡 | 部分拾取误差进入位置和时刻 | 被吸收的部分看不到（见 2.1） |
| 全网一致的拾取偏差 | 全部拾取同号同量 | 完全被发震时刻吸收（推断，定位方程含常数列） |

Billings, Sambridge & Kennett 1994 用 Monte Carlo 评估拾取误差，结论是只用 P 波时拾取误差造成的误位远小于忽略横向不均匀造成的误位；拾取误差和模型误差都影响定位且难以分开 [8]（区域—远震尺度，[只读摘要]）。

### 2. 留一残差和离群检测：能识别多大的拾取误差

#### 2.1 理论：定位会吸收误差

Hypoinverse 手册把信息密度矩阵 B = U·Uᵀ 的对角元称为该震相的 "importance"，它度量一个到时对解的贡献；全部到时的 importance 之和等于未知数个数（通常是 4）；数据冗余时单个 importance 变小；同一台站 S 的 importance 大于 P（偏导数大 Ts/Tp 倍）[7]。这正是回归中的帽子矩阵对角元 h_ii。由此（推断，标准线性回归结果）：

- 拾取 i 上的误差 δ，在它自己的残差里只剩 (1 − h_ii)·δ，其余被位置和发震时刻吸收并分摊到别的拾取上。
- 平均 h = 4/N。8 个拾取的事件平均有一半误差被吸收；控制深度的近台 S 拾取 h 可接近 1，几乎完全不可见。
- 留一（deleted）残差 d_i = r_i/(1 − h_ii) 补回被吸收的部分，但方差也放大到 σ²/(1 − h_ii)；可检测的最小误差约为 k·σ_bg/√(1 − h_ii)，k 取 3–5，σ_bg 是背景（模型 + 拾取噪声）离散。

按 1.1 的数值估算（推断）：一维模型、无校正时 σ_bg ≈ 0.1–0.15 s，可检测误差约 0.4–0.7 s；有台站校正或 SSST 时 σ_bg 可能降到 0.03–0.06 s，可检测误差约 0.15–0.3 s。

Gomberg, Shedlock & Roecker 1990 指出深度偏导数最大的数据对深度约束最强 [28]——这些恰是 importance 最高、误差最难从残差看出的拾取。Materni et al. 2019 用 Monte Carlo 显示逐步去掉近台会增大定位离散 [只读摘要，未列入参考文献]。

#### 2.2 发表的可检测性研究

- **未找到**专门报告"留一残差能检出多大单个拾取误差（0.05/0.1/0.3/1 s）"的局部地震论文。找到的最接近的是：
  - Yu et al. 2025：合成 Ridgecrest 中加入 1% P、4% S 离群（0.4–1.4 s），比较 8 个定位程序；单事件程序可能纠正不了离群事件，差分走时程序更有希望恢复 [5]。没有报告逐拾取的检出率。
  - Zhu et al. 2025（RANSAC/ADLoc）：同一合成数据上，0.2 s 内点阈值标出 184 个 P（0.9%）和 539 个 S（2.7%）离群，接近设定的 1% 和 4% [9]。这是唯一一个接近"检出率"的数字，但没有按误差大小分档。
  - BayesLoc（Johannesson, Myers & Hanley）：在内华达试验场爆炸数据中人为交换 4 对 Pn/Pg 标签并给 4 个 Pg 加 30 s，后验能以 0.91–0.97 的概率识别交换的标签 [11]。属区域尺度、粗差。
  - Yu, Z. et al.（arXiv 2512.06407，2025-12）：Student-t 加两成分污染模型，逐拾取给内点/离群概率，按震相估计污染率；摘要只报告 Luding 序列筛选后目录从 10,590 降到 6,562 事件，没有看到检出率 [10]。

#### 2.3 自做模拟：单事件留一残差的检出率（推断性证据）

设置：均匀半空间（Vp 6.0 km/s、Vp/Vs 1.73），震源深 8 km；台站均匀分布在 50 km 半径内；P 拾取全有，S 以 60%（密集，20 台）或 50%（稀疏，7 台）概率存在；拾取噪声按 [5] 取 Laplace（P 20 ms、S 40 ms）；模型误差为每台站一个高斯项 σ_m（S 乘 1.73），代表扣除台站校正后的残余模型误差；随机挑一个拾取加 ±δ；高斯—牛顿定位，算学生化留一残差（稳健尺度取其余拾取的 MAD），取绝对值最大者；阈值按 δ=0 时每事件 5% 误报率标定；"检出"指最大者正好是被加误差的拾取且超过阈值。每格 400 事件。脚本为本次调研编写，存放在 `scripts/03_residual_detectability/detect_sim2.py`（输出 `detect_sim2_out.txt`），不属于项目代码。

| 网络 | σ_m（s） | δ=0.05 s | δ=0.1 s | δ=0.3 s | δ=1.0 s | 被加误差拾取的 h 中位 |
|---|---|---|---|---|---|---|
| 密集 20 台（约 32 拾取） | 0（理想三维/完美 SSST） | 0.01 | 0.04 | 0.74 | 1.00 | 0.11 |
| 同上 | 0.05（台站校正后） | 0.01 | 0.03 | 0.46 | 1.00 | 0.11 |
| 同上 | 0.10（一维） | 0.00 | 0.01 | 0.15 | 0.96 | 0.12 |
| 同上 | 0.15（一维较差） | 0.01 | 0.00 | 0.03 | 0.73 | 0.11 |
| 稀疏 7 台（约 10 拾取） | 0 | 0.02 | 0.07 | 0.24 | 0.34 | 0.35 |
| 同上 | 0.05 | 0.01 | 0.02 | 0.14 | 0.45 | 0.35 |
| 同上 | 0.10 | 0.01 | 0.01 | 0.07 | 0.33 | 0.35 |
| 同上 | 0.15 | 0.01 | 0.01 | 0.05 | 0.26 | 0.36 |

单个错误拾取造成的定位位移（相对无该误差的定位，中位/90 分位）：

| 网络 | δ=0.05 s | δ=0.1 s | δ=0.3 s | δ=1.0 s | 对照：无拾取误差时一维模型造成的误差（σ_m=0.10） |
|---|---|---|---|---|---|
| 密集 | 水平 0.017/0.027 km，深度 0.035/0.10 km | 0.034/0.054；0.08/0.21 | 0.10/0.16；0.20/0.67 | 0.32/0.56；0.63/2.1 | 水平 0.28 km，深度 0.68 km |
| 稀疏 | 0.06/0.12；0.18/0.50 | 0.11/0.25；0.38/1.0 | 0.33/0.69；0.96/2.9 | 1.2/2.4；3.6/8.2 | 0.48 km；1.2 km |

读法：

1. 0.05–0.1 s 的误差单事件残差基本看不到（检出率 ≤7%），但它们对定位的影响也小于一维模型本身的误差。试点中 agent 与 PhaseNet 的 P 拾取 MAE 差（0.02 对 0.04 s）落在这个区间。
2. 0.3 s 误差只有在模型误差被压到 ≤0.05 s 且网络密集时才大概率可检出。
3. 1 s 级粗差在密集网络几乎总能检出；在稀疏网络中大多检不出，因为误差把解拉过去后自身残差变小（掩蔽效应），而这时它造成的误位最大（深度中位 3.6 km）。这类情况需要 RANSAC 式的子集一致性检验，而不是单次最小二乘后的残差 [9]。
4. 局限：均匀半空间、单个错误拾取、无震相识别错误、无台站校正估计误差；Laplace 噪声的长尾抬高了阈值（σ_m=0 时阈值 6.7 个尺度单位）。结论用于定量级，不用于具体阈值。

#### 2.4 按错误类型的判断（综合 2.1–2.3 和 [1][5][6][9]，推断为主）

| 错误类型 | 典型大小 | 单事件留一残差 | 多事件/台站项/SSST 后 | 波形互相关 | 对本项目 |
|---|---|---|---|---|---|
| 细调（缓起起跳点早晚） | 0.01–0.1 s | 看不到 | 系统部分被台站项吸收，随机部分接近噪声底 | 可以（相似事件，ms 级）[6] | 只能用标签或半合成评价 |
| 系统偏差（某拾取器整体偏晚） | 0.02–0.1 s | 看不到（被发震时刻吸收） | 看不到（被台站项吸收） | 能看到相对偏差 | 物理反馈学不到 |
| 跳周/错峰 | 半周期，2–5 Hz 时约 0.1–0.25 s | 一维下大多看不到；SSST 下部分可见 | 部分可见 | 可以 | 边界区，需要 SSST 或台站校正 |
| 中等错误（拾到 P 尾波、S 拾在 P 尾波上） | 0.3–1 s | 密集网络部分可见 | 多数可见 | 可以 | 残差反馈的主要目标 |
| 震相识别错误（P/S 互换、Pg/Pn、S 拾成 SmS） | 近台 S−P 约 1–3 s；Pg/Pn 交叉附近 0.1–1 s | 大的可见；Pg/Pn 交叉附近的看起来像模型误差 | 可见 | 不适用 | 残差反馈有效，但要有震相候选 |
| 误拾（噪声、其他事件） | 任意 | 稀疏时被掩蔽 | 可见 | 不适用 | 用 RANSAC/子集一致性 |
| 少拾（漏掉可用 S） | — | 残差反而更好看 | — | — | 必须单独约束（见 4 节） |

### 3. 已有的残差驱动、迭代重拾和联合优化方法

| 方法 | 做什么 | 残差的作用 | 是否重拾 | 可用性 | 来源 |
|---|---|---|---|---|---|
| Hypoinverse 残差加权 | 迭代第 ITRRES 次起，残差在 RMS×RMSW1 内满权、RMS×RMSW2 外零权，中间余弦过渡；默认 `RMS 4 .16 1.5 3`；RMSCUT 防止向内螺旋；"通常让最大约 10% 的残差被降权" | 降权 | 否 | 现成 | [7] |
| NonLinLoc EDT | 用到时差等式（equal differential time）构造似然，对离群拾取稳健 | 稳健似然 | 否 | 现成 | [未打开原文，待核] |
| L1 / 稳健范数 | Shearer 1997 用 L1 改进局部定位；Lin 2007 用 L1–L2 混合 | 稳健拟合 | 否 | COMPLOC 等 | [25][1] |
| SSST / shrinking-box SSST | 用邻近事件残差平滑出源特定台站校正；shrinking box 让平滑半径逐次缩小（如 100 km→8 km） | 校正模型误差 | 否 | COMPLOC、NLL-SSST | [2][3][1][21] |
| VELEST 最小一维模型 + 台站延迟 | 联合反演模型、台站延迟和震源；之后剔除残差 ≥0.6 s 的拾取和 gap ≥180°、P<6 的事件，再反演一次 | 剔除离群 | 否（剔除后再反演） | 现成（上游项目 SeismoAgentBench 已接入 VELEST） | [14] |
| MPX（MannekenPix） | 在参考拾取附近精拾并给出与专家一致的质量等级（误差估计） | 质量权重 | 是（自动重拾） | 不开源（待核） | [12][13] |
| ADAPT + VELEST（AlpArray） | SeisComP3 检测 → ADAPT 多拾取器高质量重拾 → VELEST 过滤和定位；迭代使用拾取器、检测和非线性定位 | 过滤 | 是 | ADAPT 为 Python 库（未核实开源状态） | [15][14] |
| GaMMA | 高斯混合关联，预测到时为均值；设置最大走时误差（如 2 s）剔除拾取 | 关联剔除 | 否 | 开源 | [19][20] |
| ADLoc + RANSAC | 随机抽样一致性定位，加时间和振幅台站项（10 次迭代）；阈值 1 s 或 0.2 s；Ridgecrest 实测 452,702 P / 463,217 S PhaseNet 拾取 → 17,967 事件 | 内点判定 | 否 | 开源（AI4EPS/ADLoc） | [9] |
| BayesLoc | 多事件分层贝叶斯：位置、走时校正、拾取精度、震相标签联合推断 | 估计每台每相精度、离群、标签 | 否（重新标注震相） | 需申请（LLNL） | [11] |
| 混合污染模型（2025） | Student-t + 内点/离群两成分，相位特定污染率，神经网络走时代理 | 逐拾取离群概率 | 否 | 论文代码未核 | [10] |
| 互相关精修（Rowe 2002） | 按波形相似聚类，簇内求相对拾取偏移，L1 共轭梯度解延迟；用于大数据集统一拾取 | 不依赖定位残差 | 是（精修） | 论文方法 | [16] |
| 模板匹配 + 差分走时（Shelly 2020） | 13,525 个 SCSN 事件作模板；P/S 模板起点在拾取前 0.3 s；差分时间上限 P 0.5 s、S 0.85 s；860 万 P 和 1580 万 S 互相关差分时间进 hypoDD | 不依赖定位残差 | 新事件的到时由互相关得到 | 方法公开 | [17] |
| HypoDD 残差加权 | 按残差和距离迭代重加权，WRCT/WRCC 设阈值 | 降权/剔除 | 否 | 开源 | [30，未打开用户手册，待核] |
| PickNet（ESPRH 流程） | EqT 拾取后用 PickNet 在 ±2 s 内精修，再关联、定位 | 无反馈 | 是（但单向） | 开源 | [23] |

没有找到的东西（负结果，有价值）：

- 没有找到 Nippress et al. 2010（ANCORP 自动拾取优化）的原文或可靠摘要（检索结果无关）。从训练知识看，该文可能用初定位的理论到时窗口重拾，[待核]。
- 没有找到"把定位残差作为监督信号反向修正深度学习拾取"的已发表工作（检索词包括 predicted arrival window、iterative repicking、residual-guided）。最接近的是 ADAPT–VELEST [15] 和 PhaseNet 原文中的迭代训练（与定位无关）。这与方向 15（新颖性核查）相关，建议那边继续核。
- 没有找到 MPX 是否开源的确认。

可作为本项目非 LLM 基线的候选（按推荐顺序）：

1. **R0 稳健定位不重拾**：PhaseNet 拾取 + Hypoinverse 默认残差降权（或 ADLoc RANSAC）。回答"agent 的重拾比单纯丢/降权多带来什么"。
2. **R1 预测窗口重拾**：初定位 → 每台预测 P/S 到时 → 在 ±w（如 0.5 s，随残差背景调）内重新取 PhaseNet 概率峰（降低阈值）或 AIC 最小值 → 稳健定位，迭代 2–3 次。与 agent 内循环同构，只是决策规则固定。对应 ADAPT–VELEST 思路 [15]。
3. **R2 R1 + 台站校正**：先在练习池用 VELEST 求最小一维模型和台站延迟 [14]，固定后再做 R1。检验"背景降低后残差反馈是否更有效"。
4. **R3 互相关精修**（选做，成本高）：对同簇相似事件做 P/S 互相关，按 Rowe 2002 的思路求一致的相对拾取 [16]。这是唯一能在 0.01–0.1 s 层面改进拾取的非标签方法，可作为"细调"的上限参照。
5. BayesLoc [11] 和 2512.06407 的污染模型 [10] 作为讨论中的相关工作，不建议当主基线（获取成本和区域尺度问题）。

### 4. 残差分数如何被刷，怎么防

| 刷分方式 | 机制 | 证据 | 约束 |
|---|---|---|---|
| 丢掉难拾取 | 去掉大残差的拾取，RMS 下降，再丢更多 | Hypoinverse 手册专门设 RMSCUT 防"向内螺旋" [7]；上游项目 SeismoAgentBench 的 RMS 识别坏事件 AUC 6/10 组合 <0.5 [26a] | 分数不用 RMS；拾取数、S 拾取数、方位空隙、最近台距离、近台 S 是否存在不得低于基线；被删除的拾取仍按其留一残差计分 |
| 把拾取挪向预测时刻 | 用其他拾取的定位预测本拾取，再挪过去，残差按构造变小；错误在台站间"从众"传播 | 推断；Hypoinverse 手册建议"手动去掉最大残差再加回"的人工流程本身就含这种风险 [7] | 重拾只能落在波形特征上（拾取器概率峰、AIC 极小、能量突变），候选点在看到预测时刻之前生成；记录每次移动的量和对应的波形证据；对移动幅度设先验（如超过 0.3 s 必须有震相解释） |
| 加入低质量拾取 | 噪声拾取被关联到真实事件，把位置拉偏 | 上游项目 SeismoAgentBench 的 Maple：为消除报警加入的 DPP 拾取 46% 残差 >0.5 s，30% 事件偏 >5 km；去掉后降到 5.9% [26b] | 新拾取组加入前后做有无对照；按台站组比较残差离散 |
| 速度模型/台站项过拟合 | 自由度吸收误差，残差降但位置偏 | 上游项目 SeismoAgentBench 的 Magna：agent 用单侧台站 S 延迟吸收真实深度偏差，并以残差变差否定正确报警 [26c]；Cianetti 2026：模型不同但都拟合数据 [18] | 速度模型和台站项在练习池上求出后冻结，测试事件不再估计；台站项按事件留出交叉验证求 |
| 用定位权衡吸收 | 误差进入发震时刻和深度 | 2.1 节 | 报告位置和时刻相对参考的变化，不只报残差 |
| 只挑容易事件 | 物理分数在约束好的事件上自然好 | 上游项目 SeismoAgentBench 的 σh 识别坏事件 AUC 0.62–0.98 [26a] | 分数按事件固定集合计算，不允许跳过事件 |

推荐的反馈信号（推断，基于以上证据）：

- **交叉验证残差**：定位时随机留出约 20% 拾取（agent 不能选），用其余拾取定位，计算留出拾取的预测残差。删除拾取会让约束变差、预测变差，所以不能靠删除获益；同时报告覆盖度。
- **相对"同模型分析员拾取定位"的位移**：用同一定位器、同一模型、同一台站校正，比较 agent 拾取的定位和分析员拾取的定位（设计稿 B8）。模型误差在两者中共有，差值主要来自拾取。这只能在有标签的集合上用，适合作最终评价，不适合作 H3 的物理反馈。
- **留一残差只用于"找可疑拾取"**，作为 agent 的工具输出，不作为门控分数。

## 对本项目的影响

1. **残差反馈能纠正什么（直接回答"粗差还是细调"）**：粗差。按 2.3 的量级，单事件残差在一维模型下只能可靠发现 ≥1 s 的错误（密集网络），有台站校正时可下探到约 0.3 s；0.1 s 以下不可见，且系统偏差（拾取器整体偏早/偏晚、某台站一致偏差）完全不可见。H3 应改写为"物理反馈能学到识别和修正粗差（错相、错波列、漏 S、误拾）的规则"，不应声称物理反馈能提高起跳细调精度。试点中 agent 的主要优势（P MAE 0.02 对 0.04 s、缓起震相）属于物理反馈学不到的部分；这一点建议在设计稿第 6 节明确写出。
2. **反馈信号的设计**：
   - 去掉 RMS 作为反馈或门控分数（证据 [7][18][26a]）。
   - 先在练习池用 VELEST 求最小一维模型和台站延迟并冻结（上游 seismotools 已有 VELEST 接口），再算残差；否则一维背景 0.1–0.17 s 会淹没大部分可纠正的错误。
   - 给 agent 的工具输出：每个拾取的留一残差、importance（h_ii）、学生化值；对 h_ii > 0.5 的拾取标注"残差不可信"。
   - 物理门控分数用交叉验证残差加覆盖度约束；任何一项覆盖度低于基线即判不合格（与设计稿一致，但把"RMS/残差"换成"交叉验证残差"）。
   - Wadati 离群和 S−P 一致性只对 S 粗差（0.3 s 以上）有用；上游项目 SeismoAgentBench 的记录 20 表明近台 S−P 深度在多数情况下方向不可靠 [26d]，不要作为深度反馈。
3. **非 LLM 基线**：至少加 R0（稳健定位不重拾）和 R1（预测窗口重拾 + 稳健定位，规则固定），最好加 R2（R1 + 冻结台站校正）。这三个与 agent 组对比，才能说明"看图重拾"比固定的残差驱动规则多带来什么。现有设计的 B5（PhaseNet + AIC）没有定位反馈环，不能替代 R1。
4. **需要增加的实验/对照**：
   - **半合成注入实验**：在分析员拾取上人为注入 0.05/0.1/0.3/1 s 误差、P/S 互换、跳周（按主频半周期），量化 agent（只看残差、不看标签）能找回多少；与 R0/R1 同条件比较。这是评价"残差驱动重拾"的唯一干净方法，可与方向 2 的半合成测试集合并。
   - 按 importance 分层报告检出率（h<0.2、0.2–0.5、>0.5）。
   - 安慰剂：把留一残差在台站间随机置换后作为反馈，检查 agent 是否真的利用了残差信息。
5. **报告方式**：每个"残差驱动修改"记录修改前后的拾取、波形证据、残差变化和最终与分析员拾取的差；统计"修改后更接近分析员"的比例，按错误类型和 importance 分层。

## 未解决与待核

- NonLinLoc EDT 的公式和对离群的定量稳健性，HypoDD 2.1 的 WRCT/WRCC 动态阈值和双权重细节：本轮未能打开文档（网络和检索配额限制），需读 NonLinLoc 文档和 hypoDD2_UserGuide.pdf（GitHub fwaldhauser/HypoDD/doc）。
- Nippress et al. 2010、Diehl et al. 2009 GJI、Di Stefano 2006 的具体重拾流程（是否用初定位理论到时开窗、是否迭代）：只读到摘要。
- Kissling et al. 1994 最小一维模型流程中关于剔除/重拾的原始建议：未打开原文。
- 南加州"一维 + 台站项"和"SSST"之后单个绝对残差（不是差分残差）的离散具体是多少：Lin et al. 2007 只给了 composite event 的一维和三维 MAD [1]；Lin, Shearer & Hauksson 2007 重定位论文（JGR B12309）应有更细统计，未打开。
- 2.3 节的模拟应在真实 Ridgecrest 台站几何、Shelly 或 Hadley–Kanamori 模型、实际 PhaseNet 残差分布上重做，并加入多事件 SSST，再定阈值。建议在第一轮实验前完成（1–2 天工作量，推断）。
- 想问 Lomax（NLL-SSST、Cianetti 2026 作者）：是否有逐拾取离群检出率的统计；想问 Waldhauser：DD 中被降权的拾取有多少是真实错误。
- ADAPT 是否公开、是否可直接用作 R1 基线。

## 参考文献

1. Lin, G., Shearer, P. M., Hauksson, E., & Thurber, C. H. (2007). A three-dimensional crustal seismic velocity model for southern California from a composite event method. *J. Geophys. Res.*, 112, B11306. https://doi.org/10.1029/2007JB004977 （PDF：https://igppweb.ucsd.edu/~shearer/mahi/PDF/2007/lin_tomo_jgr07.pdf）[已读原文]
2. Lin, G., & Shearer, P. (2005). Tests of relative earthquake location techniques using synthetic data. *J. Geophys. Res.*, 110, B04304. https://doi.org/10.1029/2004JB003380 （PDF：https://igppweb.ucsd.edu/~shearer/mahi/PDF/lin_jgr05.pdf）[已读原文]
3. Richards-Dinger, K. B., & Shearer, P. M. (2000). Earthquake locations in southern California obtained using source-specific station terms. *J. Geophys. Res.*, 105(B5), 10939–10960. https://doi.org/10.1029/2000JB900014 [只读摘要]
4. Hauksson, E., Yang, W., & Shearer, P. M. (2012). Waveform relocated earthquake catalog for southern California (1981 to June 2011). *Bull. Seismol. Soc. Am.*, 102(5), 2239–2244. https://doi.org/10.1785/0120120010 [已读原文]
5. Yu, Y., Ellsworth, W. L., & Beroza, G. C. (2025). Accuracy and precision of earthquake location programs: Insights from a synthetic controlled experiment. *Seismol. Res. Lett.*, 96(3), 1860–1874. https://doi.org/10.1785/0220240354 （NSF PAR：https://par.nsf.gov/servlets/purl/10610289）[已读原文]
6. Waldhauser, F., & Schaff, D. P. (2008). Large-scale relocation of two decades of Northern California seismicity using cross-correlation and double-difference methods. *J. Geophys. Res.*, 113, B08311. https://doi.org/10.1029/2007JB005479 （PDF：https://www.ldeo.columbia.edu/~felixw/papers/Waldhauser_Schaff_JGR2008.pdf）[已读原文]
7. Klein, F. W. User's Guide to HYPOINVERSE-2000, a Fortran program to solve for earthquake locations and magnitudes（hyp1.40 版手册；原始为 USGS Open-File Report 02-171）. https://escweb.wr.usgs.gov/content/software/HYPOINVERSE/doc/hyp1.40.pdf [已读原文：残差加权、importance 两节]
8. Billings, S. D., Sambridge, M. S., & Kennett, B. L. N. (1994). Errors in hypocenter location: picking, model, and magnitude dependence. *Bull. Seismol. Soc. Am.*, 84(6), 1978–1990. [只读摘要]
9. Zhu, W., Rong, B., Jie, Y., & Wei, S. S. (2025). Robust earthquake location using Random Sample Consensus (RANSAC). arXiv:2502.10933. https://arxiv.org/abs/2502.10933 [已读原文（HTML，经抓取摘录）]
10. Yu, Z., Sun, J., Cai, Y., Liu, Z., Wu, P., Liu, X., & Tan, J. (2025). Toward trustworthy earthquake catalogs in the era of automated detection: A probabilistic framework for robust earthquake location. arXiv:2512.06407. https://arxiv.org/abs/2512.06407 [只读摘要]
11. Myers, S. C., Johannesson, G., & Hanley, W. (2007). A Bayesian hierarchical method for multiple-event seismic location. *Geophys. J. Int.*, 171(3), 1049–1063 [只读摘要]；Johannesson, G., Myers, S. C., & Hanley, W. G. (2005). Hierarchical Bayesian approach to locating seismic events. LLNL UCRL-PROC-217057. https://www.osti.gov/servlets/purl/888581 [已读原文]；Johannesson, Hanley & Myers (2009) Incorporation of probabilistic seismic phase labels into a Bayesian multiple-event seismic locator [只读摘要]
12. Diehl, T., Kissling, E., Husen, S., & Aldersons, F. (2009). Consistent phase picking for regional tomography models: application to the greater Alpine region. *Geophys. J. Int.*, 176(2), 542–554. [只读摘要]
13. Di Stefano, R., Aldersons, F., Kissling, E., Baccheschi, P., Chiarabba, C., & Giardini, D. (2006). Automatic seismic phase picking and consistent observation error assessment: application to the Italian seismicity. *Geophys. J. Int.*, 165(1), 121–134. https://doi.org/10.1111/j.1365-246X.2005.02799.x [只读摘要]
14. Bagagli, M., Molinari, I., Diehl, T., & Kissling, E. (2025). Local earthquake tomography of the Alpine region from 24 years of data. *Geophys. J. Int.*, 241(1), 454–473. https://doi.org/10.1093/gji/ggaf028 [已读原文]
15. Bagagli, M., Molinari, I., Diehl, T., Kissling, E., Giardini, D., & AlpArray Working Group (2022). The AlpArray Research Seismicity-Catalogue. *Geophys. J. Int.*, 231(2). https://doi.org/10.1093/gji/ggac226 [只读摘要]；EGU22-6582 会议摘要 [只读摘要]
16. Rowe, C. A., Aster, R. C., Borchers, B., & Young, C. J. (2002). An automatic, adaptive algorithm for refining phase picks in large seismic data sets. *Bull. Seismol. Soc. Am.*, 92(5). [只读摘要]
17. Shelly, D. R. (2020). A high-resolution seismic catalog for the initial 2019 Ridgecrest earthquake sequence: Foreshocks, aftershocks, and faulting complexity. *Seismol. Res. Lett.*, 91(4), 1971–1978. https://doi.org/10.1785/0220190309 [已读原文：本地 MinerU 解析 `SeismoAgentBench/data/2019_ridgecrest_california/references/SHELLY2020_0220190309/`]
18. Cianetti, S., Lomax, A., Michelini, A., & Giunchi, C. (2026). Which is better: deep-learning or manual seismic arrival-time picking? *Geophys. J. Int.*, 244(3), ggaf494. https://doi.org/10.1093/gji/ggaf494 [已读原文（前半部分）]
19. Zhu, W., McBrearty, I. W., Mousavi, S. M., Ellsworth, W. L., & Beroza, G. C. (2021/2022). Earthquake phase association using a Bayesian Gaussian mixture model (GaMMA). arXiv:2109.09008. https://arxiv.org/abs/2109.09008 [只读摘要]
20. Atterholt, J., Wilding, J. D., & Ross, Z. E. (2025). The evolution of fault orientation in the 2019 Ridgecrest earthquake sequence with a new long-term catalogue of seismicity and moment tensors. *Geophys. J. Int.*, 240(3), 1579–1592. https://doi.org/10.1093/gji/ggaf001 [已读原文]
21. Lomax, A., & Savvaidis, A. (2022). High-precision earthquake location using source-specific station terms and inter-event waveform similarity. *J. Geophys. Res. Solid Earth*, 127, e2021JB023190. https://doi.org/10.1029/2021JB023190 [只读摘要]
22. Lomax, A. (2020). Absolute location of 2019 Ridgecrest seismicity reveals a shallow Mw 7.1 hypocenter, migrating and pulsing Mw 7.1 foreshocks, and evolving early aftershock structures. *Bull. Seismol. Soc. Am.*, https://doi.org/10.1785/0120200006 [只读摘要]
23. Wu, X., Huang, S., Xiao, Z., & Wang, Y. (2022). Building precise local submarine earthquake catalogs via a deep-learning-empowered workflow and its application to the Challenger Deep. *Front. Earth Sci.*, 10, 817551. https://doi.org/10.3389/feart.2022.817551 [已读原文]
24. Bondár, I., & Storchak, D. (2011). Improved location procedures at the International Seismological Centre. *Geophys. J. Int.*, 186(3), 1220–1244. https://doi.org/10.1111/j.1365-246X.2011.05107.x [已读原文（前半部分）；远震尺度，用于"相关误差导致不确定度低估"]
25. Shearer, P. M. (1997). Improving local earthquake locations using the L1 norm and waveform cross correlation: Application to the Whittier Narrows, California, aftershock sequence. *J. Geophys. Res.*, 102, 8269–8283. https://doi.org/10.1029/96JB03228 [只读摘要]
26. 上游项目记录（SeismoAgentBench，`docs/research/progress/records/`）[本地记录]：
    a. `15_locator_diagnostics.md`（σh、RMS、台站残差离散的诊断能力）；
    b. `16_maple_s3_vertical_only_picks.md`（加入低质量拾取导致误位）；
    c. `17_dev_round1.md`（以残差否定正确深度报警、单侧台站延迟吸收偏差）；
    d. `20_independent_depth_check.md`（近台 S−P 深度核对）。
27. 自做模拟：本次调研脚本 `scripts/03_residual_detectability/detect_sim2.py`（设置见 2.3 节），未纳入项目代码 [推断性证据]
28. Gomberg, J. S., Shedlock, K. M., & Roecker, S. W. (1990). The effect of S-wave arrival times on the accuracy of hypocenter estimation. *Bull. Seismol. Soc. Am.* https://earthweb.ess.washington.edu/gomberg/Papers/GombergetalBSSA90.pdf [只读摘要]
29. Kissling, E., Ellsworth, W. L., Eberhart-Phillips, D., & Kradolfer, U. (1994). Initial reference models in local earthquake tomography. *J. Geophys. Res.*, 99, 19635–19646. [未打开原文，待核]
30. Waldhauser, F. (2001). hypoDD: A program to compute double-difference hypocenter locations. USGS Open-File Report 01-113；用户手册见 https://github.com/fwaldhauser/HypoDD [未打开原文]
