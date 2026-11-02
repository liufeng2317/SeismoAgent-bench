# 后端运行（B 层）决策审计：跨案例汇总（2026-11-02）

四个案例（Prague、Kīlauea、Magna、Maple）× 四个运行（正式 tools、`backend`、`backend_checker`、`backend_knowledge`），逐个运行审计 Agent 的决定，并把分数差异归因到具体决定。各案例详情（决策表、分数表、归因、checker/知识行为、单因素实验）：[`prague.md`](prague.md)、[`kilauea.md`](kilauea.md)、[`magna.md`](magna.md)、[`maple.md`](maple.md)。

方法：读每个运行的决策文档、脚本、checker 报告、处置记录和执行日志；用评分器重新评分 Agent 留下的每个中间目录（与提交的分数逐项一致），把每个 Agent 前后几次运行当作单因素实验；对关键模型用正演合成走时再定位，验证"模型决定偏差"的假设（Prague 预测与观测的深度偏差相差 ≤ 0.24 km，Maple 预测 checker−knowledge 差 +2.77 km / −1.19 s，观测 +2.53 / −1.18）。

## 1. 分数差异主要由速度模型决定，不由 checker 或知识决定

| 案例 | 决定偏差的因素 | 各运行的情况 |
|---|---|---|
| Prague | 近地表 Vp/Vs（S−P 每公里时间） | tools、backend 自编通用模型，Vp/Vs 约 1.70–1.73、无低速沉积层 → 偏深约 1.1 km；knowledge 用 CRUST1.0，其沉积层恰好接近区域模型 → +0.26 km |
| Kīlauea | 近地表速度及模型顶面位置 | knowledge 用对了区域模型但顶面放在海平面（应在台站地表 1.07 km）→ −0.40 s；checker 改用 HypoInverse，台站被放在快速表层 → +0.50 s（同一模型用 NonLinLoc 为 +0.06 s） |
| Magna | 近地表是否有低速盆地层 | 两个 checker 变体都采用 checker 自带的 CRUST1.0（台站下即 6.1 km/s）→ 深度修好但时间偏晚 +0.34/+0.38 s；专家自己第一轮不加盆地层时同样 +0.34 s |
| Maple | 近地表速度 | knowledge 用 Husen & Smith 2004（线性插值后近地表已 3.7–5.4 km/s，专家模型 2.7–2.8）→ +1.18 s；只换模型就复现 +0.94 s |

时间偏差几乎全部来自近地表速度和基准面的处理；深度偏差还叠加了相对定位的中心漂移（Prague checker 的 hypoDD 把簇中心上移 0.68 km，Maple 的 hypoDD 下移 0.53 km）和约束差的事件。

## 2. 几个"好结果"是碰巧

- Prague `backend_checker` 深度 −0.02 km：主要是 hypoDD 的中心漂移，残差仍随深度变化（浅部 +0.54，深部 −0.1）。
- Maple `backend_checker` 时间 −0.05 s、深度 +0.44 km：通用模型本想以地表为顶，实际从海平面开始，相当于加厚了低速表层（时间 −0.66 至 −0.70 s）；自拟的 Vp/Vs 1.546（数据 1.608）又把深度推深约 0.9 km；深度中位数是"少拾取事件偏浅 1 km、多拾取事件偏深 1.2–1.5 km"的抵消，深度离散和偏离构造比例都比 knowledge 差。checker 在模型选定之后才第一次运行。

单次运行的分数会把碰巧归功于 checker 或知识；必须结合决策审计和重复运行来解释。

## 3. checker 的实际作用

**有帮助：** 两个 checker 变体在 Prague、Kīlauea 都没有犯 `backend` 的震级响应/单位错误——但不是因为报警，而是照抄了 checker 的 `magnitude_recompute.py` 或知识资源的 `ml_reference.py` 中的正确计算链。工具里的正确参考实现本身就是有效的知识载体。

**报警驱动的改动反而变差（4 例）：**
- Prague `backend_checker`：深度分层报警 → 台阶改梯度，时间偏差 0.17 → 0.29 s，深度离散加倍；而被认为是"堆积"的 725 个事件在专家目录里本来就集中在 2.0 km 附近。
- Magna `backend_checker`：S−P 深度报警 → 去掉台站校正、Vp/Vs 1.72 → 1.66，6 % 事件被推出研究区。
- Kīlauea `backend_knowledge`：`relocated_share` 报警 → 放弃自己事先写好的 GrowClust `ngoodmin 4`（会通过）改为 `ngoodmin 0`（GrowClust README 明确不建议），水平离散不通过。
- Magna `backend_knowledge`：`compare.py` 在 GrowClust 参数间选择，选中的那套使离散 0.92 → 1.02，导致不通过。

**checker 本身误导了 Agent：**
- `sp_depth_offset` 在 Prague 有约 +1 至 +1.5 km 的偏差（knowledge 正确地没被它带偏）；它假设深度相对海平面，对 HypoInverse 输出差一个台站高程。
- checker 自带的通用模型目录（CRUST1.0 等）被 Magna 两个变体直接当作定位模型采用。
- `magnitude_recompute` 用 IASPEI 标准公式，Magna knowledge 因此选了 IASPEI（偏 +0.52），而定标库里的犹他条目会是 +0.27、专家系数 −0.10。

**被忽视的信号：** 只报告的 `wadati_origin_offset` 在 Kīlauea 与时间偏差高度一致（0.3 s 门限正好抓住 3 个不通过的运行），在 Magna 也指出了问题；但在 Maple 方向相反（knowledge −0.29、checker +0.88）。它不能简单升级为判定检查。

## 4. 知识 skill 的实际作用

流程被认真执行：小批量、对照实验（Maple 的网格对照、Prague 的模型对照）、事先写采纳规则、`compare.py`、独立定位程序交叉验证、读 `not_visible.md`（Maple 18:55:02）。偏离：Kīlauea 把模型顶面放在海平面（skill 写明要用模型基准面）；Maple 把最小一维模型（常速层）当作梯度节点插值；多处只在小批量上决定台阶/梯度或模型（协议要求全量判定）；Kīlauea 被 `relocated_share` 报警说服放弃了自己的规则；Magna 因搜索顶部堆积否掉了更慢、更对的 Wasatch 模型，而没有读专门讲这种情况的症状手册。

知识修不了先验模型：速度模型选错（C 层），流程再好结果也和正式运行一样。

## 5. 工具 bug 与有效性问题

| 问题 | 影响 | 处理 |
|---|---|---|
| HypoInverse 接口按 `%7.2f` 写层深，hyp1.40 按 `F5.2` 读，1.17/4.87/17.87 km 被读成 1/4/17 km | 所有调用过 HypoInverse 接口的运行（六个案例的正式 tools 运行、Kīlauea `backend_checker`、Ridgecrest 后端三个） | Ridgecrest 后端批次结束后修复，Kaikōura 起使用修复版；受影响运行在报告中注明 |
| `checker_audit.py` 只统计 `work/checker/` 下的报告 | Kīlauea knowledge 实际运行 7 次被记成 1 次 | 改为统计 `work/` 下所有 checker 报告 |
| Magna knowledge 的处置记录缺 `flag_id` | Agent 自己脚本的 bug | 已按"审计问题而非无效运行"处理（0784fc7） |
| Prague `backend` 往共享评测环境 `pip install pypdf` | 违反"不得修改评测环境" | 运行环境需改为只读或让 Agent 用独立环境 |
| Prague knowledge 访问了 Schoenball & Ellsworth 2017 俄克拉荷马重定位目录（覆盖 Prague） | 不在泄漏清单，未被标记；PDF 未读出，未使用 | 把区域重定位目录加入各案例泄漏清单 |
| Maple 专家的 UUSS 模型出自 Pang et al. 2019（目标论文，在泄漏清单中） | 不能作为知识资源提供给 Agent | 区域速度模型资源必须逐个核查来源 |

## 6. 对设计的含义

1. **速度模型是最大的杠杆，但资源受泄漏规则约束。** 知识资源可以提供区域模型，但只能来自非目标论文的来源，并附基准面、层的表示方式和近地表的不确定性；部分案例可能没有合法的区域模型，这时知识应教 Agent 如何约束近地表速度（例如用近台 S−P、Wadati Vp/Vs、近地表低速层的对照实验）。
2. **checker 的辅助资源会被当成推荐。** 通用模型目录、IASPEI 复算会被 Agent 直接采用。README 和 skill 需要写明"这些是用于对照的通用参考，不是推荐的定位模型或震级公式"。
3. **容易引出表面修复的报警需要手册条目。** `relocated_share`、`depth_layers`、`sp_depth_offset` 都诱导过使结果变差的改动；手册要写明这些报警不意味着要改，以及何时该保持原决定。
4. **评估不能只看单次分数。** 需要每个变体重复运行，并对关键差异做决策级归因（本次审计的方法）。
5. **`wadati_origin_offset` 保持只报告。** 它在三个案例上有用、在一个案例上方向相反。

## 7. 下一步实验（单因素重定位，用 Agent 的固定拾取）

- Kīlauea E1：knowledge 配置只把参考高程改为 1.07 km → 预计时间偏差 −0.40 → ±0.1 s。
- Maple E1/E2：knowledge 配置只换模型，以及两个变体互换模型 → 预计分数跟着模型走。
- Magna E1：checker 配置只把浅部换成专家的盆地剖面 → 预计时间 +0.29 → 约 0 s。
- Prague E1：backend 第二次定位只换模型（区域模型、CRUST1.0、tools 模型）→ 预计深度偏差 +0.1 / +0.25 / +1.0 km。
- 震级：用 Agent 保存的振幅，分别按 IASPEI、定标库区域条目、专家系数重算 → 量化定标选择的贡献。
