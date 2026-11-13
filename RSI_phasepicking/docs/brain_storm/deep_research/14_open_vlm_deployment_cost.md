# 14. 开源 VLM 部署和成本

调研日期：2026-11-13。所有价格均为当天从官方页面查到的标准价，美元，按每百万 token 计（MTok）。检索预算在本轮用完，个别条目只看到二手来源，已逐条标注。

## 要回答的问题

- 截至 2026 年底，最强的开源权重多模态模型有哪些？要能读图表/曲线、能用工具做 agent。核实草稿中的 Qwen3.8-27B 和 Gemma 4 31B 是否存在及其规格；同时看其他 Qwen-VL、InternVL、GLM-V、Llama、Mistral/Pixtral、Kimi-VL 系列。列出已公布的图表基准分数。
- 在 Slurm 集群上用 vLLM 部署（Harvard FASRC；核实 Kempner Institute 的 distributed-inference-vllm 仓库）；图片 token 成本；多图 agent 循环的吞吐量；前缀缓存。
- 闭源 API 的图片输入价格和 batch/flex 折扣（OpenAI、Anthropic、Google），给出官方当前价格和查阅日期。
- GLM-5.3（上游 SeismoAgentBench 运行框架默认配置的模型，经 Anthropic 兼容接口调用）能否作为本分支的看图模型。

影响的决定：能否扩大规模；分级处理架构。

## 结论摘要

- **草稿中的两个开源模型都存在，名称和主要规格属实。**
  - Qwen3.8-27B：Apache-2.0；HF 仓库 2026-08 创建，官方 FP8 版 30.9 GB；稠密 27B，混合架构（每 4 层中 3 层 Gated DeltaNet 线性注意力 + 1 层全注意力），原生 262k 上下文。自报 CharXiv(RQ) 不用工具 83.7、用代码解释器 90.2，OSWorld-Verified 84.3 [1][2][3]。
  - Gemma 4 31B：Apache-2.0；稠密 30.7B；视觉 token 预算可选 70–1120；MMMU Pro 76.9%、τ2 76.9%；**没有公布 CharXiv 或 ChartQA** [5][7]。
- **GLM-5.3 不支持图片输入。** Z.ai 官方文档写明 GLM-5.3"目前只支持文本输入" [9]。同系列的 **GLM-5.3-Flash** 是原生多模态模型（320B 总参数 / 18B 激活，MIT 许可，开源权重），支持图片、视频、文件输入，已在 GLM Coding Plan 上开放；第三方榜单 CharXiv-R 0.894 [8][10][12]。所以本分支若沿用上游运行框架、又要用 GLM 系列看图，需要换成 GLM-5.3-Flash（或 GLM-5V-Turbo），并核实 Anthropic 兼容接口能否接收图片块 [待核]。
- **单卡部署 Qwen3.8-27B-FP8 可行。** FASRC 的 `gpu_h200` 分区有 22–24 个节点，每节点 4 张 H200（141 GB），作业时限 3 天 [18][19]。按模型配置推算，KV 缓存每 token 只占约 64 KiB（只有 16 层是全注意力），单张 H200 放下权重后还剩约 80–90 GB，足以同时跑 32–64 个上下文 ≤20k 的 agent（**推断，需实测**）。但混合架构的前缀缓存需要 `--mamba-cache-mode align`，vLLM 标为实验性功能，缓存粒度为 784 token 一块，图片 KV 缓存未经 LMCache 验证 [21][24]。
- **Kempner 仓库存在（Apache-2.0），但不能直接用于本项目。**
  - 仓库里的配方只覆盖纯文本模型：Qwen2.5-32B、Llama 3.1 70B/405B、DeepSeek-R1；
  - 环境用 uv/conda，不用容器；预装 vLLM 0.11.2，另有 2026-04 的源码编译环境；
  - **不涉及多模态，也没有给出吞吐数字** [17]。

  可以参考它的 Slurm 和多节点写法，但 Qwen3.8（`qwen3_5` 架构）需要更新的 vLLM，要自己配环境 [待核]。
- **闭源 API 价格（2026-11-13 查阅）**：
  - **OpenAI**：gpt-6.1-sol 输入 $2、缓存输入 $0.10、输出 $10；Batch 价 $1 / $0.05 / $5，Flex 按 Batch 价计费 [27][28]。
  - **Anthropic**：Opus 5.5 $4 / 缓存命中 $0.20 / $20；Sonnet 5.5 $2 / $0.10 / $10；Batch 五折；**没有 Flex 档** [31]。
  - **Google**：Gemini 3.8 Flash $0.75 / $3.75，Batch 和 Flex 都是五折；Gemini 4 系列的大多数价格将在 **2026-12-01 翻倍** [33]。
- **图片本身很便宜，贵的是 agent 循环中反复读的上下文和输出。** 一张 1600×400 的图：
  - gpt-6.1-sol 约 780 token，约 $0.0016；
  - Opus 5.5 约 870 token，约 $0.0035；
  - Gemini 固定 1120 token，在 3.8 Flash 上约 $0.0008 [29][32][34]。

  试点每个事件约 16 张图，第一次读入只要约 $0.03；而试点每个事件总成本是 $0.50–0.75。所以压缩成本的重点是缓存命中率和输出长度，而不是把图画小（推断）。
- **有能力的开源模型规模差距很大。**
  - 能单节点自部署的：Qwen3.8-27B（1 卡）、Qwen3.8-Flash-Next（125B 总参数 / 6B 激活，FP8 约 2 卡）、Gemma 4 31B（1 卡）、GLM-5.3-Flash（320B，FP8 约 4 张 H200）（显存估算为**推断**）；
  - Kimi K3（2.8T 参数）在 FASRC 上实际不可行；
  - 没有找到 InternVL 4；InternVL 的最新版本仍是 2025-08 的 InternVL3.5 [14][16]。

## 详细发现

### 1. 开源多模态模型现状（2026-11）

#### 1.1 规格与图表成绩

| 模型 | 发布（HF 仓库创建日期） | 参数 | 许可 | 上下文 | 图表/视觉成绩 | agent 成绩 | 来源 |
|---|---|---|---|---|---|---|---|
| **Qwen3.8-27B** | 2026-08-05（GitHub 称 08-14 正式开放）；FP8 版 08-13 | 稠密 27B，64 层（48 层 Gated DeltaNet + 16 层全注意力），视觉编码器 27 层 | Apache-2.0 | 262k，YaRN 可扩到 1M | CharXiv(RQ) 83.7 / 用代码解释器 90.2；OmniDocBench 1.5 91.1；RealWorldQA 85.9；llm-stats CharXiv-R 0.902 | OSWorld-Verified 84.3、AndroidWorld 81.9、Terminal Bench 2.1 73.0、SWE-bench Pro 61.7 | [1][2][3][12] |
| **Qwen3.8-Flash-Next** | 2026-08-24（有 FP8 版） | MoE：125B 总参数 / 6B 激活（另有 51B n-gram 嵌入和 4B MTP，safetensors 共 180B），512 个专家 | qwen-community-1.0 | 262k → 1M | CharXiv(RQ) 84.6 / 用代码 90.6 | SWE-bench Pro 62.5 | [4] |
| Qwen3.8-2.4T-A95B | 2026-08-08 | 2.4T / 95B 激活 | Qwen3.8-Max 许可 | — | — | — | [2] |
| **Gemma 4 31B** | 2026-03-11 | 稠密 30.7B，60 层；视觉编码器约 550M | Apache-2.0 | 256k | MMMU Pro 76.9%；MATH-Vision 85.6%；OmniDocBench 编辑距离 0.131；**没有公布 CharXiv/ChartQA** | τ2 76.9% | [5][6][7] |
| Gemma 4 26B A4B | 同上 | MoE：25.2B 总参数 / 3.8B 激活 | Apache-2.0 | 256k | MMMU Pro 73.8% | τ2 68.2% | [5] |
| **GLM-5.3-Flash** | 2026-08-25 | MoE：约 320B 总参数 / 18B 激活，稀疏 + 线性注意力，带 FP8 张量 | MIT | 1M | llm-stats CharXiv-R 0.894；OmniDocBench 90.76 | Terminal-Bench 2.1 84.3；DeepSWE 63.4 | [8][10][12] |
| Kimi K3 | 2026-07（二手来源） | MoE：2.8T 总参数 / 约 104B 激活 | Kimi K3 自定义许可 | 1M | llm-stats CharXiv-R 0.913 | — | [12][14] |
| Muse Glimmer-30B（Meta） | 2026-08-10（二手来源） | 约 30B（约 1.8B 视觉编码器） | Apache-2.0 | 128k–131k | llm-stats CharXiv-R 0.788 | — | [12][14][15] |
| Nemotron 3.5 Super VL | — | 120B / 12B 激活 | 未核 | — | llm-stats 0.808 | — | [12] |
| Qwen3.6-27B / Qwen3.5-27B（上一代） | 2026 上半年 | 稠密 27B | Apache-2.0 | — | llm-stats 0.784 / 0.795 | — | [12] |
| InternVL3.5 | 2025-08 | 1B–38B 稠密；最大 241B-A28B | MIT（各权重不同） | 40k | 2026 年没有新版本；**未找到 InternVL4** | — | [14][16] |
| Mistral Small 4 | 2026（二手来源） | 119B / 6B 激活，支持图片输入 | Apache-2.0 | — | 未找到 | — | 二手来源 [未打开原文] |
| Kimi-VL、Llama 4、Pixtral | 2025 | — | — | — | 已被上表模型超过；没有找到 2026 年的新版本 | — | — |

说明：
- llm-stats [12] 是第三方聚合榜单，同一模型常与厂商自报数字不一致（例如 Qwen3.8-27B 的 0.902 对应厂商"用代码解释器"的 90.2）。
- 自报分数中"用代码解释器"比"不用工具"高 6–7 分 [1][4]，说明这些模型调用工具读图有效。这与方向 08 的建议（看图 + 数值工具）一致。

#### 1.2 适合本项目的候选

| 用途 | 首选 | 备选 | 理由 |
|---|---|---|---|
| T1 主力（单卡、高并发） | Qwen3.8-27B-FP8 | Gemma 4 31B | 同规模中图表和 agent 成绩最好，有官方 FP8 版，Apache-2.0 |
| T1 追求更高吞吐 | Qwen3.8-Flash-Next-FP8 | — | 每 token 只激活 6B，解码快；但约 180 GB 权重需要 2 张 H200 |
| 与上游运行框架默认模型同一家族 | GLM-5.3-Flash | — | 多模态、MIT；FP8 约 320 GB，需要 4 张 H200 张量并行（推断） |
| 不可行 | Kimi K3、Qwen3.8-2.4T | — | 参数量为万亿级，FASRC 单节点只有 4 卡 |

### 2. GLM-5.3 是否支持图片

- Z.ai 的 GLM-5.3 文档写明"目前只支持文本输入"；上下文 1M，最大输出 128k；Anthropic 协议的基础地址为 `https://api.z.ai/api/anthropic` [9]。
- Z.ai 的 VLM 指南列出 GLM-5.3-Flash / FlashX 支持视频、图片、文本、文件输入，输出为文本；它已在 GLM Coding Plan 上全面开放，额度是 GLM-5.3 的 3 倍 [10]。
- GLM-5V-Turbo 也是视觉模型（据二手来源：2026-04 发布，200k 上下文，Vercel 标价 $1.2/$4）[11]。
- **未核实**：通过 `api.z.ai/api/anthropic` 用 Anthropic 消息格式发送 `image` 内容块时，GLM-5.3-Flash 能否正确接收。官方文档只给了 OpenAI 格式（`image_url`）的示例 [10][11]。这一点要实际发一个请求测试。

### 3. 在 FASRC 上用 vLLM 部署

#### 3.1 集群资源

| 分区 | GPU | 时限 | 访问 | 来源 |
|---|---|---|---|---|
| `gpu` | 每节点 4× A100（36 个节点；显存 40 GB 还是 80 GB 页面未说明） | 3 天 | 一般用户 | [19] |
| `gpu_h200` | 每节点 4× H200（141 GB），22–24 个节点（2025-08-18 公告为 24 个节点，现在的页面写 22 个） | 3 天 | 一般用户 | [18][19] |
| `gpu_test` | A100 MIG 切片（3g.20GB） | 12 小时 | 只用于交互和测试 | [19] |
| `gpu_requeue` | 各课题组的闲置 GPU，型号不定 | 3 天 | 可能被抢占后自动重新排队；建议用于 <1 天的作业 | [19] |
| `kempner_h200` / `kempner_h100` / `kempner_rtx` | 384× H200 / 384× H100 / 192× RTX PRO 6000 Blackwell | 2 天 | 需要属于 Kempner 课题组并经审批 | [20] |

- 显存 141 GB 的 H200 是最合适的单卡平台。
- A100 不支持 FP8 计算（算力 8.0 < 8.9），vLLM 只能把 FP8 当作"仅权重量化"（W8A16，Marlin 内核）运行，速度慢于 H100/H200 [23]。
- FASRC 按 fairshare 记账，是否另收费用 [待核]。

#### 3.2 Kempner distributed-inference-vllm 仓库（已核实）

- 仓库地址 github.com/KempnerInstitute/distributed-inference-vllm，Apache-2.0 [17]。
- 配方：Qwen2.5-32B（单卡 A100/H100）、Llama 3.1 70B（4× H100）、Llama 3.1 405B FP8（8× H100 或 4× H200，用 Ray 多节点）、DeepSeek-R1（16× H100 或 8× H200）[17]。
- 环境：uv 环境 `u260304_vllm`（vLLM 0.11.2）、conda 环境（vLLM 0.8.5.post1）、源码编译环境 `u260423_vllm_compiled`（2026-04-24）；**不用容器**；最近更新 2026-04-24 [17]。
- **没有多模态内容，也没有给出吞吐数字** [17]。
- 推断：Qwen3.8 的模型类型是 `qwen3_5` / `Qwen3_5ForConditionalGeneration` [3]，而 vLLM 0.11.2 早于 Qwen3.5 系列发布，很可能不支持；需要用更新的 vLLM（文档已到 v0.27.0 [22]）。最省事的办法是用 Apptainer 拉取 vLLM 官方镜像 [待核：具体版本]。

#### 3.3 Qwen3.8-27B 的显存和并发估算（推断，依据 config.json [3]）

- 权重：FP8 版 30.9 GB [2]。
- KV 缓存：只有 16 层全注意力，4 个 KV 头，head_dim 256 → 每 token 16 × 2 × 4 × 256 × 2 字节 ≈ 64 KiB（BF16 KV）。
- 线性注意力状态：48 层 × 48 个 value 头 × 128 × 128 × 4 字节（fp32）≈ 151 MB/序列，与上下文长度无关。
- 单张 H200 按 0.9 的显存利用率计算：扣除权重、视觉编码器和激活后约剩 80–90 GB。
  - 如果全部用于 KV：约 130 万 token；
  - 64 个并发序列的线性注意力状态约 10 GB。
  - 因此 32–64 个上下文约 20k 的 agent 可以同时运行。
- 这一估算没有计入前缀缓存在 align 模式下额外保存的状态，需要用 `vllm bench serve` 实测。

#### 3.4 图片 token、前缀缓存、多图 agent 循环

- **图片 token**：Qwen3.8 的 patch 为 16 px，2×2 合并，即每 32×32 像素一个 token；单张图最少 65,536 像素，最多 16,777,216 像素（约 64–16,384 个 token）[3]。1600×400 约 650 个 token。
- **限制每次请求的图片数**：用 `--limit-mm-per-prompt`，默认每种模态 999 [22]。
- **图片预处理缓存**：`mm_processor_cache_gb` 默认 4 GiB，避免重复处理同一张图；这个缓存会在每个 API 进程和引擎进程中各存一份 [22]。
- **前缀缓存与图片**：vLLM 把前端生成的图片哈希写入每个块的哈希，所以同一张图在后续轮次中可以命中缓存，不同的图不会冲突 [21]。
- **混合架构的限制**：
  - Qwen3.5/3.6/3.8 开启前缀缓存时必须用 `--mamba-cache-mode align`（Gated DeltaNet 不支持 `all` 模式），vLLM 标为实验性 [24]；
  - LMCache 给 Qwen3.8-27B 的统一块大小是 784 token，只有填满的块才会被缓存 [24]；有 issue 报告 Qwen3.5 的块大小为 528 时，短提示完全无法命中缓存 [25]；
  - LMCache 只验证过纯文本，**图片的 KV 缓存未经验证**；缓存命中和重新计算的输出不是逐位一致 [24]。
  - 对 agent 循环的影响（推断）：每轮都在上一轮基础上追加，前面已填满的 784 token 块都能复用，所以命中率应该很高；但每轮最后不满一块的部分要重新计算。
- **吞吐量**：没有找到 H100/H200 上 Qwen3.6/3.8-27B 的可靠多并发数据。第三方数据：
  - RTX PRO 6000 Blackwell + FP8：5 个并发时峰值 189 tok/s；
  - RTX 6000 Ada + FP8：16 个以内并发时峰值 314 tok/s [26]。

  这些硬件和测试设置都与本项目不同，只能作为下限参考。

#### 3.5 每个事件需要多少 GPU 时间（推断）

- 试点用 gpt-6.1-sol，每个事件约 $0.50–0.75；按输出 $10/MTok 计算，每个事件的输出（含推理过程）**最多**约 5–7.5 万 token。
- 设单张 H200 在 32–64 个并发下总解码速度为 1,000–3,000 tok/s（**未实测**），每个事件约需 17–75 GPU 秒，即 0.3–1.3 GPU 分钟，与设计稿"0.5–1 GPU 分钟/事件"一致。
- 照此计算：6,700 个事件约需 30–140 GPU 小时；"≥5 个种子 × 3 种顺序 × 600–1,500 个练习事件"约需 450–2,500 GPU 小时。用 `gpu_h200` 和 `gpu_requeue` 能承担，但学习流规模的上限要由第一周的实测决定。

### 4. 闭源 API 价格（2026-11-13 查阅）

#### 4.1 文本 token 价格（图片 token 按输入价计费）

| 厂商 | 模型 | 输入 | 缓存命中 | 输出 | Batch | Flex | 来源 |
|---|---|---|---|---|---|---|---|
| OpenAI | gpt-6.1-sol | $2.00 | $0.10 | $10.00 | $1.00 / $0.05 / $5.00 | 按 Batch 价计费；Flex 是 beta，可用模型以价格页为准，gpt-6.1-sol 是否在列 [待核] | [27][28] |
| OpenAI | gpt-6-astra | $10.00 | $1.00 | $50.00 | 约五折 | 同上 | [27] |
| OpenAI | gpt-6.1-terra | $1.00 | $0.05 | $5.00 | 约五折 | 同上 | [27] |
| OpenAI | gpt-6-luna | $0.10 | $0.01 | $0.50 | 约五折 | 同上 | [27] |
| Anthropic | Claude Opus 5.5 | $4 | $0.20（5 分钟缓存写入 $5） | $20 | $2 / $10 | 无 Flex | [31] |
| Anthropic | Claude Sonnet 5.5 | $2 | $0.10（写入 $2.50） | $10 | $1 / $5 | 无 | [31] |
| Anthropic | Claude Haiku 5.5（提示 ≤100k） | $0.10 | $0.01 | $0.50 | $0.05 / $0.25 | 无 | [31] |
| Google | Gemini 4 Carbon / Argon | $2.00 | $0.10 | $10.00 | $1.00 / $5.00 | 同 Batch | [33] |
| Google | Gemini 3.8 Flash | $0.75 | $0.075（另收存储费） | $3.75 | $0.375 / $1.875 | 同 Batch | [33] |
| Google | Gemini 3.5 Flash-Lite | $0.30 | $0.03 | $2.50 | $0.15 / $1.25 | 同 Batch | [33] |

附加说明：
- OpenAI：使用区域处理（数据驻留）加价 10% [27]。GPT-5.6 及之后的模型，缓存最少 1,024 token，默认至少保留 30 分钟，可选 12 小时；图片也会被缓存 [30]。Flex 可能返回 429（资源不足，不计费）或超时 [28]。
- Anthropic：指定 US-only 推理加价 1.1 倍；4.7 及之后的模型使用新 tokenizer，同样文本的 token 数约多 30%；Opus 5.5 和 Sonnet 5.5 的缓存命中价是输入价的 0.05 倍 [31]。
- Google：Gemini 4 的标准价只保证到 2026-11-30，"大多数价格在 12-01 翻倍"；3.x Flash 的价格保证到 12-31 [33]。**设计稿用 Gemini 做预算时必须用 12 月以后的新价格。**

#### 4.2 每张图的成本（1600×400）

| 模型 | 视觉 token | 首次读入 | 缓存命中后再读 | 来源 |
|---|---|---|---|---|
| gpt-6.1-sol | 约 780（按 gpt-6 / 5.6 系列的 32 px patch × 1.2 推算 [待核]） | $0.00156（Flex $0.00078） | $0.000078 | [27][29] |
| Claude Opus 5.5 | 870 | $0.00348 | $0.000174 | [31][32] |
| Claude Sonnet 5.5 | 870 | $0.00174 | $0.000087 | [31][32] |
| Gemini 3.8 Flash | 1120（固定） | $0.00084（Flex $0.00042） | $0.000084 | [33][34] |
| Qwen3.8-27B（自部署） | 约 650 | GPU 时间 | — | [3] |

推断：按试点每个事件约 16 张图计算，图片首次读入只要 $0.01–0.06，只占每个事件总成本（$0.50–0.75）的约 5%。主要成本来自两部分：每轮重读整个上下文，以及输出和推理 token。所以省钱的关键是：
- 保持前缀稳定，提高缓存命中率；
- 删掉不再需要的旧图（设计稿中"清理历史图片"是对的，但删图会打断其后的缓存前缀，要放在一轮结束时统一删）；
- 控制推理长度。

#### 4.3 Batch 和 Flex 适合哪些用途

- Batch 是异步的（结果最长可能要等 24 小时），**不适合多轮 agent 循环**——每一轮都依赖上一轮的结果。它适合单轮任务：本项目的"只测看图"实验、事件后的反思和总结、离线评分（推断）。
- 需要多轮交互、又想享受五折价时，用 OpenAI 或 Google 的 Flex。Anthropic 没有 Flex 档，只能靠缓存降低成本（命中价是输入价的 0.05 倍）。

## 对本项目的影响

1. **规模可以扩大，但先完成两项一周内能做完的实测。**
   - (a) 在 `gpu_h200` 上用新版 vLLM（建议用 Apptainer 镜像）部署 Qwen3.8-27B-FP8，开启 `--enable-prefix-caching --mamba-cache-mode align`，用试点的真实 agent 轨迹回放，测 16/32/64 并发下的总 tok/s、首 token 延迟、缓存命中率和每事件 GPU 秒；
   - (b) 在 A100 上跑同样的测试作为备选（W8A16，较慢）。

   如果实测在每事件 1 GPU 分钟以内，学习流就可以扩到设计稿建议的种子数和顺序数。
2. **T1 层的候选应同时包括 Qwen3.8-27B 和 Gemma 4 31B，再加一个大一些的 MoE 作为 T1.5。** 草稿中"老师目前部署的是 Gemma"——Gemma 4 31B 没有公开的图表成绩，必须在方向 08 建议的读图校准实验中实测，不能默认它和 Qwen3.8 一样好。T1.5 可以是 Qwen3.8-Flash-Next-FP8（2 卡）或 GLM-5.3-Flash（4 卡），用于 T1 判断不一致的事件，减少送往闭源模型的比例。
3. **GLM-5.3 不能作为本分支的看图模型。** 如果本分支沿用上游运行框架并希望用 GLM 系列：
   - 改用 GLM-5.3-Flash（API 或自部署）；
   - 先测试 Anthropic 兼容接口能否传图片；
   - 不行就改用 OpenAI 兼容接口。

   不要以为 GLM-5.3 能接收图片。
4. **闭源层（T2）按最新价格重算预算。**
   - gpt-6.1-sol 的价格和设计稿一致（$2 / $0.10 / $10，Batch 五折），但需要确认它在 Flex 可用模型名单上；
   - 如果 Flex 不可用，多轮 agent 只能用标准价加缓存，设计稿的"Flex + 裁图"那一列（约 $5.5k）会被低估，最多可能翻倍（约 $11–13k）；
   - 备选：Sonnet 5.5 的标价和 gpt-6.1-sol 相同，缓存命中价相同（$0.10），没有 Flex；Gemini 3.8 Flash 输入、输出价约是前两者的 1/3，且有 Flex。
5. **把"读图校准实验"放在 Batch 上跑**（单轮），成本减半，而且不受多轮限制。
6. **成本报告中按"图片 token / 文本输入 / 缓存命中 / 输出"分开记账**，以便画 H4 的成本–性能帕累托曲线时区分各部分的贡献。

## 未解决与待核

- gpt-6.1-sol 是否支持 Flex；它的图片 token 规则（OpenAI 文档表中没有列出）。
- vLLM 支持 `qwen3_5` 架构的最低版本；在 FASRC 上用 Apptainer 运行 vLLM 官方镜像是否需要额外的 CUDA/驱动配置。
- 前缀缓存 align 模式在多模态输入下是否稳定；图片 KV 缓存是否正确命中（LMCache 未验证）。
- FASRC 的 `gpu` 分区 A100 是 40 GB 还是 80 GB；本课题组能否使用 Kempner 分区；FASRC 是否按 GPU 小时收费。
- GLM-5.3-Flash 的图表成绩（官方只有 OmniDocBench）；它通过 Anthropic 兼容接口能否接收图片。
- Gemma 4 31B 和 GLM-5.3-Flash 在图表基准上的官方分数 [未找到]。
- 没有找到 H100/H200 上 27B 级 VLM 多图 agent 负载的吞吐基准，只能靠自测。
- 搜索预算在本轮用完，Mistral Small 4、Muse Glimmer、Kimi K3 只看到二手来源；需要时下一轮再核实。

## 参考文献

1. Qwen Team (2026). Qwen3.8-27B model card. https://huggingface.co/Qwen/Qwen3.8-27B [已读原文]
2. Hugging Face Hub API：Qwen/Qwen3.8-27B、Qwen3.8-27B-FP8、Qwen3.8-Flash-Next(-FP8)、Qwen3.8-2.4T-A95B 的仓库元数据（createdAt 等；2026-11-13 查询）. https://huggingface.co/api/models/Qwen/Qwen3.8-27B-FP8 ；QwenLM/Qwen3.8 GitHub README（搜索摘要）. https://github.com/QwenLM/Qwen3.8 [API 已读；GitHub 未打开原文]
3. Qwen/Qwen3.8-27B config.json 与 preprocessor_config.json. https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/config.json [已读原文]
4. Qwen Team (2026). Qwen3.8-Flash-Next model card. https://huggingface.co/Qwen/Qwen3.8-Flash-Next [已读原文]
5. Google (2026). Gemma 4 model card. https://ai.google.dev/gemma/docs/core/model_card_4 [已读原文]
6. Gemma Team (2026). Gemma 4 Technical Report. arXiv:2607.02770. https://arxiv.org/abs/2607.02770 [只读摘要]
7. google/gemma-4-31B-it model card 及 HF API 元数据. https://huggingface.co/google/gemma-4-31B-it [已读原文]
8. Z.ai (2026). GLM-5.3-Flash model card. https://huggingface.co/zai-org/GLM-5.3-Flash [已读原文]
9. Z.ai. GLM-5.3 文档. https://docs.z.ai/guides/llm/glm-5.3 [已读原文]
10. Z.ai. VLM 指南（GLM-5.3-Flash / FlashX）. https://docs.z.ai/guides/vlm [已读原文]
11. Z.ai. GLM-5V-Turbo 文档；Vercel AI Gateway 列表. https://docs.z.ai/guides/vlm/glm-5v-turbo ；https://vercel.com/ai-gateway/models/glm-5v-turbo [未打开原文（仅搜索摘要）]
12. llm-stats.com. CharXiv-R Leaderboard（2026-11-13 查阅，第三方聚合）. https://llm-stats.com/benchmarks/charxiv-r [已读原文]
13. Mercor. CharXiv leaderboard（2026-11-13 查阅）. https://www.mercor.com/apex/oss-benchmarks/oss-charxiv-leaderboard/ [已读原文]
14. Turing Post. 10 Open-Weight Multimodal Models to Know in 2026（2026-08-27 更新）. https://www.turingpost.com/p/10-open-mllms [已读原文]
15. VentureBeat 等. Meta returns to open source with Muse Glimmer（2026-08）. https://venturebeat.com/technology/meta-returns-to-open-source-with-muse-glimmer-an-apache-2-0-licensed-30b-parameter-ai-model-optimized-for-agents-available-now [未打开原文]
16. OpenGVLab. InternVL GitHub（InternVL3.5，2025-08）. https://github.com/OpenGVLab/InternVL [未打开原文]
17. Kempner Institute. distributed-inference-vllm. https://github.com/KempnerInstitute/distributed-inference-vllm [已读原文]
18. FASRC (2025-08-18). New gpu_h200 partition. https://www.rc.fas.harvard.edu/blog/new-h200-partition/ [已读原文]
19. FASRC. Running Jobs（分区表）. https://docs.rc.fas.harvard.edu/kb/running-jobs/ [已读原文]
20. FASRC. Kempner partitions（2026-09-18 更新）. https://docs.rc.fas.harvard.edu/kb/kempner-partitions/ [已读原文]
21. vLLM. Automatic prefix caching design（2026-06-23 版）. https://docs.vllm.ai/en/latest/design/prefix_caching.html [已读原文]
22. vLLM v0.27.0. MultiModalConfig API. https://docs.vllm.ai/en/v0.27.0/api/vllm/config/multimodal/ [已读原文]
23. vLLM. FP8 quantization（LLM Compressor）. https://docs.vllm.ai/en/latest/features/quantization/llm_compressor/fp8/ [已读原文]
24. LMCache. Qwen3.5 / Qwen3.6 / Qwen3.8 series recipe. https://docs.lmcache.ai/recipes/qwen3_5.html [已读原文]
25. vLLM GitHub issue #40696（Qwen3.5 前缀缓存块大小 528）. https://github.com/vllm-project/vllm/issues/40696 [未打开原文（仅搜索摘要）]
26. 第三方吞吐测试：Millstone AI（Qwen3.6-27B FP8，1× RTX Pro 6000 Blackwell）；hexgridcloud（Qwen3.6-27B-FP8，1× RTX 6000 Ada）. https://www.millstoneai.com/inference-benchmark/qwen3-6-27b-fp8-1x-rtx-pro-6000-blackwell ；https://huggingface.co/blog/hexgridcloud/qwen3-6-27b-fp8-on-one-rtx-6000-ada-fast-ttft-668 [未打开原文（仅搜索摘要）]
27. OpenAI. API Pricing（2026-11-13 查阅）. https://developers.openai.com/api/docs/pricing [已读原文]
28. OpenAI. Flex processing. https://developers.openai.com/api/docs/guides/flex-processing [已读原文]
29. OpenAI. Images and vision. https://developers.openai.com/api/docs/guides/images-vision [已读原文]
30. OpenAI. Prompt caching. https://developers.openai.com/api/docs/guides/prompt-caching [已读原文]
31. Anthropic. Pricing（2026-11-13 查阅）. https://platform.claude.com/docs/en/about-claude/pricing [已读原文]
32. Anthropic. Vision. https://platform.claude.com/docs/en/build-with-claude/vision [已读原文]
33. Google. Gemini API pricing（2026-11-13 查阅）. https://aistudio.google.com/docs/pricing [已读原文（前 10 万字符）]
34. Google. Media resolution. https://aistudio.google.com/docs/media-resolution [已读原文]
