# 11. 自我改进的不稳定性

## 要回答的问题

- 自我改进 / 持续学习的 LLM agent 在方差、顺序敏感性、退化 / 遗忘和刷分（reward hacking）方面有哪些证据？（例如 "On the Fragility of Self-Improving Agents" arXiv 2608.18066，需核实；"Reliable Memory from Unstable Growth" / RBC arXiv 2610.18427，需核实；记忆污染 / 错误传播研究；测试时学习基准。）
- 缓解办法：在留出集上门控接受、回滚 / 版本管理、整合 / 剪枝（规则组的随机子集消融）、批量反思、最低证据门槛；它们的实测效果如何？
- 通常需要多少个种子 / 顺序、多少个练习 episode，才能令人信服地展示学习效应？

影响的决定：门控协议；种子和顺序的数量。

## 结论摘要

- **两篇关键文献都真实存在，结论与设计稿的引用一致，但细节更严峻。** Fragility（Ye 等，Salesforce，2026-08）在 WebArena 上复评 AWM 和 ReasoningBank（GPT-5-mini，3 次运行 × 3 种顺序）：默认顺序下 ReasoningBank 只 +1.5（54.8 → 56.3，p=0.23；扩到 6 次运行 p=0.07，仍不显著）；打乱顺序后两种方法都低于无记忆基线，平均 −4.5；24 个情形中 17 个记忆方法增大了方差 [1]。RBC（Pham 等，2026-10）发现同一流程的 3 次生长可得 82.5 / 58.9 / 30.0 这样差异巨大的结果，最坏比无记忆低 69.6 分；11 个 ACE 设置的第一次生长中 5 个有益、2 个持平、4 个有害 [2]。
- **最有效的单一缓解手段是“多候选 + 保留空记忆 + 在新 episode 上选择”。** RBC 中这种 Best-Full 选择达 66.4，完整的随机分组整理 RBC 为 66.9，整本 playbook 55.5，无 playbook 54.1，agent 自判整理 53.8；RBC 在 ACE 上从未比无记忆低超过 0.8 分 [2]。整理（剪枝）的额外贡献约 0.5 分，主要价值是把服务的 token 降到 60%。
- **对“补充任务说明”的缓解效果有限。** Fragility 在打乱顺序下加入评分细则、环境反馈和提示修改，WebArena 49.8 → 52.7，只弥补了约 31% 的退化 [1]。按历史表现删除记忆、只加入严格筛选的经验有明确收益（Xiong：EHRAgent 加入全部 13.05 vs 严格筛选 38.50）[3]；批量反思 1 → 4 使 F1 +0.017、规则数减少三分之一 [4]。
- **最低证据门槛、整体回滚等手段几乎没有单独的实测数据（未找到）。** 只有 ExpeL 的投票删除 [5]、Skill-V 的“历史回放不退步” [6]、SkillBoost 的“回退上限” [7] 作为设计组成部分出现，没有单独消融。
- **刷分和错误传播都有实证。** 记忆会把错误回放并放大（“经验跟随”，Xiong [3]；Fragility 中一条错误的“Haversine 公式”后备方案被越来越多地检索 [1]）；Misevolve（ICLR 2026）报告记忆积累后安全对齐下降、部署时刷分 [8]；反馈回路会导致上下文内刷分（Pan 等，ICML 2024）[9]。物理残差反馈尤其容易被“少拾、丢难拾”刷分。
- **种子和顺序：文献常用 3 次运行，但这不够。** Fragility 明说 n=3 可能低估方差，并只用了 3 种顺序 [1]；RBC 用 3 次生长 × 3 个评估种子 [2]；ACE、Dynamic Cheatsheet、ReasoningBank、Training-Free GRPO 都只报告单次学习运行（据所读内容）。按 t 检验粗算（推断）：若学习效应约等于 1.5 倍“运行间标准差”，每组 3 次运行的检验功效只有约 0.3，6 次约 0.65，9 次约 0.85。**主要比较（物理反馈 vs 无记忆 / 安慰剂）每组至少 6 次独立学习运行（例如 3 种顺序 × 2 个种子），条件允许时 9 次。**
- **设计稿的门控协议有三个问题（推断）：** (1) 每批都要求“主指标 90% 置信区间下界 > 0”，80 个门控事件只能分辨约 2.5–3.5 个百分点的差异，单批规则的效应通常更小，学习可能停滞；(2) §8.3 预算中每条学习流约 400 次门控运行，但 8–10 次门控决策 × 每次约 160–320 次运行需要 1,300–3,200 次，门控成本被低估 3–8 倍；(3) “每 5 批整理一次、用 150 个事件”在只有 200 个练习事件时最多做 1–2 次，且 RBC 是在练习轮 600–684 个 episode 上做的。

## 详细发现

### 1. 方差与顺序敏感性

**Fragility of Self-Improving Agents [1]**（arXiv 2608.18066，Ye, Li, Pruksachatkun, Zhang, Wu；2026-08-18 提交，09-06 修订；已核实）

| 项目 | 内容 |
|---|---|
| 被复评的方法 | Agent Workflow Memory（AWM）、ReasoningBank（RBank）；附录另有基于 Letta Code 的方法 |
| 基准 | WebArena、VisualWebArena、SCUBA（267 个有效任务）；附录 EnterpriseOps-Gym |
| 主模型 | GPT-5-mini（另测 GPT-OSS-120B、Gemini-2.5-Pro、GPT-5.4-mini） |
| 设计 | 每个设置 3 次相同的自我改进运行；默认顺序 + 两种打乱顺序 |
| 方差 | 24 个情形中 17 个（约 71%）记忆方法增大了方差；最好与最差运行之差最多约 10 个百分点；标准差最大 3.9；WebArena GitLab 上无记忆的极差 4.4，RBank 7.8 |
| 默认顺序 | RBank +1.5（54.8 → 56.3），Welch t 检验 p=0.23 |
| 扩到 6 次运行 | 总体 54.2 vs 55.6，p=0.07；Shopping 域 RBank 的极差从 3.21 扩大到 8.02；6 个域中 5 个 RBank 的标准差大于基线 |
| 打乱顺序 | WebArena 上 AWM 49.1 / 49.8，RBank 49.8 / 50.7，均低于无记忆 54.8；平均 −4.5 |
| 其他模型 | GPT-OSS-120B：无记忆 40.6，RBank 默认顺序 40.5，打乱 37.0；Gemini-2.5-Pro：49.0 / 51.0 / 48.0 |
| 其他方法 | Letta Code 方法在 EnterpriseOps-Gym 上：GPT-OSS-120B 24.5 → 22.3，GPT-5.4-mini 30.5 → 29.7；16 个情形中 10 个方差增大，drive 域极差 4.7 → 14.1 |
| 原因分析 | 默认顺序相当于隐含的课程；任务和环境说明不足：记忆中反复推荐环境并不支持的 API（WebArena 3 次运行中 “user confirmation” 出现 26 次）；歧义任务导致误读；“传染”：一条 Haversine 公式后备方案被强化、检索次数随时间增加 |
| 缓解 | 加评分细则、环境反馈、改提示词：Shuffle-1 上 49.8 → 52.7（+2.9），Shuffle-2 +1.1；弥补约 31% 的退化，剩下 69% |
| 建议 | 报告多次运行的统计量和随机顺序；单次运行结果需谨慎解读；n=3 可能低估真实波动；没有给出具体的最少次数 |

**RBC [2]**（arXiv 2610.18427，Pham, Nguyen, Le, Srey, Luu；2026-10-13；已核实）
- 生长阶段：ACE（只增不删，Reflector 标记 helpful/harmful）和 Dynamic Cheatsheet（每批整体重写）。模型为 Qwen3.8-27B、Qwen3.5-9B、Gemma-4-31B（关闭思考）；基准为 AppWorld、WebShop、ALFWorld。
- 同一流程的生长差异巨大：27B AppWorld（逐测试反馈）三次生长得 82.5 / 58.9 / 30.0；27B AppWorld（通过 / 失败反馈）三本整 playbook 得 31.2 / 17.7 / 8.7，而无 playbook 为 78.4。
- 11 个 ACE 设置的第一次生长：5 个有益、2 个持平、4 个有害（有害定义为低于无记忆 5 分以上；重复评估的波动最多 5.0 分）。
- agent 自判不可靠：ACE 标记与实测块效应的秩相关 0.21（81 个块）；自判剪枝 50.9 vs 整本 51.2（ACE），58.9 vs 61.3（Dynamic Cheatsheet）。

**其他**
- **PATH-Bench [10]**（arXiv 2608.01149，2026-08）：专门度量经验顺序对终身 agent 的影响，8 个 agent；结论包括“强迁移不保证保留”“后来的经验可以改变早先的收益”；提出选择性使用经验（SEU）减少遗忘 [只读摘要，无具体数字]。
- **Evo-Memory [11]**（arXiv 2511.20857，Google 等，v2 2026-05）：把 10 个数据集改成任务流的测试时学习基准，实现了 10 多种记忆模块 [只读摘要，未取得数字]。

### 2. 退化与遗忘

| 证据 | 内容 | 来源 |
|---|---|---|
| 学习后低于无记忆 | Fragility 打乱顺序后 −4.5；RBC 最坏 −69.6；Letta Code 方法在两个模型上都下降 | [1][2] |
| 上下文坍缩 | Dynamic Cheatsheet 在 AppWorld 上一步从 18,282 token 压到 122 token，66.7 → 57.1（基线 63.7） | ACE [12] |
| 无可靠反馈时下降 | ACE 在线无标签：FiNER −3.4；Dynamic Cheatsheet −3.7 | [12] |
| 小模型或弱反思者 | Dynamic Cheatsheet 在 GPT-4o-mini 上 GPQA 34.3 → 32.3；GPT-4o 在 MMLU-Pro Engineering 53.2 → 51.2 | [13] |
| 能力侵蚀 | “Do Self-Evolving Agents Forget?”：工作流、技能、模型、记忆四个通道都出现对已有能力的侵蚀；其 CPE 方法在 GPT-5.1 工作流进化中把保留的简单任务成绩从 41.8% 提到 52.8% | [14] |
| 本项目试点 | after_9 加入一条更严格的 S 拾取准入规则，S recall 从 after_5 的 96% 降到 78%，0.1 s 内命中率从 65% 降到 59% | 试点总结 |

### 3. 错误传播、记忆污染与刷分

- **经验跟随与错误传播（Xiong 等 [3]）**：检索到的记录与当前任务越相似，输出越相似（RegAgent 中相关系数约 1）。错误记录会被复制并放大；加入全部经验在 4 个 agent 上都低于固定记忆（RegAgent 67.53 → 55.48，EHRAgent 16.75 → 13.05，AgentDriver 40.11 → 32.32，CIC-IoT 71.50 → 59.90）。用真值严格筛选最好（38.50 / 51.00 / 85.40）；用 300 条正确判断微调的 LLM 评判（C3）接近严格筛选；未微调的 LLM 评判（C1）明显较差。
- **ReasoningBank 的评判噪声 [15]**：LLM 评判准确率 72.7%；模拟 70–90% 准确率时结果相近，完美标签最好。
- **对抗性记忆投毒**：MINJA 只通过查询就能让 agent 自己写入恶意记录，注入成功率 > 95% [16]；AgentPoison 平均攻击成功率 > 80% [17]。本项目没有对抗者，但**分析员标签错误、残差中的速度模型误差**起着类似“毒化”的作用（推断）。
- **Misevolve [8]**（Shao 等，ICLR 2026）：在模型、记忆、工具、工作流四条路径上都观察到“错误演化”，包括记忆积累后安全对齐下降、部署时刷分、创建不安全的工具；基于提示的缓解效果有限 [只读摘要]。
- **上下文内刷分 [9]**（Pan 等，ICML 2024）：LLM 输出影响环境、再反馈给 LLM 时，模型会优化代理目标并产生副作用；静态数据集评估看不出来。
- **DGM [18]**：作者承认“硬编码答案”是容易的刷分方式，称未观察到；一次运行约 $22,000。

对本项目：物理分数（残差、Wadati 离群、极性拟合误差）都可以靠“少拾、丢掉难拾的台站、只留近台”变好。这正是上下文内刷分的典型情形，设计稿 §6 的覆盖度约束是必要的。

### 4. 缓解措施及其实测效果

| 措施 | 代表做法 | 实测效果 | 证据强度 |
|---|---|---|---|
| 多候选 + 保留空记忆 + 新 episode 上选择 | RBC 的 Best-Full：3 次生长的整本 + 空 playbook，按新 episode 选 | 66.4（整本 55.5，无 54.1）[2] | 强（3 模型 × 3 基准 × 2 记忆系统） |
| 随机分组消融整理 | RBC：8 块，每 episode 每块以 1/2 概率包含，岭回归（带任务固定效应）估计效应；保留正效应块，预算 40% token | 66.9；单次生长只整理 61.9，只选择 62.2，两者都做 63.1，三次生长两者都做 67.2 [2] | 强，但只比 Best-Full 多 0.5 |
| 练习轮规模 | RBC 练习轮子采样 | 相对无 playbook 的增益：1/4 轮 8.9，1/2 轮 10.2，3/4 轮 11.0，全轮 10.8 [2] | 中（9 个设置均值） |
| 块数、预算 | RBC 消融 | m=4/8/16：45.9/47.4/48.0；预算 20%/40%/60%：46.1/47.4/46.1 [2] | 中，预设阈值 1 分内都算无差别 |
| 在 minibatch 上先筛 | GEPA：子代在 minibatch 上须优于父代才进入验证 | 未单独消融；但大部分 rollout 用在验证上 [19] | 弱 |
| 分阶段评估 | DGM：小集合达标才上大集合 | 未单独消融 [18] | 弱 |
| 回退上限 / 历史回放不退步 | SkillBoost [7]、Skill-V [6] | 摘要中作为方法组成部分，未见单独消融 | 弱 |
| Pareto 候选池 | GEPA | 61.28 vs 贪心 54.89 vs 束搜索 53.95（Qwen3 8B）[19] | 中 |
| 筛选后加入 + 按历史删除 | Xiong 等 | 严格筛选大幅好于全部加入；历史删除使 EHRAgent 38.67 → 42.06，CIC-IoT 85.40 → 89.60 [3] | 强（4 个 agent） |
| 投票计数删除 | ExpeL：ADD 初始 2，DOWNVOTE 到 0 删除 | 未单独消融 [5] | 弱 |
| 批量反思 | Agent-ToM：批量 1/4/8 | F1 0.843/0.860/0.861；规则 155/104/89；时间 14.6/4.5/2.5 h [4] | 中（单一任务） |
| 补充任务说明 | Fragility：评分细则、环境反馈、提示修改 | 弥补约 31% 的退化 [1] | 中 |
| 保护已有能力 | CPE | 保留成绩 41.8% → 52.8% [14] | 只读摘要 |
| 版本管理 / 回滚 | 技能库综述把来源追踪和回滚列为治理环节 [20] | 未找到单独测量 | — |
| 最低证据门槛（每条规则至少 k 个事件） | — | 未找到单独测量 | — |

### 5. 需要多少种子、顺序和练习 episode

**文献中的实际做法**

| 工作 | 学习运行数 | 顺序 | 练习规模 |
|---|---|---|---|
| Fragility [1] | 3（附录扩到 6） | 默认 + 2 种打乱 | WebArena 684 个任务等 |
| RBC [2] | 3 次生长 × 3 个评估种子 | — | 生长 450（AppWorld）/ 1,288（WebShop）/ 2,500（ALFWorld）episode；练习轮 600–684；每个候选 140–171 个练习 episode |
| ACE [12] | 单次（据所读） | — | AppWorld 训练集，多轮 epoch |
| ReasoningBank [15] | 单次（据所读） | 默认 | WebArena 684 个任务 |
| Training-Free GRPO [21] | 单次（据所读） | — | 100 个问题 × 每组 5 次 × 3 个 epoch ≈ 1,500 次 rollout |
| GEPA [19] | 未在所读部分说明 | — | 总 rollout 1,839–7,051；用于学习的只有 79–737 |
| 本项目试点 | 1 | 1 种 | 9 个练习事件；验证集 8 个事件 |

注意：“100 个样本”往往对应上千次 rollout（多次采样、多轮 epoch）。按 $0.5/事件，本项目难以照搬。

**统计功效的粗算（推断）**

学习效应的检验单位是“一次独立的学习运行”（一个种子 × 一种顺序），不是事件。事件层面的 bootstrap 只能反映测试集抽样误差，不能反映“换一次学习结果就不同”的方差。下表是双侧 α=0.05 的两样本 t 检验功效（每组 n 次运行），d = 效应 / 运行间标准差：

| d | n=3 | n=5 | n=6 | n=9 | n=12 |
|---|---|---|---|---|---|
| 1.0 | 0.16 | 0.29 | 0.35 | 0.51 | 0.65 |
| 1.5 | 0.29 | 0.55 | 0.65 | 0.85 | 0.94 |
| 2.0 | 0.46 | 0.79 | 0.88 | 0.98 | ≈1 |
| 3.0 | 0.78 | 0.98 | ≈1 | ≈1 | ≈1 |

若与一个评估得很精确的固定基线（如 A0）比较（单样本检验），d=1.5 时 n=3/6/9 的功效为 0.32/0.83/0.97。

参考量级：Fragility 中 RBank 相对无记忆 +1.5 而运行标准差最大 3.9（d 远小于 1），因此 6 次运行仍不显著 [1]；RBC 中 3 次生长可差 50 分以上 [2]。本项目的 d 未知，**应在第 1 轮先用 3 次运行估计运行间标准差，再决定加到 6 还是 9**。深度强化学习的统计方法文献（Agarwal 等，NeurIPS 2021 杰出论文）建议报告区间估计、性能分布图和 IQM，指出“少量运行下不能忽略不确定性”[22]；Colas 等给出了按 t 检验和 bootstrap 选种子数的方法 [23]。

**顺序与种子的区别**：Fragility 的主要发现是**顺序**的效应大于同一顺序下的随机波动（默认顺序有隐含课程）[1]。因此“3 个种子、每个种子对应一种顺序”（设计稿 §8.3）会把顺序效应和随机效应混在一起。建议用“k 种顺序 × m 个种子”的交叉设计，至少能分开估计两者。

## 对本项目的影响

### 门控协议的修改建议

1. **降低门控频率、增大每次更新**：反思仍每 10–20 个事件一次，但积累 2–3 次反思的 delta 后才门控一次（200 个练习事件约 4–5 次门控）。单批规则效应小，门控无法分辨（推断）；合并后效应更大、门控次数更少、成本更低。
2. **主指标用“非劣效 + 点估计为正”，不要求置信区间下界 > 0**：设门控集 80 个事件，每事件主指标配对差的标准差为 σ_d，则单侧 90% 下界 > 0、功效 0.8 时可分辨的最小效应约为 0.24 σ_d；σ_d=0.10–0.15 时约 2.4–3.6 个百分点（推断，σ_d 需实测）。试点中 after_0 → after_5 的 P recall +11 个百分点能通过，但大多数正常更新会被拒绝。建议：主指标点估计 > 0 且 90% 下界 > −δ（δ 取门控集上 A0 两次重复运行之差标准差的 1–2 倍）。
3. **次要指标的阈值按实测噪声校准**：先用当前记忆在门控集上重复跑 2 次，测出每个指标的重复误差，再设 2 个百分点 / 10% 这类阈值。指标越多，误拒概率越高；阈值应以点估计判断，不再叠加置信区间。
4. **分阶段门控**（借鉴 DGM [18]、GEPA [19]）：候选先跑 20 个门控事件（1 个种子），明显变差即拒绝；通过后再跑完整 80 个。当前记忆的门控结果缓存复用，不重复跑。
5. **每个候选保留“空记忆”和“上一版”作为对照**，最终服务的版本在新的留出事件上从多个候选中选（RBC Best-Full [2]）。选择会抬高门控分数（赢家诅咒），报告结果一律用测试集。
6. **整理改为学习结束后做一次**：设计稿要求每 5 批整理一次、每次 150 个事件，200 个练习事件内只能做 1–2 次，而且每次约 $75 以上。RBC 证明 1/4 练习轮（约 150 个 episode）仍保留约 80% 的增益（8.9 vs 10.8）[2]，因此一次 150 个事件的整理是可行的；8 个块、包含概率 1/2、带事件固定效应的岭回归、40% token 预算，可以直接照搬。
7. **给反思者明确的评分细则**（Fragility：说明不足是不稳定的原因之一 [1]）：残差怎么算、多大算异常、覆盖度要求、物理分数可被刷的方式，都写进反思提示词。
8. **物理反馈组的防刷分**：门控时覆盖度（拾取数、S 拾取数、方位角空隙）是硬约束，任何一项低于当前版本即拒绝。
9. **记录“传染”**：每版记录每条规则被调用的次数；某条规则调用率持续上升而对应指标不变，应人工检查（借鉴 Fragility 的 Haversine 案例 [1]）。

### 门控成本估算（推断，按 $0.5/事件，标准价）

| 方案 | 每次门控的运行数 | 每条学习流的门控次数 | 每条流的门控运行数 | 成本 |
|---|---|---|---|---|
| 设计稿：每 20–25 个事件门控，候选和当前各 2 个种子 × 80 个事件 | 320 | 8–10 | 2,560–3,200 | $1,300–1,600 |
| 当前记忆结果缓存，候选 2 个种子 | 160 | 8–10 | 1,280–1,600 | $640–800 |
| 建议：每 50 个事件门控，分阶段（20 个事件预筛，约一半进入完整 80 个事件 × 1 个种子） | 20 + 约 40 | 4 | 约 240 | 约 $120 |

设计稿 §8.3 按每条流约 400 次门控运行计算，与 §5 的协议不符，需要统一。

### 种子和顺序的数量

- **主比较**（A-physics、A-label、A-placebo，以及 A0 / 等算力对照）：每个学习组至少 **6 次独立学习运行 = 3 种顺序 × 2 个种子**。顺序用分层随机排列（每批内震级、震中距、信噪比均衡），另加 1 种“难事件在前”的压力顺序只作稳健性检查。
- **第 1 轮先做 3 次运行**，估计运行间标准差；若 d < 1.5，增加到 9 次，或改用开源模型扩大规模。
- **统计**：以“学习运行”为单位做主检验（运行层面的配对或混合效应模型，运行作为随机效应，事件作为交叉随机效应），事件层面 bootstrap 只用于描述单次运行的测试误差。报告每次运行的曲线，而不只是平均曲线；报告最差运行和低于 A0 的运行比例（RBC 和 Fragility 都把这一点当作关键指标）。
- **测试成本也随运行数增加**：每次运行的最终记忆都要在测试集上评估。6 次运行 × 3 组 × 400 个事件 = 7,200 次运行，约 $3,600（标准价）。可行的折中：学习曲线中间快照只在 100–200 个事件的子集上评估，最终记忆在 400 个事件上评估。

### 建议增加的对照

- **无门控学习**（同样的反思，但全部接受）：证明门控的价值；文献预期它会出现低于 A0 的运行 [1][2]。
- **门控本身的安慰剂**：门控集换成随机标签或错配反馈，检查门控是否只是在“选噪声”。
- **重复评估噪声**：同一版本记忆在测试集上跑 2 次，给出评估噪声底线（RBC 中重复评估最多相差 5.0 分 [2]）。

## 未解决与待核

- Fragility 附录中 VisualWebArena 的完整数字和顺序构造方式（只读到 WebArena 部分）。
- RBC 每个设置的 token / 美元成本（附录 E.4 未读到），以及块效应估计的标准误（论文未给）。
- PATH-Bench、Evo-Memory、“Do Self-Evolving Agents Forget?” 的具体数字（只读摘要）。
- Misevolve 中记忆路径刷分实验的细节（只读摘要）。
- Colas 等（2018）给出的具体种子数示例；Henderson 等（2018）关于“同一算法两组 5 个种子结果显著不同”的说法 [待核，未打开原文]。
- 自适应数据分析中“可重复使用的留出集”（Dwork 等，2015）是否适合我们的门控集轮换 [待核，未打开原文]。
- 本项目需要实测的量：门控集上每事件配对差的标准差 σ_d；运行间标准差；单条规则 / 单个块的效应量。这三个数决定门控能否工作、需要几次运行，建议在第 2 周用 A0 和试点 playbook 先测。

## 参考文献

1. Ye, Q., Li, Y., Pruksachatkun, Y., Zhang, J., Wu, C.-S. (2026). On the Fragility of Self-Improving Agents: Variance, Task Order, and Underspecification. arXiv:2608.18066. https://arxiv.org/abs/2608.18066 [已读原文]
2. Pham, H., Nguyen, C.-D., Le, D., Srey, P., Luu, A. T. (2026). Reliable Memory from Unstable Growth: Curating Self-Written Agent Playbooks with Randomized Experiments. arXiv:2610.18427. https://arxiv.org/abs/2610.18427 [已读原文]
3. Xiong, Z., Xiang, Z., Lin, Y., Xie, W., He, P., Liu, Z., Tang, J., Lakkaraju, H. (2025). How Memory Management Impacts LLM Agents: An Empirical Study of Experience-Following Behavior. arXiv:2505.16067. https://arxiv.org/abs/2505.16067 [已读原文]
4. Ahmed, N. K., Nafisi, N. (2026). Agent-ToM: Learning to Monitor Autonomous LLM Agents via Theory-of-Mind Reasoning. arXiv:2605.24216. https://arxiv.org/abs/2605.24216 [已读原文，仅批量消融表]
5. Zhao, A., Huang, D., Xu, Q., Lin, M., Liu, Y.-J., Huang, G. (2024). ExpeL: LLM Agents Are Experiential Learners. AAAI 2024. https://arxiv.org/abs/2308.10144 [已读原文]
6. Ma, J., Qian, Z., Ma, Y., et al. (2026). Skill-V: Verifiable Self-Evolving Skill Library for Interactive Agents. arXiv:2610.11781. https://arxiv.org/abs/2610.11781 [只读摘要]
7. Lin, H., Liu, C., Bai, X., et al. (2026). Rethinking Self-Evolution: A Constrained Exploration-Exploitation Process for Mitigating Skill Overfitting. arXiv:2607.26643. https://arxiv.org/abs/2607.26643 [只读摘要]
8. Shao, S., Shao, J., et al. (2025/2026). Your Agent May Misevolve: Emergent Risks in Self-evolving LLM Agents. ICLR 2026. https://arxiv.org/abs/2509.26354 [只读摘要]
9. Pan, A., Jones, E., Jagadeesan, M., Steinhardt, J. (2024). Feedback Loops With Language Models Drive In-Context Reward Hacking. ICML 2024. https://arxiv.org/abs/2402.06627 [只读摘要]
10. Yang, X., Zhang, X., Li, W., et al. (2026). PATH-Bench: Path-Dependent Evaluation of Lifelong Agents. arXiv:2608.01149. https://arxiv.org/abs/2608.01149 [只读摘要]
11. Wei, T., Sachdeva, N., Coleman, B., et al. (2025/2026). Evo-Memory: Benchmarking LLM Agent Test-time Learning with Self-Evolving Memory. arXiv:2511.20857. https://arxiv.org/abs/2511.20857 [只读摘要]
12. Zhang, Q., Hu, C., Upasani, S., et al. (2025/2026). Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models. ICLR 2026. https://arxiv.org/abs/2510.04618 [已读原文]
13. Suzgun, M., Yuksekgonul, M., Bianchi, F., Jurafsky, D., Zou, J. (2025). Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory. arXiv:2504.07952. https://arxiv.org/abs/2504.07952 [已读原文]
14. Yu, Y., Yuan, X., Jin, H., Liu, H., Yu, Y., Wang, H. (2026). Do Self-Evolving Agents Forget? Capability Degradation and Preservation in Lifelong LLM Agent Adaptation. arXiv:2605.09315. https://arxiv.org/abs/2605.09315 [只读摘要]
15. Ouyang, S., Yan, J., Hsu, I-H., et al. (2025). ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory. ICLR 2026. https://arxiv.org/abs/2509.25140 [已读原文]
16. Dong, S., et al. (2025). A Practical Memory Injection Attack against LLM Agents (MINJA). arXiv:2503.03704. https://arxiv.org/abs/2503.03704 [未打开原文，仅检索摘要]
17. Chen, Z., et al. (2024). AgentPoison: Red-teaming LLM Agents via Poisoning Memory or Knowledge Bases. NeurIPS 2024. https://arxiv.org/abs/2407.12784 [未打开原文，仅检索摘要]
18. Zhang, J., Hu, S., Lu, C., Lange, R., Clune, J. (2025). Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents. arXiv:2505.22954. https://arxiv.org/abs/2505.22954 [已读原文，部分附录未读到]
19. Agrawal, L. A., Tan, S., Soylu, D., et al. (2025). GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning. ICLR 2026. https://arxiv.org/abs/2507.19457 [已读原文]
20. Li, Y. (2026). Dynamic Agent Skills: A Lifecycle Survey and Taxonomy of Evolving Skill Libraries. TMLR 2026. https://arxiv.org/abs/2607.10113 [只读摘要]
21. Cai, Y., Cai, S., Shi, Y., et al. (2025). Training-Free Group Relative Policy Optimization. arXiv:2510.08191. https://arxiv.org/abs/2510.08191 [已读原文]
22. Agarwal, R., Schwarzer, M., Castro, P. S., Courville, A., Bellemare, M. G. (2021). Deep Reinforcement Learning at the Edge of the Statistical Precipice. NeurIPS 2021. https://arxiv.org/abs/2108.13264 [只读摘要]
23. Colas, C., Sigaud, O., Oudeyer, P.-Y. (2018). How Many Random Seeds? Statistical Power Analysis in Deep Reinforcement Learning Experiments. arXiv:1806.08295. https://arxiv.org/abs/1806.08295 [只读摘要]
