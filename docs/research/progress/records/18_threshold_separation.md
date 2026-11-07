# 判定门槛的区分度（2026-11-08）

问题：checker 的判定检查都用一个门槛把测量值变成报警，这些门槛能不能把有错的目录和没错的目录分开？脚本 `workflows/development/tools_case_validation/threshold_separation.py`，输出 `outputs/threshold_separation/separation.json`（不纳入版本库）。

## 方法

- **目录：** E1 的 6 个 human-in-loop 定位目录（按干净处理，但其中有早期轮次的真问题）和 31 次已完成运行（checker 1.3 的测量值），加上开发循环的 9 次运行（各自最终报告的测量值，1.4–1.5）。
- **真值：** 每项检查对应它要抓的错误会使哪个可信判据不通过（深度堆积 → `depth_pileup`，S−P 深度 → `depth_bias`，Wadati → `time_bias`/`time_spread`，孤立事件和拾取过少 → `off_structure`/`horizontal_scatter`，震级 → `magnitude_offset`）；运行不通过该判据即为"有错"。震级另按真实偏差是否超过 0.9（单位或响应错误）单独算。
- **统计：** 干净目录的最大值、有错运行的最小值和中位数、没错运行的最大值、AUC（有错对其余）、现行门槛下的误报和检出；只给方向的检查另看符号与真实偏差是否一致。

## 结果

| 检查 | 门槛 | AUC | 门槛处：干净目录报警 / 有错检出 / 没错运行报警 | 读数 |
|---|---|---|---|---|
| `magnitude_recompute`（单位或响应错误） | 0.5 | — | 0 / 6 of 6 / 0 | 有错的测量值 ≥ 0.69，其余 ≤ 0.48，空当约 0.2 |
| `depth_single_value` | 5 % | 0.97 | 3 / 8 of 8 / 1 | 干净目录的 3 次是早期轮次的真实堆积 |
| `sp_depth_offset` | 1.5 km | 0.64 | 0 / 6 of 25 / 0 | 方向：超过门槛 6/6 正确；全部运行只有 35 % 正确 |
| `isolated_events` | 10 % | 0.83 | 0 / 4 of 19 / 0 | 干净目录最大 9.3 %，门槛贴着干净目录的上沿 |
| `events_with_few_picks` | 20 % | 0.77 | 0 / 6 of 19 / 4 | 衡量约束程度，不是对错 |
| `depth_layers` | 5 % | 0.72 | 1 / 3 of 8 / 9 | 判据通过的运行也常报警，过于敏感 |
| `depth_at_edges` | 5 % | 0.67 | 1 / 4 of 8 / 1 | 与 `depth_single_value` 大部分重合，自身区分弱 |
| `wadati_origin_offset` | 1.5 s | 0.76 | 0 / 1 of 18 / 0 | 只抓严重错误；数值与真实时间偏差的秩相关 −0.06 |
| `wadati_origin_spread` | 0.5 s | 0.56 | 0 / 3 of 18 / 3 | 几乎分不开 |
| `largest_events_magnitude` | 0.5 | 0.67 | 0 / 7 of 23 / 0 | 单位错误与其余重叠（其余最大 0.80） |
| `magnitude_detection` | [−2.3, 0.5] | 0.50 | 0 / 5 of 16 / 0 | 单位错误多数落在范围内 |
| `silent_stations` | 10 % | — | 1 / — / 12 | 无对应判据；干净目录最大 11.9 %，门槛在干净目录之内 |
| `duplicate_picks`、`pick_onset_offset` | 2 %、0.2 s | — | 0 / — / 1、0 | 无对应判据；靠合成测试和个别已知错误验证 |

## 结论

1. **真正起"探测器"作用的门槛只有少数：** 震级复算（单位或响应错误）和单一深度值的堆积。它们在门槛处检出全部已知错误、几乎没有误报。
2. **S−P 深度的门槛有意义，但含义是"方向可靠的界线"：** 超过 1.5 km 时方向 6/6 正确；低于门槛时只有 35 % 正确，比随机还差。它只检出 25 次深度偏差中的 6 次，不是深度偏差的探测器。
3. **一批门槛分不开对错：** Wadati 离散和偏差、深度分层、深度边缘、大事件震级、检测震级的 AUC 在 0.50–0.76；深度分层在没错的运行上报警 9 次。这些报警会要求 Agent 处置，却不对应真实错误，正是"报警诱导表面修复"的来源。
4. **拾取过少、无拾取台站的门槛贴着或落在干净目录之内：** 它们反映的是约束程度或配置，不是目录对错。`silent_stations` 曾引导 Agent 补进噪声拾取（记录 16）。

## 局限

- 样本少：干净目录 6 个，有错运行每项 6–25 次；不同运行的错误常常同时出现。
- 真值借用可信判据，判据本身也是约定的门槛；human-in-loop 目录是早期定位轮次，并不全干净。
- 门槛和检查都是在这六个案例上设计的，结论需要不参与校准的案例复核。

## 建议（待定）

- 保留二元报警：`magnitude_recompute`、`depth_single_value`，以及以错误特征为依据的安全检查（`pick_onset_offset`、`duplicate_picks` 等）。
- `sp_depth_offset` 保留门槛，但报警写成"方向可靠，按此方向纠正"，不要求数值归零。
- 改为分级报告（给出干净目录和已知有错目录的范围，说明数值给的是方向还是大小，不要求处置）：`depth_layers`、`depth_at_edges`、`wadati_origin_spread`、`wadati_origin_offset`（严重错误仍报警）、`largest_events_magnitude`、`magnitude_detection`、`isolated_events`、`events_with_few_picks`、`silent_stations`。
