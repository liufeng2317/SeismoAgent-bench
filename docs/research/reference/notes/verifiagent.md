# VerifiAgent: a Unified Verification Agent in Language Model Reasoning

- Authors: Jiuzhou Han, Wray Buntine, Ehsan Shareghi (Monash University, VinUniversity)
- arXiv: 2504.00406, version read: v2 (21 Aug 2025)
- URL: https://arxiv.org/abs/2504.00406; code https://github.com/Jiuzhouh/VerifiAgent (not read)
- Reading: full text (Sec. 1–6, limitations, App. D cost, App. F system prompt)

## Earlier claim under review

[claimed: meta verification (completeness, consistency) then tool-based adaptive verification] — Correct.

## What the paper says

### How the two levels are split (Sec. 3)

- **Level 1, meta verification.**
  - Checks "completeness and consistency". "The completeness refers to a solution that is self-contained, fully addresses every part of the question, and contains a clear result or conclusion. The consistency refers to reasoning that follows a logical structure with no jumps, gaps, or inconsistencies."
  - Uses no tools. The solution is first normalised: "list all the known conditions and the final objective provided in the problem, then divide the solution into individual and explicit logical steps" (Sec. 3.1).
- **Level 2, tool-based adaptive verification.**
  - "evaluates factual and computational accuracy". "The agent will first solve the question using appropriate tools, and then verify the results by comparing them with the original solution" (Sec. 3.2).
  - Tools: Python interpreter, search engine, symbolic solver. The paper's description of Level 2 is that of an independent re-derivation compared against the answer.
- **Output.** A binary verdict, a confidence score from the softmax over the verdict token's top-5 log-probabilities, and, if the answer is wrong, "fine-grained feedback" giving "the identified error reason ... and a potential revision method that incorporates observations from tool execution results" (Sec. 3.3).

### When tools are invoked

- The paper frames the levels as a gate: "This initial layer acts as a foundational check, preventing incomplete or inconsistent solutions from progressing further ... only solutions with structural integrity and coherent reasoning proceed to the next tool-based adaptive verification" (Sec. 3.1).
- In the actual system prompt (App. F), both levels run inside one ReAct-style agent: "Before you perform tool verification, you should first do a meta verification without tool ... Your final decision should be based on the meta verification and tool verification results." The gating is therefore prompt-level and soft, not a hard programmatic short-circuit. This is my reading; the paper does not state it explicitly.
- Tool choice follows reasoning type, and the agent "autonomously determines the required number of external tool calls". Observed choices (Sec. 5, Fig. 4): Python on MATH 98.6% (symbolic solver 1.4%), search engine on StrategyQA 100%, symbolic solver (the Z3 theorem prover) only, 100%, on ProverQA.

### Ablation (Table 7)

| Variant | MATH Acc/Pre/Rec | ProverQA Acc | StrategyQA Acc |
|---|---|---|---|
| Full VerifiAgent | 0.85/0.86/0.92 | 0.77 | 0.84 |
| w/o meta verification | 0.79/0.78/0.96 | 0.74 | 0.83 |
| w/o tool verification | 0.75/0.75/0.98 | 0.74 | 0.78 |

- Paper: "removing tool verification results in even more substantial performance reductions, bringing the performance close to baseline levels. Additionally, tool verification tends to enhance accuracy and precision, whereas meta verification primarily improves recall."

### Cost discussion

- No separate cost analysis of verification itself versus the baseline verifiers.
- Cost appears only for inference scaling (Sec. 4.3, App. D, Table 10). The procedure samples until VerifiAgent accepts, falling back to majority vote at the cap, and this beats majority voting "with fewer samples and less cost" on MATH and StrategyQA, with "similar cost levels" on ProverQA.
- It is also reported as cheaper than two 7B PRMs for MATH inference scaling.
- Limitations: only three tools; limited model coverage "due to the significant computational costs".
- **Verifier strength matters.** "When the reasoner (o3-mini) surpasses the VerifiAgent (GPT-4o) in capability, the performance gain is limited" (Sec. 4.3).

## Implication for us

- **Two-level checker.** VerifiAgent is a clean precedent for a two-level verification: cheap structural checks (complete? internally consistent?) followed by tool-grounded correctness checks. Our checker maps onto it:
  - Level 1: completeness and consistency of stage products — every stage output present, schemas valid, event and pick counts consistent across stages, provenance recorded.
  - Level 2: tool-computed seismological symptoms — residual statistics, Vp/Vs, depth artefacts, magnitude–amplitude consistency.
- **Split the gate in code.** Their prompt-level gating suggests implementing the gate in code: run Level 2 only on stages that pass Level 1, which also saves compute on broken runs.
- **Recall vs precision split.** The ablation pattern (meta raises recall, tools raise precision) is worth testing on our checker. Structural checks may flag more problems; tool-based symptoms may be more specific.
- **Weak checkers cap gains.** The "verifier weaker than reasoner yields limited gain" finding argues for a checker built from deterministic tools rather than an LLM judge, whose ceiling is the judge model.
- **Difference.** VerifiAgent verifies single reasoning answers that have ground truth. We verify long multi-stage processing without a reference catalog, so "re-solve and compare" is replaced by internal-consistency and physics checks.
