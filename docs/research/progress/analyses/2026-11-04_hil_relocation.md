# human-in-loop 最终目录的互相关重定位（2026-11-04）

**问题。** 六个最终目录看起来是网格状的：坐标完全重合的事件占 22–78 %。其中 80–100 % 来自 Match&Locate 检测事件，它们落在模板周围的搜索格点上（水平 0.25 km，Kaikōura 0.5 km；深度 0.5 km），之后没有再精细定位。其余来自 Prague、Maple 的 NonLinLoc 八叉树格子，这两个案例的拾取定位事件也有 43 % 和 31 % 重合。双差（dd）事件没有重合。

**做法。** 脚本 `workflows/development/hil_relocation/cc_relocate.py`，每个案例的设置在 `cases/<case>.yaml`。

- 互相关时差用 ccdt 计算；模板推导出的到时只用来放置互相关窗口。
- 重定位有两个后端：
  - GrowClust：只用互相关时差，ngoodmin 2，用于六个案例。
  - hypoDD 1.3：沿用 Ridgecrest 第 62 步的做法，互相关时差加上拾取事件自身拾取的目录时差，控制参数 cc3_d1，`--step hypodd --run-name hypodd`。只在 Prague 上测试。
- 接受条件：水平移动 < 3 km，发震时刻变化 < 1 s，深度在模型内。

**评价指标。** 与参考目录的绝对震中差混入了整体框架平移，所以另加一个不受框架影响的相对位置指标：在参考目录中相距 2 km 以内的匹配事件对上，比较本目录与参考目录的事件间位置向量之差（水平，取中位数），重定位前后使用同一批事件对。

## 结果

| 案例 | 后端 | 重定位事件 | 坐标重合比例 | 相对位置误差，两事件都重定位（前 → 后，km） | 绝对震中差（前 → 后，km） |
|---|---|---|---|---|---|
| Kaikōura | GrowClust | 7,913 | 50 % → 17 % | Chamberlain 1.53 → **0.69**，Tan 2.59 → 2.32，GeoNet 1.92 → 1.78 | Lanza 3.05 → 3.16，Chamberlain 3.41 → 3.29 |
| Maple | GrowClust | 4,144 | 92 % → 60 % | ComCat 0.69 → 0.74 | ComCat 0.89 → 0.92 |
| Prague | GrowClust | 1,400 | 89 % → 72 % | Cochran 0.29 → 0.46，McMahon 0.25 → 0.47 | Cochran 0.36 → 0.40，McMahon 0.21 → 0.27 |
| Prague | hypoDD（拾取 + 互相关） | 2,759 | 89 % → 51 % | Cochran 0.32 → 0.41，McMahon 0.27 → 0.31 | Cochran 0.36 → 0.79（扣除整体平移后 0.45） |
| Kīlauea | GrowClust | 3,290 | 44 % → 25 % | Wei 0.70 → 0.84，Matoza 0.73 → 0.86 | Shelly 0.72 → 0.80 |
| Ridgecrest | GrowClust | 3,512（另 4,785 个 dd 锚点） | 45 % → 30 % | Shelly 0.25 → 0.41，Ross 0.33 → 0.52，Liu 0.51 → 0.47 | Shelly 0.43 → 0.44 |
| Magna | GrowClust | 380（另 1,969 个 dd 锚点） | 32 % → 27 % | Pang 0.81 → 1.46，Baker 1.35 → 1.75 | Pang 1.08 → 1.09 |

（"坐标重合比例"按经纬度取 5 位小数判断。只有一个事件被重定位的事件对，误差在所有案例里都变大，Kaikōura 也是如此。）

## 结论

1. **除 Kaikōura 外，重定位让相对位置变差。** 网格本身的量化误差只有半个格距（±0.125 km），比重定位后事件位置的散布（0.3–0.6 km）小。Match&Locate 的格点位置本来就是相对于模板的定位：叠加多台站互相关后，在模板周围的网格上取最大值。弱事件的互相关时差太稀疏（Prague 平均每个事件约 8 条，Ridgecrest 约 50 条，Shelly 约 700 条），重新反演时引入的散布比网格量化更大。
2. **hypoDD 在 Prague 上没有改变结论。** 加入拾取时差后，被移动的事件更多（2,759 个），网格降得更多（51 %），双重定位事件对的相对误差也比 GrowClust 小（Cochran 0.41 对 0.46），但仍比不重定位差（0.32）。另外，hypoDD 把拾取事件整体向北移了约 0.7 km：只用一个 Vp/Vs 比值，也不考虑台站高程。Ridgecrest 第 62 步与 Shelly 的绝对吻合度改善（0.62 → 0.46 km），也是这种框架平移造成的（见 Ridgecrest expert PLAN.md）。
3. **Kaikōura 是例外。** 它的格距大（0.5 km），格点位置在一维模型下误差也大，重定位明显改善了相对结构。

## 决定（2026-11-04，已执行）

新的最终目录与评分基准（各案例 `evaluation/metrics.yaml`）：

| 案例 | 原最终目录 | 新最终目录 | 位置 |
|---|---|---|---|
| Kaikōura | r8 | r9 | 7,913 个事件采用 GrowClust 重定位（`location_source` 加后缀 `_cc`），其余保留 |
| Prague | r7 | r8 | 不变，只加标注 |
| Maple | r11 | r12 | 不变，只加标注；先前导出的重定位版本改名为 `r12/60_catalog_relocated_not_adopted` |
| Kīlauea | r9 | r10 | 不变，只加标注 |
| Ridgecrest | 57_coda_duplicates | 68_cc_relocation | 不变，只加标注 |
| Magna | r11 | r12 | 不变，只加标注 |

- 仍在格点上的检测事件（`location_source` = `ml`）标注 `location_precision_h_km` / `location_precision_z_km` = 半个格距。只标注、不移动位置的导出用 `cc_relocate.py CASE --step export --label-only`；所有事件的 `relocation_status` 为 `not_applied`。
- 五个只加标注的案例重算后，基线与原来完全相同（时间戳和路径除外）。
- Kaikōura 基线的变化（相对于 Chamberlain）：
  - 变好：深度偏差 −0.87 → −0.32 km，时间偏差中位数 0.62 → 0.49 s；
  - 变差：水平偏移 1.13 → 1.37 km，水平离散 2.78 → 3.06 km；
  - 几乎不变：找回率 0.813 → 0.813。
  - 阶梯（`expert_ladder.yaml`）加入 r9 一步。
- 待定：是否对 Prague、Maple 的 NonLinLoc 八叉树格子也做同样的标注。

可信度的依据是相对误差，不是图面上的平滑程度。人为加入抖动只会掩盖网格，不能改善精度，所以不做。
