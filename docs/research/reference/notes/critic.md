# CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing

- Authors: Zhibin Gou, Zhihong Shao, Yeyun Gong, Yelong Shen, Yujiu Yang, Nan Duan, Weizhu Chen (Tsinghua, Microsoft); ICLR 2024
- arXiv: 2305.11738, version read: v4 (21 Feb 2024)
- URL: https://arxiv.org/abs/2305.11738
- Reading: full text (Sec. 1–5; App. C.1, D.1, D.6)

## Earlier claim under review

[claimed: LLMs unreliable at self-verification; external tools ground it] — Correct in substance, but the strong form ("self-correction without tools fails") is overstated. The paper's own numbers show self-correction without tools is mixed: sometimes a small gain, sometimes a loss, never as good as with tools. The cleanest evidence that self-verification is unreliable is the hallucination-detection AUROC table (Table 5).

## What the paper says

### Framework (Sec. 3)

- The LLM produces an output, critiques it while interacting with a tool (search engine, Python interpreter, Perspective API), and then corrects it. The loop iterates up to a cap; for QA it stops early "if the answer remains the same for two consecutive corrections" (Sec. 4.1).
- Two correction settings. CRITIC corrects every sample. CRITIC* is an oracle that corrects only the wrong ones, so it is an upper bound and not deployable.

### Evidence on self-correction without tools ("CRITIC w/o Tool")

**Free-form QA** (Table 1; AmbigNQ, TriviaQA, HotpotQA; 500 sampled validation questions each). In the "w/o Tool" variant the LLM generates its own evidence instead of searching.

| Model | Dataset | CoT (EM/F1) | CRITIC w/o Tool | CRITIC |
|---|---|---|---|---|
| text-davinci-003 | AmbigNQ | 44.2/58.6 | 42.0/58.3 | 50.0/64.9 |
| text-davinci-003 | TriviaQA | 67.4/74.5 | 67.3/74.7 | 72.7/80.6 |
| text-davinci-003 | HotpotQA | 33.7/46.1 | 34.9/46.1 | 38.7/50.5 |
| ChatGPT | AmbigNQ | 51.8/64.3 | 55.2/67.3 | 62.0/74.9 |
| ChatGPT | HotpotQA | 32.7/42.8 | 33.1/46.1 | 40.3/52.9 |

- Paper summary: "the model's own critiques contribute marginally to the improvement (-0.03 and +2.33 F1 with the two LLMs), and even fall short compared to the initial output" (Sec. 4.1, result 4).

**Math program synthesis** (Table 2, exact match). In the "w/o Tool" variant the interpreter information is removed.

| Model | Dataset | PoT | w/o Tool | CRITIC |
|---|---|---|---|---|
| text-davinci-003 | GSM8k | 70.1 | 68.3 (−1.8) | 72.2 (+2.1) |
| text-davinci-003 | SVAMP | 84.0 | 80.7 (−3.3) | 80.7 (−3.3) |
| ChatGPT | GSM8k | 72.5 | 77.0 (+4.5) | 78.2 (+5.7) |
| ChatGPT | TabMWP | 75.0 | 87.0 (+12.0) | 89.0 (+14.0) |

- Paper: "Without execution feedback from the interpreter, the ability of LLMs to correct programs becomes limited and unstable. This can result in surprising performance deterioration, such as the 1.8-point decrease observed on text-davinci-003".
- Self-Refine on Codex/PAL dropped GSM8k from 71.3 to 26.7 (−44.6) when it was not run in oracle mode (Table 10, App. D.6, numbers quoted from Madaan et al.). This is the most dramatic deterioration cited.
- Note the SVAMP row: even the tool-using CRITIC lost 3.3 points for davinci. So tools are not a guarantee either.

**Toxicity** (Table 3). With the LLM scoring toxicity instead of Perspective API, toxicity probability barely moves (ChatGPT 0.192 → 0.223) versus 0.040 with the API.

**Self-verification as uncertainty estimation** (App. D.1, Table 5, hallucination detection).

| Method | AmbigNQ AUROC | TriviaQA AUROC | HotpotQA AUROC |
|---|---|---|---|
| Expressed self-evaluation (Kadavath et al.) | 0.668 | 0.731 | 0.713 |
| CRITIC (tool-based verification) | 0.810 | 0.818 | 0.831 |

- Paper: "our tested LLMs are incapable of accurately identifying 'what they know' without relying on external tools ... without the aid of oracle verification ... self-correction might surprisingly deteriorate performance for many tasks, even worsening the initial answer" (App. C.1).

### Other findings

- "2-3 rounds of corrections yield most of the benefits" (Sec. 4.4).
- Gains scale with model size; for example, TabMWP improves by +4.7, +9.4 and +16.0 for LLaMA-2 7B, 13B and 70B (Sec. 4.2).
- Much of the reported headline gain sits in the oracle CRITIC* rows, which assume a perfect error detector.

## Implication for us

- **Main citation.** CRITIC is the right citation for "verification should be grounded in tool-computed evidence, not the agent's own judgement". In our setting the checker computes symptoms from intermediate catalog products: pick residual distributions, Wadati consistency, depth histograms, station-delay patterns. The agent then reasons over those numbers instead of judging its own catalog.
- **Use the measured form.** Say that LLM self-assessment discriminates poorly (AUROC 0.67–0.73) and that self-correction without external feedback is "marginal" and "unstable", with occasional large losses. Do not say it always fails.
- **Detection is the bottleneck.** The gap between CRITIC and the oracle CRITIC* (e.g. ChatGPT AmbigNQ F1 74.9 vs 79.9) shows that most of the value is in deciding which outputs need correction. This supports investing in the checker as a detector of symptoms, separately from the playbook that repairs them.
- **Tools do not guarantee improvement** (SVAMP −3.3 with tools). Our adoption rules should require a measured improvement on the checker before a change is accepted, rather than accepting any tool-informed revision.
