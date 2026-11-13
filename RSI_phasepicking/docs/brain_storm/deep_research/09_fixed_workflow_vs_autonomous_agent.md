# 09. 固定流程与自主 agent

## 要回答的问题

- 什么情况下写死的、人工编排的 LLM 流程（fixed workflow）优于自主调用工具的 agent，反过来又如何？有哪些指导意见和证据（例如 Anthropic "Building effective agents" 对 workflow 与 agent 的区分；在成本、可靠性、准确率上比较脚本化流水线与 ReAct 式 agent 的研究；软件工程中 "Agentless"（Xia et al. 2024）与 agentic SWE agent 的对比）。
- 地学/地震学及其他学科的科学 agent（如 TRACE arXiv 2603.21152——需核实；SeisAgent / QuakeFlow agent；ChemCrow、Coscientist、The AI Scientist、Biomni 等）：怎么搭的，怎么失败的，怎么评估的，成本多少。
- 混合设计（固定外层框架 + 自主内层 agent；只把被标记/不确定的条目交给 LLM 的 "triage"/"cascade" 设计）及其实测收益。

影响的决定：编排方式（固定流程 / 通用 agent / 混合）与对照组设计。

## 结论摘要

- **指导原则一致：任务步骤可预先写清时用 workflow，步骤数不可预测、需要模型自己决定下一步时才用 agent，并且先从最简单的方案做起。** Anthropic 把 workflow 定义为"LLM 和工具通过预定义代码路径编排"，agent 为"LLM 动态决定自己的流程和工具使用"；并指出 agent 用延迟和成本换性能，且错误会累积 [1]。
- **2024 年的对照证据普遍支持"简单流程不输复杂 agent、成本低一个数量级"**：Agentless 三段式流程（定位→修复→验证）在 SWE-bench Lite 上 32.00%、每题约 $0.70，高于当时所有开源 agent [2]；ScienceAgentBench 上 Claude-3.5-Sonnet 用 self-debug 解出 32.4%，用 OpenHands CodeAct 只有 21.6%，而成本是前者的约 17 倍（$0.958 vs $0.057）[3]；HumanEval 上简单的 retry/warming 与最好的复杂 agent 无显著差异，LATS 成本高 50 倍以上 [4]；AlphaCodium 的固定多阶段流程把 GPT-4 在 CodeContests 上的 pass@5 从 19% 提到 44% [5]。
- **但"简单"不等于"无自主"**：到 2025–2026 年，只有 bash 一个工具、约 100 行代码的 mini-swe-agent 配强模型在 SWE-bench Verified 上 >74% [6]。更准确的结论是：**极简控制循环 + 强模型 + 好工具接口**胜过复杂的多 agent 编排；多 agent 结构本身通常不加分——在 10 个基准、GPT-4.1 统一底座下，6 种多 agent 配置中 5 种的合并准确率比单 agent 低 1.71–8.76 个百分点 [7]；7 个多 agent 框架的失败率为 41%–86.7%，主要来自系统设计 [8]。
- **可靠性是 agent 的主要短板**：τ-bench 上 gpt-4o 函数调用 agent 成功率 <50%，零售域 pass^8 <25% [9]；对本项目意味着同一事件重复运行结果会不同，必须报告多次运行的一致性。
- **科学 agent 的结构正在向"约束图/模板 + 局部自主"收敛**：TRACE 有 7 类 agent 角色，规划时从"专家验证案例库"检索并改编模板，104 个任务上成功率约 99.4%，但没有报告与单 agent/固定流程的对比和成本 [10]；FA-Agent 的阶段顺序由 skills 规定，模型只在阶段内决定看哪里、怎么改 [11]；GeoAgent 用固定 9 阶段状态图 + 4 类"契约"把能由图决定的事从模型手里拿走 [12]；TREMORS 用受约束的 LangGraph 执行图 [13]。相反，Biomni 强调"不依赖预定义模板" [14]，The AI Scientist 从 v1 的人写代码模板改为 v2 的 agentic 树搜索 [15][16]。
- **科学 agent 的典型失败**：独立评估 The AI Scientist 时 12 个实验中 5 个（42%）因代码错误失败，跑通的也常有逻辑错误；每篇约 $6–15 [17]；ChemCrow 发现 GPT-4 当评审分不清明显错误的答案和正确答案，必须有专家评估 [18]；TRACE 自述仍需专家复核，并且 S-net 上的深度学习拾取产生大量不合理的 S 到时，需要人工质控 [10]。
- **分级（cascade/triage）有可观的成本收益**：FrugalGPT 在其数据集上以最高 98% 的成本降幅达到 GPT-4 水平 [19]；带人工兜底的 LLM 级联在多数情况下准确率高于单模型、成本更低 [20]（[只读摘要]）。地震台网本身就是分级：SCSN 只对 M≥2.5、RMS≥0.4 等事件做完整人工分析（见 design.md §3.1），并已用 PhaseNet/GaMMA 做后处理以减轻分析员负担 [21]。
- **对本项目的建议（推断）**：采用**混合**——确定性的外层框架（取数、出图、DL 拾取、定位、评分、门控、记忆写入）+ 受限的内层 agent（每个事件内看图、改拾取、按残差重拾，带步数和预算上限）+ 按 DL 不确定度分级。对照组中必须加入一个**同一模型、同一工具、但步骤写死的固定流程组**，否则无法回答"自主性本身是否带来收益"。

## 详细发现

### 1. 什么时候用 workflow，什么时候用 agent

**1.1 指导意见**

| 来源 | 观点 |
|---|---|
| Anthropic, Building effective agents (2024-12-19) [1] | workflow = 预定义代码路径；agent = 模型动态决定流程和工具。workflow 适合定义清楚的任务，提供可预测性和一致性；agent 适合需要灵活性、步骤数无法预知的开放问题。agent "用延迟和成本换性能"，自主性带来更高成本和错误累积，需要沙箱测试和护栏。建议先找最简单的方案，很多任务一次 LLM 调用加检索和示例就够。列出的模式：prompt chaining、routing、parallelization（sectioning/voting）、orchestrator-workers、evaluator-optimizer、autonomous agent。 |
| Kapoor et al. 2024, AI Agents That Matter [4] | 只看准确率的 agent 评测导致 agent 不必要地复杂和昂贵；应联合优化成本与准确率；很多基准缺少 holdout，导致 agent 走捷径、过拟合。 |

**1.2 软件工程中的直接对比**

| 研究 | 设置 | 结果 |
|---|---|---|
| Agentless（Xia et al.，arXiv 2024 → PACMSE/FSE 2025）[2] | 三段式：定位、修复、补丁验证；不让 LLM 决定后续动作 | SWE-bench Lite 32.00%（96 题），约 $0.70；作者称为当时开源方法最高，且成本低 |
| AlphaCodium（Ridnik et al. 2024）[5] | 测试驱动的多阶段固定流程（"flow engineering"） | GPT-4 在 CodeContests 验证集 pass@5：单个精心设计的 prompt 19% → 流程 44% |
| Kapoor et al. 2024 [4] | HumanEval，简单基线 vs LDB / LATS / Reflexion | warming（GPT-4）93.2%、$2.45；retry 92.0%、$2.51；LATS（GPT-4）88.0%、$134.50；Reflexion（GPT-4）87.8%、$3.90。作者：warming 与最好的 agent 结构"无显著差异" |
| mini-swe-agent（SWE-agent 团队）[6] | 只有 bash、每步独立 subprocess、agent 类约 100 行 | SWE-bench Verified >74%（官方页面；PyPI 记录为 Gemini 3 Pro）。分数主要取决于底座模型 [只读摘要] |

解读（推断）：2024 年"Agentless 胜过 agent"的结论，部分来自当时 agent 框架太复杂、模型太弱。模型变强后，最简单的自主循环反而成为最强方案之一。两条结论并不矛盾：**都在说复杂编排不划算**；区别只在于"每一步由谁决定"。

**1.3 科学计算任务中的对比**

ScienceAgentBench（ICLR 2025）[3]：102 个来自 44 篇论文的数据驱动科学任务，表 3：

| 框架 | 模型 | 成功率（无专家知识） | 每题成本 |
|---|---|---|---|
| Direct prompting | Claude-3.5-Sonnet | 17.7% | $0.017 |
| OpenHands CodeAct | Claude-3.5-Sonnet | 21.6% | $0.958 |
| Self-debug | Claude-3.5-Sonnet | 32.4% | $0.057 |
| OpenHands CodeAct | GPT-4o | 19.6% | $0.803 |
| Self-debug | GPT-4o | 22.6% | $0.047 |

作者原话大意：self-debug 比 OpenHands 多解出 10.8% 的任务，API 费用低 17 倍。self-debug 本质上是"生成→运行→看报错→改"的固定循环，介于 workflow 和 agent 之间。

**1.4 多 agent 与可靠性**

- Fu et al. 2026（arXiv 2606.05670）[7]：统一用 GPT-4.1、10 个基准、每配置 3,302 例 × 3 次。单 agent 参照合并准确率 76.65%；EvoAgent 79.70%（唯一更好）；其余 5 种多 agent 配置低 1.71–8.76 个百分点；LLM-Debate 低 1.96 个百分点且 token 1.39 倍；ChatEval token 4.34 倍。
- Cemri et al.（MAST，NeurIPS 2025 D&B）[8]：7 个多 agent 框架、1,600+ 条标注轨迹，失败率 41%–86.7%；失败多来自系统设计（角色、终止条件、步骤重复等），不只是模型能力。
- τ-bench（Yao et al. 2024）[9]：gpt-4o 等函数调用 agent 成功率 <50%；零售域 pass^8 <25%，即同一任务跑 8 次全部成功的比例很低。
- ReliabilityBench（Gupta 2026，单作者预印本）[22]：扰动下成功率从 96.9% 降到 88.1%；联合压力下 ReAct 比 Reflexion 更稳。[只读摘要]

### 2. 地学/地震学和其他学科的科学 agent

| 系统 | 领域 | 结构 | 评估方式与结果 | 成本 | 主要失败/局限 |
|---|---|---|---|---|---|
| **TRACE**（Liu, Cui, …, Bai；arXiv 2603.21152 v4，2026-09-30）[10] | 地震学（Ridgecrest 2019、三陆 2025–26） | 7 类角色：Planning、Plan Aggregation、Workflow、Coding、Result Checking、按视角的 Analysis、Cross-Perspective Analysis；规划从结构化知识库（含"专家验证案例库"）检索模板并改编，可选人工确认；编码工作流最多 20 轮纠错、任务级最多 3 轮 | 104 个任务（74 个 L1 + 30 个 L2）× 3 个底座 = 312 次运行，310 次成功（约 99.4%）；GPT-5.1 均分 4.85，Gemini 3 Flash 4.82，Claude Sonnet 4 4.79；L3 为两个端到端案例 | 未报告（[已读原文]，前 20 万字符） | 未与单 agent/ReAct/固定流程比较；S-net 上 DL 拾取产生大量不合理 S 到时，需人工质控；作者称仍需专家复核；不能排除底座模型见过 Ridgecrest 文献。拾取本身调用 PhaseNet（阈值 0.4）+ GaMMA + HypoDD |
| **FA-Agent**（Li & Yuan；arXiv 2611.06555，投 *Geophysics*）[11] | 勘探地震初至波 | GPT-6 Astra；skills 规定阶段：常规初拾→整道集浏览找关注窗→放大看→逐段保留/修正/删除→终审；模型在阶段内决定看什么、调用工具 | 半合成：常规拾取约 2% 在 ±20 ms 内，agent 全部或几乎全部在 ±20 ms 内；野外数据只报决策计数；没有与 DL 拾取器的定量比较；没有学习曲线 | 每道集 30–90 s（本地单核）；token 只定性提到 | 无正式控制/终止机制描述 |
| **GeoAgent**（Fang et al.；arXiv 2610.31096）[12] | 勘探地震处理（Madagascar） | 固定 9 阶段状态图 + 54 个算子 agent + 4 类契约（命名产物、输入解析、参数接管、产物验证）；确定性几何工具检查 8 个一致性条件 | 单个 2-D 陆上数据集：流程 6–11 分钟，每阶段产物均通过验证；检索把每轮工具上下文从约 12k 降到 2k token | 未报美元 | 把自由调用工具称为"脆弱"，但没有量化对比 [只读摘要] |
| **TREMORS**（Hill et al.；arXiv 2609.01777，LANL 作者）[13] | 地震数据下载 | LLM 把自然语言转为结构化 schema，再由受约束的 LangGraph 执行图执行 | 示例工作流，无可靠性数字 [只读摘要] | 未报告 | — |
| Seismology modeling agent（Ren et al.；arXiv 2512.14429）[23] | SPECFEM 正演 | MCP 工具套件，支持全自动或人在环 | [只读摘要] | — | — |
| SeisEvo（Xu, Yu, Ma；arXiv 2608.18272）[24] | 勘探数据插值 | 多 agent 进化搜索算法本身；违反物理约束的候选直接拒绝，其余按执行结果打分 | Evo-POCS 平均 +3.49 dB | — | 产物是白盒算法，推理时不需要 agent |
| ChemCrow（Bran et al., *Nat. Mach. Intell.* 2024）[18] | 化学 | GPT-4 + 18 个专家工具，ReAct 式 | LLM 评审 + 专家评审 | — | GPT-4 评审分不清明显错误的 GPT-4 答案与 ChemCrow 的答案 |
| Coscientist（Boiko et al., *Nature* 2023）[25] | 化学实验 | GPT-4 规划器 + 联网/文档检索、代码执行、实验自动化模块 | 6 类任务，含钯催化偶联条件优化 | — | — |
| The AI Scientist v1（Lu et al. 2024）[15] / v2（Yamada et al. 2025）[16] | ML 研究 | v1：人写代码模板上的固定流水线（想法→代码→实验→作图→写作→模拟评审）；v2：去掉模板，改为 experiment manager 管理的 agentic 树搜索，加 VLM 看图反馈 | v2 三篇投 ICLR workshop，一篇超过平均录用线 | v1 每篇 <$15 [15]；独立评估约 $6–15/篇、每篇约 3.5 小时人工 [17] | 独立评估：12 个实验 5 个因代码错误失败；文献检索粗糙；把已知概念判为新颖 [17] |
| Biomni（Huang et al., bioRxiv 2025）[14] | 生物医学 | 先用"动作发现 agent"从文献挖出工具/数据库/协议构成统一环境，再由通用 agent 用检索增强规划 + 代码执行，"不依赖预定义模板" | 多类任务泛化（摘要）；二手来源称同一环境下 ReAct agent 不如 Biomni-A1 [待核] | — | — |

关于提示中提到的 **SeisAgent / QuakeFlow agent**：没有找到名为 SeisAgent 的 arXiv 论文，也没有找到 QuakeFlow 的 LLM agent 版本。找到的同名项目是 ICML 2026 AI4Science workshop 海报 "SeisAgentBench: A Failure-Aware Core Benchmark for Multi-Agent Earthquake Rupture Inversion and Forward Validation"（Shinohara），内容为破裂反演多 agent 编排基准 [26]，以及一个 ICLR 2027 投稿 "SeisAgentBench: Benchmarking and Reinforcement Learning for Seismic Data-Processing Agents"（OpenReview 正文因验证页面未能打开）[27]。详见 15 号文件。

**地学 agent 的共同模式（推断）**：凡是要产出可复核科学产物的系统（GeoAgent、TREMORS、TRACE、FA-Agent），都把"阶段顺序"交给代码或 skills，把"阶段内的判断"交给模型，并在每阶段后做确定性检查。这正是 Anthropic 所说的 prompt chaining + evaluator-optimizer 的组合，而不是开放式 agent。

### 3. 混合设计：固定外壳 + 自主内核；只把不确定的条目交给 LLM

**3.1 级联与分级**

| 研究 | 设计 | 结果 |
|---|---|---|
| FrugalGPT（Chen, Zaharia, Zou 2023）[19] | 学习何时从便宜模型升级到贵模型 | 最高 98% 成本降幅达到 GPT-4 水平，或同成本准确率 +4%（最好情况，非典型值）[只读摘要] |
| Fanconi & van der Schaar（arXiv 2506.11887）[20] | 小模型 → 大模型 → 人工；按不确定度逐级上交 | 多数情况下准确率高于单模型基线、成本更低；用强模型"验证"比"重新生成"更便宜、校准更好 [只读摘要] |
| Tavakoli & Zamani 2025（检索澄清标注）[28] | 用置信度阈值和多个 LLM 的分歧决定哪些条目交给人 | 人工量最多减少 45%，可靠性提高 [只读摘要，未打开原文] |
| Kapoor et al. 2024 escalation [4] | 先用便宜模型，失败再升级 | HumanEval 85.0%、$0.27，优于 LDB（GPT-3.5）80.2%、$0.63 |

**3.2 地震学中的分级先例**

- SCSN：M<3 事件的自动后处理改用 PhaseNet，拾取数增加约 2–3 倍、精度略好；ST-Proc 用 PhaseNet + GaMMA 处理未关联的子台网触发，正确检出 65–70% 含事件的触发，误报约 5%；两条流水线都减轻了分析员负担 [21]。完整人工分析只针对一部分事件（design.md §3.1 引用的 SCEDC 变更历史）。这就是一个"自动处理全部 + 人工只看被标记的"设计。
- LANL 的 Park（SSA 2026 海报）提出相反的分工：分析员目视判定"有没有到时"并给粗略时刻，模型输出起始时刻的概率分布做精修；理由是精修步骤最耗时也最主观 [29]。这提示**人/LLM 与 DL 模型之间的分工方向值得作为一个设计变量**：本项目默认"DL 先拾、LLM 复核"，而 Park 的设计是"人先判有无、模型精修"。

**3.3 本项目试点的成本参照**

Advikar 试点：每个事件 agent 运行 $0.50–0.75，每次反思约 $0.07，整个试点约 $60（advikar_pilot_summary.md §3.5）。若对 Ridgecrest 07-04 至 07-06 约 6,700 个事件全量运行，按此单价约 $3.4k–5k（推断，未计重跑和多种子）。分级只把 15–30% 的拾取交给 GPT（design.md §8.2），成本可降到同一量级的几分之一。

## 对本项目的影响

**编排选择：建议用混合架构，并把"自主程度"做成实验变量，而不是先验决定。**

1. **外层固定（代码负责，不交给模型）**：取波形、预渲染标准图、运行 DL 拾取器集成、计算难度分数、调用定位器、计算残差、宿主机评分、门控、记忆版本管理。理由：这些步骤顺序确定、错误代价高，交给模型只会引入方差（τ-bench、MAST 的证据）[8][9]；而且"定位由宿主机重算"本身是防作弊措施（试点 §2.6）。
2. **内层受限 agent（模型负责）**：对一个事件，模型决定看哪些台站、换什么滤波/分量/窗口、改哪些拾取、哪些台站因残差大需要重拾。给步数上限、预算上限和明确的终止条件（Anthropic 建议的 stopping condition）[1]。工具集保持小而稳（mini-swe-agent 的经验）[6]。
3. **分级**：只把 DL 集成不一致、低置信、低信噪比或缓起的拾取交给 LLM；随机抽 5% "简单"事件审计（design.md §8.2 已有，保留）。

**对照组（新增或强调）：**

| 组 | 内容 | 回答的问题 |
|---|---|---|
| **F-fixed（新增，必须）** | 同一模型、同一工具、同一图片，但步骤写死：对每个被标记的拾取依次"看标准图 → 看放大图 → 输出调整量与置信度"；定位一次；对残差最大的 k 个台站按固定规则重拾一次；不允许自选工具和顺序 | 自主性本身有没有用（Agentless 式对照）[2] |
| F-fixed + playbook | 同上，但把学到的 playbook 放进固定流程的提示 | 学习收益是否依赖自主性；若固定流程也能吃到 playbook 的收益，论文可以把"学习"和"自主"分开报告 |
| **D-residual（新增，非 LLM）** | PhaseNet + AIC 精修 + 残差离群剔除/重拾（如 RANSAC 式定位 [30] 或按残差阈值重跑 AIC） | LLM 带来的增益是否只是"残差驱动的确定性重拾"就能得到 |
| A-bestofN（已有） | 等算力多次采样/投票 | 排除"多花算力就有用"；对应 Kapoor 的 retry/warming 基线 [4] |

**报告要求：**
- 每组报告**成本–准确率**（token、图片数、工具调用数、美元、耗时），画帕累托图，而不是只报准确率 [4]。
- 每组至少在一个子集上重复运行 ≥3 次，报告 pass^k 类一致性指标或事件级方差 [9]。
- 记录内层 agent 的失败类型（不终止、重复操作、越权修改、工具报错），参考 MAST 的分类 [8]，作为附录。

**应避免：**
- 不要做多 agent 角色分工（规划者/执行者/审查者等），除非有明确证据；现有证据显示多 agent 通常不如单 agent 且更贵 [7][8]。
- 不要用 LLM 评审作为评分（ChemCrow 的教训）[18]；评分始终用宿主机上的确定性程序。
- 不要把 TRACE 的 99.4% 成功率当作"agent 可靠"的证据引用：它没有固定流程对照，任务是工具调用和代码执行，不是波形判读 [10]。

## 未解决与待核

- **没有找到在同一科学任务上、保持模型和工具不变、只改变控制流的严格对比**（workflow vs agent）。ScienceAgentBench 最接近，但 OpenHands 和 self-debug 的工具也不同 [3]。本项目的 F-fixed vs 内层 agent 对照本身可以成为一个小贡献。
- mini-swe-agent >74% 的数字来自项目页和 PyPI 记录，未打开 SWE-bench 官方排行榜核对具体模型和日期 [6]。
- Biomni 正文的具体数字（如 Biomni-Eval1 准确率、与 ReAct 的对比）只来自二手来源，bioRxiv 页面当时返回 429，未核实 [14]。
- TRACE 的成本和单 agent 消融：原文前 20 万字符里没有，剩余约 2 万字符未读；建议直接问 TRACE 作者（同组）是否有成本和消融数据，可直接用于本项目的成本估算。
- FrugalGPT、级联/人工兜底类研究的收益来自 NLP 分类和问答，迁移到拾取复核是推断 [19][20]。
- WebSearch 本轮配额已用完，未能进一步检索"人–模型分工方向"在地震拾取中的对照研究（Park 的设计是否有定量结果）。

## 参考文献

1. Erik S.（页面致谢处只写 "Erik S."）& Barry Zhang (2024-12-19). Building effective agents. Anthropic Engineering. https://www.anthropic.com/engineering/building-effective-agents [已读原文]
2. Xia, C. S., Deng, Y., Dunn, S., & Zhang, L. (2024/2025). Agentless: Demystifying LLM-based Software Engineering Agents. arXiv:2407.01489；正式版 "Demystifying LLM-Based Software Engineering Agents", *Proc. ACM Softw. Eng.* 2 (FSE), 801–824, 2025. https://doi.org/10.1145/3715754 [只读摘要]
3. Chen, Z., …, Sun, H. (2024/2025). ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery. ICLR 2025. arXiv:2410.05080. https://arxiv.org/abs/2410.05080 [已读原文，表 3]
4. Kapoor, S., Stroebl, B., Siegel, Z. S., Nadgir, N., & Narayanan, A. (2024). AI Agents That Matter. arXiv:2407.01502. https://arxiv.org/abs/2407.01502 [已读原文，表 A1]
5. Ridnik, T., Kredo, D., & Friedman, I. (2024). Code Generation with AlphaCodium: From Prompt Engineering to Flow Engineering. arXiv:2401.08500. https://arxiv.org/abs/2401.08500 [只读摘要]
6. SWE-agent team. mini-swe-agent（GitHub 与 PyPI 页面）. https://github.com/SWE-agent/mini-swe-agent ; https://pypi.org/project/mini-swe-agent/ [只读摘要，经搜索摘要]
7. Fu, Y., Fang, R., Shao, J., Zheng, H., Zhu, Z., Luo, B., Wen, Z., & Lin, T. (2026). Do More Agents Help? Evaluating Accuracy and Cost in LLM Multi-Agent Workflows. arXiv:2606.05670. https://arxiv.org/abs/2606.05670 [只读摘要]
8. Cemri, M., Pan, M. Z., Yang, S., Agrawal, L. A., et al. (2025). Why Do Multi-Agent LLM Systems Fail? NeurIPS 2025 Datasets & Benchmarks. arXiv:2503.13657. https://arxiv.org/abs/2503.13657 [未打开原文，经搜索摘要]
9. Yao, S., Shinn, N., Razavi, P., & Narasimhan, K. (2024). τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. arXiv:2406.12045. https://arxiv.org/abs/2406.12045 [只读摘要]
10. Liu, F., Cui, X., Xu, J., Wang, X., Guo, Z., Wang, J., Mousavi, S. M., Gu, X., Chen, H., Fei, B., Fang, L., Ling, F., Li, Z., & Bai, L. (2026). TRACE: A Multi-Agent System for Autonomous Physical Reasoning for Seismology. arXiv:2603.21152 (v4, 2026-09-30). https://arxiv.org/abs/2603.21152 [已读原文，约前 90%]
11. Li, W., & Yuan, C. (2026). FA-Agent: An extensible multimodal agent framework for first-arrival picking in mountainous seismic data. arXiv:2611.06555（投 *Geophysics*）. https://arxiv.org/abs/2611.06555 [已读原文，HTML v2]
12. Fang, Z., Zhang, Q., Yan, J., Wang, Z., Gu, X., Zhang, Z., & Wang, H. (2026). GeoAgent: Contract-Constrained LLM Agents for Seismic Data Processing. arXiv:2610.31096. https://arxiv.org/abs/2610.31096 [只读摘要]
13. Hill, R. G., Alfaro-Diaz, R., MacCarthy, J., Kintner, J. A., & Johnson, C. W. (2026). TREMORS: An Agentic Assistant for Multi-Datacenter Seismic Data Acquisition. arXiv:2609.01777. https://arxiv.org/abs/2609.01777 [只读摘要]
14. Huang, K., Zhang, S., Wang, H., Qu, Y., Lu, Y., Roohani, Y., et al. (2025). Biomni: A General-Purpose Biomedical AI Agent. bioRxiv. https://doi.org/10.1101/2025.05.30.656746 [只读摘要（Crossref）]
15. Lu, C., Lu, C., Lange, R. T., Foerster, J., Clune, J., & Ha, D. (2024). The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery. arXiv:2408.06292. https://arxiv.org/abs/2408.06292 [只读摘要]
16. Yamada, Y., Lange, R. T., Lu, C., Hu, S., Lu, C., Foerster, J., Clune, J., & Ha, D. (2025). The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search. arXiv:2504.08066. https://arxiv.org/abs/2504.08066 [只读摘要]
17. Beel, J., Kan, M.-Y., & Baumgart, M. (2025). Evaluating Sakana's AI Scientist: Bold Claims, Mixed Results, and a Promising Future? arXiv:2502.14297 (v3). https://arxiv.org/abs/2502.14297 [未打开原文，经搜索摘要]
18. Bran, A. M., Cox, S., Schilter, O., Baldassari, C., White, A. D., & Schwaller, P. (2024). Augmenting large language models with chemistry tools. *Nature Machine Intelligence* 6, 525–535. https://doi.org/10.1038/s42256-024-00832-8 [只读摘要]
19. Chen, L., Zaharia, M., & Zou, J. (2023). FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance. arXiv:2305.05176. https://arxiv.org/abs/2305.05176 [未打开原文，经搜索摘要]
20. Fanconi, C., & van der Schaar, M. (2025). Cascaded Language Models for Cost-Effective Human–AI Decision-Making. arXiv:2506.11887. https://arxiv.org/abs/2506.11887 [未打开原文，经搜索摘要]
21. Tepp, G., Yu, E., Bhaskaran, A., Tam, R., Zhu, W., Newman, Z., Jaski, E., & Scheckel, N. (2025). Improvements from incorporating machine learning algorithms into near real-time operational post-processing. *Scientific Reports* 15, 28938. https://doi.org/10.1038/s41598-025-14491-1 [只读摘要]
22. Gupta, A. (2026). ReliabilityBench: Evaluating LLM Agent Reliability Under Production-Like Stress Conditions. arXiv:2601.06112. https://arxiv.org/abs/2601.06112 [只读摘要]
23. Ren, Y., Yu, S., Chen, K., & Ma, J. (2025). Seismology modeling agent: A smart assistant for geophysical researchers. arXiv:2512.14429. https://arxiv.org/abs/2512.14429 [未打开原文，经搜索摘要]
24. Xu, Y., Yu, S., & Ma, J. (2026). SeisEvo: Evolution of Seismic Data Reconstruction Algorithms by Agents. arXiv:2608.18272. https://arxiv.org/abs/2608.18272 [只读摘要]
25. Boiko, D. A., MacKnight, R., Kline, B., & Gomes, G. (2023). Autonomous chemical research with large language models. *Nature* 624, 570–578. https://doi.org/10.1038/s41586-023-06792-0 [只读摘要]
26. Shinohara, T. (2026). SeisAgentBench: A Failure-Aware Core Benchmark for Multi-Agent Earthquake Rupture Inversion and Forward Validation. ICML 2026 AI4Science workshop poster. https://icml.cc/virtual/2026/73526 [未打开原文，经搜索摘要]
27. 匿名（2026）. SeisAgentBench: Benchmarking and Reinforcement Learning for Seismic Data-Processing Agents. ICLR 2027 投稿. https://openreview.net/forum?id=KskpeXIMbk [未打开原文：OpenReview 返回人机验证页面，只见标题]
28. Tavakoli, L., & Zamani, H. (2025). Reliable Annotations with Less Effort: Evaluating LLM-Human Collaboration in Search Clarifications. arXiv:2507.00543. [未打开原文，经搜索摘要]
29. Park, Y. (2026). Human-centered AI for Seismic Phase Picking in Operational Monitoring. SSA 2026 Annual Meeting, poster 27（摘要见 SSA 2026 程序册）. https://meetings.seismosoc.org/wp-content/uploads/2026/02/SSA-Program-2026.pdf [已读原文（程序册中的摘要）]
30. Zhu, W., Rong, B., Jie, Y., & Wei, S. S. (2025). Robust Earthquake Location using Random Sample Consensus (RANSAC). arXiv:2502.10933. https://arxiv.org/abs/2502.10933 [只读摘要]
