# 16. 投稿去向

## 要回答的问题

- 这类工作在 GRL、SRL、Seismica、JGR: Machine Learning and Computation，以及 ML 会议（NeurIPS/ICLR/ICML 中关于 agent、持续/测试时学习、AI for science 的 workshop；若存在则核实 NeurIPS 2026 TTCL workshop）上的要求、范围、篇幅限制和先例论文。
- 2026–2027 年各轮已公布的截止日期。

## 结论摘要

- **GRL**：正文上限 12 个 publication unit（1 PU = 500 词或 1 个图/表），摘要 <150 词，最多 3 条 key points（每条 ≤140 字符），必须有 ≤200 词的 Plain Language Summary [1][2]（AGU 页面被拦截，数字来自 AGU 页面的检索摘要，[只读摘要]）。**先例**：SeisMoLLM（GRL 2026，LLM 骨干做地震监测）[3]；"Large Language Models as Calibration Agents in Hydrological Modeling: Feasibility and Limitations"（GRL 2026，LLM 当水文模型率定 agent）[4]。design.md 的 4 幅图 + 约 4,000 词正好落在 12 PU 内。
- **SRL**：普通文章建议 6,000 词、10 幅图、3 个表，摘要 300 词；"Electronic Seismologist" 栏目明确收录开源软件、AI/ML 与数据管理工具；Data and Resources 节为必需 [5]。**特别注意：SRL 只接受"作者保留版权且未以 Creative Commons 许可发布"的预印本** [5]——若先在 arXiv 以 CC-BY 发布，可能失去投 SRL 的资格。SSA 的 AI 指南不鼓励 AI 生成的文字和图，除非属于研究设计本身，需要披露 [6]。先例：Digital Archivist（Gemini 2.5 Pro 工作流，SRL 2026）[7]。
- **The Seismic Record（SSA 短文刊）**：≤3,500 词、≤5 个图表、≤30 篇参考文献、摘要 ≤200 词；金色开放获取，2026 年投稿 APC $2,100 [8]。可作为 GRL 的同类替代。
- **Seismica**：钻石开放获取（作者零费用）；研究论文通常 3,000–10,000 词、≤10 个图表；Fast Reports 约 3,000 词、2–3 个图表，接受"概念验证研究"，目标约 30 天出版；另有 Software Reports、null-result reports；必须有数据与代码可用性声明（"联系作者获取"不被接受）；可选双盲；鼓励预印本 [9][10]。先例：PyOcto（2024）[11]、区域震相 DL 拾取（Aguilar Suarez & Beroza 2025）[12]、关联器基准（2025）[13]。
- **JGR: Machine Learning and Computation**：AGU 2024 年创刊的 ML/计算方向期刊（ISSN 2993-5210）。**先例**：Bassani et al. 2026，微调 TinyLlama 从 P 到时估计震级和位置 [14]。篇幅上限和 APC 本轮未能从官方页面核实（Wiley/AGU 页面拒绝访问）[待核]。
- **NeurIPS 2026 TTCL workshop 确实存在**：Towards Test-Time Continual Learning Agents，2026-12-13 亚特兰大，4–9 页，**非存档**，投稿已于 2026-09-05 截止；录用 85 篇，无地震相关 [15][16]。NeurIPS 2026 所有 workshop 的建议截止日为 2026-08-29，均已过 [17]。
- **下一轮可投的 ML 窗口**：ICLR 2027 主会截止已过（2026-09-25），workshop 在 2027-04-29/30 [18]，workshop 投稿一般在 1–2 月（推断，各 workshop 尚未公布）；ICML 2027 主会摘要 2027-01-14、全文 2027-01-22，workshop 2027-08-05/06 [19]。ICML 2026 AI4Science workshop 已收录过地震 agent 海报（SeisAgentBench，破裂反演）[20]，说明 AI4Science 类 workshop 接受地震 agent 工作。
- **地学会议摘要**：EGU 2027（2027-04-04 至 09，维也纳）摘要截止 **2027-01-12 13:00 CET** [21]；SSA 2027（2027-04-20 至 24，西雅图）摘要截止日期本页未列出 [22]（往年为 1 月，[待核]）。

## 详细发现

### 1. 地学期刊

| 期刊 | 范围（与本项目相关的部分） | 篇幅 | 费用/许可 | 数据/代码 | 预印本 | 先例 |
|---|---|---|---|---|---|---|
| **GRL**（AGU） | 高影响、短篇、时效强的研究快报 | 12 PU（500 词或 1 个图/表 = 1 PU；标题、作者、key points、表内文字、参考文献不计）；摘要 <150 词；3 条 key points ≤140 字符、无缩写；PLS ≤200 词、单段 [1][2] | [待核]（AGU 页面未能打开） | AGU 要求数据可用性声明 [待核细节] | AGU 接受预印本 [待核] | SeisMoLLM（2026）[3]；LLM 率定 agent（2026）[4] |
| **JGR: Machine Learning and Computation**（AGU） | 地球与空间科学中的 ML 与计算方法 | [待核]（推测与 JGR 系列相同的 PU 制） | [待核]（推测为金色 OA） | [待核] | [待核] | Bassani et al. 2026（LLM 定位/震级）[14]；GeoFWI 基准（2026） |
| **SRL**（SSA） | 简洁、聚焦的研究，可围绕某个方法、数据集或事件；Electronic Seismologist 栏目收"开源软件、AI/ML、数据管理工具" [5] | 建议上限：普通文章与 Electronic Seismologist 6,000 词、10 图、3 表；摘要 300 词（可由主编酌情放宽）[5] | 两种许可：Page Charges（版权归 SSA，正式版仅会员/订户可见）或 Open Access（CC-BY，作者保留版权）；印刷彩图每幅 $250 [5] | Data and Resources 节必需，所有 URL 放此节 [5] | **仅接受作者保留版权且未以 CC 许可发布的预印本**（如 ESSOAr 等非营利预印本服务器）[5] | Digital Archivist（2026）[7]；ChatGPT 与诱发地震（2023）[23]；PickerXL（2025） |
| **The Seismic Record**（SSA） | 覆盖地震学全领域的短文 | ≤3,500 词（含摘要、数据与资源等，不含参考文献和图题）、≤5 图表、≤30 篇参考文献、摘要 ≤200 词；排版后 6–8 页 [8] | 金色 OA；2026 年投稿 APC $2,100，SSA 会员通讯作者 9 折 [8] | Data and Resources 声明必需 [8] | [待核] | — |
| **Seismica** | 地震学与地震科学全领域；社区驱动 | 研究论文通常 3,000–10,000 词、≤10 个图表；Fast Reports 约 3,000 词、2–3 个图表；Reports 包括 null results、软件报告、仪器部署 [9][10] | **钻石 OA，作者零费用**；CC-BY 4.0，作者保留版权 [9][24] | 必须有数据与代码可用性声明，"联系作者获取"不可接受；软件报告需提交用户手册和代码到公共仓库，代码接受审稿 [10] | 鼓励预印本，任何渠道均可 [10] | PyOcto（2024）[11]；区域震相拾取（2025）[12]；关联器基准（2025）[13]；全球云端拾取数据库（2025） |

**补充：**
- Seismica Fast Reports 除地震快报外，也接受"概念验证研究、模型/技术应用、假设验证"等时效性工作，至少 1 位外审，目标约 30 天出版；需要大修时可能转为普通文章类型 [10]。
- Seismica 摘要外可附最多两种其他语言的摘要（每种 ≤200 词）；鼓励附约 200 词的非技术摘要 [10]。
- SSA 的 AI 指南：所有 SSA 期刊不鼓励提交 AI 工具生成的文字、图像、图表，"除非它们是研究正式设计或方法的一部分"；审稿人不得把稿件上传到生成式 AI [6]。本项目中 agent 生成的波形图和决策记录属于方法本身，但论文正文和图件应由作者制作，并在方法中披露。

### 2. 先例论文（LLM/agent 进入地学期刊）

| 论文 | 期刊 | 类型 | 对本项目的参考意义 |
|---|---|---|---|
| Wang et al. 2026, SeisMoLLM [3] | GRL 53 | LLM 骨干微调做 5 类地震监测任务 | 说明 GRL 接受"LLM + 地震监测"；本组已有发表经验 |
| Zhu et al. 2026, LLMs as Calibration Agents in Hydrological Modeling [4] | GRL | 5 种 LLM 当率定 agent，与 SCE-UA、NSGA-III 比较；题目带 "Feasibility and Limitations" | GRL 接受"agent 可行性 + 局限"式的短文，且以与传统算法的对照为核心 |
| Bassani et al. 2026 [14] | JGR: MLC 3 | 微调 TinyLlama，从到时和 PGV 估计震级、位置 | JGR-MLC 接受 LLM 地震学方法文 |
| Agrawal et al. 2026, Digital Archivist [7] | SRL | Gemini 2.5 Pro 工作流抽取宏观地震资料 | SRL 接受"LLM 工作流 + 地震学应用" |
| Wilson et al. 2023 [23] | SRL | ChatGPT 问答观察 | SRL 早期 LLM 文章 |
| Li & Yuan 2026, FA-Agent [25] | 投 *Geophysics*（审稿中） | 勘探初至波多模态 agent，45 页 | 勘探方向选择 SEG 期刊；天然地震方向的对口期刊是 GRL/SRL/Seismica/BSSA |

### 3. ML 会议与 workshop

**3.1 NeurIPS 2026（已过截止，仅作参考）**

- 会期：Sydney workshop 12-11/12，Paris 与 Atlanta workshop 12-12/13；建议 workshop 投稿截止 2026-08-29（各 workshop 自定）[17]。
- 与本项目相关的 workshop（名称来自官方公告）[17]：
  - 持续/测试时学习：Towards Test-Time Continual Learning Agents（Atlanta）、Continual Learning for Enterprise AI Agents（Atlanta）、Continual Learning in the Era of Foundation Models and Embodied Agents（Sydney）、Continual World Models（Sydney）。
  - 自我改进/科研 agent：Workshop for Autonomous Machine Learning Research（Sydney）、Self-Evolving Diversity-Driven Search for Robust AI Systems（Sydney）。
  - agent 评估与可靠性：Who Verifies the Agents?（Sydney）、Workshop on Evaluation of Interactive Agents（Atlanta）、Workshop on Resource-Aware Agentic AI（Atlanta）。
  - AI for science：AI for Science: Verification in the Age of AI Scientists（Sydney）、Sim2Science（Paris）、AI & Science: Evolution or Extinction?（Atlanta）。
  - 时间序列：Foundation Models for Temporal Systems（Sydney）。
- **TTCL 详情** [15][16]：2026-12-13，亚特兰大，线下；组织者来自 JHU、Michigan、Georgia Tech、Lambda；一般研究轨正文 4–9 页（参考文献和附录不计）；非存档，接受在投或已录用论文；主题：测试时适应与学习、无灾难性遗忘的持续学习、记忆与知识整合、从经验中学习的 agent、评估/安全/鲁棒性；附带基于 AgentOdyssey 的挑战赛。录用 85 篇，其中与本项目方法学最相关的有 "Position: Adapt Fast, Evolve Slowly: Evidence-Gated Escalation for Agentic Continual Learning"、"Learning What to Keep: Evidence-Gated Parameterized Skills for Frozen LLM Agents"、"Useful Memories Become Faulty When Continuously Updated by LLMs"、"Self-Consolidation for Self-Evolving Agents"、"AgentCL: Toward Rigorous Evaluation of Continual Learning in Language Agents"、"Is One Score Enough? Rethinking the Evaluation of Sequentially Evolving LLM Memory"（仅标题，未读）[16]。这些可交给 10–13 号方向核查，且说明"门控、证据、整合"正是该社区当前的关注点。

**3.2 2027 年窗口**

| 会议 | 已公布日期 | 备注 |
|---|---|---|
| ICLR 2027 | 主会 2027-04-26 至 28；workshop 04-29/30；主会摘要 2026-09-18、全文 09-25（已过）；最终决定 2026-12-16 [18] | workshop 列表与投稿截止尚未公布；地点未定 |
| ICML 2027 | 主会 2027-08-02 至 04；workshop 08-05/06；投稿开放 2027-01-08；摘要 01-14；全文 01-22；首轮拒稿通知 02-23；最终通知 05-03 [19] | 页面未写地点。workshop 截止通常在 5 月下旬至 6 月（推断） |
| NeurIPS 2027 | 未找到 | 通常主会 5 月截止、workshop 8 月底截止（推断） |
| Agents4Science | 2025 年版：2025-10-22 线上，截止 2025-09-15；要求 AI 为主要作者 [26] | 页面未提 2026/2027 年版；AI 作者要求与本项目不符，不建议 |

**3.3 地学会议（摘要）**

| 会议 | 日期与地点 | 摘要截止 |
|---|---|---|
| EGU 2027 | 2027-04-04 至 09，维也纳 + 线上 [21] | 2027-01-12 13:00 CET [21] |
| SSA 2027 | 2027-04-20 至 24，西雅图 [22] | 本页未列出；旅行资助申请截止 11-30 [22]；往年摘要截止在 1 月 [待核] |
| AGU 2026 Fall Meeting | 2026 年 12 月 [待核] | 已过（推断） |
| SCEC 2027 | — | 未查 |

SSA 2026 设有 "Developing Data-Driven Methods in the AI Era: New Approaches to Earthquake Science" 专题（Chatting With the Earth 即在此）[27]；SSA 2027 很可能有类似专题（推断），适合首次公开报告结果。

### 4. 双投与存档规则

- NeurIPS 2026 TTCL 明确为非存档，接受在投论文 [15]。ICML/ICLR 的 workshop 多数为非存档，但需逐个核实（推断）。
- 投 ML 主会（ICLR/ICML/NeurIPS 主轨，存档）与投地学期刊通常构成重复发表，需要内容显著不同；建议 ML 方向只投非存档 workshop（推断）。
- SRL 对预印本许可证的限制见 §1：若计划投 SRL，arXiv 预印本应选 arXiv 默认的非独占许可，而不是 CC-BY [5]。Seismica 对预印本无此限制 [10]。GRL/JGR-MLC 的预印本政策本轮未核实 [待核]。

## 对本项目的影响

**推荐路线（推断，基于上面的要求和先例）：**

1. **主投 GRL**（老师的目标），条件是：T3 半合成精度结果（H1）和带对照的学习曲线（H2/H3）至少有一项强而清楚。GRL 12 PU 正好容纳 design.md §11 的 4 幅图 + 约 4,000 词；方法细节（门控协议、对照组、提示词）放补充材料。可参照 Zhu et al. 2026 的 "Feasibility and Limitations" 写法 [4]。
2. **备选 Seismica 研究论文**：若结果偏"方法学 + 负结果"（例如门控后学习收益很小、半合成上优势消失——design.md §12 的风险情形），Seismica 无篇幅压力、零费用，并接受 null results [9][10]；也适合完整发布 agent 框架和记忆仓库。
3. **SRL Electronic Seismologist**：若论文重心转向"开源工具 + 可复现的 agent 分析员框架"，这是对口栏目 [5]。注意预印本许可证。
4. **JGR-MLC**：若需要更长篇幅讲清方法（多种对照、统计、成本分析），且先例显示接受 LLM 地震学方法文 [14]。篇幅和费用待核。
5. **ML 方向**：ICML 2027 workshop（2027 年 8 月；截止预计 5–6 月）中选择持续学习/agent 评估/AI for science 类 workshop，投非存档版本，重点讲"物理反馈 + 门控的无权重学习"和"安慰剂对照"。ICLR 2027 workshop（4 月）若在 1–2 月有截止，时间上可能更合适，需在 workshop 列表公布后（通常 12 月–1 月）再核。
6. **首次公开**：EGU 2027 摘要（1 月 12 日截止）或 SSA 2027 摘要（约 1 月），在投期刊前先建立优先权（推断）。

**对设计的具体影响：**
- 预印本：投稿前先挂 arXiv（FA-Agent 等近邻工作出现很快，见 15 号文件），**选非 CC 许可**以保留 SRL 选项。
- 数据与代码：Seismica 和 SRL 都要求明确的数据/代码可用性；AGU 也有类似要求 [待核]。从现在起把 agent 框架、提示词、记忆版本、评分程序和数据下载脚本放进可公开的仓库，避免投稿时补工作。
- 图件：遵守 SSA AI 指南，论文图件由作者用确定性代码绘制；agent 自己画的检查图只作为补充材料中的决策记录示例，并在方法中披露 [6]。
- 写作长度：按 GRL 12 PU 规划主文，同时准备一个 Seismica/JGR-MLC 长版本的大纲，以便被 GRL 拒稿后快速转投。

## 未解决与待核

- **AGU（GRL、JGR-MLC）官方作者指南页面本轮被拒绝访问**（agu.org 与 Wiley 均返回 403），GRL 的篇幅数字来自 AGU 页面的检索摘要；JGR-MLC 的篇幅、APC、预印本政策、数据政策均未核实。建议在浏览器中直接查看 AGU "Text Requirements" 和 JGR-MLC "Author Guidelines"。
- Seismica 页面上 "Submissions" 和 "Author Guidelines" 对研究论文是否严格上限 10,000 词措辞不同（"typically" vs "no more than"）[9][10]，以 Author Guidelines 为准。
- SSA 2027 摘要截止日、AGU 2026 Fall Meeting 日期、ICLR/ICML 2027 workshop 列表与截止日：均未公布或未查到。
- NeurIPS 2027 日期未找到。
- Agents4Science 是否有 2026/2027 年版本：未找到。
- 本轮 WebSearch 配额已用完，未能进一步搜索 GRL/Seismica 中"agent + 地震"的更多先例；Crossref 检索只覆盖了标题/摘要匹配的条目。

## 参考文献

1. AGU. Text Requirements（publications.agu.org/author-resource-center/text-requirements，现重定向至 agu.org）. https://www.agu.org/Publish-with-AGU/Publish/Author-Resources/Text-requirements [只读摘要：页面 403，数字来自检索摘要]
2. AGU. Summarizing Your Science / Plain Language Summary 与 AGU Manuscript Word template (2025-02-12). https://www.agu.org/publications/authors/journals/plain-language-summary ; https://www.agu.org/-/media/Files/Publications/AGU_Manuscript_Word_Feb12_2025.pdf [只读摘要]
3. Wang, X., Liu, F., Su, R., Wang, Z., Fang, L., Zhou, L., Bai, L., & Ouyang, W. (2026). SeisMoLLM: Advancing Seismic Monitoring via Cross-Modal Transfer With Pretrained Large Language Model. *Geophysical Research Letters* 53, e2025GL118505. https://doi.org/10.1029/2025GL118505 [只读摘要（Crossref）]
4. Zhu, Z., Tang, Y., Tang, X., Zhang, J., Gao, C., Zhang, S., et al. (2026). Large Language Models as Calibration Agents in Hydrological Modeling: Feasibility and Limitations. *Geophysical Research Letters*. https://doi.org/10.1029/2025GL120043 [只读摘要（Crossref）]
5. Seismological Society of America. SRL Submission Guidelines. https://www.seismosoc.org/publications/srl-authorsinfo/ [已读原文]
6. Seismological Society of America. Artificial Intelligence Guidelines for Authors and Reviewers. https://www.seismosoc.org/publications/ai-guidelines/ [已读原文]
7. Agrawal, A., Hough, S. E., Mousavi, S. M., Hellweg, M., Ellsworth, W. L., & Yoon, C. E. (2026). The Digital Archivist: Automating Legacy Macroseismic Data Processing Using Large Language Models. *Seismological Research Letters*. https://doi.org/10.1785/0220250362 [只读摘要]
8. Seismological Society of America. The Seismic Record Submission Guidelines. https://www.seismosoc.org/publications/the-seismic-record/submission-guidelines/ [已读原文]
9. Seismica. Submissions. https://seismica.library.mcgill.ca/about/submissions [已读原文]
10. Seismica. Author Guidelines. https://seismica.library.mcgill.ca/author-guidelines [已读原文]
11. Münchmeyer, J.（作者据记忆，Crossref 只核了标题）(2024). PyOcto: A high-throughput seismic phase associator. *Seismica* 3(1). https://doi.org/10.26443/seismica.v3i1.1130 [只读摘要（Crossref 标题）]
12. Aguilar Suarez, A. L., & Beroza, G. (2025). Picking Regional Seismic Phase Arrival Times with Deep Learning. *Seismica* 4(1). https://doi.org/10.26443/seismica.v4i1.1431 [只读摘要]
13. Benchmarking seismic phase associators: Insights from synthetic scenarios (2025). *Seismica* 4(2). https://doi.org/10.26443/seismica.v4i2.1559 [只读摘要（Crossref 标题，作者未核）]
14. Bassani, A., Trappolini, D., Poggiali, G., Tinti, E., Galasso, F., Michelini, A., & Marone, C. (2026). Adapting a Pretrained LLM to Rapidly Recover Earthquake Magnitude and Location. *JGR: Machine Learning and Computation* 3, e2026JH001578. https://doi.org/10.1029/2026JH001578 [只读摘要]
15. NeurIPS 2026 TTCL Workshop: Towards Test-Time Continual Learning Agents. https://ttcl-agents.github.io/ [已读原文]
16. NeurIPS 2026 virtual site: Workshop on Towards Test-Time Continual Learning Agents. https://neurips.cc/virtual/2026/loc/atlanta/workshop/137567 [已读原文]
17. NeurIPS Blog (2026-08-10). Announcing the NeurIPS 2026 Workshops. https://blog.neurips.cc/2026/08/10/announcing-the-neurips-2026-workshops/ [已读原文]
18. ICLR 2027 Dates. https://iclr.cc/Conferences/2027/Dates [已读原文]
19. ICML 2027 Dates. https://icml.cc/Conferences/2027/Dates [已读原文]
20. Shinohara, T. (2026). SeisAgentBench: A Failure-Aware Core Benchmark for Multi-Agent Earthquake Rupture Inversion and Forward Validation. ICML 2026 AI4Science workshop poster. https://icml.cc/virtual/2026/73526 [未打开原文，经搜索摘要与 OpenReview 元数据]
21. EGU General Assembly 2027. https://www.egu27.eu/ [已读原文]
22. SSA Annual Meeting site. https://meetings.seismosoc.org/ [已读原文]
23. Wilson, M. P., Foulger, G. R., Wilkinson, M. W., Gluyas, J. G., Mhana, N., & Tezel, T. (2023). Artificial Intelligence and Human-Induced Seismicity: Initial Observations of ChatGPT. *Seismological Research Letters*. https://doi.org/10.1785/0220230112 [只读摘要]
24. Seismica. About the Journal（首页）. https://seismica.org/ [已读原文]
25. Li, W., & Yuan, C. (2026). FA-Agent: An extensible multimodal agent framework for first-arrival picking in mountainous seismic data. arXiv:2611.06555. https://arxiv.org/abs/2611.06555 [已读原文]
26. Agents4Science 2025 conference site. https://agents4science.stanford.edu/ [已读原文]
27. SSA 2026 Annual Meeting Program. https://meetings.seismosoc.org/wp-content/uploads/2026/02/SSA-Program-2026.pdf [已读原文（相关页）]
