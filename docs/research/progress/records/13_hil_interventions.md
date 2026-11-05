# human-in-loop 干预编码

本记录对应登记表 B14：把六个案例 human-in-loop 流程（专家流程）建成可达结果目录所做的每一项干预逐条编码，用来估计 S3（工具 + 知识 + checker）最多能补上多少差距，以及哪一部分没有参考目录任何 Agent 都达不到。四个类别：**1 执行或工具**——修正工具调用、文件处理、重采样、接口错误，可由工具自动化（S1）；**2 方法选择**——在看结果之前就能知道的方法或参数范围（模板匹配、EDT 似然、大事件直接 ML、台站延迟、分层与梯度模型等），可由知识自动化（S2/S3）；**3 无参考诊断**——只从目录自身症状发现的问题（网格边界深度堆积、尾波幽灵、发震时刻与深度耦合等），可由 checker 自动化（S3）；**4 依赖参考的诊断**——通过与参考目录比较才发现或调好的改动（取自目标论文的速度模型、按官方目录重标定的震级、按参考召回率调的门槛等），没有参考就无法自动化。来源：各案例 `workflows/tasks/<case>/expert/PLAN.md`（Ridgecrest 另读 `expert/docs/EVOLUTION.md`、`OPTIMIZATION.md`、`export/03_location_experiments/01_relative_location/14_tune_hypodd/README.md`、`03_experiments/67_coda_duplicates_audit/README.md`），`evaluation/human_in_loop/expert_ladder.yaml` 与 `expert_ladder.json`（metrics v2，2026-11-05 生成，评分器提交 bb1fde8；位置指标相对主绝对定位参考），以及 [`00_expert_experience_evidence.md`](00_expert_experience_evidence.md)、[`11_hil_relocation.md`](11_hil_relocation.md)。编码日期 2026-11-05。

## 1. 编码约定

- 编码单位：阶梯中每个被采纳的轮次或步骤一行；同一轮里性质不同的子项（例如工具修正与方法改动）分行；PLAN.md 中写清楚、并且留下教训的未采纳尝试也各占一行，在“干预”栏注明“未采纳”。各案例起点（r1 / 01_baseline）的速度模型选择也作为一行，它的效果包含在起点里，阶梯无法度量。
- 类别按改动是怎样被发现或调定的来判：来源写明是因为与参考目录比较而改的，即使同时存在无参考症状也归 4，并在备注里说明（规则来自任务说明）。改动本身是标准方法（第 2 类），但来源显示其触发或取舍依据参考比较时，仍按方法归 2，标“存疑”并写出备选类别 4；参数取值本身是按参考召回或残差调定的（门槛、盆地层、eps 等），归 4。
- 每个存疑项都给出“备选”类别，第 3 节据此给出主编码、乐观（存疑项取更易自动化的类别）和悲观（存疑项取更难自动化的类别）三种口径。
- 阶梯效果摘自 `expert_ladder.json` 的 headline：`recall_norm`（归一化召回）、`shift_km`、`scatter_median_km`（简写 scatter）、`dz_median_km`（dZ）、`dmag_std`、`off_structure_fraction`（off）、`f1_M2`（F1(M2+)）。PLAN.md 中的数字多为当时的 metrics v1 或阶段 05 读数，引用时注明“PLAN”。

## 2. 逐案例编码

### Prague 2011（阶梯 r1–r7；最终目录 r8 = r7 加网格精度标注）

| 轮次 | 干预（简述） | 类别 | 依据（PLAN.md 的段落或阶梯步骤） | 阶梯效果 |
|---|---|---|---|---|
| r1 起点 | 速度模型取 Keranen et al. (2013)，从 figshare 矢量图 DR1 读出 6 层，按阶跃分层使用 | 2（存疑，备选 4：该模型由本序列自身到时反演，属目标事件的专门文献；Cochran 引用它，但不是评分参考本身） | Data preparation；r1 读数“signed dt vs Cochran +0.07 s，不需要发震时刻校正” | 起点：recall_norm 1.173，scatter 0.442 km，shift 0.185 km |
| r1 | TA 台站日文件改变分量采样相位，FFT 重采样保留了原起点；改为抗混叠后重采样到绝对 100 Hz 网格（Lanczos a=20） | 1 | r1 “02: … 18 TA blocks failed the component-grid check” | r1 内部修复，无独立阶梯步 |
| r2 | NonLinLoc 台站延迟（两次迭代） | 2 | Expected knob ladder 第 1 项（Maple r5 的经验）；r2 “Neutral … Kept (harmless)” | recall_norm 1.173→1.171；scatter 0.442→0.442 km（中性） |
| r3 | 加入阶段 60 Match&Locate；门槛 N×MAD 9.5 由零假设运行（通道循环平移）定出 | 2 | Expected knob ladder 第 2 项（r1 之前已列出，理由含“Cochran 本身是模板增强目录”）；r3 零假设表 | recall_norm 1.171→1.833；scatter 0.442→0.451 km；dmag_std 0.344→0.374 |
| r3（未采纳） | 复核合并门槛（1 s/2 km、0.5 s/1 km 等），按 Cochran 召回和近重复数比较，保留 2 s/5 km；查明“并集比 M&L 单独低约 1 点”是评分框的假象 | 4 | r3 “The union scoring ~1 point below M&L alone is a box-scoring artifact” | 无（未形成新轮次） |
| r4 | 定位质量规则：拾取事件和模板都须有 ≥ 1 条波形互相关连接 | 4（存疑，备选 3：规则只用内部量，checker 的孤立事件检查可发现；但触发是 Ridgecrest 之后的跨案例复核，偏离构造比例按“距所有 Cochran/McMahon 事件 > 1 km”定义，候选规则按 Cochran 召回取舍） | r4 (2026-10-26) | recall_norm 1.833→1.835；scatter 0.451→0.409 km；off 1.54 %→0.98 % |
| r5 | NonLinLoc LOCMETH 由 GAU_ANALYTIC 改为 EDT_OT_WT；阶段 64 把 M&L 事件随模板位移搬到新框架 | 2（存疑，备选 4：EDT 对离群拾取稳健是先验知识，合成测试中一个 2 s 离群拾取使 GAU 深度移动 2.3 km；但采纳依据是阶段 70 按 Cochran/McMahon 评分的方法比较） | Method comparison (stage 70)；r5 (2026-10-27)。阶段 70 另发现定位器间离散可作无参考质量指标（与误差 Spearman 0.59） | recall_norm 1.835→1.850；scatter 0.409→0.306 km；shift 0.225→0.176 km；dZ −0.02→+0.12 km；off 0.98 %→0.04 % |
| r6 | 阶段 65：大事件直接计算 ML（24 个事件采用） | 2（存疑，备选 4：直接 ML 是标准做法，但缺陷是 metrics v1 按震级分档与参考比较后才暴露） | Baseline corrections (2026-10-28)；阶梯步 “direct ML (stage 65)” | 阶梯主指标不变（dmag_std 0.373→0.373，F1(M2+) 0.984→0.984） |
| r7 | 阶段 67：删除较大事件尾波中的 M&L 幽灵检测（本案 1 个） | 4（存疑，备选 3：规则来自不看参考的盲审波形复核，症状无参考可见；但缺陷由 metrics v1 的分档精度暴露） | Baseline corrections；阶梯步 “coda ghosts removed (stage 67)”；Ridgecrest 盲审 README | F1(M2+) 0.984→0.992；其余不变 |
| r8（未采纳重定位） | 互相关重定位（GrowClust；另测 hypoDD 拾取 + 互相关）：相对位置误差变差，不采用，只标注网格精度 | 4 | 11_hil_relocation 结果与决定（Cochran 相对误差 0.29→0.46 km；hypoDD 0.32→0.41 km） | 未进入阶梯 |

### Magna 2020（阶梯 r1–r8、r10、r11；r9 被否决；最终目录 r12 = r11 加标注）

| 轮次 | 干预（简述） | 类别 | 依据（PLAN.md 的段落或阶梯步骤） | 阶梯效果 |
|---|---|---|---|---|
| r1 起点 | 速度模型 Bjarnason & Pechmann (1989) Wasatch front；震级暂用南加州 Hutton–Boore | 2 | Round mechanics 的 knob ladder；r1 (2026-10-18) | 起点：recall_norm 0.678，scatter 0.823 km，dmag_std 0.208 |
| r2 | 犹他 ML 重标定：按 UUSS ML 拟合几何扩散项和常数（385 个匹配事件） | 4 | r2 “Utah ML recalibration”；r1 读数“ML 系统性偏高 +0.62…+0.65（相对三个参考）” | dmag_std 0.208→0.147；召回、定位不变 |
| 关联阶梯（未采纳） | DBSCAN eps、oversample、max_sigma11、最小拾取数四个变体，按 Pang 匹配数判为无效或变差 | 4 | Association rung (2026-10-19) | 无 |
| r3 | ML 台站校正（31 项，取自 UUSS ML 锚定拟合的台站中位残差） | 4 | r3 “ML station corrections” | dmag_std 0.147→0.127 |
| r3 子项 | 台站校正符号写反：每事件台站 ML 的 MAD 翻倍（0.131→0.246），丢弃该运行并更正 | 1 | r3 “Sign convention (learned the hard way)” | 无（被丢弃的运行） |
| r4 | 速度模型加 0–2 km 盆地充填层（Vp 4.0）；变体按相对 Pang/UUSS 的 dt、dZ 选定 | 4（来源写明诊断为“相对参考偏深且偏晚”；同时存在无参考症状：194 个事件贴近深度网格边界，r4 后为 46） | r4 “Diagnosis on r3 … deep … and late vs both references”；扫描表 | recall_norm 0.678→0.721；scatter 0.823→0.895 km；shift 1.118→1.228 km；dZ +0.41→+0.08 km |
| r5 | PhaseNet 门槛 0.3→0.2，按三个参考的锚定增长与噪声代价在 0.3/0.2/0.15 中选定 | 4（存疑，备选 2：降低拾取门槛属已知做法，但取值依据参考召回） | r5 “PhaseNet pick thresholds” | recall_norm 0.721→0.771；scatter 0.895→0.899 km；dZ +0.08→−0.01 km |
| r6 | 新增阶段 52 双差重定位（hypoDD，CT + CC，控制文件取 Ridgecrest cc3_d1） | 2（存疑，备选 4：双差是标准方法；动机写作“r4 之后 Pang dZ MAD 停在绝对定位下限”，即按参考判断） | r6 “double-difference relocation (new stage 52)” | 本步阶梯无变化（DD 位置在 r7 进入目录）；PLAN：Pang dEpi 1.42→0.85 km，dZ MAD 1.07→0.81 km |
| r6 子项 | 自建 CC 内核：放弃 FDTCC（文件组织不符）、按 TRACE 库重编 hypoDD 并加大容量、合成双道单元测试核对时差符号 | 1 | r6 “Architecture … Kernel … Sign convention unit-tested” | 并入 r6/r7 |
| r6 子项 | hypoDD 平层解析射线、台站钉在模型顶，深度比 NLL 浅约 0.9 km；用仅 CT 对照和空间均匀性确认后加常数基准偏移 0.90 km | 3（存疑，备选 4：偏移相对 NLL 可在内部测出，但文中称其为“与 r2 ML 常数同等地位的样本内标定”，配对读数用的是 Pang dZ） | r6 “Depth datum” | 并入 r6/r7 |
| r7 试点子项 | 工具修正：越界插值、km→度换算丢掉一个网格点（360 对 405）、零填充模板窗口 SNR = ∞ 被放行 | 1 | r7 pilot “Fixes found by the pilot (tool side)” | 无独立阶梯步 |
| r7 | 加入阶段 60 Match&Locate；门槛 N×MAD 9 由零假设运行定出 | 2（存疑，备选 4：动机是“Pang 未匹配的主体是低于拾取下限的模板检测”；试点中通道距离 ≤ 20 km、0.5 km 模板覆盖和 6 s 合并间隔都按 Pang 召回选定） | r7 pilot、pilot round 2、full run、catalog | recall_norm 0.771→1.142；scatter 0.899→0.462 km；shift 1.217→0.725 km；dmag_std 0.126→0.209；F1(M2+) 0.993→0.942（含 r6 双差位置进入目录） |
| r7（未采纳） | 用“推导拾取”（模板到时 + 节点时差，经相关修正）把新事件送入双差：每事件中位 3 个拾取，过弱，删除该阶段 | 3（存疑，备选 4：拒绝的主要理由是内部拾取数；另一理由“M&L 位置相对 Pang 已达双差水平”依赖参考） | r7 catalog “Relocation” | 无 |
| r8 | 弱约束事件加深度先验 N(9.24, 2 km)（取自本轮自身约束好的事件，不用参考）；双差从修正后深度出发；双差竖向位移 > 3 km 的结果不接受 | 4（存疑，备选 3：发现经过是“沿走向剖面 0–5 km 条带在 Pang 中不存在”，并用 Pang 匹配确认；症状本身——浅部条带、σz 大、拾取少、发震时刻偏晚、模型界面下的细线——无参考可见） | r7 known issue；r8 (2026-10-22) | recall_norm 1.142→1.142；scatter 0.462→0.474 km；shift 0.725→0.951 km；dZ −0.23→+0.09 km；PLAN：浅部条带 528→224 行 |
| r9（未采纳） | 速度模型改为阶跃分层：所有相对参考的定位统计变差，否决（盆地层是在线性渐变下调定的） | 4 | r9 “test: step velocity layering (rejected)” | 无 |
| EDT 测试（未采纳） | NLL EDT_OT_WT：震中离各参考远 0.4 km，深度移约 1 km，保留 GAU | 4 | NonLinLoc EDT_OT_WT test (2026-10-27) | 无 |
| r10 | 阶段 65：直接 ML（13 个事件采用） | 2（存疑，备选 4：同 Prague r6） | Baseline corrections；阶梯步 “direct ML (stage 65)” | dmag_std 0.209→0.207；F1(M2+) 0.948→0.945；PLAN：dmag_mean_M5 −0.98→−0.24 |
| r11 | 阶段 67：删除尾波幽灵（15 个） | 4（存疑，备选 3：同 Prague r7） | Baseline corrections | recall_norm 1.1423→1.1428；F1(M2+) 0.945→0.958 |
| r12（未采纳重定位） | 互相关重定位（GrowClust）：相对位置误差变差，不采用 | 4 | 11_hil_relocation（Pang 0.81→1.46 km） | 未进入阶梯 |

### Maple Creek 2017（阶梯 r1–r11；最终目录 r12 = r11 加标注）

| 轮次 | 干预（简述） | 类别 | 依据（PLAN.md 的段落或阶梯步骤） | 阶梯效果 |
|---|---|---|---|---|
| r1 起点 | 速度模型取 UUSS Yellowstone 1-D（Pang et al. 2019 SI Table S1） | 4（存疑，备选 2：取自研究本序列的目标论文附录；模型本身是 UUSS 的业务模型，懂区域的 Agent 也可能找到） | Data preparation | 起点：recall_norm 0.942，scatter 0.990 km，shift 0.678 km |
| r2 | 修正速度模型表示：GaMMA `np.interp` 和 NLL `LAYER` 把层顶之间做了线性渐变，改为阶跃分层 | 1（存疑，备选 4：这是流程实现的接口错误；发现经过是 NLL 发震时刻相对 ComCat 晚 +0.47 s、深 +0.9 km，并用 Shelly 到时排除拾取原因；无参考症状是 P 晚 S 早的残差图样和发震时刻–深度耦合） | r1 “Diagnosis — systematic origin-time/depth bias”；r2 | recall_norm 0.942→0.927；scatter 0.990→1.220 km；shift 0.678→1.014 km；PLAN：dt vs ComCat +0.47→−0.05 s |
| r3 | 加入 8 个仅垂直分量的 WY 台站（只用 P 拾取） | 2 | Expected knob ladder 第 1 项（r1 之前列出） | recall_norm 0.927→0.947；scatter 1.220→0.928 km |
| r4 | 仅垂直分量台站的水平分量改为复制 Z（原为补零，PhaseNet 在零水平分量上欠拾取） | 1（发现依据为内部拾取数：YGC 8 天 502 个 P，对 YMC 12,822；测试用邻台拾取佐证，不用参考） | r3 结尾；r4 | recall_norm 0.947→0.962；scatter 0.928→0.825 km；off 4.4 %→7.3 % |
| r5 | NLL 台站延迟（两次迭代） | 2（r2 读数中 P 晚 S 早的内部残差图样指向台站项；文献 Vp/Vs 偏低作旁证） | r2 Verdict；r5 | recall_norm 0.962→0.961；scatter 0.825→0.682 km；shift 0.838→0.460 km |
| r6 | 加入阶段 60 Match&Locate；门槛 N×MAD 9 由零假设运行定出 | 2 | Expected knob ladder 第 5 项（r1 之前列出）；r6 | recall_norm 0.961→1.006；scatter 0.682→0.702 km；off 7.2 %→2.3 % |
| r7 | 加密模板（min_stations 10→8，覆盖半径 0.5→0.3 km），门槛按零假设调到 9.25 | 2（存疑，备选 4：模板密度是已知参数；取舍参考了 Magna 按 Pang 调出的经验，效果按 Shelly 召回读） | r7 “knob: Match&Locate template density” | recall_norm 1.006→1.004；scatter 0.702→0.700 km；off 2.3 %→3.5 % |
| r8 | 定位质量规则（≥ 1 条 CC 连接 + 方位间隙 ≤ 150° + σx ≤ 0.8 km，即 Ridgecrest 规则） | 4（存疑，备选 3：同 Prague r4，偏离构造按 ComCat 定义，候选规则按 Shelly/ComCat 召回取舍） | r8 (2026-10-26) | recall_norm 1.004→0.992；scatter 0.700→0.715 km；off 3.5 %→1.5 % |
| r9 | NLL EDT_OT_WT；阶段 64 搬移 M&L 事件 | 2（存疑，备选 4：同 Prague r5） | r9 (2026-10-27) | recall_norm 0.992→0.994；scatter 0.715→0.653 km；shift 0.525→0.591 km；off 1.5 %→0.28 % |
| r10 | 阶段 65：直接 ML（2 个事件采用） | 2（存疑，备选 4：同 Prague r6） | Baseline corrections | dmag_std 0.291→0.288；PLAN：dmag_mean_M4 −0.90→−0.21 |
| r11 | 阶段 67：删除尾波幽灵（2 个） | 4（存疑，备选 3：同 Prague r7） | Baseline corrections | 阶梯指标不变 |
| r12（未采纳重定位） | 互相关重定位（GrowClust）：相对位置误差变差，不采用 | 4 | 11_hil_relocation（ComCat 0.69→0.74 km） | 未进入阶梯 |

### Kīlauea 2018（阶梯 r1、r2、r3、r4、r7–r9；r2、r5、r6 被否决；最终目录 r10 = r9 加标注）

| 轮次 | 干预（简述） | 类别 | 依据（PLAN.md 的段落或阶梯步骤） | 阶梯效果 |
|---|---|---|---|---|
| r1 起点 | 速度模型取 HVO 业务 HYPOINVERSE 模型（Klein 线性梯度，USGS OFR 02-157），线性表示；Vs = Vp/1.78 | 2（存疑，备选 4：Vp/Vs 1.78 取自主参考 Shelly & Thelen (2019)） | Data preparation | 起点：recall_norm 0.965，scatter 0.678 km，dmag_std 0.135 |
| r2（未采纳） | 关联范围收缩到山顶：前主震召回不变，判为检测门槛问题，恢复 r1 | 4（存疑，备选 3：触发是前 Mw 6.9 相对 Shelly 召回 0.10；机制——412 个吸收事件堆在关联范围东边界、发震时刻早 4.3 s——无参考可见，00 号记录把它列为 checker 关联检查的来源） | r1 Diagnosis；r2 “rejected” | 阶梯中的分支：recall_norm 0.965→0.964；scatter 0.678→0.685 km（r3 回到 r1 配置） |
| r3 | Wood–Anderson 预滤波 0.1–0.2 Hz 改为 0.5–1 Hz（3,644 个台站测量中 3,132 个因 SNR < 3 被拒） | 3 | r3 | 相对 r1：dmag_std 0.135→0.252（有 ML 的事件 55→74，新增的多为低 SNR）；F1(M2+) 0.851→0.865 |
| r4 | 加入阶段 60 Match&Locate；门槛 N×MAD 9.5 由零假设运行定出 | 2（存疑，备选 4：动机写作“Shelly 是模板匹配目录，前主震缺口是检测问题”） | r4 | recall_norm 0.965→1.218；scatter 0.678→0.705 km；shift 0.440→0.564 km；dmag_std 0.252→0.502；F1(M2+) 0.865→0.749 |
| r4 子项 | 工具输入适配：HVO 梯度模型加密为 0.2 km 常数子层（工具按常数层处理）；山顶 S−P < 1.7 s，关闭 `exclude_p_overlapping_s` | 1 | r4 第一段 | 并入 r4 |
| r5（未采纳） | 收不含 S 的事件（最小拾取 6 P / 0 S）并按主震前后分期选模板：一个错误定位的模板（gamma_0000094）把约 160 个检测放到 Shelly 前主震簇外约 6 km | 4（缺陷靠与 Shelly 前主震簇比较发现；偏离构造指标没有看出） | r5 “not adopted as exported” | 未进入阶梯（PLAN：Shelly 0.641→0.716，前主震匹配偏离 5.9 km） |
| r5 子项（未采纳轮内） | NLL 最小相数仍为 10/3，所有仅 P 事件定位失败；改为 6/无 S | 1 | r5 Knobs 第 1 项括注 | 无 |
| r6（未采纳） | 阶段 62 模板互相关双差重定位，再加 Ridgecrest/Maple 定位质量规则：前主震族整体错位，相对重定位修不了；规则误删大量正常事件 | 4 | r6 表与 Decision (2026-10-26) | 未进入阶梯 |
| r7 | NLL EDT_OT_WT；阶段 64 搬移 M&L 事件 | 2（存疑，备选 4：同 Prague r5） | r7 (2026-10-27) | recall_norm 1.218→1.224；scatter 0.705→0.612 km；F1(M2+) 0.749→0.768 |
| r8 | 阶段 65：直接 ML（313 个事件采用） | 2（存疑，备选 4：同 Prague r6） | Baseline corrections | dmag_std 0.501→0.497 |
| r9 | 阶段 67：删除尾波幽灵（49 个） | 4（存疑，备选 3：同 Prague r7） | Baseline corrections | recall_norm 1.224→1.223；F1(M2+) 0.765→0.785 |
| r10（未采纳重定位） | 互相关重定位（GrowClust）：相对位置误差变差，不采用 | 4 | 11_hil_relocation（Wei 0.70→0.84 km） | 未进入阶梯 |

### Kaikōura 2016（阶梯 r1–r9；r9 为采纳的互相关重定位）

| 轮次 | 干预（简述） | 类别 | 依据（PLAN.md 的段落或阶梯步骤） | 阶梯效果 |
|---|---|---|---|---|
| r1 起点 | 速度模型取 Chamberlain et al. (2021) 代码库中 NZ3D 的一维平均（25 行） | 4（存疑，备选 2：来自参考目录 Chamberlain 的论文代码；NZ3D 本身公开，懂区域的 Agent 可以自己求平均） | Data preparation | 起点：recall_norm 0.800，scatter 2.940 km，shift 2.122 km |
| r1 | GeoNet 日文件在午夜改变采样相位，18 个块失败：偏离绝对网格的目标采样率道也做 Lanczos 插值；元数据分段（几何相同、时间连续）的台站允许跨段 | 1 | Data preparation（split epochs）；r1 “02: first attempt failed …” | r1 内部修复 |
| r2 | NLL 台站延迟（两次迭代，Maple r5 设置） | 2（理由“~200 km 范围单一一维平均、RMS 0.39 s，台站项是第一杠杆”） | r1 结尾；r2 | recall_norm 0.800→0.806；scatter 2.940→2.348 km；shift 2.122→2.381 km |
| r3 | GaMMA DBSCAN eps 10→15 s，按 GeoNet/Chamberlain/Tan 匹配在 5、10、15、20 s 中选定 | 4（存疑，备选 3：触发是“漏掉的 GeoNet 事件随震级增大而变多”；机制——260 km 孔径下一个事件的拾取跨 > 40 s，被拆成过不了最小拾取门槛的子簇，大事件拾取 0 % 被关联——无参考可见） | r3 | recall_norm 0.806→0.882；scatter 2.348→2.971 km；shift 2.381→1.136 km；F1(M2+) 0.855→0.944 |
| r3（未采纳） | 降低最小拾取数 / 台站数：新增事件约 25 % 匹配参考，判为多数虚假 | 4 | r3 “Pick-gate test on top of eps 15” | 无 |
| r4 | 加入阶段 60 Match&Locate；门槛 N×MAD 9.5 由零假设运行定出 | 2（存疑，备选 4：动机是相对 Tan、Chamberlain 的小事件缺口） | r4 | recall_norm 0.882→1.105；scatter 2.971→3.139 km；dmag_std 0.198→0.324 |
| r4 子项 | 工具输入适配：NZ 模型加密为 0.5 km 常数子层至 60 km（首波搜索随层数平方增长）；`max_distance_km` 80（中位事件 20 km 内只有 1 个台站） | 1 | r4 第一段 | 并入 r4 |
| r5 | 加密模板（覆盖半径 2→1 km，min_stations 10→8），门槛按零假设调到 10 | 2（存疑，备选 4：漏检诊断是“Tan 召回随与最近模板距离下降”，依赖参考） | r5 | recall_norm 1.105→1.167；scatter 3.139→2.961 km；dmag_std 0.324→0.429 |
| r6 | NLL EDT_OT_WT；阶段 64 搬移 M&L 事件 | 2（存疑，备选 4：同 Prague r5） | r6 (2026-10-27) | recall_norm 1.167→1.170；scatter 2.961→2.785 km；dZ −1.20→−0.87 km |
| r7 | 阶段 65：直接 ML（278 个事件采用） | 2（存疑，备选 4：同 Prague r6） | Baseline corrections | dmag_std 0.431→0.412；F1(M2+) 0.933→0.927 |
| r8 | 阶段 67：删除尾波幽灵（3 个） | 4（存疑，备选 3：同 Prague r7） | Baseline corrections | 基本不变（F1(M2+) 0.9274→0.9278） |
| r9 | 互相关重定位（GrowClust）：7,913 个事件采用，依据是相对 Chamberlain 的相对位置误差 1.53→0.69 km | 4 | 11_hil_relocation 结论 3 与决定；阶梯步 “CC relocation (GrowClust)” | recall_norm 1.1703→1.1706；scatter 2.785→3.059 km；shift 1.135→1.366 km；dZ −0.87→−0.32 km |

### Ridgecrest 2019（阶梯 01_baseline、07–12、53、56、57；最终目录 68_cc_relocation = 57 加标注）

| 轮次 | 干预（简述） | 类别 | 依据（PLAN.md 的段落或阶梯步骤） | 阶梯效果 |
|---|---|---|---|---|
| 01_baseline 起点 | 速度模型取 Shelly (2020) Table 1（主参考的论文），按线性插值使用 | 4 | PLAN Workflow 第 4 步；EVOLUTION.md “The original linear-interpolated velocity implementation …”；00 号记录 1.4 节 | 起点：recall_norm 1.146，scatter 0.755 km，dZ −1.23 km，off 8.3 % |
| 阶段 06–20（未采纳） | 深度诊断、主震审查、强震动 S、固定台站校正（17）、深度耦合（18）、S 到时复核（19）、HK 剖面（20）：均因相对 Shelly 深度差变大或证据不足而不提升 | 4 | EVOLUTION.md Completed branches、Stage 17 decision、Stage 20 | 无 |
| 阶段 14 | hypoDD 权重/阻尼 12 组预设，按内部 CT/CC 残差和验证台站门槛选出 cc3_d1（“参考只在排序后查看，不用于选择”）；后来用于阶段 52、Magna r6、Kīlauea r6 和 11 号记录的 hypoDD | 3（存疑，备选 2：属于用内部残差选参数，不是症状诊断） | `14_tune_hypodd/README.md` Selection rules | 无独立阶梯步 |
| 阶段 21–51（未采纳） | 30 轮有界优化（有效观测误差、EDT、台站校正、三维模型、换拾取器等），每轮按含 Shelly 深度差在内的预设门槛判定，几乎全部不提升 | 4 | OPTIMIZATION.md 轮次表；EVOLUTION.md Stage 21–51 | 无 |
| 阶段 52 | 绝对到时与波形差分联合定位（6,520 个工作事件），从上面 30 轮中按含参考的门槛选出 | 4（存疑，备选 2：相对定位是标准方法；具体求解配置经参考门槛筛出） | EVOLUTION.md Stage 52 completed；PLAN Stage 60 “templates … at their stage-52 double-difference positions” | 并入 07（下行） |
| 07 | 加入阶段 60 Match&Locate（1 km 覆盖，门槛 N×MAD 9.5 由零假设运行定出，合并间隔 4 s 也由零假设日比较定出） | 2（存疑，备选 4：触发是跨案例复核“只有 Ridgecrest 的召回低于参考之间的互相召回”） | PLAN “Stage 60 — Match&Locate (2026-10-24)”；阶梯步 “double difference (stage 52) + Match&Locate (stage 60)” | 07 合计（阶段 52 + 60）：recall_norm 1.146→1.313；scatter 0.755→0.384 km；dZ −1.23→−0.46 km；off 8.3 %→5.2 %；F1(M2+) 0.888→0.797 |
| 阶段 62（教训） | 模板推导的到时不得进入 dt.ct：同一模板的两个检测在每个台站上 dt = 0，hypoDD 把它们压到模板上（厚度 0.05 km）；改为 dt.ct 只用拾取 | 3（存疑，备选 4：dt = 0 的机制和不合理的薄簇无参考可见；文中以“只有 Shelly 厚度的三分之一”作对照） | PLAN “Stage 62 … Findings 1” | 无（试点） |
| 阶段 62（未采纳） | 三天互相关重定位（hypoDD cc3_d1）：变的是框架（向 Shelly、Liu 平移，离 Ross 更远），清晰度不变，不采用 | 4 | PLAN Stage 62 三天表与结论 | 无 |
| 08_location_quality | 定位质量规则：拾取事件和模板须有 ≥ 1 条阶段 52 CC 连接、方位间隙 ≤ 150°、NLL σx ≤ 0.8 km | 4（存疑，备选 3：规则只用内部量；但触发是用户看到“断层刻画比 ComCat 还差”，偏离构造按 Shelly/Ross/Liu 定义，三档规则按它和召回取舍） | PLAN “Location quality (2026-10-25)” | recall_norm 1.313→1.294；scatter 0.384→0.367 km；off 5.2 %→1.1 % |
| 09_close_events | 4 s 内的近邻事件只在 ≥ 3 个模板支持时保留（用模板台站上 PhaseNet P 拾取命中率对 +1 s 对照来判真实与否） | 4（存疑，备选 3：触发是剩余缺口分析中“两个参考事件相距 < 4 s，我们只留一个”；门槛本身由无参考的拾取命中检验定出） | PLAN “Remaining-gap analysis” | recall_norm 1.294→1.306；scatter 0.367→0.368 km |
| 10 / 12（阶段 63） | 分层框架：按 Shelly Table 1 原样的常数层（阶段 62 的 hypoDD）重定位，M&L 事件随模板位移；10 加在 09 上，12 加在 11 上 | 4（模型取自主参考论文；采纳依据是四个参考中三个震中、四个深度变好） | PLAN “Depth/frame → round 10_layered_frame” | 10（相对 09）：recall_norm 1.306→1.309；scatter 0.368→0.212 km；shift 0.466→0.371 km；dZ −0.49→−0.09 km。12（相对 11）：scatter 0.346→0.206 km；shift 0.463→0.370 km；dZ −0.48→−0.10 km |
| 11_dense_templates | 0.5 km 覆盖、只从通过定位质量的事件取模板；近邻规则随模板密度改为 ≥ 6 个模板（同一拾取命中检验） | 2（存疑，备选 4：漏检诊断是“召回随与最近模板距离下降”，依赖参考） | PLAN “Dense templates → rounds 11/12” | 相对 09：recall_norm 1.306→1.385；scatter 0.368→0.346 km；off 1.1 %→0.53 % |
| 53_direct_magnitude | 阶段 65：直接 ML（35 个事件采用） | 2（存疑，备选 4：同 Prague r6） | Baseline corrections | dmag_std 0.162→0.162；F1(M2+) 0.8015→0.8031 |
| 56_large_events | 阶段 66：恢复只因深度贴网格边界被排除、直接 ML ≥ 3.5 的 38 个事件（含 M7.1、M6.4、M5.4），去掉 29 个同事件 M&L 行 | 4（存疑，备选 3：主震缺失和网格顶部堆积无参考可见，00 号记录把“最大事件是否存在”列为 checker 检查；但缺陷由 metrics v1 的 F1(M5+) 0.57 暴露） | Baseline corrections；EVOLUTION 主震审查 | recall_norm 1.3895→1.3906；PLAN：f1_M5 0.57→1.00（53–57 合计） |
| 54（未采纳） | 恢复所有排除原因的大事件：15 个定位质量剔除中 10 个距任何 ComCat 事件 20–77 km，否决 | 4 | Baseline corrections “Round 54 … rejected” | 无 |
| 57_coda_duplicates | 阶段 67：删除尾波幽灵（629 个）；规则来自 40 个检测的盲审波形复核（图中不显示参考目录） | 4（存疑，备选 3：复核与规则无参考；触发是 metrics v1 的 M2–3 分档精度） | Baseline corrections；`67_coda_duplicates_audit/README.md` | recall_norm 1.391→1.383；F1(M2+) 0.804→0.825 |
| 68（未采纳重定位） | 互相关重定位（GrowClust）：相对位置误差变差，不采用 | 4 | 11_hil_relocation（Shelly 0.25→0.41 km） | 未进入阶梯 |

## 3. 汇总

**干预计数。** 每个案例按“采纳 / 未采纳”分别计四类的条数（主编码），存疑项按备选类别改写后的乐观与悲观计数写在表下。起点模型和子项都计入。

**阶梯归因的算法。** 对每个案例取被采纳的阶梯路径，逐步取 headline 指标相对上一步的变化，把这一步的变化记到该步的类别上，各类之和除以首步到末步的总变化即该类的份额（各步变化之和恒等于总变化，所以份额之和为 100 %；某类份额为负表示该类步骤合计使指标变差，份额超过 100 % 表示其余类别合计使指标变差）。路径：Prague r1→r7；Magna r1→r8→r10→r11（r6 本身无目录变化，双差位置并入 r7，r6、r7 主编码同为 2）；Maple r1→r11；Kīlauea r1→r3→r4→r7→r8→r9（跳过被否决的分支 r2）；Kaikōura r1→r9；Ridgecrest 01→07→08→09→11→12→53→56→57（10 是 12 的同一改动在 09 上的分支，跳过；11→12 记为分层框架）。不能归属的情况：Ridgecrest 07 同时含阶段 52（主编码 4）和阶段 60（主编码 2），召回变化记给阶段 60（双差不增减事件），scatter 变化记为“未归属”；起点模型和未采纳尝试没有阶梯变化；Kaikōura 的 scatter 从首步到末步净变差（2.940→3.059 km），份额无意义，只给各类的变化量。“S3 可及”指类 1–3 之和的份额；乐观口径把存疑项取更易自动化的类别（Ridgecrest 07 整步记 2），悲观口径取更难的类别（07 整步记 4）。全体一行的计数为加总，份额为各案例份额的简单平均（scatter 不含 Kaikōura）。

| 案例 | 采纳 类1/2/3/4 | 未采纳 类1/2/3/4 | recall_norm 首→末 | recall_norm 份额 类1/2/3/4（主编码） | S3 可及 recall：主（乐观 / 悲观） | scatter 首→末（km） | scatter 份额 类1/2/3/4（主编码） | S3 可及 scatter：主（乐观 / 悲观） |
|---|---|---|---|---|---|---|---|---|
| Prague | 1/5/0/2 | 0/0/0/2 | 1.173→1.850 | 0/100/0/0 % | 100 %（100 / 97） | 0.442→0.306 | 0/69/0/31 % | 69 %（100 / −7） |
| Magna | 3/4/1/6 | 0/0/1/4 | 0.678→1.143 | 0/80/0/20 % | 80 %（91 / 0） | 0.823→0.474 | 0/125/0/−25 % | 125 %（121 / 0） |
| Maple Creek | 2/6/0/3 | 0/0/0/1 | 0.942→0.994 | 0/124/0/−24 % | 124 %（100 / 154） | 0.990→0.653 | −38/142/0/−4 % | 104 %（100 / 154） |
| Kīlauea | 1/4/1/1 | 1/0/0/4 | 0.965→1.223 | 0/101/0/−1 % | 101 %（100 / 0） | 0.678→0.611 | 0/98/0/2 % | 98 %（100 / 0） |
| Kaikōura | 2/5/0/4 | 0/0/0/1 | 0.800→1.171 | 0/79/0/21 % | 79 %（100 / 2） | 2.940→3.059（净变差） | 类 2 −0.78 km，类 4 +0.90 km | 不适用 |
| Ridgecrest | 0/3/2/7 | 0/0/0/5 | 1.146→1.383 | 0/104/0/−4 % | 104 %（98 / 0） | 0.755→0.206 | 0/4/0/28 %，未归属 68 % | 4 %（74 / 0） |
| 全体 | 9/27/4/23（共 63） | 1/0/1/17（共 19） | — | 0/98/0/2 %（平均） | 98 %（98 / 42） | — | −8/88/0/6 %，未归属 14 %（平均，五案例） | 80 %（99 / 29） |

存疑项共 43 条（采纳 41、未采纳 2）。存疑项改写后，采纳干预的类别计数为：乐观 类1/2/3/4 = 9/32/16/6，悲观 = 8/7/2/46；未采纳的为乐观 1/0/2/16，悲观 1/0/0/18。

## 4. 解读

- **阶梯上的收益几乎全部来自方法选择（类 2）。** 主编码下，类 2 占 recall_norm 提高的约 98 %（平均）和 scatter 改善的约 88 %；收益集中在少数几步：模板匹配（Prague +0.66、Magna +0.37、Kīlauea +0.25、Kaikōura +0.29 recall_norm）、EDT（scatter 降 0.06–0.18 km）、台站延迟（Maple 降 0.14 km，Kaikōura 降 0.59 km）、双差（Magna、Ridgecrest）。类 1 的修正数量不少（9 条），但多是让流程跑通的前提，阶梯上看不到正收益（Maple r2 修正线性渐变反而使 scatter 变大 0.23 km，r4 复制 Z 使 scatter 降 0.10 km）。严格意义上的无参考诊断（类 3）只有 4 条，阶梯效果接近零。
- **但大多数方法选择是在与参考比较之后才做的。** 采纳的 41 条存疑项中，多数是“方法属先验知识、触发或取舍依据参考”。悲观口径下 S3 可及的 recall 份额从 98 % 降到 42 %、scatter 从 80 % 降到 29 %。所以“S3 能补上的最大差距”取决于知识能不能在看结果之前就把这些方法交给 Agent：知识条目若事先写明“用模板匹配并以零假设定门槛、用 EDT、加台站延迟、大事件直接 ML”，接近乐观口径（约 98 % 的召回提高、约 99 % 的位置改善都可及）；只靠 checker 从症状反推，则接近悲观口径。
- **没有参考就达不到的部分集中在三处。** (1) 取自目标或参考论文的速度模型：Ridgecrest 的 Shelly 分层框架一步就把 scatter 降 0.14–0.16 km、dZ 从 −0.49 改到 −0.09 km（类 4 合计占该案例 scatter 改善的 28 %，其中分层框架 25 %），Kaikōura 和 Maple 的起点模型也来自参考或目标论文，它们的作用包含在起点里，阶梯测不到；(2) 按官方目录重标定的震级（Magna r2、r3 使 dmag_std 0.208→0.127）；(3) 按参考召回调的门槛与规则（Magna 盆地层和 PhaseNet 门槛，约占 Magna 召回提高的 20 %；Kaikōura eps 约占 21 %；各案例的定位质量规则）。此外 19 条未采纳尝试中 17 条是按参考否决的，Agent 没有参考时既不知道这些尝试会失败，也可能误采纳。
- **有几项依赖参考的改动换来的不是阶梯指标。** Kaikōura 的 eps 15 s 和互相关重定位使 scatter 合计变差 0.90 km（eps 改善了偏移 2.38→1.14 km 和 F1(M2+)，重定位改善了 dZ 和相对位置误差）；Magna 的盆地层和深度先验使 scatter 变差 0.08 km 而 dZ 改善。归因份额只反映 recall_norm 和 scatter 两个指标，深度和震级的改善大多落在类 4（Magna 震级）和存疑项（直接 ML、尾波幽灵）。
- **对 S3 的含义。** S3 的上限约为：召回提高的大部分和位置改善的大部分，前提是方法知识事先给出、尾波幽灵与大事件缺失这类症状由 checker 检出（它们在乐观口径下归类 3，症状无参考可见，但这次是由参考指标暴露的）。不论 checker 多好，区域分层模型（来自目标论文）、震级标定、按参考调的门槛都留在类 4；按本编码（各案例主编码），它们最多约占召回提高的 20 %（Magna 20 %、Kaikōura 21 %，其余案例为零或负）、位置改善的 0–31 %，Ridgecrest 另有 68 % 的位置改善因阶段 52 与 60 混在一步而无法拆分。
