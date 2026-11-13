# 10. 自我演化的技能和记忆

## 要回答的问题

- 按“演化对象”梳理已有方法：规则 / playbook / cheatsheet（ACE arXiv 2510.04618，Dynamic Cheatsheet arXiv 2504.07952），提示词（GEPA arXiv 2507.19457，TextGrad，DSPy 优化器），经验 / 洞见（含失败经验；ReasoningBank arXiv 2509.25140，ExpeL，Reflexion），工作流（Agent Workflow Memory，ICML 2025），代码技能库（Voyager，SkillWeaver，Agent Skills / SKILL.md 式技能库），整个 agent 或自修改代码（Darwin Gödel Machine，AlphaEvolve，自我改进的编码 agent），以及记忆系统（MemGPT/Letta，A-Mem，Mem0）和近期综述（Self-Evolving Agents survey arXiv 2507.21046，需核实）。包括 2026 年的工作。
- 对每一类：更新单位是什么，谁提出更新，更新如何验证 / 接受，如何处理记忆膨胀和“上下文坍缩” / 简短偏差（brevity bias），报告的收益及所用基准，反馈来自真值还是自生成。
- 哪些设计适合我们的条件：单个 episode 贵（约 $0.5/事件）、练习事件少（几十到几百）、需要看图使用工具、反馈有噪声？为本 agent 推荐具体的记忆结构和更新协议（规则 + 代码技能 + 流程），并说明每一部分借鉴自哪篇论文。

影响的决定：记忆的结构和更新协议。

## 结论摘要

- **更新单位决定了验证成本。** 规则 / playbook 类（ACE、Dynamic Cheatsheet、ExpeL、Training-Free GRPO）一次更新只改几条文字，便宜，但效果只能靠跑 episode 来测；代码技能（Voyager、SkillWeaver、Skill-V）可以用单元测试或回放来验证；整个 agent 自修改（DGM）每次运行约 $22,000 [3]，远超本项目预算。本项目应把“能用确定性测试验证的东西”尽量写成代码技能，把门控预算留给规则。
- **ACE 用“增量 delta + 确定性合并 + 嵌入去重”防止上下文坍缩。** ACE 记录到 Dynamic Cheatsheet 在 AppWorld 上一步把上下文从 18,282 token 压到 122 token，准确率从 66.7 降到 57.1（低于 63.7 的无记忆基线）[1]。ACE 在 AppWorld 上 +17.0（有标签）/ +14.8（无标签，仅执行反馈），但在金融任务上无标签在线学习时 FiNER 下降 3.4 [1]。设计稿中“只做增量编辑、不许整体重写”是对的。
- **让 agent 自己评判教训好坏并不可靠。** RBC（arXiv 2610.18427，已核实存在）发现：同一流程长出的 ACE playbook 可能比无记忆差 69.6 分；ACE 自带的 helpful/harmful 标记与实测效果的秩相关只有 0.21；agent 自己挑选的子集（53.8）不比整本 playbook（55.5）或无 playbook（54.1）好；用随机分组消融筛选后达 66.9 [2]。但**只在 3 次生长的整本 playbook 与空 playbook 之间按新 episode 选最优（Best-Full）就有 66.4**，筛选本身只多 0.5 分 [2]。对我们最重要的是“多候选 + 保留空记忆 + 在新事件上选”，块级消融是锦上添花。
- **只加入经验质量合格的记录。** Xiong 等人在 4 个 agent 上发现“全部加入”在每个任务上都比固定记忆差（如 EHRAgent 16.75 → 13.05），用真值严格筛选最好（38.50），粗糙的 LLM 评判介于两者之间 [4]。ReasoningBank 的 LLM 评判准确率 72.7%，模拟 70–90% 准确率时结果相近，但完美标签最好 [5]。物理残差反馈相当于“粗糙评判”，必须有准入标准。
- **反思批量化省钱且记忆更紧凑。** Agent-ToM 中批量 1 → 4 时 F1 0.843 → 0.860、训练时间降 3.2 倍，规则数 155 → 104；批量 8 几乎不再变化 [6]。本项目每次反思约 $0.07，而每个事件 $0.5–0.75，**成本瓶颈在门控评估的 episode，不在反思**。
- **适合本项目的组合（推荐）：** 三层记忆 = 流程（AWM 式工作流，极少改动）+ 规则 playbook（ACE 的条目格式与 delta 合并 + ExpeL 的投票计数 + 设计稿的证据门槛）+ 代码技能（Agent Skills 的 SKILL.md 格式 + Voyager/Skill-V 的测试与契约）；更新先过廉价检查，再过门控集（DGM 的分阶段评估），最后在多次生长的候选中按新事件选择（RBC）。不推荐：GEPA 式整体提示词进化（每个任务 1,839–7,051 次 rollout [7]，按 $0.5 计约 $900–3,500）、DGM 式自修改代码、ReasoningBank 式无筛选追加的检索记忆。
- **2026 年的技能库工作集中在“准入验证”和“防回退”。** Skill-V 把技能写成可证伪的版本化契约，修改须在历史回放上不退步 [8]；SkillBoost 只在“有提升且回退不超过界限”时提交修改 [9]；TMLR 2026 的技能库综述（124 篇）把“准入 / 修复 / 回滚”列为反复出现的关键环节，并指出平铺检索随库增大而变差 [10]。这与设计稿的门控思路一致。

## 详细发现

### 1. 总览：按演化对象分类

| 类别 | 代表工作 | 更新单位 | 谁提出更新 | 验证 / 接受方式 | 膨胀与坍缩的处理 | 报告收益（基准） | 反馈来源 |
|---|---|---|---|---|---|---|---|
| 规则 / playbook | ACE [1] | 带 ID 和 helpful/harmful 计数的条目（bullet） | Reflector 提炼，Curator 生成 delta | 无独立门控；delta 由非 LLM 逻辑确定性合并 | 增量更新 + 语义嵌入去重；超窗口时惰性整理 | AppWorld +17.0（DeepSeek-V3.1，离线有标签）；金融 +12.8 [1] | 有标签或仅执行反馈；无标签时收益变小甚至为负 |
| 规则 / cheatsheet | Dynamic Cheatsheet [11] | 整份 cheatsheet（策略、代码片段） | 模型自身作为 curator | 无；模型自判正误 | 依靠 curator 自我压缩，无上限；会出现“前文保留……”式省略 | GPT-4o Game of 24：10% → 99%；Claude 3.5 Sonnet AIME 2024：23.3 → 50.0 [11] | 无真值，自评 |
| 规则（经验池） | ExpeL [12] | 自然语言洞见，带重要性计数 | LLM 比较同一任务的成功/失败轨迹 | ADD 初始计数 2；UPVOTE/DOWNVOTE 加减；计数归零即删除 | 投票淘汰 | ALFWorld：ReAct 40.0% → 59.0%；HotpotQA 28.0% → 39–40% [12] | 训练任务的环境成功信号（真值） |
| 规则（经验库） | Training-Free GRPO [13] | 经验条目（Add/Delete/Modify/Keep） | LLM 在每组 rollout 间做“语义优势”比较 | 无独立门控；多轮 epoch | 修改、合并、删除操作；示例库 48 条 | 只用 100 个训练样本、约 $18；AIME25 67.9 → 73.3（ReAct + CI）[13] | 少量真值；不用真值时 AIME25 为 68.9 [13] |
| 规则（事后筛选） | RBC [2] | 由约 8 个“块”组成的整本 playbook | 生长阶段由 ACE/DC 提出；筛选不靠 LLM | 每个练习 episode 以 1/2 概率随机包含每块，岭回归估计块效应；在新 episode 上从 7 个候选中选最优 | 只保留正效应块，预算为原 token 的 40% | 平均 66.9，对比整本 55.5、无 54.1、agent 自选 53.8 [2] | 练习任务的成败（真值或单元测试） |
| 提示词 | GEPA [7] | 各模块的指令文本 | LLM 读取轨迹和文字反馈后反思改写 | 子代在 minibatch 上平均分须高于父代，再在 D_pareto 上评分；按 Pareto 前沿选父代 | 无记忆增长问题；提示词比 MIPROv2 短最多 9.2 倍 | 比 GRPO 平均高 6%、最多 20%，rollout 少最多 35 倍；比 MIPROv2 高 10% 以上 [7] | 指标分数 + 评估器文字反馈（真值） |
| 提示词 | MIPROv2 [14]、TextGrad [15] | 指令和示例 / 任意文本变量 | 优化器 LLM | 在训练/验证集上打分 | — | 见原文 [未打开原文] | 真值指标 |
| 经验 / 反思 | Reflexion [16] | 单任务内的文字反思（情节记忆） | agent 自身 | 同一任务重试，靠环境或测试信号 | 只保留最近几条 | HumanEval pass@1 91%（GPT-4 为 80%）[16] | 环境信号或自生成测试 |
| 经验 / 洞见 | ReasoningBank [5] | 记忆条目（标题、描述、内容），每条轨迹最多 3 条 | LLM 从成功和失败轨迹中提炼 | 无门控，简单追加 | 嵌入检索 top-1 | WebArena：Gemini-2.5-flash 40.5 → 48.8；SWE-Bench-Verified 34.2 → 38.8 [5] | LLM-as-judge 自评（准确率 72.7%） |
| 工作流 | AWM [17] | 可复用的操作流程（workflow） | LLM 从轨迹归纳 | 离线（训练集）或在线（测试流）归纳，无单独门控 | 选择性提供 | 相对提升：Mind2Web 24.6%，WebArena 51.1% [17] | 在线版本用模型自评 [推断，待核] |
| 代码技能库 | Voyager [18] | 可执行 JS 函数 | GPT-4 | 自我验证（critic 判断任务是否完成）+ 执行报错反馈，验证通过才入库 | 嵌入检索；技能可组合 | 独特物品 3.3 倍、科技树里程碑最多快 15.3 倍 [18] | 环境状态 + 自评 |
| 代码技能库 | SkillWeaver [19] | 网站操作 API | agent 自主探索、练习、提炼 | 练习执行后提炼（具体测试方式见原文 [待核]） | — | WebArena 相对 +31.8%；强 agent 的 API 给弱 agent 用最多 +54.3% [19] | 自生成任务 + 自评 |
| 代码技能库（2026） | Skill-V [8] | 版本化、可证伪的技能契约 | 失败时新增，契约与结果不一致时修订边界 | 修订须保留受保护约束，且在历史回放上不降低指标 | 过滤“明确不适用”的技能；库更紧凑 | ALFWorld 95.3%，WebShop 85.9% [8] | 环境结果 |
| 代码技能库（2026） | SkillBoost [9] | 技能文档中可编辑的组件 | 把失败定位到组件，再生成多样修复 | “有提升且回退不超过界限”才提交 | 防止对当前批次过拟合 | 23 个模型–基准组合上称最优（具体数字未见）[9] | 任务结果 |
| 代码技能库（2026） | SkillOS [20]、MUSE-Autoskill [21] | SKILL.md 包 / 技能仓库 | 可训练的 curator（RL）或 Skill Creator | SkillOS 用后续相关任务的成败作为 curator 奖励 | 仓库逐渐形成“元技能” | 摘要无具体数字 [20] | 任务成败 |
| 整个 agent | DGM [3] | agent 自身代码库 | 基础模型提出修改 | 在编码基准上分阶段评估（SWE-bench：60 题 → 200 题）；保存全部变体的存档 | 存档 + 开放式选择 | SWE-bench 20.0% → 50.0%；单次运行约 $22,000 [3] | 基准测试（真值） |
| 整个 agent | SICA [22] | agent 自身代码 | agent 自己 | 基准测试 | — | SWE-Bench Verified 随机子集 17% → 53% [22] | 基准测试 |
| 代码 / 算法进化 | AlphaEvolve [23] | 程序代码 | LLM 集成 + 进化算法 | 一个或多个自动评估器打分 | 进化数据库 | 4×4 复矩阵乘法 48 次标量乘法 [23] | 自动评估器（必须可机器计算） |
| 通用记忆 | MemGPT/Letta [24]、A-Mem [25]、Mem0 [26] | 事实 / 笔记 / 对话片段 | LLM | 无效果验证，只做存取 | 分层存储、链接、合并 | Mem0：LOCOMO 上比 OpenAI 记忆 LLM 评判分高 26%，p95 延迟低 91% [26] | 对话内容，不涉及任务成败 |

综述：Self-Evolving Agents survey（arXiv 2507.21046）已核实存在，作者 Gao 等 27 人，v4 于 2026-01 修订，已被 TMLR 接收；按“演化什么、何时演化、如何演化”组织文献 [27]。2026 年另有两篇综述：Dynamic Agent Skills（TMLR 2026，124 篇文献）[10] 和 Self-Improvements in Modern Agentic Systems（Schmidhuber 等，97 页）[28]。

### 2. 规则 / playbook 类

**ACE [1]**（ICLR 2026）
- 三个角色：Generator 产生轨迹，Reflector 从成功和错误中提炼洞见，Curator 把洞见变成 delta 条目。
- 条目格式：唯一 ID + helpful/harmful 计数 + 内容（策略、领域概念或失败模式）。
- delta 由确定性、非 LLM 的逻辑合并进上下文，避免整体重写，也能并行合并。
- “grow-and-refine”：新条目追加，旧条目原位更新，用语义嵌入去重；可每次更新后做，也可在超出窗口时惰性做。
- 上下文坍缩的实例：Dynamic Cheatsheet 在 AppWorld 上一步把上下文从 18,282 token 压缩到 122 token，准确率 66.7 → 57.1，低于 63.7 的基线。
- 消融（AppWorld 离线）：去掉 Reflector 和多轮 epoch 为 +12.7，只去掉多轮 epoch 为 +14.4，完整为 +17.0；在线学习有离线预热时 +17.1，无预热时 +13.7。
- 无标签时：AppWorld 离线仍 +14.8；金融任务离线 +8.0（有标签 +12.8），在线 +3.8（有标签 +7.5）；在线无标签时 FiNER 下降 3.4，Dynamic Cheatsheet 下降 3.7。作者明确说 Reflector 弱时会产生有害上下文。
- 成本：AppWorld 离线比 GEPA 少 75.1% rollout、少 82.3% 延迟。

**Dynamic Cheatsheet [11]**
- 两个变体：DC-Cu（先答后更新，无检索）和 DC-RS（检索 3 个相似历史问答对，先更新后答）。
- 不用真值，模型自判。
- 记录到的失败：小模型（GPT-4o-mini、Claude 3.5 Haiku）收益小，GPT-4o-mini 在 GPQA-Diamond 上 34.3 → 32.3；GPT-4o 在 MMLU-Pro Engineering 上 53.2 → 51.2；作者原话指出“混入记忆的错误启发式同样会被放大”。
- 收益集中在“发现一段可复用代码”就能解决的任务（Game of 24：10% → 99%，方程配平 50% → 99.2%）。这提示**能写成代码的经验比文字规则收益更大、更稳**（推断）。

**ExpeL [12]**（AAAI 2024）
- 比较同一任务的失败与成功轨迹，或比较多条成功轨迹（HotpotQA、ALFWorld 用 L=8 条，WebShop 用 4 条）。
- 操作：ADD（新洞见计数为 2）、EDIT（改写并加计数）、UPVOTE、DOWNVOTE；计数降到 0 即删除。作者的理由是“成功轨迹也可能不是最优”，投票机制使规则集更稳健。
- 只用洞见 vs 只用检索：HotpotQA 36% vs 31%，ALFWorld 50% vs 55%，两者结合最好。

**Training-Free GRPO [13]**
- 每个问题做一组 rollout（数学 5 条，网页搜索 3 条），LLM 比较组内好坏得到“语义优势”，据此增删改经验库。
- 规模很小：100 个训练样本、3 个 epoch，DeepSeek-V3.1-Terminus 上学习成本约 $18。
- 收益小但为正：AIME24 80.0 → 82.7，AIME25 67.9 → 73.3；WebWalkerQA 63.2 → 67.8。
- 不用真值的消融：AIME25 68.9（仍高于 67.9 基线，低于有真值的 73.3）；不分组（组大小 1）为 69.3。
- QwQ-32B 上 pass@1 反而 27.5 → 25.5。
- 只报告一次学习运行，没有多种子方差（据所读内容）。

**RBC [2]**（arXiv 2610.18427，2026-10，已核实）详见第 11 号文件，这里只列与记忆结构有关的部分：
- 用 all-mpnet-base-v2 嵌入 + Ward 聚类把教训分为 m=8 块；有害块含 6–21 条教训。
- 块数影响不大：m=4/8/16 时为 45.9/47.4/48.0。
- 保留预算 40% token 优于 20% 和 60%（46.1/47.4/46.1）。
- 整本重写型记忆（如 Dynamic Cheatsheet）难以拆成独立的块，RBC 只能退回到“选最好的整本”，因此**条目化、可拆分的记忆格式是后续能做消融和整理的前提**。

### 3. 提示词优化类

**GEPA [7]**（ICLR 2026 oral）
- 反馈函数返回分数 + 文字反馈（如编译错误、未通过的评分项），可以按模块给。
- 接受规则：子代在 minibatch 上的平均分须高于父代，接受后再在 D_pareto 上评分入池。
- Pareto 选父代优于贪心选最优：Qwen3 8B 上总分 61.28 vs 54.89（贪心）vs 53.95（束搜索）。意义：保留“在某些实例上最好”的候选，避免过早收敛。
- 预算：Qwen3 8B 上每个任务总 rollout 1,839–7,051，其中**大部分花在验证上**，真正用于学习的只有 79–737 次。
- Merge 效果不稳定（Qwen3 8B 总分 54.85 → 52.40）。
- 对本项目的含义：GEPA 的“minibatch 先筛、再上验证集”和“Pareto 候选池”值得借鉴；整体流程的 rollout 量对 $0.5/事件 的 agent 太贵。

**MIPROv2 [14] 与 TextGrad [15]**：都需要带真值的训练集和大量调用 [未打开原文]，适用于固定流水线而非长程 agent。本项目不建议作为主方法。

### 4. 经验 / 洞见类（含失败经验）

**Reflexion [16]**：在同一任务内重试时用文字反思，HumanEval pass@1 91%。这对应本项目的“事件内循环”（残差大 → 重拾 → 重定位），而不是跨事件学习。

**ReasoningBank [5]**（ICLR 2026）
- 记忆条目 = 标题 + 一句话描述 + 内容；每条轨迹最多提炼 3 条；嵌入检索 top-1；整合方式是简单追加。
- 成败由 LLM 评判，无真值；评判准确率 72.7%；模拟 70–90% 准确率时成功率相近，完美标签最好。
- 加入失败经验：WebArena-Shopping 上 ReasoningBank 46.5 → 49.7，而 AWM 加入失败经验反而 44.4 → 42.2。说明**失败经验要提炼成“教训”，不能当示范直接复用**。
- MaTTS（每个任务多次 rollout 后对比提炼）：Best-of-5 从 49.7 到 55.1。
- 注意：第 11 号文件中的 Fragility 研究在 WebArena 上复评 ReasoningBank，默认顺序下 +1.5（p=0.23，3 次运行），打乱顺序后低于无记忆基线 [29]。

**Xiong 等（经验跟随与错误传播）[4]**：见结论摘要；另外，基于历史表现的删除使 EHRAgent 38.67 → 42.06、CIC-IoT 85.40 → 89.60，同时记忆量减少。

### 5. 工作流类

**AWM [17]**（ICML 2025）：从轨迹中归纳常用操作流程，离线或在线提供给 agent；Mind2Web 相对 +24.6%，WebArena 相对 +51.1%，并减少步数。本项目的“README / 流程”就是一份工作流记忆。地震分析的步骤序列（看全图 → 放大 → 拾取 → 定位 → 查残差 → 重拾）相对固定，归纳空间有限，**流程层应基本手写、少改**（推断）。

### 6. 代码技能库类

- **Voyager [18]**：技能是可执行代码；先自我验证再入库；按描述嵌入检索；可组合。
- **SkillWeaver [19]**：agent 自己探索网站、练习、提炼成 API；强模型写的 API 能帮弱模型（最多 +54.3%）。对本项目的意义：GPT 写的代码技能可以直接给开源模型用，这与设计稿 §8 的分级处理一致（推断）。
- **Agent Skills / SKILL.md [30]**（Anthropic，2025-10-16）：技能是一个目录，SKILL.md 含 YAML 头（name、description）和正文，可附脚本；渐进加载（先只加载名称和描述，相关时再读正文和附件）；建议“从评估出发”，先找到 agent 的薄弱处再写技能。
- **Skill-V [8]**（2026-10）：技能写成“意图 → 可观测行为标准”的契约，带版本；契约评估与任务结果不一致时修订适用边界；修订不得降低历史回放上的指标。
- **SkillBoost [9]**（2026-07）：指出把技能当可训练参数会过拟合当前批次、造成已解决案例回退；用“验证接受 + 回退上限”约束。
- **Dynamic Agent Skills 综述 [10]**：八阶段生命周期（证据获取、提议、验证/准入、存储、检索/组合、维护、蒸馏/迁移、治理）；平铺检索随库增大而变差；验证器质量对技能学习影响很大。
- **视觉 / GUI 记忆（2026）**：HyMEM（文字洞见 + 视觉嵌入的图记忆）、AutoMMemo（学习多模态经验的记忆设计）等 [只见检索摘要，未打开原文]。没有找到针对“看波形图”这类科学图像任务的记忆研究（未找到）。

**地震领域的同类实例：FA-Agent [31]**（arXiv 2611.06555，2026-11）有技能库和专家复核案例库，经专家复核的案例自动写入技能；摘要没有给出学习曲线或前后对比。

### 7. 整个 agent / 自修改代码

- **DGM [3]**：每次迭代生成一个新 agent，共 80 次；分阶段评估（Polyglot：10 题达 40% 才上 50 题；SWE-bench：60 题达 40% 且排名前二才上 200 题）；单次 SWE-bench 运行约 $22,000，基线约 $10,000。作者讨论了“硬编码答案”的风险，称未观察到；关于“删除幻觉检测标记来刷分”的说法未在所读部分找到 [待核]。
- **SICA [22]**：17% → 53%（SWE-Bench Verified 随机子集）。
- **AlphaEvolve [23]**：核心前提是“有可自动计算的评估器”。

对本项目：整个 agent 自修改不现实；但 **AlphaEvolve 的思路适用于单个代码技能**——例如 AIC 精修、偏振滤波参数选择等纯函数，可以在半合成数据（T3）上用确定性指标评估，不需要调用 LLM，评估几乎免费（推断）。

### 8. 通用记忆系统

MemGPT/Letta [24]、A-Mem [25]、Mem0 [26] 解决的是“存什么、怎么取”，目标是对话一致性，不验证记忆对任务的效果。Fragility 研究中基于 Letta Code 的自我改进方法在 EnterpriseOps-Gym 上没有稳定收益（GPT-OSS-120B 24.5 → 22.3）[29]。本项目事件数少（几百），记忆总量小，不需要这类检索基础设施。

### 9. 膨胀与坍缩的处理方式汇总

| 机制 | 来源 | 实测效果 |
|---|---|---|
| 增量 delta + 确定性合并，不整体重写 | ACE [1] | 避免 18,282 → 122 token 式坍缩 |
| 语义嵌入去重 | ACE [1] | 未单独量化 |
| 投票计数，归零删除 | ExpeL [12] | 未单独量化 |
| 质量筛选后再加入 + 按历史表现删除 | Xiong 等 [4] | 加入全部经验低于固定记忆；严格筛选 + 删除最好，记忆量减少 |
| 随机分组消融 + token 预算 40% | RBC [2] | 平均服务 token 为整本的 60%，成功率 +11.4（相对整本） |
| 批量反思 | Agent-ToM [6] | 批量 8 时规则 155 → 89 条，字数 22,860 → 14,032 |
| 渐进加载（只先加载名称和描述） | Agent Skills [30] | 未量化 |
| 技能适用性过滤 | Skill-V [8] | 库更紧凑（数字未见） |

### 10. 哪些设计适合本项目的条件

| 条件 | 适合 | 不适合 | 理由 |
|---|---|---|---|
| episode 贵（$0.5–0.75/事件） | ACE 式条目 + 批量反思；代码技能用离线测试 | GEPA 全流程（1,839–7,051 rollout/任务 [7]）；DGM（$22k/次 [3]）；MaTTS 每任务 5 次 rollout [5] | 反思约 $0.07/次，便宜；评估 episode 贵 |
| 练习事件少（几十到几百） | Training-Free GRPO 规模（100 样本 [13]）；RBC 1/4 练习轮（约 150 episode）仍保留大部分收益（8.9 vs 10.8 分）[2] | 依赖上千 episode 的生长（ALFWorld 2,500 [2]） | — |
| 看图用工具 | 文字规则 + 代码技能（绘图、滤波、旋转、AIC） | 存图片的检索记忆 | 存图会增加视觉 token；没有证据表明图像记忆对科学图更有效（未找到） |
| 反馈有噪声（残差、有时用标签） | 严格准入、投票计数、多事件证据门槛、门控、多候选选择 | 不筛选的追加（add-all）[4]；agent 自判去留 [2] | ACE 无标签时可能下降 [1]；自判与实测相关仅 0.21 [2] |

## 对本项目的影响

### 推荐的记忆结构（沿用试点的 README / playbook / skills 三件套，并加以规范）

| 层 | 文件 | 内容与格式 | 借鉴自 | 如何改动 |
|---|---|---|---|---|
| L0 流程 | `README.md` | 固定的步骤序列与工具调用顺序，手写为主 | AWM [17] | 很少改；改动必须经门控 |
| L1 规则 | `playbook.yaml`（渲染成 markdown 给模型看） | 每条：`id`、`block`（主题块，如 P 起始 / S 起始 / 极性 / 残差重拾 / 滤波 / 台站类型 / 震中距 / 通用）、`when`（适用条件：震相、震中距区间、信噪比、起始类型、仪器类型）、`do`（动作）、`expect`（预期影响的指标）、`evidence`（支持事件数、批次号，不含事件 ID）、`helpful`/`harmful` 计数、`status`（候选 / 生效 / 退役）、`since`（版本） | ACE 条目格式 [1]；ExpeL 投票 [12]；RBC 的块结构 [2] | 只允许 ADD / MODIFY / MERGE / RETIRE 的 delta，由脚本确定性合并 |
| L2 代码技能 | `skills/<name>/SKILL.md` + `*.py` + `test_*.py` | SKILL.md 头含 `name`、`description`、`when_to_use`、`contract`（可观测的预期行为，如“在 T3 半合成数据上 AIC 精修后中位误差不大于输入”） | Agent Skills [30]；Voyager [18]；Skill-V 契约 [8] | 必须通过单元测试 + 半合成回放；参数类改动可以用 AlphaEvolve 式离线搜索 [23] |
| L3 案例（可选，默认关闭） | `cases/` | 少量经严格筛选的对照案例（成功 / 失败成对，文字描述，不存图） | ExpeL 成败对比 [12]；ReasoningBank 失败教训 [5] | 只收录有分析员标签或物理分数非常确定的案例；作为消融组单独测试 |

规模上限：L1 不超过约 40 条、3k token（与设计稿一致）；8 个块，便于 RBC 式消融。L2 只把名称和描述放进系统提示，正文按需读取。

### 推荐的更新协议

1. **记录**：每个练习事件结束后，harness 生成结构化记录（拾取、残差、工具调用、决策理由、所用规则 ID）。所用规则 ID 用于更新 helpful/harmful 计数（ACE [1]、ExpeL [12]）。计数只作为参考，**不能作为删除依据**，因为 RBC 发现这类自评与实测效果几乎不相关 [2]。
2. **批量反思**：每 B=10–20 个事件反思一次（Agent-ToM 显示批量 4–8 已足够 [6]；设计稿的 20–25 也可以，但练习事件只有 200 时只能反思 8–10 次，可能太少）。反思输入是汇总误差表 + 3–5 对对照案例（同一类拾取中做对和做错的，借鉴 ExpeL [12] 和 Training-Free GRPO 的组内比较 [13]）。
3. **证据门槛**：新规则至少有本批 3 个事件支持（设计稿已有）；物理反馈组额外要求覆盖度指标不变差。
4. **delta 合并**：Curator 只能输出 delta，脚本合并并做嵌入去重（ACE [1]）。新规则先进入“候选”状态。
5. **代码技能另走一条路**：新增或修改的函数先过单元测试、再过半合成回放（确定性、几乎免费），最后过 10 事件回归。这一步不用门控集，节省门控预算。
6. **分阶段门控**（DGM [3] + GEPA minibatch [7]）：候选版本先在 20 个门控事件上跑，明显变差就直接拒绝；通过后再跑完整门控集。门控的统计细节见第 11 号文件。
7. **版本与选择**：每个接受的版本打 git tag；最终使用的记忆从“空记忆 / 专家 playbook / 各次生长的最终版 / 整理版”中，在**未参与门控的新事件**上选（RBC 的 Best-Full 和 RBC 候选集 [2]）。
8. **整理**：在学习结束后做一次 RBC 式块消融，而不是每 5 批做一次（理由和样本量见第 11 号文件）。

### 要避免的做法

- 整体重写 README 或 playbook（ACE 记录的坍缩 [1]）。
- 让 agent 自己决定删除哪些规则（RBC：自选 53.8 ≤ 整本 55.5 [2]）。
- 把所有事件经验直接加入检索库（Xiong：add-all 在每个任务上都低于固定记忆 [4]）。
- 在记忆中存图片或事件特定的答案（成本高；且有泄漏风险）。

### 建议增加的实验或对照

- **“写进初始提示词”对照**：试点中 after_0 到 after_5 的提升基本来自一条规则。把学到的最终 playbook 当成固定提示词（不再学习）跑一遍，区分“学习过程有用”和“这几条规则有用”。这与设计稿的 A-expert 不同。
- **代码技能 vs 文字规则消融**：只开 L1、只开 L2、两者都开。Dynamic Cheatsheet 的结果提示代码化经验的收益更大 [11]，值得验证。
- **记忆迁移**：GPT 学到的 playbook 和技能直接给开源模型用（SkillWeaver 的强到弱迁移 [19]）。

## 未解决与待核

- ACE 在线学习的批量大小设置和对应消融（检索摘要称批量为 1，未在原文中确认）。
- SkillWeaver 的 API 验证方式、AWM 在线版的成败判断方式 [待核]。
- DGM 是否出现过“删除检测标记刷分”的情况（未在所读部分找到）[待核]。
- SkillBoost 的回退上限和具体收益数字（摘要未给）。
- 是否有针对科学图像（波形、谱图）任务的记忆研究：本轮未找到。
- MIPROv2、TextGrad、MemGPT 的细节未打开原文。
- 需要试点数据才能回答：每条规则对 P/S 指标的效应量有多大；如果大多数规则效应 < 2 个百分点，任何门控都难以分辨，需要按块而不是按条评估。

## 参考文献

1. Zhang, Q., Hu, C., Upasani, S., et al. (2025/2026). Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models. ICLR 2026. https://arxiv.org/abs/2510.04618 [已读原文]
2. Pham, H., Nguyen, C.-D., Le, D., Srey, P., Luu, A. T. (2026). Reliable Memory from Unstable Growth: Curating Self-Written Agent Playbooks with Randomized Experiments. arXiv:2610.18427. https://arxiv.org/abs/2610.18427 [已读原文]
3. Zhang, J., Hu, S., Lu, C., Lange, R., Clune, J. (2025). Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents. arXiv:2505.22954 (v3 2026-03). https://arxiv.org/abs/2505.22954 [已读原文，部分附录未读到]
4. Xiong, Z., Xiang, Z., Lin, Y., et al. (2025). How Memory Management Impacts LLM Agents: An Empirical Study of Experience-Following Behavior. arXiv:2505.16067. https://arxiv.org/abs/2505.16067 [已读原文]
5. Ouyang, S., Yan, J., Hsu, I-H., et al. (2025). ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory. ICLR 2026. https://arxiv.org/abs/2509.25140 [已读原文]
6. Ahmed, N. K., Nafisi, N. (2026). Agent-ToM: Learning to Monitor Autonomous LLM Agents via Theory-of-Mind Reasoning. arXiv:2605.24216. https://arxiv.org/abs/2605.24216 [已读原文，仅批量消融表]
7. Agrawal, L. A., Tan, S., Soylu, D., et al. (2025). GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning. ICLR 2026 (oral). https://arxiv.org/abs/2507.19457 [已读原文]
8. Ma, J., Qian, Z., Ma, Y., et al. (2026). Skill-V: Verifiable Self-Evolving Skill Library for Interactive Agents. arXiv:2610.11781. https://arxiv.org/abs/2610.11781 [只读摘要]
9. Lin, H., Liu, C., Bai, X., et al. (2026). Rethinking Self-Evolution: A Constrained Exploration-Exploitation Process for Mitigating Skill Overfitting. arXiv:2607.26643. https://arxiv.org/abs/2607.26643 [只读摘要]
10. Li, Y. (2026). Dynamic Agent Skills: A Lifecycle Survey and Taxonomy of Evolving Skill Libraries. TMLR 2026. https://arxiv.org/abs/2607.10113 [只读摘要]
11. Suzgun, M., Yuksekgonul, M., Bianchi, F., Jurafsky, D., Zou, J. (2025). Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory. arXiv:2504.07952. https://arxiv.org/abs/2504.07952 [已读原文]
12. Zhao, A., Huang, D., Xu, Q., Lin, M., Liu, Y.-J., Huang, G. (2024). ExpeL: LLM Agents Are Experiential Learners. AAAI 2024. https://arxiv.org/abs/2308.10144 [已读原文]
13. Cai, Y., Cai, S., Shi, Y., et al. (2025). Training-Free Group Relative Policy Optimization. arXiv:2510.08191. https://arxiv.org/abs/2510.08191 [已读原文]
14. Opsahl-Ong, K., et al. (2024). Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs (MIPROv2). EMNLP 2024. https://arxiv.org/abs/2406.11695 [未打开原文]
15. Yuksekgonul, M., et al. (2024/2025). TextGrad: Automatic "Differentiation" via Text. https://arxiv.org/abs/2406.07496 [未打开原文]
16. Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., Yao, S. (2023). Reflexion: Language Agents with Verbal Reinforcement Learning. NeurIPS 2023. https://arxiv.org/abs/2303.11366 [只读摘要]
17. Wang, Z. Z., Mao, J., Fried, D., Neubig, G. (2025). Agent Workflow Memory. ICML 2025, PMLR 267:63897–63911. https://proceedings.mlr.press/v267/wang25bx.html [只读摘要]
18. Wang, G., Xie, Y., Jiang, Y., et al. (2023). Voyager: An Open-Ended Embodied Agent with Large Language Models. https://arxiv.org/abs/2305.16291 [只读摘要]
19. Zheng, B., Fatemi, M. Y., Jin, X., et al. (2025). SkillWeaver: Web Agents can Self-Improve by Discovering and Honing Skills. https://arxiv.org/abs/2504.07079 [只读摘要]
20. Ouyang, S., Yan, J., Chen, Y., et al. (2026). SkillOS: Learning Skill Curation for Self-Evolving Agents. arXiv:2605.06614. https://arxiv.org/abs/2605.06614 [只读摘要]
21. MUSE-Autoskill: Self-Evolving Agents via Skill Creation, Memory, Management, and Evaluation (2026). arXiv:2605.27366. https://arxiv.org/abs/2605.27366 [未打开原文，仅检索摘要]
22. Robeyns, M., Szummer, M., Aitchison, L. (2025). A Self-Improving Coding Agent. arXiv:2504.15228. https://arxiv.org/abs/2504.15228 [只读摘要]
23. Novikov, A., et al. (2025). AlphaEvolve: A coding agent for scientific and algorithmic discovery. arXiv:2506.13131. https://arxiv.org/abs/2506.13131 [只读摘要]
24. Packer, C., et al. (2023). MemGPT: Towards LLMs as Operating Systems. https://arxiv.org/abs/2310.08560 [未打开原文]
25. Xu, W., Liang, Z., Mei, K., Gao, H., Tan, J., Zhang, Y. (2025). A-MEM: Agentic Memory for LLM Agents. NeurIPS 2025. https://arxiv.org/abs/2502.12110 [只读摘要]
26. Chhikara, P., Khant, D., Aryan, S., Singh, T., Yadav, D. (2025). Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory. https://arxiv.org/abs/2504.19413 [只读摘要]
27. Gao, H., Geng, J., Hua, W., et al. (2025/2026). A Survey of Self-Evolving Agents: What, When, How, and Where to Evolve on the Path to Artificial Super Intelligence. TMLR 2026. https://arxiv.org/abs/2507.21046 [只读摘要]
28. Ren, Z., Chen, Y., Guo, D., et al. (2026). Self-Improvements in Modern Agentic Systems: A Survey. arXiv:2607.13104. https://arxiv.org/abs/2607.13104 [只读摘要]
29. Ye, Q., Li, Y., Pruksachatkun, Y., Zhang, J., Wu, C.-S. (2026). On the Fragility of Self-Improving Agents: Variance, Task Order, and Underspecification. arXiv:2608.18066. https://arxiv.org/abs/2608.18066 [已读原文]
30. Anthropic (2025-10-16). Equipping agents for the real world with Agent Skills. https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills [已读原文]
31. Li, W., Yuan, C. (2026). FA-Agent: An extensible multimodal agent framework for first-arrival picking in mountainous seismic data. arXiv:2611.06555. https://arxiv.org/abs/2611.06555 [只读摘要]
