# 15. 同类工作（新颖性核查）

## 要回答的问题

- 截至 2026 年 11 月，是否有人发表过（论文、预印本、workshop、AGU/SSA/SCEC 摘要、GitHub）在天然地震上拾取震相、复核 ML 拾取、读取初动极性、或用定位残差驱动重拾的 LLM 或 VLM agent？广泛检索（arXiv、类 Google Scholar 结果、ESSOAr、2025–2026 年 AGU/SSA 摘要、SCEC 年会、GitHub）。
- 逐条核实 design.md §1.1 的相关工作（FA-Agent arXiv 2611.06555；TRACE arXiv 2603.21152；SeisMoLLM；MULTISEISMO arXiv 2605.26320；Tepp et al. 2025 *Sci. Rep.*；Zhou et al. SCEC 2026；Münchmeyer 2022；"On the Fragility of Self-Improving Agents" arXiv 2608.18066）：是否存在，题目、作者、主张是否准确？
- 是否有地震台网在业务事件复核中使用 LLM 或 agent？
- 尝试找到 Advikar 的 workshop 版本（合作者的试点；可能是 NeurIPS 2026 测试时/持续学习 agent 的 workshop）。

影响的决定：新颖性主张与定位。

## 结论摘要

- **没有找到在天然地震上用 LLM/VLM agent 看图拾取、复核 ML 拾取、读极性或用定位残差驱动重拾的已发表工作**（arXiv API 关键词检索、OpenReview 全文检索、SSA 2026 程序册全文检索、SCEC 2026 摘要、EGU26 摘要、多轮网页检索）。最接近的是 FA-Agent（勘探初至波、看图、skills + 专家案例库）[1]，其次是 TRACE（调度 PhaseNet/GaMMA/HypoDD，本组工作）[2]。主卖点"天然地震 + 端到端分析员 + 残差反馈 + 跨事件学习"目前仍成立。
- **新出现、design.md 未列的近邻工作**（需要引用或区分）：SSA 2026 海报 "Chatting With the Earth"（Blanco、Mousavi、Liu；在 STEAD 上重训 OpenTSLM，问答式输出到时、震级、距离，非 agent、非看图）[3]；SSA 2026 Si et al. "A Systematic Comparison of Foundation Models for Earthquake Detection"（预训练大模型的拾取评测：比较作者的 LLM 拾取方法与其他地震基础模型，在 Ridgecrest 与 2023 土耳其序列上比较建成的目录；非 agent）[4]；Bassani et al. 2026 *JGR: MLC*（TinyLlama 从 P 到时与 PGV 估计震级和位置）[5]；GeoAgent [6]、TREMORS [7]、SeisEvo [8]、Seismology modeling agent [9]；以及 ICLR 2027 投稿 "SeisAgentBench: Benchmarking and Reinforcement Learning for Seismic Data-Processing Agents"（用户核实：勘探地震数据处理的 agent 基准 + 强化学习，不涉及天然地震拾取）[10]。
- **design.md §1.1 的 8 条全部存在**，题目和作者基本准确，但有 3 处需要改写：(a) FA-Agent 用的是 "GPT-6 Astra"，且只与自研常规拾取器做了定量比较 [1]；(b) Zhou et al. SCEC 2026 摘要讲的是 4 种 SCSN 优化拾取器（SAR、PhaseNet、Res-UNet、Frame-Transformer）的多窗口/多模型一致性筛选，**摘要中没有提到分析员**，"分析员仍在环中"应引用 Tepp et al. 2025 而不是它 [11][12]；(c) **Münchmeyer et al. 2022 把"缓起和低信噪比"用来解释远震数据集（GEOFON、NEIC，MAE 0.57/0.74 s）的大残差，不是区域数据**；对区域数据，它指出的是经典 Baer-Kradolfer 拾取器在低信噪比下离群值多、INSTANCE 的标注者多导致一致性差 [13]。
- **业务化使用**：没有找到任何台网在业务事件复核中使用 LLM 或 agent。已业务化的是 SCSN 的 PhaseNet 后处理与 PhaseNet + GaMMA 的 ST-Proc（Tepp et al. 2025）[12]；SCSN 正在搭建 AI 近实时编目框架（Zhou et al. SCEC 2026）[11]；LANL 有"人判有无、模型精修"的人本 AI 原型（SSA 2026）[14]。"台网尚无 LLM 参与复核"可以写，但措辞应是"据我们检索未见报道"。
- **Advikar 的 workshop 版本未找到**。NeurIPS 2026 "Towards Test-Time Continual Learning Agents"（TTCL）workshop 确实存在（2026-12-13，亚特兰大，非存档，4–9 页，投稿截止 2026-09-05）[15]；其 NeurIPS 页面列出的 85 篇录用论文中没有任何标题涉及地震，页面全文也没有 "Advikar" [16]。OpenReview 上能查到一位 Advikar Ananthkumar（ICML 2026 论文合作者，与 Tomaso Poggio 等合著），是否为同一人未确认 [17]。
- **与 TRACE 的作者关系**：TRACE 作者包括 Feng Liu、Xin Cui、S. Mostafa Mousavi、Zefeng Li、Lei Bai 等 [2]；SeisMoLLM 作者也包括 Feng Liu、Lei Bai [18]。design.md 称 TRACE 为"我们自己的工作"，与作者列表一致；论文中自引时应明确说明。

## 详细发现

### 1. 检索范围与方法

| 渠道 | 做法 | 结果 |
|---|---|---|
| arXiv API | `abs:agent AND abs:seismic AND (picking OR earthquake)`；`"language model" AND "phase picking"`；`(LLM OR "language model" OR agentic) AND (earthquake OR seismology OR seismic) AND cat:physics.geo-ph`；`(agentic OR "LLM agent" OR "AI agent") AND (seismology OR earthquake)` | 相关命中：FA-Agent、TRACE、GeoAgent、TREMORS、SeisEvo、Seismology modeling agent、SeisMoLLM、SeisLM、QuakeGPT、Gemini & Physical World；没有天然地震看图拾取 agent |
| OpenReview 全文检索 | "Advikar"、"seismic agent"、"phase picking"、"seismologist"、"earthquake"、"seismogram"、"seismology agent"、"seismic analyst"、"earthquake agent"、"Ananthkumar" | 发现 ICLR 2027 投稿 SeisAgentBench（RL + 地震数据处理 agent）、ICML 2026 AI4Science 海报 SeisAgentBench（破裂反演）、ICLR 2027 投稿 SeisTailFlow（拾取，非 LLM）；无 Advikar 地震论文 |
| SSA 2026 程序册（167 页 PDF 全文） | grep "language model / LLM / agentic / agent / GPT" | 3 条 LLM 相关：Chatting With the Earth [3]、Si et al. LLM 拾取比较 [4]、Digital Archivist（宏观地震资料抽取）[19]；"Pycorelator" 是软件名，非 LLM agent |
| SCEC 2026 | Zhou et al. 海报 #149 全文摘要 | 无 LLM |
| EGU26 | 拾取相关摘要（EGU26-6122） | 无 LLM |
| AGU 2025 Fall Meeting | 搜索引擎未索引到相关摘要；本轮未能直接检索 AGU 摘要库 | **未覆盖，见"未解决"** |
| ESSOAr | 未找到相关预印本（仅经搜索引擎） | 覆盖不完整 |
| GitHub | 经搜索引擎；发现 liufeng2317/SeismoAgent-bench（本组仓库） | 未发现天然地震 LLM 拾取仓库 |

### 2. 与本项目最接近的工作（按相近程度排序）

| 工作 | 数据 | 是否 agent | 是否看图 | 拾取/极性/定位 | 学习/反馈 | 与本项目的关系 |
|---|---|---|---|---|---|---|
| **FA-Agent**（Li & Yuan，arXiv 2611.06555，2026-11-04/05）[1] | 山地勘探炮集；半合成 + 野外 | 是（GPT-6 Astra + 工具 + skills） | 是（整道集浏览 + 放大） | 只有初至波；无 S、无极性、无定位 | 专家复核案例自动加入 skills；**无学习曲线** | 最近的方法学先例，必须引用并区分：天然地震、多震相、极性、定位残差、无标签反馈、有对照的学习曲线 |
| **TRACE**（Liu et al.，arXiv 2603.21152 v4）[2] | Ridgecrest 2019、三陆 2025–26 连续波形 | 是（7 类角色多 agent） | 有 Result Checking，未见看波形图拾取 | 调用 PhaseNet（阈值 0.4）+ GaMMA + HypoDD | 案例库检索，无跨事件学习 | 本组工作；"调度工具"与"自己当分析员"的区别成立 |
| **Chatting With the Earth**（Blanco, Mousavi, Liu；SSA 2026 海报 62）[3] | STEAD | 否（对话式时间序列 LM） | 否（MLP 把波形 token 化） | 输出起始时刻、震级、距离、深度、波形分类，带思维链 | 无 | 说明"用 LLM 读波形"已有人做，但走的是"训练专用模型"路线；本项目是"通用 VLM + 工具 + 记忆" |
| **Si et al.**（Georgia Tech/USTC 等；SSA 2026）[4] | Ridgecrest 2019、2023 土耳其 | 否 | 否 | **预训练大模型的评测**：比较作者基于大语言模型的拾取方法（预训练模型经微调）与其他地震基础模型，评价落到拾取 → 关联 → 定位后的目录 | 无 | 是“预训练基础模型能否改进拾取”的评测，不是 agent。可作为“训练式 LLM 拾取器”一类的背景引用；其“比较建成的目录而不只比拾取精度”的评估思路可借鉴 |
| **SeisMoLLM**（Wang et al., *GRL* 2026）[18] | DiTing、STEAD | 否（GPT-2 骨干微调） | 否 | 拾取、极性、震中距、方位角、震级 | 无 | 已列 |
| **Bassani et al. 2026**（*JGR: MLC*）[5] | 意大利（INGV） | 否（TinyLlama 微调） | 否 | 从 P 到时 + PGV 估计震级、位置、发震时刻 | 无 | 新增；"LLM 直接定位"的先例 |
| **MULTISEISMO**（Munikoti et al., arXiv 2605.26320）[20] | 16,000+ 事件多模态数据集 | 否 | 有图（烈度图等）+ 波形编码器 | 问答式任务 | 无 | 已列 |
| GeoAgent [6] / SeisEvo [8] / Seismology modeling agent [9] | 勘探处理 / 勘探插值 / SPECFEM 正演 | 是 | 否 | 否 | SeisEvo 有进化搜索 | 地学 agent 背景 |
| TREMORS（LANL，arXiv 2609.01777）[7] | FDSN 数据下载 | 是（受约束执行图） | 否 | 否 | 无 | 台网相关机构开始做 agent，但只用于取数 |
| SeisAgentBench: A Failure-Aware Core Benchmark…（Shinohara，ICML 2026 AI4Science 海报）[21] | 破裂反演 + 正演验证 | 多 agent 基准 | — | 否 | — | 名字相近，内容不同。用户已读全文（2026-11-13，`reference/3_SeisAgentBench_A_Failure_Awa.pdf`）：检验 agent 能否组织完整的反演计算流程，并在结果冲突或计算失败时做出合理判断；稿件是 benchmark 设计方案与路线图，**没有报告数据集规模、基线成绩或定量结果** |
| SeisAgentBench: Benchmarking and RL for Seismic Data-Processing Agents（ICLR 2027 投稿，匿名）[10] | **勘探地震数据处理**：95 个任务、19 类处理（增益、去噪、F–K 滤波、面波压制、反褶积、Radon 去多次、速度分析、动校、叠加、偏移等） | 是（SeisAgent：轨迹级监督学习 + 组相对强化学习后训练） | 看中间产物的 QC 指标 | **否**：唯一带 pick 的是速度谱拾取和初至切除，没有天然地震震相拾取、极性或定位 | 强化学习更新权重 | 用户已读全文（2026-11-13，`reference/18300_SeisAgentBench_Benchmark.pdf`）。与上一行 Shinohara 的 ICML 海报是两篇不同的稿件。**不是直接竞争者**；可作为方法上的邻近工作引用：agent 根据中间产物的科学质量诊断修改参数、比较候选再决定停止，与本项目“按残差重拾、重定位”的内循环相似，区别是勘探数据、靠强化学习更新权重 |
| EarthVerse（arXiv 2608.23525）[22] | 19 类灾害、405 个任务 | agent 基准 | — | 摘要未提拾取 | — | 背景 |
| RANSAC 定位（Zhu et al., arXiv 2502.10933）[23] | Ridgecrest | 否 | 否 | 用残差剔除离群拾取，不重拾 | 无 | "残差驱动"的非 LLM 近邻；可作为确定性对照组 |

**新颖性判断（推断）**：
1. "多模态 LLM agent 在天然地震上端到端做分析员工作（P/S 拾取、极性、定位、残差驱动重拾）"——未见先例，可作主卖点。
2. "只用物理残差、不用人工标签的跨事件记忆学习"——未见先例（地震领域内）。FA-Agent 的学习来源是专家复核 [1]。
3. "看图拾取 + 技能/案例记忆"——FA-Agent 已提出（勘探），不能单独作为新点。
4. "LLM 用于拾取"——已有（SeisMoLLM、Si et al.、Chatting With the Earth），但都是训练/微调专用模型，不是通用 VLM agent。论文里应明确划出这条线：**训练式 LLM 拾取器 vs 不训练的 agent 分析员**。
5. "在 Ridgecrest 上比较 LLM 拾取建成的目录"——Si et al. 做过（预训练基础模型的评测，不是 agent）[4]；T1 写法上注明区别即可。

### 3. 逐条核实 design.md §1.1

| design.md 条目 | 核实结果 | 需要改的地方 |
|---|---|---|
| **FA-Agent**（Li & Yuan，arXiv 2611.06555，2026-11，投稿 *Geophysics*）"GPT-6 多模态 agent 目视拾取勘探初至波；先扫描道集，再放大问题区，保留、修正或删除初始拾取；配技能库和专家复核案例库"；区别"没有度量学习曲线，也没有和深度学习基线对比" [1] | **准确**。作者 Wenda Li、Congcong Yuan；v1 2026-11-04，v2 2026-11-05；45 页、9 图、3 个补充视频；投 *GEOPHYSICS* 审稿中。模型为 "GPT-6 Astra"。定量比较只针对自研常规拾取器（能量比 + AIC + 横向连续性）：半合成测试 1 中常规拾取约 2% 在 ±20 ms 内，agent 全部或几乎全部在内、约 60% 在 ±8 ms 内；测试 2 中保留的 324 个拾取全部在 ±20 ms 内。野外数据只报决策计数。无学习曲线。每道集 30–90 s | 写成 "GPT-6 Astra"；补一句"仅与常规能量/AIC 拾取器比较，无 DL 基线、无学习曲线" |
| **TRACE**（arXiv 2603.21152，我们自己的工作）"多 agent 调度深度学习拾取器、关联和 HypoDD，构建 Ridgecrest 目录" [2] | **准确**。题目 "TRACE: A Multi-Agent System for Autonomous Physical Reasoning for Seismology"；14 位作者（Feng Liu 第一作者，Lei Bai 末位）；v1 2026-03-22，v4 2026-09-30；还包含三陆序列案例和 104 个基准任务 | 可补"也用于三陆序列"；自引说明 |
| **SeisMoLLM**（GRL 2026）"用 LLM 骨干直接处理波形" [18] | **准确**。*GRL* 53, e2025GL118505，2026-04-14；作者 Xinghao Wang, Feng Liu, Rui Su, Zhihui Wang, Lihua Fang, Lianqing Zhou, Lei Bai, Wanli Ouyang；GPT-2 骨干微调，5 类任务 | 参考文献应改用 GRL DOI 10.1029/2025GL118505（design.md 目前给的是 arXiv HTML） |
| **MULTISEISMO**（arXiv 2605.26320）"构建多模态指令数据集；报告通用多模态模型处理地震时间序列效果差" [20] | **准确**。作者 Sai Munikoti, Ian Stewart, Chengping Chai, Lisa Linville, Scott Vasquez, Sameera Horawalavithana, Karl Pazdernik；2026-05-25；数据集 16,000+ 事件（2010–2023）；指令集 MISCE；模型 SeisModal（Unified-IO 2 + 时间序列编码器）；摘要称通用模型处理时间序列"有显著困难" | "这正好支持需要工具和绘图"是我们的推断：MULTISEISMO 说的是通用模型处理时间序列数据难，并没有测试"画成图 + 工具"的方案。写作时标为推断 |
| **Tepp et al. 2025, *Sci. Rep.*** "PhaseNet + GaMMA 进入后处理……分析员仍在环中" [12] | **准确**。题目 "Improvements from incorporating machine learning algorithms into near real-time operational post-processing"；*Sci. Rep.* 15, 28938，2025-08-07；作者 Tepp, Yu, Bhaskaran, Tam, Zhu, Newman, Jaski, Scheckel。M<3 事件后处理用 PhaseNet，拾取多 2–3 倍（S 尤其多），精度略好于 STA/LTA；ST-Proc（PhaseNet + GaMMA）正确检出 65–70% 含事件的触发，误报约 5%；摘要明确是"在分析员复核之前"改进事件，并"减轻分析员负担" | 无需改；"分析员仍在环中"的出处应是这篇 |
| **Zhou et al. SCEC 2026** "四种拾取器共识编目，分析员仍在环中" [11] | **存在，部分准确**。题目 "Toward an AI-Enhanced Near-Real-Time Earthquake Cataloging System for the Southern California Seismic Network"，SCEC 2026 年会海报 #149（SCEC Contribution #15369）；作者 Yijian Zhou, Ryan Tam, Gabrielle Tepp, Rayomand Bhadha, Ellen Yu, Zachary E. Ross, Zhongwen Zhan, Allen L. Husker。离线：用 PAL 规则流程生成正负样本，训练 SAR、PhaseNet、Res-UNet、Frame-Transformer 四种拾取器，并生成 2020–2025 增强目录；在线：10 分钟窗口、5 分钟步长，每个拾取器 2.5 s 滑动，重复检出或多拾取器检出的候选保留，分子台网关联后去重，结果送入现有 SCSN 定位和震级模块。**摘要没有提分析员** | 改为"四种 SCSN 优化拾取器多窗口/多模型一致性筛选，输出接入现有业务定位模块"；"分析员仍在环中"改引 Tepp 2025。注意 SCEC 现名 Statewide California Earthquake Center |
| **Münchmeyer et al. 2022 *JGR*** "大残差主要来自低信噪比和缓起震相" [13] | **存在，主张需改写**。"Which Picker Fits My Data? A Quantitative Evaluation of Deep Learning Based Seismic Pickers"，*JGR Solid Earth* 127, e2021JB023499。原文：区域数据集平均 MAE（跨模型）STEAD 0.08 s、ETHZ 0.12 s、SCEDC 0.14 s、Iquique 0.21 s、INSTANCE 0.26 s（后者归因于约 15–20 名标注者一致性较低）；GEOFON 0.57 s、NEIC 0.74 s 的高残差"可由远震记录解释"——远震起始常为缓起、频率较低、信噪比更差。另指出 Baer-Kradolfer 在信噪比好时与 DL 相当，信噪比差时离群值明显更多；S 残差比 P 大约 25%–60% | 改写为："Münchmeyer et al. (2022) 发现残差分布为尖峰重尾，远震数据中缓起、低频、低信噪比的到时残差显著更大；区域数据中标注者一致性也影响残差。" 若要支撑"缓起难"，应另找区域尺度的证据（见 04、02 号文件） |
| **On the Fragility of Self-Improving Agents**（arXiv 2608.18066）"方差大、受任务顺序影响" [24] | **准确**。完整题目 "On the Fragility of Self-Improving Agents: Variance, Task Order, and Underspecification"；作者 Qinyuan Ye, Yu Li, Yada Pruksachatkun, Jiaxin Zhang, Chien-Sheng Wu（Salesforce AI Research，代码在 SalesforceAIResearch/self-improve-fragility）；v1 2026-08-18，v2 2026-09-06。还指出任务欠明确是原因之一，加入细化评分标准和环境反馈能部分缓解 | 可补"欠明确"这一点，它与本项目"用物理残差给出明确反馈"的设计相呼应 |

### 4. 地震台网业务中的 LLM/agent

- **没有找到任何台网在业务复核中使用 LLM 或 agent 的报道**（检索 USGS NEIC、GeoNet、INGV、SeisComP、SCSN 相关关键词；SSA 2026 程序册全文；SCEC 2026）。
- 已业务化的 ML：SCSN PhaseNet 后处理与 ST-Proc [12]。
- 正在建设：SCSN AI 近实时编目框架 [11]。
- 原型：LANL Park 的"人本 AI 拾取"——分析员确认到时存在并给粗略时刻，模型输出起始时刻概率分布，取最大概率样本；作者邀请台网运营方反馈以接入业务系统 [14]。
- 台网相关机构做的 LLM 系统目前只用于数据获取（LANL TREMORS）[7]、历史宏观资料抽取（Digital Archivist，Gemini 2.5 Pro，SRL 2026）[19]。
- 其他 SSA 2026 相关信号：Alaska Earthquake Center 报告全局预训练 ML 模型在其指标上不如分析员，正在做本地训练（Noel & West 相关海报）[25]；"Pick Aggregator" 多模型集成 [25]。这些可以作为"DL 拾取器仍需分析员把关"的动机引用。

### 5. Advikar 的 workshop 版本

- NeurIPS 2026 TTCL workshop 存在：全名 "Towards Test-Time Continual Learning Agents"，2026-12-13，亚特兰大，线下；组织者 Zheyuan Zhang、Chuanyang Jin、Jacob Sansom、Zekun Wang、Jianwen Xie、Joyce Chai、Daniel Khashabi、Tianmin Shu；一般研究轨 4–9 页；**非存档**；截止日期页面同时出现 2026-08-29 和 09-05 [15]。
- NeurIPS 虚拟会议页面列出 85 篇录用论文；标题中没有地震、拾取、地球物理相关词；下载页面全文检索 "Advikar"、"seism"、"earthquake"、"geophys" 均无结果 [16]。
- 同期还有 "Continual Learning for Enterprise AI Agents"（亚特兰大）等相关 workshop，未逐一检查其论文列表。
- OpenReview 上 "Advikar" 只命中 Advikar Ananthkumar 参与的 "Momentum Further Constrains Sharpness at the Edge of Stochastic Stability"（ICML 2026，与 Arseniy Andreyev、Marc Walden、Tomaso Poggio 等合著）[17]。是否为同一位合作者：未确认（推断：名字少见，可能是同一人）。
- 结论：**未找到**。可能情况（推断）：(a) 投稿未录用或撤回；(b) 投在其他 workshop 且论文不在公开列表；(c) 标题不含地震字样。design.md 中"需要直接问本人或老师"的处理是对的。

## 对本项目的影响

**新颖性主张的写法：**

1. 主张一（端到端分析员 agent）可以保留为"首个"，但限定为："据我们所知，首个在天然地震上以通用多模态 LLM agent 完成拾取、极性判读和残差驱动重拾的工作"。必须同时引用 FA-Agent（勘探初至波的看图 agent）和 TRACE（调度型）。
2. 增加一句与"训练式 LLM 拾取器"的区分：SeisMoLLM [18]、Si et al. [4]、Chatting With the Earth [3]、Bassani et al. [5] 都是对 LLM 做微调或重训；本项目不更新权重。这条线也是 H3（无权重更新的物理反馈学习）的自然背景。
3. "台网目前没有 LLM 参与复核"改为"未见报道"，引用 Tepp 2025 [12] 和 Zhou 2026 [11] 说明业务化 ML 的现状，引用 Park 2026 [14] 说明人机分工正在被讨论。
4. 删除或改写 Münchmeyer 2022 的"缓起难"表述（见 §3 表）。

**design.md §1.1 表格的具体修改：**
- FA-Agent：GPT-6 → GPT-6 Astra；补"仅与常规拾取器定量比较"。
- Zhou et al. SCEC 2026：改内容描述，去掉"分析员仍在环中"。
- SeisMoLLM：参考链接换成 GRL DOI。
- 新增三行：Si et al. SSA 2026、Chatting With the Earth SSA 2026、Bassani et al. 2026 JGR-MLC；可选新增 GeoAgent/TREMORS（"地学 agent 多为受约束执行图"，与 09 号文件的编排结论呼应）。

**风险与行动：**
- ~~确认 ICLR 2027 投稿 SeisAgentBench 的内容~~：已由用户核实（2026-11-13），是勘探地震数据处理的 agent 基准和强化学习，不涉及天然地震拾取，不构成直接竞争。
- Si et al. 是预训练大模型的拾取评测（用户核实，2026-11-13），不是 agent；在讨论中把它归入“训练式 LLM 拾取器”，与“不更新权重的 agent 分析员”区分即可。
- FA-Agent 发布于 2026-11-04，距今仅一周；勘探方向可能很快出现跟进工作。建议尽早挂预印本占位（注意 16 号文件中 SRL 对预印本许可证的要求）。

## 未解决与待核

- **AGU 2025 Fall Meeting 摘要库和 ESSOAr 未直接检索**（只经搜索引擎间接覆盖，未见相关结果）。AGU 2026 Fall Meeting（2026 年 12 月）的摘要也可能已有相关工作——建议在 AGU 会议摘要库中用 "LLM"、"agent"、"phase picking"、"vision language" 检索一次。本轮 WebSearch 配额已用完，未能完成。 **用户决定不再补查（2026-11-13）。**
- ICLR 2027 SeisAgentBench 投稿正文：OpenReview 命令行无法读取；用户已从浏览器下载并核实（见上表）。
- Advikar 的 workshop 论文：联系不上本人，用户决定放弃（2026-11-13）。
- TRACE 的剩余约 2 万字符（附录末尾）未读。
- Si et al. 的 LLM 拾取方法细节（用哪种 LLM、是否开源）只有 SSA 摘要；可留意是否已有预印本。摘要没有单独网页，只在 SSA 2026 程序册里（*SRL* 97(2B)，2026-04）：程序册 PDF 第 32 页是分会场列表中的标题，第 72 页是摘要全文。作者 Si X.、Peng Z.（Georgia Tech）、Wu X.、Li J.、Cui X.、Li Z.（USTC 等）；其中 Cui X. 和 Li Z. 也是 TRACE 的作者，可以直接联系。
- Chatting With the Earth 的摘要在同一份程序册 PDF 第 73 页，海报列表在第 34 页（海报 62）；作者 Blanco、Mousavi（Harvard）、Liu（MIT），Mousavi 也是 TRACE 的作者。
- 未检查 NeurIPS 2026 其他 workshop（如 "AI for Science: Verification in the Age of AI Scientists"、"Workshop for Autonomous ML Research"、"Continual Learning for Enterprise AI Agents"）的录用列表中是否有地震相关论文。
- 未检查 2025–2026 年 *Seismica*、*SRL*、*BSSA*、*GJI* 中是否有 "VLM + 地震图" 的短文；Crossref 上 SRL "large language model" 检索只命中 Digital Archivist 和 2023 年 ChatGPT 诱发地震问答文章 [19][26]。

## 参考文献

1. Li, W., & Yuan, C. (2026). FA-Agent: An extensible multimodal agent framework for first-arrival picking in mountainous seismic data. arXiv:2611.06555（v2 2026-11-05；投 *Geophysics*）. https://arxiv.org/abs/2611.06555 [已读原文]
2. Liu, F., Cui, X., Xu, J., Wang, X., Guo, Z., Wang, J., Mousavi, S. M., Gu, X., Chen, H., Fei, B., Fang, L., Ling, F., Li, Z., & Bai, L. (2026). TRACE: A Multi-Agent System for Autonomous Physical Reasoning for Seismology. arXiv:2603.21152 (v4). https://arxiv.org/abs/2603.21152 [已读原文，约前 90%]
3. Blanco, S., Mousavi, S. M., & Liu, J. (2026). Chatting With the Earth: LLMs for Seismic Data Processing. SSA 2026 Annual Meeting, poster 62. https://seismosoc.secure-platform.com/a/gallery/rounds/47/details/14162 [已读原文（摘要）]
4. Si, X., Peng, Z., Wu, X., Li, J., Cui, X., Li, Z., et al. (2026). A Systematic Comparison of Foundation Models for Earthquake Detection. SSA 2026 Annual Meeting（摘要见程序册）. https://meetings.seismosoc.org/wp-content/uploads/2026/02/SSA-Program-2026.pdf [已读原文（摘要）]
5. Bassani, A., Trappolini, D., Poggiali, G., Tinti, E., Galasso, F., Michelini, A., & Marone, C. (2026). Adapting a Pretrained LLM to Rapidly Recover Earthquake Magnitude and Location. *JGR: Machine Learning and Computation* 3, e2026JH001578. https://doi.org/10.1029/2026JH001578 [只读摘要]
6. Fang, Z., Zhang, Q., Yan, J., Wang, Z., Gu, X., Zhang, Z., & Wang, H. (2026). GeoAgent: Contract-Constrained LLM Agents for Seismic Data Processing. arXiv:2610.31096. https://arxiv.org/abs/2610.31096 [只读摘要]
7. Hill, R. G., Alfaro-Diaz, R., MacCarthy, J., Kintner, J. A., & Johnson, C. W. (2026). TREMORS: An Agentic Assistant for Multi-Datacenter Seismic Data Acquisition. arXiv:2609.01777. https://arxiv.org/abs/2609.01777 [只读摘要]
8. Xu, Y., Yu, S., & Ma, J. (2026). SeisEvo: Evolution of Seismic Data Reconstruction Algorithms by Agents. arXiv:2608.18272. https://arxiv.org/abs/2608.18272 [只读摘要]
9. Ren, Y., Yu, S., Chen, K., & Ma, J. (2025). Seismology modeling agent: A smart assistant for geophysical researchers. arXiv:2512.14429. https://arxiv.org/abs/2512.14429 [未打开原文，经搜索摘要]
10. 匿名 (2026). SeisAgentBench: Benchmarking and Reinforcement Learning for Seismic Data-Processing Agents. ICLR 2027 投稿. https://openreview.net/forum?id=KskpeXIMbk [用户已读原文，`reference/18300_SeisAgentBench_Benchmark.pdf`]
11. Zhou, Y., Tam, R., Tepp, G., Bhadha, R., Yu, E., Ross, Z. E., Zhan, Z., & Husker, A. L. (2026). Toward an AI-Enhanced Near-Real-Time Earthquake Cataloging System for the Southern California Seismic Network. 2026 SCEC Annual Meeting, poster #149, SCEC Contribution #15369. https://central.scec.org/publication/15369 [已读原文（摘要）]
12. Tepp, G., Yu, E., Bhaskaran, A., Tam, R., Zhu, W., Newman, Z., Jaski, E., & Scheckel, N. (2025). Improvements from incorporating machine learning algorithms into near real-time operational post-processing. *Scientific Reports* 15, 28938. https://doi.org/10.1038/s41598-025-14491-1 [只读摘要（Caltech 库元数据）]
13. Münchmeyer, J., Woollam, J., Rietbrock, A., Tilmann, F., Lange, D., Bornstein, T., Diehl, T., Giunchi, C., Haslinger, F., Jozinović, D., Michelini, A., Saul, J., & Soto, H. (2022). Which Picker Fits My Data? A Quantitative Evaluation of Deep Learning Based Seismic Pickers. *JGR: Solid Earth* 127, e2021JB023499. https://doi.org/10.1029/2021JB023499 ；预印本 arXiv:2110.13671 [已读原文（预印本 §3.3）]
14. Park, Y. (2026). Human-centered AI for Seismic Phase Picking in Operational Monitoring. SSA 2026 Annual Meeting, poster 27. 程序册 https://meetings.seismosoc.org/wp-content/uploads/2026/02/SSA-Program-2026.pdf [已读原文（摘要）]
15. NeurIPS 2026 TTCL Workshop: Towards Test-Time Continual Learning Agents（官方网站）. https://ttcl-agents.github.io/ [已读原文]
16. NeurIPS 2026 虚拟会议页面：Workshop on Towards Test-Time Continual Learning Agents（录用论文列表）. https://neurips.cc/virtual/2026/loc/atlanta/workshop/137567 [已读原文]
17. Andreyev, A., Ananthkumar, A., Walden, M., Poggio, T., et al. (2026). Momentum Further Constrains Sharpness at the Edge of Stochastic Stability. ICML 2026（OpenReview 记录 mL4i6z7Miy）. [只读摘要（仅元数据）]
18. Wang, X., Liu, F., Su, R., Wang, Z., Fang, L., Zhou, L., Bai, L., & Ouyang, W. (2026). SeisMoLLM: Advancing Seismic Monitoring via Cross-Modal Transfer With Pretrained Large Language Model. *Geophysical Research Letters* 53, e2025GL118505. https://doi.org/10.1029/2025GL118505 ；arXiv:2502.19960 [只读摘要]
19. Agrawal, A., Hough, S. E., Mousavi, S. M., Hellweg, M., Ellsworth, W. L., & Yoon, C. E. (2026). The Digital Archivist: Automating Legacy Macroseismic Data Processing Using Large Language Models. *Seismological Research Letters*. https://doi.org/10.1785/0220250362 [只读摘要]
20. Munikoti, S., Stewart, I., Chai, C., Linville, L., Vasquez, S., Horawalavithana, S., & Pazdernik, K. (2026). MULTISEISMO: A Multimodal Seismic Dataset and Model for Cross-Modal Seismic Understanding. arXiv:2605.26320. https://arxiv.org/abs/2605.26320 [只读摘要]
21. Shinohara, T. (2026). SeisAgentBench: A Failure-Aware Core Benchmark for Multi-Agent Earthquake Rupture Inversion and Forward Validation. ICML 2026 AI4Science workshop poster. https://icml.cc/virtual/2026/73526 [用户已读原文，`reference/3_SeisAgentBench_A_Failure_Awa.pdf`]
22. Cui, Z., Yin, X., Tang, Y., et al. (2026). EarthVerse: Benchmarking Scientific Agents Across Dynamic Earth Systems and Natural Hazards. arXiv:2608.23525. https://arxiv.org/abs/2608.23525 [只读摘要]
23. Zhu, W., Rong, B., Jie, Y., & Wei, S. S. (2025). Robust Earthquake Location using Random Sample Consensus (RANSAC). arXiv:2502.10933. https://arxiv.org/abs/2502.10933 [只读摘要]
24. Ye, Q., Li, Y., Pruksachatkun, Y., Zhang, J., & Wu, C.-S. (2026). On the Fragility of Self-Improving Agents: Variance, Task Order, and Underspecification. arXiv:2608.18066 (v2). https://arxiv.org/abs/2608.18066 [只读摘要]
25. SSA 2026 Annual Meeting Program（Alaska 本地训练海报、Pick Aggregator 等摘要）. https://meetings.seismosoc.org/wp-content/uploads/2026/02/SSA-Program-2026.pdf [已读原文（相关摘要片段）]
26. Wilson, M. P., Foulger, G. R., Wilkinson, M. W., Gluyas, J. G., Mhana, N., & Tezel, T. (2023). Artificial Intelligence and Human-Induced Seismicity: Initial Observations of ChatGPT. *Seismological Research Letters*. https://doi.org/10.1785/0220230112 [只读摘要]
