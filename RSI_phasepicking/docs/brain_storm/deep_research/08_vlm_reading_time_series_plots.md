# 08. 多模态模型读时间序列图

调研日期：2026-11-13。检索预算在本轮用完，个别条目只看到摘要或搜索摘要，已逐条标注。

## 要回答的问题

- 现有视觉语言模型（VLM）从折线图、时间序列图中读数值、定位拐点或起始点的精度如何？相关评测：ChartQA、PlotQA、CharXiv、PlotChain（草稿称 arXiv 2602.13232，需核实），把时间序列画成图的评测（如 TimeSeriesExam、"Plots unlock time-series understanding"、VisionTS、用 VLM 做时间序列推理），以及从图上做异常或变点检测。已知的失败模式（读坐标轴、细粒度定位、数刻度）。
- 绘图选择的影响：分辨率、长宽比（长条图）、子图数量、网格线和刻度密度、放大窗口、各厂商的图片 token 预算；"图 + 数值片段"混合输入、只给图、只给数值三者的对比。
- 地震学领域：MULTISEISMO（arXiv 2605.26320，需核实）、SeisMoLLM（GRL 2026，需核实）、FA-Agent（arXiv 2611.06555，需核实；多模态 agent 拾取初至），以及任何 LLM/VLM 拾取震相或读地震图的研究（如用 Gemini 看地震图、SeisLM、地震基础模型）及其报告的精度。
- 目前哪些模型（闭源和开源）读细节最好？

影响的决定：图怎么画；要不要加数值辅助工具；选哪个模型。

## 结论摘要

- **VLM 擅长"看形状、找区间"，不擅长"读一个点的精确位置"。** 把时间序列画成图做异常检测时，最好的 VLM 在区间型异常上 F1 最高 50.33，在单点型异常上最高只有 4.09；GPT-4o 从文本换成图后，单点 F1 从 5.71 降到 2.61，区间 F1 从 11.95 升到 29.88 [17]。VLM4TS 作者直接写道，VLM 在一张长图上"无法借助拥挤的 x 轴刻度确定区间的精确边界" [18]。拾取起始时刻属于"单点定位"，所以单靠看图很难达到 0.02 s 级的精度，需要放大窗口或数值工具。
- **常用的图表基准已经饱和，不能用来区分前沿模型的细读能力。** ChartQA 上 Claude Sonnet 3.5 有 90.5%，换到更难的 ChartQAPro 只有 55.81% [7]；CharXiv 推理题在 2024 年最好的是 GPT-4o 47.1%（人类 80.5%）[2]，到 2026-11 第三方榜单上前沿模型已到 93–96% [3][4]。真正考"读数"的新基准分数仍然低：密集折线图数字化（EpiCurveBench）最好 52.3% [9]；专业图表（Chartography）最好 45.0%，主要错误之一是"在刻度标注稀疏的轴上读错数值" [10]；工程图读数（PlotChain）最好 80.4%，频域图（带通响应）不超过 23% [1]。
- **画图优于直接塞数字，但数字在精确数值题上更好，两者一次性混合的增益很小。** 在多项任务上，画成图比把数值写成文本的效果高出最多约 120%–150%，输入 token 少约 90% [13]；TSRBench 中 GPT-5 用图在感知类任务上更好（异常检测 61.2→69.8），用文本在数值推理上更好（72.2 vs 64.0），图文一起给只比最好的单一模态高 0.1–0.5 分 [16]。所以数值更适合做成按需调用的工具，而不是每次都和图一起塞进去。
- **渲染参数中，长宽比和刻度比 DPI 更重要。** Google 的消融实验中，DPI（25–400）、图幅、风格对趋势分类"没有明显正面作用" [13]；但极端长宽比会让准确率下降约 5%–18%，作者认为原因是位置编码脆弱，而不是 token 太多 [21]；OpenAI 文档也列出模型"难以处理全景图" [24]。设计稿中 1600×400（4:1）的长条图，在 OpenAI、Anthropic 和 Qwen3.8 上都不会被缩小（约 650–870 个视觉 token）；Gemini 3/4 不论图多大，每张图都固定为 1120 个 token（默认档）[24][25][26]。
- **地震学方面，没有找到任何论文用通用 VLM 看天然地震波形图拾取 P/S 并报告精度。** FA-Agent 已核实（Li & Yuan，2026-11-04，投稿 *Geophysics*），用的是 GPT-6 Astra 网页交互，而不是 API。处理对象是勘探共炮集初至，在半合成数据上全部保留的拾取都落在 ±20 ms 内、约 56%–60% 落在 ±8 ms 内；唯一对比的基线是传统能量比 + AIC 拾取器，没有和深度学习拾取器比 [28]。MULTISEISMO 已核实，但它是**把波形当原始数字喂给 Phi-4**（降采样到 1024 点），唯一的时间序列任务是"地震还是噪声"二分类，**没有测试看图，也没有拾取任务** [29]。设计稿把它当作"需要绘图"的证据，这一点说过头了。SeisMoLLM 已核实发表于 GRL 第 53 卷第 8 期（e2025GL118505，2026-04-14）。它是把 GPT-2 骨干微调在原始波形上，不看图；STEAD 上 P 波 MAE 为 0.498 个采样点（约 5 ms）[30]。
- **前沿闭源模型的读图能力在现有基准上已不可区分，开源模型中 Qwen3.8-27B 最强。** Mercor 的 CharXiv 榜单：Opus 5.5 96.4%、GPT-6 Astra 96.1%、Sonnet 5.5 96.1%、GPT-6.1 Sol 96.0%、Gemini 3.8 Flash 95.4% [4]。开源模型中，Qwen3.8-27B 自报 CharXiv(RQ) 不用工具 83.7、用代码解释器 90.2 [5]；Gemma 4 31B 没有公布 CharXiv 或 ChartQA 成绩 [27]。没有任何基准测"在波形上定位起始点"，所以选模型必须靠本项目自己做的读图测试。

## 详细发现

### 1. 通用 VLM 读图的精度

#### 1.1 图表问答基准（ChartQA → ChartQAPro → CharXiv → ChartMuseum）

| 基准 | 内容 | 关键数字 | 来源 |
|---|---|---|---|
| ChartQA / ChartQAPro | 图表问答 | Claude Sonnet 3.5：ChartQA 90.5%，ChartQAPro 55.81%；开源最好的 Qwen2-VL-7B 在 ChartQAPro 上 37.17% | [7] |
| CharXiv（2024） | 2,323 张 arXiv 论文中的真实图表，分描述题和推理题 | 推理题：GPT-4o 47.1%、最好的开源模型 29.2%、人类 80.5%；对图或问题稍作改动，分数最多下降 34.5% | [2] |
| CharXiv（2026-11 榜单） | 同上 | llm-stats CharXiv-R：Claude Mythos Preview 0.932、Kimi K3 0.913、Claude Opus 4.7 0.910、Qwen3.8 Flash 0.906、Qwen3.8-27B 0.902、GLM-5.3-Flash 0.894 [3]；Mercor：Opus 5.5 96.4%、GPT-6.1 Sol 96.0%、Gemini 3.8 Flash 95.4% [4] | [3][4] |
| ChartMuseum（NeurIPS 2025） | 1,162 道需要视觉推理的图表题 | Gemini-2.5-Pro 63.0%，Qwen2.5-VL-72B 38.5%，人类 93.0%；以视觉推理为主的题目比以文字推理为主的题目低 35%–55% | [8]（只看到搜索摘要） |

注意：[3][4] 是第三方聚合榜单，没有说明测的是推理子集还是全部题目，Mercor 自己跑的配置也不进入正式排名 [4]。这些数字只能说明前沿模型在"图表问答"上已接近满分，不能说明它们能精确读坐标。

#### 1.2 专门考"读数"和"定位"的基准

| 基准 | 任务 | 结果 | 与本项目的关系 | 来源 |
|---|---|---|---|---|
| PlotChain（arXiv 2602.13232，2026-01-29，单作者 Mayank Ravishankara）**已核实存在** | 15 类工程图（Bode/FFT、阶跃响应、应力-应变等）共 450 张，参数已知，按字段容差评分 | Gemini 2.5 Pro 80.42%、GPT-4.1 79.84%、Claude Sonnet 4.5 78.21%、GPT-4o 61.59%；频域题最差，带通响应 ≤23% | 测的是上一代模型；频域图差，提示频谱图读数要慎重 | [1] |
| EpiCurveBench（EMNLP 2026） | 把密集的流行病曲线图数字化成表格 | 最好的是 Gemini 2.5 Pro（高推理档）52.3% ECS；GPT-5.2 45.4%、Claude Opus 4.5 42.0%、Qwen3-VL-235B 27.5%。折线图比柱状图难（Gemini 47.5% vs 72.7%），折线图平均每张 842 个数据点。给模型加"代码 + 裁剪放大"工具后，效果有升有降（Qwen +2.0、GPT-5.2 +0.9、Claude −1.5、Gemini −4.3），主要失败是裁出的区域重叠或残缺 | **放大工具不一定有用**，裁剪方式要由程序控制，不要让模型自己随意裁 | [9] |
| Chartography（ECCV 2026 workshop） | 100 道专业图表题 | 30 种模型配置中最好的只有 45.0% pass@1；主要失败是"在刻度标注稀疏的轴上读错数值"、漏看细微的视觉特征 | 直接支持"刻度要密、要标数字" | [10] |
| VisOnlyQA | 只考几何和数值感知，不需要推理 | 人类 93.5% / 95.0%；最好的 Gemini 2.5 Pro 在真实/合成两个子集上分别为 79.0% / 55.4%；"图表交点"等子任务接近随机 | 细粒度几何感知是瓶颈 | [11]（只看到搜索摘要） |
| VLMs are blind（ACCV 2024） | 数两条折线有几个交点（0、1 或 2） | 四个前沿模型的准确率在约 41%–76% 之间 | 数交点、数刻度这类简单任务也不可靠 | [12]（只看到搜索摘要） |
| ChartAB（arXiv 2510.26781） | 图表定位和对齐（提取数据、定位元素） | 摘要说 VLM"仍缺乏对细节的准确感知"，没有给数字 | — | [只读摘要] |

厂商文档自己也承认这些局限：OpenAI 列出"精确空间定位困难""颜色或线型（实线、虚线、点线）变化的图表可能读错""计数是近似的""难以处理全景图"[24]；Anthropic 写明"坐标和定位输出是近似的""计数可能不准"[25]。

#### 1.3 时间序列画成图的研究

| 研究 | 做法 | 关键结果 | 来源 |
|---|---|---|---|
| Plots unlock time-series understanding（Daswani 等，Google，2024） | 同一批数据分别以图和文本输入 GPT-4o/4o-mini、Gemini 1.5 Pro/Flash | 用图在合成任务上最多提升约 120%，在真实任务（跌倒检测、活动识别）上最多提升约 150%，API 成本最多降 90%；例外是需要判断幅度的"二次函数导数"题，GPT-4o 用文本更好（图 −37.5%）。跌倒检测上最好的模型（灵敏度/特异度 0.92/0.81）仍不如专用 SVM（0.96/0.96） | [13] |
| VL-Time / TimerBed（Liu 等，2024） | 先由 LLM 规划可视化方式，再基于图推理 | 少样本 GPT-4o：RCW 任务 91.03%（数值输入 50.00%），EMG 任务 91.67%（数值输入 33.33%）；平均提升 140%，token 少 99% | [14]（只看到搜索摘要） |
| TimeSeriesExam（Cai 等，2024） | 时间序列概念考试，比较图和文本输入 | 用图通常更好；多序列、多步推理时所有模型都吃力 | [15]（只看到搜索摘要） |
| TSRBench（Yu 等，2026） | 比较文本、图、图文一起三种输入 | GPT-5：文本 55.5、图 52.4、图文一起 55.6；感知类任务用图更好，数值推理用文本更好；**100 PPI 最好，更高或更低都变差** | [16] |
| VisualTimeAnomaly（Xu 等，2025） | 8 个 MLLM 零样本从图上做异常检测 | 能力排序为"多变量 >> 区间 >> 单点"；变量数多时把图拆成多张子图有帮助（Gemini 在 M=36 时从 33.2 降，拆图后 M=100 时达 59.91）；用图后幻觉显著减少 | [17] |
| VLM4TS（He 等，AAAI 2026） | 先由 ViT 在小窗口图上提出候选区间，再让 VLM 在整段图上确认 | 平均 F1 0.665，比纯文本 LLM 方法好约 2 倍，token 少约 30–36 倍；作者明确指出 VLM 在长图上无法凭拥挤的刻度确定精确边界 | [18] |
| VisAnomReasoner（NeurIPS 2026） | 微调一个小 VLM 从图上定位异常并解释 | 比基线 F1 高 23.87 个百分点（摘要数字） | [19]（只读摘要） |
| VisionTS（ICML 2025） | 把一维序列切段、排成二维灰度图，用图像 MAE 做预测 | 这是预测任务，不是读图问答，和本项目关系不大 | [20]（未打开原文） |

**变点和起始点定位**：没有找到报告"VLM 定位变点时刻误差"（例如容差内命中率、平均时刻误差）的研究。和它最接近的就是上面的单点异常和区间边界结果，都指向同一结论：VLM 能说出"大概在哪一段"，但给不出精确的采样点位置。

### 2. 渲染选择的影响

#### 2.1 分辨率、DPI、图幅

- 在 Google 的消融实验中（函数形状分类，Gemini 1.5 Pro），DPI 从 25 到 400、图幅、风格预设、配色"都没有明显正面作用"；例如无噪声时 25 dpi 为 0.91、200 dpi 为 0.98，噪声大时各档都只有 0.35–0.42 [13]。坐标轴等图元素"全部保留"略好于"最少"或"全部去掉"（线性函数 0.94 vs 0.89 vs 0.85）[13]。
- TSRBench 报告 100 PPI 最好 [16]；"Can't Find Waldo"发现把图放大（双三次插值 1.5×–6×）后准确率不单调变化，有的模型先升后降，有的一放大就降 [21]。
- **推断**：分辨率只要达到"不被厂商缩小、线条清晰"即可，靠无损放大整张图来提高精度没有证据支持；真正决定读时精度的是"每个视觉 token 覆盖多少秒"（见 2.4）。

#### 2.2 长宽比和长条图

- 极端长宽比（一维方向填充）使准确率下降约 5%–18%，比二维填充（≤10%）更严重；作者归因于位置编码脆弱，而不是注意力被稀释 [21]。
- OpenAI 文档列出"难以处理全景图" [24]。
- VLM4TS 把整段序列画成一张长图时，模型会漏掉异常、定错边界 [18]。
- **推断**：4:1（1600×400）不算极端，但不要为了显示整段记录画 8:1 甚至更长的图。整段概览图和放大图应分开出。

#### 2.3 子图数量

- 变量多时，拆成多张子图或多张图比挤在一张图里好 [17]；加速度计和陀螺仪分开画只有"轻微好处"，而且随少样本示例增多而减小 [13]。
- **推断**：三分量（Z/N/E）按上下三个子图共用时间轴是合理的。但每个子图的纵向像素会减少，判断极性时应单独出一张 Z 分量放大图。

#### 2.4 刻度、网格和放大窗口

- 刻度稀疏是读数出错的主要原因之一 [10]；刻度拥挤又会让边界无法确定 [18]。两者需要平衡：主刻度要标数字，次刻度只画网格线。
- 放大和裁剪工具的效果不稳定：EpiCurveBench 中加"代码裁剪放大"后两家下降 [9]；DeepEyes 用强化学习训练"放大"工具，在 V* 上比基座模型提高 18.9 个点 [22]，但 EMNLP 2026 Findings 的一篇审视文章认为这类模型常常只有很小甚至负的增益 [23]（两者都只看到搜索摘要）。
- **定量推断（本项目自己的换算）**：大多数厂商每个视觉 token 对应约 28–32 像素（Anthropic 28 px [25]、OpenAI 32 px 的 patch [24]、Qwen3.8 为 16 px patch × 2×2 合并 = 32 px [5]）。设绘图区宽约 1,400 像素：
  - 显示 60 s 全记录时，每个 token 约 1.4 s，只能用来识别震相和大致位置；
  - 显示 4 s 窗口时，每个 token 约 0.09 s；
  - 显示 1 s 窗口时，每个 token 约 0.02 s。

  试点报告的 P 波 MAE 为 0.02 s。如果只靠视觉，大约需要宽度 ≤1 s 的放大窗口，或者交给 AIC 等数值方法精修。这和试点"先看图、后用数值精修"的流程一致，也说明试点的精度优势中有多少来自看图、有多少来自 AIC，需要单独拆开测（见"对本项目的影响"）。

#### 2.5 各厂商的图片 token 预算（以 1600×400 为例，2026-11-13 查阅）

| 厂商/模型 | 规则 | 1600×400 的 token 数 | 来源 |
|---|---|---|---|
| OpenAI gpt-6 / gpt-5.6 系列 | 每 32×32 像素一个 patch，`high` 档上限 2,500 个 patch，`original`/`auto` 保持原尺寸；token 数 = patch 数 × 1.2 | 50×13 = 650 个 patch → 780 个 token（不缩小）。**gpt-6.1-sol 不在文档表中，按同系列规则推断 [待核]** | [24] |
| Anthropic Claude 4.7 及以后（含 Opus/Sonnet 5.5） | 每 28×28 像素一个视觉 token；长边上限 2,576 px，上限 4,784 个 token | 58×15 = 870 个 token（不缩小） | [25] |
| Google Gemini 3/4 | 按 `media_resolution` 档位固定：low 280、medium 560、high 1120、ultra_high 2240；默认 1120；读图表建议用 high | 与图片尺寸无关，固定 1120 个 token；4:1 的图内部如何缩放没有公开 [待核] | [26] |
| Gemma 4 | 视觉 token 预算可设为 70/140/280/560/1120；读小字、文档用高档 | 最多 1120 个 token | [27] |
| Qwen3.8-27B（自部署） | 16 px patch，2×2 合并 → 每 32×32 像素一个 token；每张图最少 64、最多 16,384 个 token | 约 50×13 = 650 个 token（不缩小） | [5] |

结论：设计稿的 1600×400 在主要厂商上都不会被悄悄缩小（Gemini 除外，其内部缩放方式不公开）。如果想把放大图画得更大（例如 2400×600），在 OpenAI 上需要用 `original` 档，在 Gemini 上需要用 `ultra_high` 档。

#### 2.6 图 + 数值、只有图、只有数值

| 证据 | 结论 |
|---|---|
| Plots unlock [13]、VL-Time [14]、TimeSeriesExam [15] | 对于长序列，画成图远好于把数字写成文本，而且便宜得多 |
| TSRBench [16] | 感知类任务用图更好，数值推理用文本更好；图文一起给的增益很小，而且答对的题目大多已被单一模态答对 |
| VisualTimeAnomaly [17] | 单点异常用文本比用图好（GPT-4o 5.71 vs 2.61），区间异常用图更好 |
| MULTISEISMO [29] | 把地震波形作为文本数字喂给 Phi-4，几乎完全失败（时间序列 BLEU 0.02），即使输入加长到 8k token 也没有明显改善 |

**推断**：最合适的是"先看图、再按需调用数值工具"——由图决定是哪个震相、大致在哪个窗口、极性如何；由数值工具（采样值、AIC、STA/LTA、初动符号）给出精确时刻。不应该把长段原始数值默认塞进每一轮。

### 3. 地震学领域的已有工作

| 工作 | 是否核实 | 实际内容 | 报告的精度 | 与设计稿说法的差异 | 来源 |
|---|---|---|---|---|---|
| **FA-Agent**（Wenda Li, Congcong Yuan；arXiv 2611.06555，v1 2026-11-04，v2 11-05；投稿 *Geophysics*） | 已核实 | 多模态 LLM agent 拾取山区陆上勘探数据的初至：先看整张道集（720 道，每道 751 个采样点、间隔 4 ms），再放大问题区，对每个初始拾取选择保留、修正或删除；画图前做 AGC（窗口 400 ms，最大增益 30）；图上用不同颜色标出初始、保留、修正、删除的拾取；有技能库，并把专家复核过的案例加入其中 | 半合成数据：强噪声下全部（只差 1 个）拾取在 ±20 ms 内，约 60% 在 ±8 ms 内；弱或隐藏初至时，保留的 324 个拾取都在 ±20 ms 内，56% 在 ±8 ms 内；传统拾取器只有 2% 或 0% 在 ±20 ms 内。可见道 100% 拾取，不可见道 81% 删除。实际数据没有真值 | 模型是 **GPT-6 Astra，通过网页交互使用，没有调用 API**，所以没有 token 和成本数字；**没有和深度学习拾取器对比**；图片尺寸和 DPI 没有报告；没有 S 波、极性、定位，没有学习曲线 | [28] |
| **MULTISEISMO**（Munikoti 等，PNNL；arXiv 2605.26320，2026-05-25） | 已核实 | 16,000 多个事件的多模态数据集（波形、烈度图、人口暴露图、文字描述），微调 Unified-IO 2 + Chronos 时序编码器得到 SeisModal | 时间序列任务只有"地震还是噪声"；Phi-4（波形以文本数字输入）BLEU 0.0218，SeisModal 0.675 | 设计稿说它"报告通用多模态模型处理地震时间序列效果差，这正好支持需要工具和绘图"。**实际上它从没把波形画成图给模型看**，只能说明"把数字写成文本不行"，不能说明"看图行" | [29] |
| **SeisMoLLM**（Xinghao Wang, Feng Liu 等；GRL 53(8) e2025GL118505，2026-04-14；arXiv 2502.19960） | 已核实（GRL 页面通过检索结果确认，正文读的是 arXiv v2） | GPT-2 骨干 + 卷积波形嵌入，在原始波形上微调，同时做五个任务 | STEAD：P 波 F1 98.08、MAE 0.498 个采样点（100 Hz 下约 5 ms，本项目换算）；S 波 F1 81.66。DiTing：P 波 F1 95.69、S 波 F1 72.82。作者承认拾取任务上的提升"不如其他任务明显" | 不是 VLM，不看图，不是 agent。它代表"专用模型"的精度上限，可作为对照 | [30] |
| SeisLM（Liu 等，2024） | 只看到搜索摘要 | 用自监督方式在波形上预训练的 transformer，微调后做检测和拾取 | 未打开原文 | 不是 VLM | [31] |
| Gemini 估计烈度（arXiv 2405.18732） | 只看到搜索摘要 | Gemini 1.5 Pro 读社交媒体帖子估计 MMI | — | 不是读地震图 | [32] |
| "用 Gemini 看一张波形图回答一个问题"（试点总结中提到的此前工作） | **未找到** | — | — | 需要向 Advikar 要出处 | 本地试点总结 |

多轮检索（"VLM seismogram"、"GPT-4o phase picking image"、"multimodal LLM first break" 等）都**没有找到**其他用通用 VLM 从波形图上拾取天然地震震相并报告精度的论文或会议摘要。这对新颖性有利，但也意味着本项目没有现成的"看图拾取误差"先验可以参照。

### 4. 哪些模型读细节最好

| 类别 | 模型 | 图表基准证据 | 备注 |
|---|---|---|---|
| 闭源 | Opus 5.5、GPT-6 Astra、Sonnet 5.5、GPT-6.1 Sol、Gemini 3.8 Flash | Mercor CharXiv 95.4%–96.4% [4] | 差距在误差范围内，基准已饱和 |
| 闭源 | Claude Mythos Preview、Claude Opus 4.7 | llm-stats CharXiv-R 0.932、0.910 [3] | Mythos 只对部分机构开放 |
| 闭源（上一代） | Gemini 2.5 Pro | PlotChain 80.42% [1]、EpiCurveBench 52.3% [9]、VisOnlyQA 79.0% [11] | 在细粒度读数基准上一直排第一，但这些基准没有测 2026 下半年的模型 |
| 开源 | Qwen3.8-27B（稠密，Apache-2.0） | CharXiv(RQ) 83.7，用代码解释器 90.2（自报）[5]；llm-stats 0.902 [3] | 同规模开源中最强；用代码工具后提高 6.5 分，说明"工具 + 看图"对它有用 |
| 开源 | Qwen3.8-Flash-Next（125B 总参数 / 6B 激活，MoE） | CharXiv(RQ) 84.6 / 90.6（用代码）[6] | 见方向 14 |
| 开源 | GLM-5.3-Flash（320B / 18B 激活，MIT） | llm-stats 0.894 [3] | 见方向 14 |
| 开源 | Gemma 4 31B | **没有公布 CharXiv 或 ChartQA**；MMMU Pro 76.9% [27] | 读图能力需要自己测 |

## 对本项目的影响

### 图怎么画

1. **至少出三类图，不要只用一张长条图。**
   - (a) 概览图：整段三分量，约 1600×400 或更低，用来识别震相和判断是否可用；
   - (b) P 放大图：以候选时刻为中心、宽 1–2 s 的 Z 分量，用来定时间和判极性；
   - (c) S 放大图：以候选时刻为中心、宽 2–4 s 的水平分量（可加 R/T 旋转）。

   按 2.4 节的换算，只有 ≤1–2 s 宽的窗口才能让一个视觉 token 对应 ≤0.02–0.04 s。
2. **刻度要密，并且标上数字。** 放大图每 0.1 s 一个带数字的主刻度，0.02 s 一条浅色竖网格线；时间轴用"相对候选拾取的秒数"（如 −0.5 … +0.5），不要用绝对时刻，以免模型读长串数字。依据：稀疏刻度导致读错 [10]，拥挤刻度导致无法确定边界 [18]。
3. **在图上画出带编号的候选线，让模型做选择或微调，而不是让它凭空估坐标。** 例如 PhaseNet、AIC、STA/LTA 各画一条细竖线并标 A/B/C，问"哪条最接近真实起始？要不要向左或向右移几个网格？"。依据：VLM 擅长在给定候选中确认，不擅长回归精确坐标（VLM4TS 先由别的方法提出候选、再让 VLM 确认 [18]；单点定位 F1 极低 [17]）。
4. **长宽比不要超过约 4:1，不要为了全景画超长图** [21][24]。三分量用上下三个共享时间轴的子图 [17]。
5. **显式设置分辨率档位**：OpenAI 用 `detail: "original"`（或确认 `high` 不会缩小），Gemini 用 `media_resolution: high`，自部署的 Qwen 不要把 `max_pixels` 调小。不要把整张图无损放大来"提高清晰度" [21]。
6. 频谱图等频域图只作辅助，不要让模型从频域图上读数值（PlotChain 中频域题最差 [1]）。

### 需不需要数值辅助工具

7. **需要，而且应该设为按需调用的工具，不要每轮默认附带。** 设计稿中 ±0.2 s 采样值、初动符号、STA/LTA 值的工具是对的。数值结果应该以结构化短文本返回（例如"AIC 最小值位于 +0.034 s；第一个超过噪声 3σ 的采样点位于 +0.028 s，符号为 +"），而不是返回 40 个原始采样值让模型自己算 [16][17][29]。
8. **必须加一个"没有 VLM 的同一数值流程"对照组**：PhaseNet → 同样的 AIC 精修 → 同样的残差剔除。否则无法区分精度来自看图还是来自 AIC（试点问题第 6 条已经指出这一点）。

### 选哪个模型

9. **公开基准不能用来选模型，必须先做本项目自己的"只测看图"实验**（设计稿 §8.1 第一步）。建议扩充成一个**读图校准实验**，成本很低，可以一次回答"怎么画"和"选谁"两个问题：
   - 用已知分析员拾取的波形，把真实起始点随机平移后重新渲染；
   - 自变量：窗口宽度（0.5/1/2/4/60 s）、刻度密度（稀/密）、有无候选线、图片尺寸（800/1600/2400 宽）、是否附带数值摘要；
   - 因变量：读出时刻的误差分布、极性正确率；
   - 模型：GPT-6.1-sol、一个 Claude 5.5、Gemini 3.8 Flash、Qwen3.8-27B、Gemma 4 31B；
   - 每个条件约 100 张图即可画出"误差随每 token 秒数变化"的曲线。
10. 这个实验的结果用来确定放大窗口宽度和默认绘图参数，然后再进入完整 agent 运行。
11. 如果开源模型在"选择候选线"这种问题形式下与闭源模型相差很小，而在"直接读坐标"时差距大，那么分级架构中的 T1 层就应该只用"选择/确认"这种问题形式。

## 未解决与待核

- gpt-6.1-sol 的图片 token 规则（OpenAI 文档表中只列了 gpt-6-astra 和 gpt-5.6 系列）[待核]；Gemini 在固定 1120 token 下如何缩放 4:1 的图 [待核]。
- ChartMuseum、VisOnlyQA、VLMs are blind、VL-Time、TimeSeriesExam、DeepEyes 及其审视文章只看到了搜索摘要，引用具体数字前应打开原文。
- Chartography 的逐模型结果、Gemini 4 Argon/Carbon 的图表成绩没有拿到 [待核]。
- 没有找到任何"VLM 定位变点或起始时刻的误差"研究——本项目的读图校准实验本身可能就是一个有价值的补充结果。
- 向 Advikar 确认：试点中每张图的实际尺寸、窗口宽度、是否给了候选线；"Gemini 看波形图"那项此前工作的出处。
- FA-Agent 的作者说之后会做本地部署版本；可以关注它的 v3 或后续是否给出模型对比和 token 成本。
- 搜索预算在本轮用完，没能继续查 Gemma 4 的图表成绩和 "Set-of-Mark" 类"候选标注"提示法的原始文献；如有需要，下一轮再补。

## 参考文献

1. Ravishankara, M. (2026). PlotChain: Deterministic Checkpointed Evaluation of Multimodal LLMs on Engineering Plot Reading. arXiv:2602.13232. https://arxiv.org/abs/2602.13232 [只读摘要]
2. Wang, Z., Xia, M., He, L., et al. (2024). CharXiv: Charting Gaps in Realistic Chart Understanding in Multimodal LLMs. arXiv:2406.18521. https://arxiv.org/abs/2406.18521 [只读摘要]
3. llm-stats.com. CharXiv-R Leaderboard（2026-11-13 查阅，第三方聚合）. https://llm-stats.com/benchmarks/charxiv-r [已读原文]
4. Mercor. CharXiv leaderboard（2026-11-13 查阅，第三方运行）. https://www.mercor.com/apex/oss-benchmarks/oss-charxiv-leaderboard/ [已读原文]
5. Qwen Team (2026). Qwen3.8-27B model card 及 preprocessor_config.json / config.json. https://huggingface.co/Qwen/Qwen3.8-27B [已读原文]
6. Qwen Team (2026). Qwen3.8-Flash-Next model card. https://huggingface.co/Qwen/Qwen3.8-Flash-Next [已读原文]
7. Masry, A., et al. (2025). ChartQAPro: A More Diverse and Challenging Benchmark for Chart Question Answering. Findings of ACL 2025; arXiv:2504.05506. https://aclanthology.org/2025.findings-acl.978/ [未打开原文]
8. Tang, L., et al. (2025). ChartMuseum: Testing Visual Reasoning Capabilities of Large Vision-Language Models. NeurIPS 2025; arXiv:2505.13444. https://arxiv.org/abs/2505.13444 [未打开原文]
9. Berkane, T., & Majumder, M. S. (2026). EpiCurveBench: Evaluating VLMs on Epidemic Curve Digitization. EMNLP 2026; arXiv:2605.27195. https://arxiv.org/html/2605.27195 [已读原文]
10. Garre, S., Mutty, C., Mehta, S., & Chen, E. (2026). Chartography: A Benchmark for Professional Chart Understanding. BEAM 2 workshop, ECCV 2026; arXiv:2608.10677. https://arxiv.org/abs/2608.10677 [只读摘要]
11. Kamoi, R., et al. (2024/2025). VisOnlyQA: Large Vision Language Models Still Struggle with Visual Perception of Geometric Information. arXiv:2412.00947. https://arxiv.org/abs/2412.00947 [未打开原文]
12. Rahmanzadehgervi, P., Bolton, L., Taesiri, M. R., & Nguyen, A. T. (2024). Vision language models are blind. ACCV 2024; arXiv:2407.06581. https://arxiv.org/abs/2407.06581 [未打开原文]
13. Daswani, M., Bellaiche, M. M. J., Wilson, M., et al. (2024). Plots Unlock Time-Series Understanding in Multimodal Models. arXiv:2410.02637. https://arxiv.org/html/2410.02637v2 [已读原文]
14. Liu, H., Liu, C., & Prakash, B. A. (2024). A Picture is Worth A Thousand Numbers: Enabling LLMs Reason about Time Series via Visualization. arXiv:2411.06018. https://arxiv.org/abs/2411.06018 [未打开原文]
15. Cai, Y., et al. (2024). TimeSeriesExam: A time series understanding exam. arXiv:2410.14752. https://arxiv.org/abs/2410.14752 [未打开原文]
16. Yu, F., Guo, X., Yuan, L., et al. (2026). TSRBench（时间序列推理基准，文本、图、图文三种输入对比）. arXiv:2601.18744. https://arxiv.org/html/2601.18744v1 [已读原文（前 10 万字符）]
17. Xu, X., Wang, H., Liang, Y., Yu, P. S., Zhao, Y., & Shu, K. (2025). Can Multimodal LLMs Perform Time Series Anomaly Detection? arXiv:2502.17812. https://arxiv.org/html/2502.17812v2 [已读原文]
18. He, Z., Alnegheimish, S., & Reimherr, M. (2025/2026). Harnessing Vision-Language Models for Time Series Anomaly Detection. AAAI 2026; arXiv:2506.06836. https://arxiv.org/html/2506.06836 [已读原文]
19. Zhou, X., Wahed, M., Yu, T., Brif, C., & Lourentzou, I. (2026). Tiny but Trusted: Efficient Vision-Language Reasoning for Time-Series Anomaly Detection. NeurIPS 2026; arXiv:2605.30344. https://arxiv.org/abs/2605.30344 [只读摘要]
20. Chen, M., et al. (2025). VisionTS: Visual Masked Autoencoders Are Free-Lunch Zero-Shot Time Series Forecasters. ICML 2025; arXiv:2408.17253. https://arxiv.org/abs/2408.17253 [未打开原文]
21. Schild, A., & de Melo, G. (2026). Can't Find Waldo: Evaluating VLMs' Sensitivity to Image Resolution and Detail Level. arXiv:2609.31706. https://arxiv.org/html/2609.31706 [已读原文]
22. DeepEyes: Incentivizing "Thinking with Images" via Reinforcement Learning (2025). ICLR 2026; arXiv:2505.14362. https://arxiv.org/abs/2505.14362 [未打开原文]
23. （作者未核实）关于"裁剪放大"类 VLM 增益的审视文章. Findings of EMNLP 2026. https://aclanthology.org/2026.findings-emnlp.728.pdf [未打开原文]
24. OpenAI. Images and vision guide（2026-11-13 查阅）. https://developers.openai.com/api/docs/guides/images-vision [已读原文]
25. Anthropic. Vision（2026-11-13 查阅）. https://platform.claude.com/docs/en/build-with-claude/vision [已读原文]
26. Google. Media resolution（2026-11-13 查阅）. https://aistudio.google.com/docs/media-resolution [已读原文]
27. Google. Gemma 4 model card. https://ai.google.dev/gemma/docs/core/model_card_4 ；https://huggingface.co/google/gemma-4-31B-it [已读原文]
28. Li, W., & Yuan, C. (2026). FA-Agent: An extensible multimodal agent framework for first-arrival picking in mountainous seismic data. arXiv:2611.06555（投稿 *Geophysics*）. https://arxiv.org/html/2611.06555v2 [已读原文]
29. Munikoti, S., Stewart, I., Chai, C., Linville, L., Vasquez, S., Horawalavithana, S., & Pazdernik, K. (2026). MULTISEISMO: A Multimodal Seismic Dataset and Model for Cross-Modal Seismic Understanding. arXiv:2605.26320. https://arxiv.org/html/2605.26320 [已读原文]
30. Wang, X., Liu, F., Su, R., Wang, Z., Fang, L., Zhou, L., Bai, L., & Ouyang, W. (2026). SeisMoLLM: Advancing Seismic Monitoring via Cross-Modal Transfer With Pretrained Large Language Model. *Geophysical Research Letters*, 53(8), e2025GL118505. https://doi.org/10.1029/2025GL118505 ；arXiv:2502.19960 [arXiv v2 已读原文；GRL 页面未打开]
31. Liu, T., et al. (2024). SeisLM: a Foundation Model for Seismic Waveforms. arXiv:2410.15765. https://arxiv.org/abs/2410.15765 [未打开原文]
32. Gemini & Physical World: Large Language Models Can Estimate the Intensity of Earthquake Shaking from Multi-Modal Social Media Posts (2024). arXiv:2405.18732. https://arxiv.org/abs/2405.18732 [未打开原文]
