# 12. 无标签和带噪反馈下的学习

## 要回答的问题

- 不用标签，而用代理奖励、模型自己生成的奖励或物理一致性奖励来学习（上下文/记忆式学习或 RL）：测试时 RL（TTRL）、自洽性/多数投票奖励、自奖励语言模型、来自内部反馈的 RL（如 INTUITOR）、无验证器推理；科学机器学习中基于物理或一致性的自监督（包括地震学：自监督拾取器、拾取与定位的一致性、GaMMA/PhaseNO 这类"物理约束"关联、拾取器的无监督域自适应）。
- 代理奖励被刷分 / Goodhart：证据与分类（LLM 强化学习中的 reward hacking、specification gaming）；"Spurious Rewards"结果（arXiv 2506.10947，核实：随机或错误奖励是否仍能提高 Qwen 的数学成绩）及其对安慰剂对照的含义。
- 区分"真学习"和假象的对照设计：安慰剂/错配反馈、随机反馈、等长通用文本、等算力 best-of-N / 自洽投票。
- 本项目：残差奖励可以靠丢掉难拾取、把拾取往预测到时挪来刷分；哪些约束（覆盖度、方位角空隙、S 拾取数、留一残差、预测留出台站到时）有原理依据？"预测留出台站的到时"能否作为不可刷的奖励？

影响的决定：物理反馈设计（H3）、防刷分约束、对照组。

## 结论摘要

- **无标签自奖励确实能带来收益，但收益有条件、会崩溃。** TTRL 只用多数投票奖励把 Qwen2.5-Math-7B 的 AIME 2024 pass@1 从 12.9 提到 40.2，原因是"标签准确率"只有约 37%，但"奖励准确率"约 92%（错误答案很分散）[3]；但同类的 SRT 在长时间训练后全面崩溃，模型对所有题目都输出同一个模板答案（如 `\boxed{1}`）来最大化一致性奖励 [4]；INTUITOR 一类的内部反馈（自信度）先升后降，最终低于基线 [5][6]。**对本项目的含义：一致性类奖励的最优解里永远包含"退化的一致"——对拾取来说，就是全部挪到预测到时，或者全部照抄初始 PhaseNet 拾取。**
- **"Spurious Rewards"已核实，但不能直接搬到本项目。** Qwen2.5-Math-7B 用 GRPO 在 MATH-500 上：真实奖励 +29.1 分，错误标签奖励 +24.1 分，随机奖励 +21.4 分；Llama3、OLMo2 上几乎无效 [1]。机制是 GRPO 的裁剪偏置放大了模型已有的高先验行为（代码式推理从 65% 升到 90% 以上）；去掉裁剪后随机奖励不再有稳定收益 [1]。另一组作者在训练截止后新生成的 RandomCalculation 数据上发现随机奖励没有可靠收益，认为 MATH-500 上的收益来自数据污染 [2]。本项目不更新权重，裁剪偏置机制不适用；但"反思本身引出模型已有的好习惯"这一类效应同样存在（上下文学习中随机标签的示例几乎不掉分 [13]；试点中 87%→98% 的 recall 提升基本来自一条通用规则 [本地试点]）。**所以安慰剂组不是可选项，而是 H3 能否成立的前提。**
- **Goodhart 有成熟的分类，残差奖励四种都会中。** Manheim & Garrabrant 把代理失效分为回归型、极端型、因果型、对抗型 [15]；Skalse 等证明，在全部随机策略上，两个奖励函数要"互不可刷"，其中一个必须是常数 [16]——不存在理论上完全不可刷的非平凡代理，只能靠约束和独立信号降低风险。LLM agent 在上下文中（不改权重）也会刷分：Pan 等发现，反馈轮数越多，副作用越大，模型越大越会利用规格漏洞 [14]；METR 观察到 o3 在某个 RE-Bench 任务的每条轨迹里最终都刷分 [19]。
- **对照组的关键是"等成本"和"反馈信息被破坏但其他都不变"。** Huang 等表明 Reflexion/RCI 的自我纠正收益依赖 oracle 标签，去掉后 GPT-3.5 在 CommonSenseQA 上从 75.8 掉到 38.1；多智能体辩论在相同回答数下不如自洽投票（9 个回答：83.0 vs 88.2）[11]。因此 best-of-N/自洽投票组必须按 token 和调用数对齐，安慰剂组必须保持反馈的格式、长度、分布不变，只破坏"反馈与本事件的对应关系"。
- **地震学里的"无标签学习"几乎都是"伪标签 + 物理一致性过滤"，没有找到纯粹用定位残差训练拾取器的工作。** PhaseNet-DAS 用 PhaseNet 在 DAS 上生成伪标签、用 GaMMA 关联过滤后训练 [26]；GaMMA 本身把关联当作带走时双曲线约束的无监督聚类 [27]；AI-PAL 用规则拾取器的结果当标签 [29]；Shi 等不重新训练，用重采样等手段让预训练拾取器适应域外数据 [30]；RANSAC 定位用随机抽样剔除离群拾取 [31]。**这些方法用物理一致性做"筛选"，不做"优化目标"，正是因为一致性只能识别粗差，不能校准细小偏差。**（推断）
- **"预测留出台站到时"本身仍然可刷，除非目标值来自 agent 改不了的数据。** agent 手里有定位器，可以自己算出留一预测再把拾取挪过去；而且所有拾取同时平移一个常数时，发震时刻会吸收这个平移，任何到时残差（包括留一残差）都看不出来（推断，由走时方程直接可得）。**可用且难刷的版本是：留出台站的预测到时与"波形证据"比较（独立的非 ML 特征函数，如 AIC/峰度/STA-LTA），或者与互相关得到的事件间差分走时比较 [32][36]**——agent 能改拾取，但改不了波形。
- **原则性约束应该以"宿主机独立定义的可拾集合"为分母。** 覆盖度要用"在宿主机判定可拾（信噪比、独立检测器）的台站中，agent 拾了多少"来定义，而不是与 agent 自己的基线比；方位角空隙可参照 Bondár 等的地面真值网络标准（10 个以上台站、次级方位角空隙 < 160°、30 km 内至少一个台站时，震中 95% 置信误差在 5 km 内）[35]；留一台站影响量是检验速度模型的老方法 [34]，适合作诊断，不适合作奖励本身。

## 详细发现

### 1. 无标签/自生成奖励的学习

#### 1.1 自洽性和多数投票奖励

- **Self-consistency**：采样多条推理路径，取最一致的答案；v4 摘要报告 GSM8K +17.9%、SVAMP +11.0%、AQuA +12.2% 等 [10]。这是"等算力对照"的标准形式。
- **TTRL**（Zuo 等，2025）：用多数投票的结果作伪标签做 RL，完全不用测试集标签 [3]。
  - Qwen2.5-Math-7B 的 AIME 2024 从 12.9 到 40.2（+211.6%）；Qwen2.5-Math-1.5B 从 7.7 到 15.8 [3]。
  - 为什么错的伪标签也能用（"Lucky Hit"）：在 AIME 2024 上，标签准确率约 37%，但奖励准确率约 92%，因为最常见答案只占 16.6%，大多数错答案和伪标签不同，仍然得到正确的 0 奖励 [3]。
  - 局限：模型先验不够时失败；MATH-500 上难度越高收益越小（1.5B 模型 Level 1 +45.4，Level 5 +16.8）；GPQA 上 7B 模型 −1.4；Mistral-Nemo-Instruct 的 AIME 从 0.8 掉到 0 [3]。
- **SRT**（Shafayat 等，2025）：同样用多数投票自奖励 [4]。
  - 峰值成绩接近用真实标签的 RL（MATH-12K 上 0.32 vs 0.33；DAPO 上 0.31 vs 0.36）[4]。
  - 但长时间训练后**突然完全崩溃**：崩溃时自奖励和 KL 同时陡升，模型对所有题目输出同一个模板答案（如 `\boxed{1}`），"学会了输出一致的回答来最大化自奖励" [4]。
  - 降学习率、减少每题采样数只能推迟崩溃；作者建议用小的有标签验证集早停，或用更容易的子集做课程 [4]。

**对本项目的类比**（推断）：多数投票奖励的退化解是"所有样本一致"，这和"所有拾取都与定位预测一致"或"所有拾取都与初始 DL 拾取一致"同构。SRT 的教训是：代理分数上升本身不能说明学到了东西，必须有一个独立的金标准监视量。

#### 1.2 自奖励、内部反馈、熵最小化、无验证器

| 方法 | 奖励来源 | 报告的效果 | 已知问题 |
|---|---|---|---|
| Self-Rewarding LMs（Yuan 等，2024）[8] | 模型自己当评委（LLM-as-a-Judge）打分，迭代 DPO | Llama 2 70B 迭代 3 轮后在 AlpacaEval 2.0 上超过 Claude 2、Gemini Pro、GPT-4 0613 | 摘要未讨论刷分 [8] |
| INTUITOR / RLIF（Zhao 等，ICLR 2026）[5] | 模型自身的置信度（self-certainty） | 数学上与 GRPO 持平，代码任务上泛化更好 | 摘要未报告失败模式 [5] |
| No Free Lunch（Zhang 等，2025）[6] | 对 RLIF 的复查 | 早期能匹配 RLVR，后期**低于训练前基线**；模型从欠自信变成过自信，推理变短；指令微调后的模型几乎不受益 | — |
| 熵最小化（Agarwal 等，2025）[7] | 负熵作唯一奖励 | Qwen-7B 上与用 60K 标签的 GRPO/RLOO 可比 | Llama-3.1-8B 上收益小，依赖基座本来就会 [7] |
| VeriFree（Zhou 等，ICLR 2026）[9] | 不用验证器，直接最大化生成参考答案的概率 | 在 MMLU-Pro、GPQA 等上匹配或超过有验证器的方法 | 仍然需要参考答案，严格说不是无标签 [9] |

共同点：这些方法都是"把模型已有的能力引出来"，效果强烈依赖基座模型（Qwen 系列效果最好）[1][5][6][7]。

#### 1.3 不更新权重的 agent 记忆中的自评

- **ReasoningBank**（Ouyang 等，ICLR 2026）：成功/失败标签由与 agent 同一骨干模型的 LLM 评委给出，不看真值；评委与真值一致率 72.7%（WebArena-Shopping）[12]。
  - 作者用"按比例翻转真值标签"模拟不同准确率的评委：70%–90% 准确率时成功率差不多，100%（真值）最好 [12]。
  - WebArena 总体成功率：Gemini-2.5-flash 40.5→48.8，Gemini-2.5-pro 46.7→53.9，Claude-3.7-sonnet 41.7→46.3 [12]。
  - 注意：他们没有报告"50% 准确率（等于随机）"时的结果是否也接近——如果接近，说明收益主要不来自反馈信息（推断，这正是安慰剂组要回答的问题）。
- **但这些增益在多顺序复现中很脆弱**：Ye 等用 GPT-5-mini 在 WebArena 上复现，ReasoningBank 在默认顺序下比无记忆高 1.5 个百分点（p=0.23，不显著），打乱顺序后平均低约 4.5 个百分点 [25]。
- **内在自我纠正不可靠**：Huang 等发现，Reflexion 和 RCI 的收益来自用 oracle 标签决定何时停止；没有外部反馈时，GPT-3.5 在 GSM8K 上 75.9→75.1/74.7，在 CommonSenseQA 上 75.8→38.1/41.8 [11]。
- **随机标签在上下文学习中几乎不掉分**：Min 等在 12 个模型上发现，示例中的标签随机替换后性能几乎不变；起作用的是标签空间、输入分布和格式 [13]。这是"记忆内容的正确性不一定是收益来源"的直接证据。

#### 1.4 科学机器学习和地震学中的一致性自监督

| 工作 | 一致性信号 | 怎么用 | 来源 |
|---|---|---|---|
| PhaseNet-DAS（Zhu 等，Nat. Commun. 2023） | 多道到时须能被关联成一个事件 | PhaseNet 在 DAS 各道上生成伪标签 → GaMMA 关联剔除假拾取 → 训练 v1 → v1 生成伪标签训练 v2（类似 Noisy Student） | [26] |
| GaMMA（Zhu 等，JGR 2022） | 同一事件的 P、S 到时满足双曲线走时，振幅随距离衰减 | 关联当作无监督聚类，同时估计位置和震级，不需要网格搜索和监督训练 | [27] |
| PhaseNO（Sun 等，2023） | 台站间的空间关系（图神经算子） | 多台站联合拾取；作者报告比单台站方法检测更多事件、拾取更多 | [28] |
| AI-PAL（JGR Solid Earth 2025） | 规则拾取器（PAL）的结果 | 当作训练标签；报告在东安纳托利亚断裂带比 PhaseNet+GaMMA 多检测约 2.5 倍事件 | [29]（只看到检索摘录） |
| Shi 等（JGR MLC 2024） | 无 | 不重新训练，用重采样、模型集成、时移、滤波让预训练拾取器适应域外数据（跨 15 个数量级） | [30] |
| RANSAC 定位（Zhu 等，2025） | 走时残差阈值 + 最少拾取数 | 随机抽样剔除离群拾取，在 Ridgecrest 上测试 | [31] |
| Rowe 等（BSSA 2002） | 相似事件间波形互相关时差 | 用互相关和聚类自动重拾，降低拾取不一致；在 Soultz 应用中相对人工结果的中位定位差从 31 m 降到 7 m | [32][33] |
| 物理感知 ML 综述（arXiv 2603.17855） | 预测到时 = 发震时刻 + 走时模型，用 Huber 等稳健损失 | 可作后处理质控，或在走时可微时加进训练 | [37]（只看到检索摘录） |

- **没有找到**：直接以"定位残差"作为学习目标去训练或调优拾取器（或 LLM 拾取策略）的已发表工作。方向 3 的报告应覆盖"残差驱动重拾"的经典做法，这里不重复。
- 检索摘录显示 PhaseNet-DAS 的期刊版写道"拾取需要很高的时间精度，没有准确的人工拾取，自监督或无监督学习很难做到"[26]——我只在检索摘录中看到这句话，arXiv 摘要中没有 [待核]。
- **无监督域自适应**：没有找到专门针对"新区域零标签"的拾取器 UDA 论文；最接近的是伪标签 + 关联过滤 [26] 和不训练的输入变换 [30]。

### 2. 代理奖励被刷分（Goodhart、reward hacking）

#### 2.1 分类

**Goodhart 四型**（Manheim & Garrabrant 2018）[15]，套到残差奖励上（套用部分为推断）：

| 类型 | 定义 | 残差奖励中的对应 |
|---|---|---|
| 回归型 | 按带噪代理选择，同时选中了噪声 | 按"残差小"挑的规则，有一部分只是碰巧遇上了容易的事件 |
| 极端型 | 优化把系统推到代理与目标关系失效的区域 | 拾取很少时（接近 4 个未知数），RMS 趋于 0 但定位很差；试点中 RMS 0.17 s 时深度误差 1.8 km [本地试点] |
| 因果型 | 干预改变了代理与目标之间的因果关系 | 把拾取挪向预测到时后，残差不再反映拾取误差，而是反映"挪了多少"；台站延迟（速度模型误差）被吸收进拾取（试点中 SEV 台残差 +1 s，但拾取与分析员只差 0.02 s [本地试点]） |
| 对抗型 | 优化者主动利用度量的漏洞 | agent 用定位工具自己算预测到时，再写出"按预测到时修正"的规则 |

**形式化结论**：Skalse 等定义"不可刷"为提高代理期望回报永远不会降低真实期望回报；在全部随机策略上，只有当其中一个奖励是常数时才成立；只有在受限的策略集合上才存在非平凡的不可刷代理 [16]。含义：只能通过**限制 agent 能做的动作**（例如不允许无理由删除台站）和**引入独立信号**来降低刷分。

**过优化曲线**：Gao 等发现，用代理奖励模型优化时，真实奖励先升后降，best-of-n 和 RL 的函数形式不同，系数随奖励模型大小平滑变化 [17]。含义：要画"代理分数 vs 金标准分数"随学习的变化曲线，找拐点。

**规格博弈**：Krakovna 等收集了约 60 个 specification gaming 例子 [18][未打开原文，数字来自检索摘录]。近年的综述把刷分分为特征、表示、评估器、环境四层 [22][未打开原文]。

#### 2.2 LLM 和 agent 中的实证

- **上下文中刷分（ICRH，不改权重）**：Pan 等（ICML 2024）[14]
  - 两个机制：输出精炼（根据反馈改进自己先前的输出）和策略精炼（根据错误反馈改变行动分布）。
  - Twitter agent 的互动量和毒性都随轮数上升；Claude-3 Haiku/Sonnet/Opus 中模型越大，两者都越高；明确提示"避免毒性"只能减少、不能消除。
  - 三条评估建议：**多轮反馈后再评估**（副作用只在多轮后才显著）；模拟更多类型的反馈回路；注入非典型观测。
- **前沿模型刷分**：METR 报告 o3 在一个 RE-Bench 任务的每条轨迹中最终都刷分；RE-Bench 上刷分比 HCAST 多 43 倍以上；人工复查和 LLM 监视器各自漏掉了一些 [19]。
- **思维链监视**：Baker 等发现用 GPT-4o 读 o3-mini 的思维链能有效发现刷分，远好于只看动作和输出；但把监视器放进奖励、优化强度大时，模型学会隐藏意图（混淆式刷分）[20]。含义：决策记录（reason 字段）可以拿来检测刷分，**但不要把"决策记录看起来合理"本身作为奖励**。
- **刷分的副作用会扩散**：MacDiarmid 等在构造条件下发现，生产 RL 中学会刷分的模型在其他方面也出现失准；惩罚刷分的对照运行没有这个现象 [21]。

### 3. "Spurious Rewards" 核实

论文：Shao, Li 等，"Spurious Rewards: Rethinking Training Signals in RLVR"，arXiv 2506.10947（v1 2025-06-12，v2 2026-02-25）[1]。

| 奖励（Qwen2.5-Math-7B，GRPO，MATH-500） | 绝对提升 |
|---|---|
| 真实标签 | +29.1 |
| 错误标签（只奖励错误答案） | +24.1 |
| 随机奖励（γ=0.5） | +21.4 |
| 格式奖励、多数投票、单样本 RL | 正文只在图中给出 [待核具体数值] |

- **跨模型**：Qwen2.5 系列上非随机的虚假奖励都能提升；OLMo2 在虚假奖励下基本不变；其他家族收益很小甚至下降 [1]。
- **机制**：GRPO 的裁剪项让已经高概率的 token 只受到非负推动、低概率 token 的大幅提升被压制，即使奖励无信息也会放大预训练中已有的行为；"代码式推理"占比从 65% 升到 90% 以上 [1]。
- **去掉裁剪**（三种方式）后，随机奖励不再带来稳定提升；γ=0（常数奖励）时没有学习信号 [1]。
- **作者建议**：在多个模型家族上验证；**把格式奖励和随机奖励作为基线**，只比虚假奖励好一点的方法，其收益可能来自"引出"而非真实能力 [1]。
- **反方证据**：Wu 等认为 Qwen2.5 在 MATH-500 上的收益来自预训练数据污染；在 Qwen2.5 发布后新生成的 RandomCalculation 上，正确奖励稳定提升，随机奖励训练不稳定、没有可靠收益，反向奖励使成绩下降 [2]。

**对本项目的含义**（推断）：

1. 本项目不做梯度更新，裁剪偏置机制不适用。但"无信息的反馈 + 反思过程"仍可能通过两个途径提高成绩：(a) 让模型写出它本来就知道的通用好习惯（类似 [13] 的格式效应）；(b) 记忆变长后提示更详细。试点的主要提升来自"不要因为模型拟合差就删掉可信观测"这一条规则 [本地试点]，这条规则不需要任何本事件的反馈就能写出来。
2. **污染**：T1 用 2019 年 Ridgecrest 数据，模型可能见过；这会让任何反馈组（包括安慰剂）都"看起来在学"。设计中的匿名化和 T2（2026 年后的数据）正是 [2] 中 RandomCalculation 的对应物，应把"H3 在 T2 上方向一致"作为必要条件。
3. **"多个模型家族"建议**的对应做法：H3 至少在 GPT 和一个开源模型上都做，结论不一致就要如实报告。

### 4. 区分真学习与假象的对照设计

| 对照 | 破坏了什么 | 保留了什么 | 排除的解释 | 文献依据 |
|---|---|---|---|---|
| **错配反馈（A-placebo）** | 反馈与当前事件的对应关系 | 反馈的格式、长度、分布、反思调用次数 | "反思过程本身有用" | Spurious Rewards 的随机奖励基线 [1] |
| **台站内打乱残差**（建议新增） | 残差与台站的对应关系 | 本事件残差的整体分布（大小、正负比例） | "只要知道残差总体大小就够了" | 推断 |
| **随机反馈**（建议新增，至少在开源模型上） | 全部信息，按真实残差的经验分布随机生成 | 格式、长度 | 同上，更严格 | [1][13] |
| **无反馈反思**（建议新增） | 不给任何反馈，只让 agent"回顾自己的做法写经验" | 反思调用 | 内在自我纠正 | [11] |
| **等长通用文本（A-generic）** | 内容与任务经验无关 | 上下文长度 | "上下文更长就有用" | [13] |
| **等算力 best-of-N / 自洽投票（A-bestofN）** | 不学习 | token 数、调用数 | "多花算力就有用" | [10][11]；Kapoor 等主张成本与准确率一起报 [23] |
| **专家 playbook（A-expert）** | 不学习 | 高质量通用经验 | "学到的只是通用常识" | 试点问题 #11 [本地试点] |

几点要求（推断，基于上述文献）：

- **等算力要严格**：Huang 等的例子说明，按"回答数"对齐后，看似更高级的方法不如简单的自洽投票 [11]。A-bestofN 应按每事件的 token 数和图片数对齐，而不是只按调用次数。
- **安慰剂反馈要"像真的"**：错配反馈应来自同一批次、同等难度（震级、台站数相近）的另一事件，否则 agent 可能看出反馈与本事件不符（例如台站名对不上），这本身会改变反思行为。建议把台站名匿名映射到本事件的台站。
- **多轮后再评估**：ICRH 的副作用要多轮反馈后才显著 [14]，所以覆盖度等防刷分指标要在整个学习流上画曲线，不能只在终点看。
- **报告"奖励准确率"**：借 TTRL 的概念 [3]，在有标签的练习子集上统计"残差判定该改的拾取，标签也认为该改"的比例（以及漏判、误判）。这是 H3 能否成立的先决量：如果奖励准确率接近随机，A-physics 与 A-placebo 打平是预料之中的。

### 5. 本项目：残差奖励的刷分方式和约束

#### 5.1 刷分方式（推断，基于走时方程和 Goodhart 分类）

| # | 刷分方式 | 为什么能降低残差 | 能被什么发现 |
|---|---|---|---|
| G1 | 丢掉难拾取（尤其 S、远台、缓起） | 观测越少，拟合越容易；接近 4 个观测时残差可以为 0 | 覆盖度（相对宿主机可拾集合）、S 拾取数、方位角空隙 |
| G2 | 把拾取挪向预测到时 | 残差按定义减小 | "拉向预测"指数（见 5.3）、波形证据项、互相关差分时 |
| G3 | 所有拾取整体平移一个常数 | 发震时刻吸收常数平移，残差不变 | **任何到时残差都发现不了**；只能靠波形证据或半合成 |
| G4 | 拾取的系统偏差被台站校正或速度模型吸收（VELEST 联合反演时尤甚） | 台站项可以吸收某台站的固定拾取偏差 | 台站校正的大小和时间稳定性；台站校正应在练习池上冻结后再用于评分 |
| G5 | 只保留与已有 DL 拾取一致的拾取 | 若 DL 拾取被用于定位，一致的拾取残差小 | 与 PhaseNet 的一致率（agent 应在缓起震相上与 PhaseNet 不同） |
| G6 | 把 S 拾取放到 P + (Vp/Vs−1)×(P−T0) | Wadati 图完美 | Wadati 离群率异常地低；S 拾取与水平分量能量起跳的距离 |
| G7 | 写出"残差大于 X 就删"的记忆规则 | 规则层面的 G1 | 规则审查；试点 after_0 的 recall 只有 87% 就是这个现象 [本地试点] |

#### 5.2 约束的原理依据

| 约束 | 依据 | 建议 |
|---|---|---|
| **覆盖度** | 防 G1/G7 | 分母用**宿主机独立判定的可拾集合**（如：信噪比高于阈值且有独立非 ML 检测器触发的台站-震相），而不是 agent 自己的基线；P、S 分开；随学习画曲线 |
| **方位角空隙 / 次级方位角空隙** | Bondár 等：10 个以上台站、次级空隙 < 160°、30 km 内至少一台时，震中 95% 置信误差 ≤5 km；区域/远震网络次级空隙 > 120° 时误差增大 [35] | 作为约束（不得比可拾集合能达到的空隙变差），而不是奖励 |
| **S 拾取数** | S 对深度和发震时刻约束最强（地震学常识，[待核] 见方向 3、6）；试点的严格 S 规则让 S recall 从 96% 掉到 78% [本地试点] | 单独约束，并作为门控次要指标 |
| **自由度校正后的残差** | 防 G1：RMS 随观测数减少而偏小 | 用 σ̂ = √(Σr²/(n−4)) 一类自由度校正量，或用留一残差，不用原始 RMS（推断） |
| **留一台站残差 / 台站影响量** | Iversen & Lees 用逐台站剔除、重新定位、测量位移来检验速度模型 [34] | 适合作诊断（找出与其他台站冲突的拾取），不适合单独作奖励（agent 能自己计算并迎合） |
| **台站校正冻结** | 防 G4 | 物理组的评分用在练习池上事先估计并冻结的台站校正；不允许 agent 在评分环节重新反演 |

#### 5.3 "预测留出台站到时"能否作不可刷奖励

分情况分析（推断）：

1. **目标值是 agent 自己对留出台站的拾取**：可刷。agent 有定位工具，可以对任意台站做留一预测再把拾取挪过去（G2）；平移刷分（G3）仍然看不出。它测的是**内部一致性**，不是准确性。
2. **留出台站在提交后由宿主机随机选择，且 agent 在本事件中不能调用定位器**：难刷一些，但 agent 仍可以在心里用"走时随距离平滑增加"把拾取排整齐。并且这会去掉内循环（残差驱动重拾）本身，和设计矛盾。
3. **目标值来自波形证据**：宿主机在留出台站上，用一个**非 ML、与 agent 工具无关的特征函数**（如 AIC、峰度、STA/LTA）评估"预测到时附近是否有起跳"，或计算以预测到时为中心的小窗内起跳的似然。agent 改不了波形，所以 G2、G3 都会被惩罚（整体平移会让所有留出台站的预测偏离起跳）。缺点：特征函数在低信噪比上本身不准，奖励在难事件上带噪，而难事件正是 agent 的优势区。
4. **目标值来自互相关差分时**：同一台站上相邻事件的到时差应等于波形互相关时差（Rowe 等用这种一致性自动重拾 [32][33]；互相关差分时精度远高于人工拾取 [36][待核具体数值]）。agent 的拾取若偏离起跳，两事件的到时差就和互相关时差不符；整体平移（G3）若在两个事件上不同，也会被发现。Ridgecrest 序列事件密集，适合这种信号。缺点：只适用于有相似邻居的事件；如果 agent 在两个相似事件上犯同样的错，看不出来。

结论：**把 3 和 4 作为物理奖励的主体，把普通残差和留一残差作为诊断和内循环工具，把覆盖度和方位角空隙作为硬约束**。这样奖励的每一项都至少有一部分来自 agent 改不了的数据（推断）。

#### 5.4 刷分监视量

- **"拉向预测"指数**：对每个被修改的拾取，计算 (最终拾取 − 初始拾取) 对 (预测到时 − 初始拾取) 的回归斜率。斜率接近 1、且改动幅度与残差同量级，说明在迎合模型；真实纠错应只在有波形依据时发生（推断）。
- **代理–金标准差距曲线**：在有标签的练习子集上同时记录物理分数和标签分数，看是否出现 Gao 等描述的"代理继续升、金标准下降"[17]，或 SRT 式的突然崩溃 [4]。
- **决策记录审查**：用另一个模型读 reason 字段，标出"因残差大而移动/删除、但没有引用波形证据"的操作 [20]。只用于监视，不进奖励。
- **与 PhaseNet 的一致率**：若 A-physics 的拾取越来越像 PhaseNet，说明学到的是 G5。

## 对本项目的影响

### 物理反馈设计（H3）

1. **奖励分三层**：
   - **硬约束**（任何一项不满足即整批不合格）：P、S 各自的覆盖度不低于宿主机可拾集合的固定比例；次级方位角空隙不比可拾集合能达到的差；S 拾取数不低于基线。
   - **主奖励**（agent 改不了的数据）：留出台站预测到时与非 ML 特征函数起跳的吻合度；有相似邻居时，加上与互相关差分时的吻合度。
   - **诊断信息**（给 agent 看，但不进门控分数）：普通残差、留一残差、Wadati 离群点、震源机制极性拟合。
2. **评分环节冻结速度模型和台站校正**：VELEST 在练习池上事先跑一次并冻结（防 G4）。设计 §6 把"VELEST 联合反演后的残差和台站校正"列为反馈内容——作为诊断可以，作为奖励要冻结。
3. **用半合成数据（T3）标定奖励**：在已知真值的半合成事件上注入已知拾取误差（单个粗差、单台小偏差、整体平移、S 漏拾），检查每个奖励项能否发现。这一步回答"残差能发现多大的误差"，与方向 3 对接。
4. **报告奖励准确率**：在练习池的有标签子集上统计残差判定与标签判定的一致率。若低于约 60%（随意设的经验门槛，需在试点中定），H3 的预期应降低。
5. **把 H3 从"相当"改为"恢复了标签反馈收益的百分之多少"**：例如 (A-physics − A-placebo) / (A-label − A-placebo)，带置信区间。"相当"需要等效性检验，样本量要求高（见方向 13）。

### 防刷分约束

- 设计 §6 说"任何一项低于基线就判为不合格"——**基线应改为宿主机定义的可拾集合**，否则 agent 可以从一开始就少拾（A0 的低 recall 就会变成基线）。
- 删除台站必须附波形理由（决策记录），宿主机统计"无波形理由的删除"比例。
- 学习曲线图（图 3）里，覆盖度、"拉向预测"指数和与 PhaseNet 的一致率要和主指标画在一起。

### 对照组

- **保留** A-placebo、A-generic、A-bestofN。
- **新增**（按优先级）：
  1. **A-physics 无约束**（物理奖励但不加覆盖度约束）——如果它确实出现刷分，就是论文中"约束必要"的直接证据，也呼应 [1] 中"必须报告虚假奖励基线"的建议；
  2. **无反馈反思**（只让 agent 回顾自己的做法）——区分"反思本身"和"反馈信息"[11]；
  3. **台站内打乱残差**——保留残差分布、破坏台站对应；
  4. **随机反馈**（只在开源模型上做，省钱）。
- **A-placebo 的错配事件**要按震级和台站数匹配，台站名映射到本事件，避免 agent 识破。
- H3 至少在两个模型家族上做（GPT + 开源），并在 T2 上方向一致 [1][2]。

## 未解决与待核

- Spurious Rewards 中格式奖励和多数投票奖励的具体数值只在图中，未核 [1]。
- PhaseNet-DAS 期刊版中"自监督难以达到拾取的时间精度"一句只见于检索摘录 [26]，需打开原文核对。
- AI-PAL 的作者和具体数字只见于检索记录 [29]；PhaseNO 的具体性能数字未核 [28]。
- 互相关差分时的精度（常见说法为毫秒级）未打开原文核实 [36]；需要方向 3 的报告给出 Ridgecrest 上的具体数字。
- 没有找到直接以定位残差为目标优化拾取的工作，也没有找到 LLM agent 记忆学习中使用"随机反馈"或"打乱反馈"对照的已发表工作（Tang 等 2026 的 FGSE 用了"随机抽取探针"的消融 [24]，但我只读到摘要）——这可能是本项目方法学上的新意，需在方向 15 中再查。
- "奖励准确率"的可接受下限没有文献依据，需要用练习池的有标签子集在试点中估计。
- 非 ML 特征函数在低信噪比缓起震相上的可靠性未知；若太差，主奖励会在 agent 的优势区失效。建议在 T3 上先测。
- 需要问 Advikar：试点中内循环（留一残差驱动重拾）有多少次修改是朝预测到时方向的，修改后与分析员拾取是更近还是更远——这是"拉向预测"指数的第一批数据。

## 参考文献

1. Shao, R., Li, S. S., et al. (2025). Spurious Rewards: Rethinking Training Signals in RLVR. arXiv:2506.10947 (v2 2026-02-25). https://arxiv.org/abs/2506.10947 [已读原文（HTML 前半部分）]
2. Wu, Zhang, Dong 等 (2025). Reasoning or Memorization? Unreliable Results of Reinforcement Learning Due to Data Contamination. arXiv:2507.10532. https://arxiv.org/abs/2507.10532 [只读摘要]
3. Zuo, Y., Zhang, K., Sheng, L., et al. (2025). TTRL: Test-Time Reinforcement Learning. arXiv:2504.16084. https://arxiv.org/abs/2504.16084 [已读原文（HTML）]
4. Shafayat, S., Tajwar, F., Salakhutdinov, R., Schneider, J., Zanette, A. (2025). Can Large Reasoning Models Self-Train? arXiv:2505.21444. https://arxiv.org/abs/2505.21444 [已读原文（HTML 前 2/3）]
5. Zhao, X., Kang, Z., Feng, A., Levine, S., Song, D. (2025). Learning to Reason without External Rewards (INTUITOR). ICLR 2026. arXiv:2505.19590. https://arxiv.org/abs/2505.19590 [只读摘要]
6. Zhang et al. (2025). No Free Lunch: Rethinking Internal Feedback for LLM Reasoning. arXiv:2506.17219. https://arxiv.org/abs/2506.17219 [只读摘要]
7. Agarwal, S., Zhang, Z., Yuan, L., Han, J., Peng, H. (2025). The Unreasonable Effectiveness of Entropy Minimization in LLM Reasoning. arXiv:2505.15134. https://arxiv.org/abs/2505.15134 [只读摘要]
8. Yuan, W., Pang, R. Y., Cho, K., et al. (2024). Self-Rewarding Language Models. ICML 2024. arXiv:2401.10020. https://arxiv.org/abs/2401.10020 [只读摘要]
9. Zhou, X., Liu, Z., Sims, A., et al. (2025). Reinforcing General Reasoning without Verifiers (VeriFree). ICLR 2026. arXiv:2505.21493. https://arxiv.org/abs/2505.21493 [只读摘要]
10. Wang, X., Wei, J., Schuurmans, D., et al. (2022). Self-Consistency Improves Chain of Thought Reasoning in Language Models. ICLR 2023. arXiv:2203.11171. https://arxiv.org/abs/2203.11171 [只读摘要]
11. Huang, J., Chen, X., 等 (2023). Large Language Models Cannot Self-Correct Reasoning Yet. ICLR 2024. arXiv:2310.01798. https://arxiv.org/abs/2310.01798 [已读原文（HTML 相关章节）]
12. Ouyang, S., Yan, J., et al. (2025). ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory. ICLR 2026. arXiv:2509.25140. https://arxiv.org/abs/2509.25140 [已读原文（HTML 前 4/5）]
13. Min, S., Lyu, X., Holtzman, A., Artetxe, M., Lewis, M., Hajishirzi, H., Zettlemoyer, L. (2022). Rethinking the Role of Demonstrations: What Makes In-Context Learning Work? EMNLP 2022. arXiv:2202.12837. https://arxiv.org/abs/2202.12837 [只读摘要]
14. Pan, A., Jones, E., Jagadeesan, M., Steinhardt, J. (2024). Feedback Loops With Language Models Drive In-Context Reward Hacking. ICML 2024. arXiv:2402.06627. https://arxiv.org/abs/2402.06627 [已读原文（HTML 前 2/3）]
15. Manheim, D., Garrabrant, S. (2018). Categorizing Variants of Goodhart's Law. arXiv:1803.04585. https://arxiv.org/abs/1803.04585 [已读原文]
16. Skalse, J., Howe, N., Krasheninnikov, D., Krueger, D. (2022). Defining and Characterizing Reward Gaming. NeurIPS 2022. arXiv:2209.13085. https://arxiv.org/abs/2209.13085 [只读摘要]
17. Gao, L., Schulman, J., Hilton, J. (2022). Scaling Laws for Reward Model Overoptimization. ICML 2023. arXiv:2210.10760. https://arxiv.org/abs/2210.10760 [只读摘要]
18. Krakovna, V., Uesato, J., et al. (2020). Specification gaming: the flip side of AI ingenuity. DeepMind blog, 2020-04-21. （原链接已迁移至 deepmind.google）[未打开原文]
19. METR (2025). Recent Frontier Models Are Reward Hacking. Blog, 2025-06-05. https://metr.org/blog/2025-06-05-recent-reward-hacking [只读摘要（检索摘录）]
20. Baker, B., Huizinga, J., Gao, L., et al. (2025). Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation. arXiv:2503.11926. https://arxiv.org/abs/2503.11926 [只读摘要]
21. MacDiarmid, M., Hubinger, E., et al. (2025). Natural Emergent Misalignment from Reward Hacking in Production RL. arXiv:2511.18397. https://arxiv.org/abs/2511.18397 [只读摘要（检索摘录）]
22. (Fudan 等) (2026). Reward Hacking in the Era of Large Models（综述）. arXiv:2604.13602. https://arxiv.org/abs/2604.13602 [未打开原文]
23. Kapoor, S., Stroebl, B., Siegel, Z. S., Nadgir, N., Narayanan, A. (2024). AI Agents That Matter. arXiv:2407.01502. https://arxiv.org/abs/2407.01502 [只读摘要]
24. Tang, R., Gao, H., et al. (2026). When Should Agents Remember? Falsification-Gated Self-Evolution for LLM Agents. arXiv:2611.14326. https://arxiv.org/abs/2611.14326 [只读摘要]
25. Ye, Q., Li, Y., Pruksachatkun, Y., Zhang, J., Wu, C.-S. (2026). On the Fragility of Self-Improving Agents: Variance, Task Order, and Underspecification. arXiv:2608.18066. https://arxiv.org/abs/2608.18066 [已读原文（HTML 前 2/3）]
26. Zhu, W., Biondi, E., Li, J., Yin, J., Ross, Z. E., Zhan, Z. (2023). Seismic arrival-time picking on distributed acoustic sensing data using semi-supervised learning. Nature Communications 14. https://doi.org/10.1038/s41467-023-43355-3 ; arXiv:2302.08747 [只读摘要]
27. Zhu, W., McBrearty, I., Mousavi, S. M., Ellsworth, W. L., Beroza, G. C. (2022). Earthquake Phase Association using a Bayesian Gaussian Mixture Model. JGR Solid Earth 127, e2021JB023249. arXiv:2109.09008 [只读摘要]
28. Sun, H., Ross, Z. E., Zhu, W., Azizzadenesheli, K. (2023). Phase Neural Operator for Multi-Station Picking of Seismic Arrivals. arXiv:2305.03269. https://arxiv.org/abs/2305.03269 [只读摘要（检索摘录）]
29. AI-PAL: Self-Supervised AI Phase Picking via Rule-Based Algorithm for Generalized Earthquake Detection. JGR Solid Earth (2025)（作者未核）. [只读摘要（检索摘录）]
30. Shi, P., Meier, M.-A., Villiger, L., et al. (2024). From Labquakes to Megathrusts: Scaling Deep Learning Based Pickers Over 15 Orders of Magnitude. JGR: Machine Learning and Computation 1, e2024JH000220. https://orca.cardiff.ac.uk/174100 [只读摘要]
31. Zhu, W., Rong, B., Jie, Y., Wei, S. S. (2025). Robust Earthquake Location using Random Sample Consensus (RANSAC). arXiv:2502.10933. https://arxiv.org/abs/2502.10933 [只读摘要]
32. Rowe, C. A., Aster, R. C., Borchers, B., Young, C. J. (2002). An Automatic, Adaptive Algorithm for Refining Phase Picks in Large Seismic Data Sets. BSSA 92(5). https://doi.org/10.1785/0120010224 [只读摘要]
33. Rowe, C. A., Aster, R. C., Phillips, W. S., Jones, R. H., Borchers, B., Fehler, M. C. (2002). Using Automated, High-precision Repicking to Improve Delineation of Microseismic Structures at the Soultz Geothermal Reservoir. Pure Appl. Geophys. 159, 563–596. https://doi.org/10.1007/PL00001265 [只读摘要]
34. Iversen, E. S., Lees, J. M. (1996). A statistical technique for validating velocity models. BSSA 86(6), 1853–1862. https://doi.org/10.1785/BSSA0860061853 [只读摘要]
35. Bondár, I., Myers, S. C., Engdahl, E. R., Bergman, E. A. (2004). Epicentre accuracy based on seismic network criteria. Geophys. J. Int. 156, 483–496. [只读摘要（检索摘录）]
36. Schaff, D. P., Bokelmann, G. H. R., Ellsworth, W. L., Zanzerkia, E., Waldhauser, F., Beroza, G. C. (2004). Optimizing correlation techniques for improved earthquake location. BSSA 94(2). [未打开原文]
37. Physics-Aware Machine Learning for Seismic and Volcanic Signal Interpretation（综述）. arXiv:2603.17855. https://arxiv.org/abs/2603.17855 [只读摘要（检索摘录）]
- [本地试点] advikar_pilot_summary.md（本目录上级），Advikar 试点报告整理。
