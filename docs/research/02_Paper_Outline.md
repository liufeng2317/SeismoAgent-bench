# Paper outline and work plan

Status: outline agreed 2026-10-29. Numbers are metrics v1
(`docs/framework/03_EVALUATION_METRICS.md`) unless a source is named. This
document supersedes the S2/S3 definitions written on 2026-10-28 in
[`00_Research_Plan.md`](./00_Research_Plan.md) and
[`04_Expert_Experience_and_Checker.md`](./04_Expert_Experience_and_Checker.md).

## 1. Goal and core question

> **Can an agentic approach build high-precision earthquake catalogs
> automatically — and if not, is the missing piece tools, knowledge, or
> the ability to validate its own results?**

The paper answers it in four parts:

1. **Cases in tiers.** Six cases, from basic to hard, across induced,
   swarm, volcanic, moderate and large mainshock–aftershock, and complex
   multi-fault settings (§3).
2. **Tools.** What a validated tool library adds to a general Agent (S0 →
   S1).
3. **Knowledge.** What case-agnostic expert knowledge, given up front,
   adds on top of tools (S1 → S2).
4. **Improving agentic catalogs.**
   - *Human-in-loop iteration*: the human-in-loop final is the upper
     bound; coding each human intervention shows which of them could be
     automated (§7).
   - *Expert experience as automated validation*: a reference-free checker
     run on the Agent's own products, with the Agent required to repair
     upstream (S2 → S3), and how much of the S1-to-final gap it closes.

## 2. Claims and the evidence each needs

| Claim | Evidence | Status |
|---|---|---|
| Difficulty rises across the tiers | tier features (§3) and expert difficulty: rounds, blind → final gap, ceiling | features to tabulate |
| Tools are necessary | S0 vs S1 on six cases: completion, recall_norm, pick timing | Prague, Magna done; Maple min running |
| Tools are not sufficient | S1 vs final: detection ~75 % of final (template matching barely used), back-end systematic errors (swap) | Prague, Magna done |
| Knowledge helps, and where | S2 vs S1 per dimension and tier | not started |
| Automated validation closes the gap | S3 vs S2; gap closure (S3 − S1)/(final − S1) per dimension | not started |
| Part of the final is unreachable without references | human-in-loop intervention coding (§7); expert ladder | ladder done; coding not started |
| A usable catalog is (or is not) reached | usability criteria (§6), pass/fail per case × stage | criteria drafted, not frozen |

## 3. Case tiers

Tiers are assigned from features known before any run; the expert's
experience then has to confirm the order. Events per day are from the
human-in-loop final.

| Tier | Case | Regime | Stations | Window | Final events/day | Main difficulty |
|---|---|---|---:|---|---:|---|
| Basic | Prague 2011 | induced, aftershocks of Mw 5.7 (mainshock before window) | 23 | 8 d | ~850 | compact network, 1-D layered model; changing deployment |
| Basic | Magna 2020 | moderate mainshock–aftershock, Mw 5.7 in window | 47 | 8 d | ~680 | basin velocity structure, depth control |
| Intermediate | Maple Creek 2017 | Yellowstone swarm, max Mw 4.4 | 27 | 8 d | ~1,550 | vertical-only sites; high rate of small events; magnitude of the largest events |
| Intermediate | Kīlauea 2018 | volcanic summit collapse, Mw 6.9 in window | 25 | 8 d | ~650 | 3-D structure, template families mislocate; Mw 6.9 coda |
| Hard | Ridgecrest 2019 | M6.4 and M7.1 sequence | 42 | 3 d | ~6,000 | mainshock coda, extreme association density, large-event QC |
| Hard | Kaikōura 2016 | multi-fault aftershocks of Mw 7.8 | 53 | 8 d | ~1,600 | 260-km network, 3-D structure, 1-D vs 3-D frame offset (expert scatter 2.78 km) |

To tabulate in Phase A (`evaluation/tiers.json`): network aperture and
median inter-station distance, largest magnitude inside the window, event
rate, structural complexity (1-D adequate or not), station defects;
expert difficulty: human-in-loop rounds, blind → final change per
dimension, reference-to-reference ceiling. Kīlauea (Mw 6.9 inside the
window) is the case most likely to move tier; a move is recorded with its
reason, not hidden.

## 4. Agent stages

Each stage adds exactly one factor to the one before. The Agent, its
harness, the model and the output contract stay the same, except that S3
adds the checker report to the contract (§5).

| Stage | Arm | Agent additionally gets | Answers | Status |
|---|---|---|---|---|
| S0 | `min` | task, data, output contract | baseline | formal runs in progress |
| S1 | `tools` | validated tool library `seismotools` with usage docs | 2. tools | formal runs in progress |
| S2 | `knowledge` | tools + case-agnostic expert knowledge given up front (§5.2) | 3. knowledge | not implemented |
| S3 | `checker` | tools + knowledge + reference-free checker after every stage, with upstream repair required (§5.3) | 4b. automated validation | not implemented |
| — | human-in-loop final | — | 4a. upper bound | done (all six) |

Optional: `tools + checker` without knowledge on three cases chosen from
the S1 failure modes. It separates *knowing how to do it* from *knowing
that it went wrong*.

The `guided` arm (expert scaffolding, fixed window, `report.md` contract)
is not on this ladder and stays optional.

**Headline number:** gap closure per dimension,
`(S_k − S1) / (final − S1)`, for detection `recall_norm`, `shift`,
`dz_median`, and the magnitude offset, reported by tier.

## 5. Form of the knowledge and the checker

**Principle.** The paper claims something about *general-purpose* Agents.
So the Agent, its loop and the model are never modified. Every stage only
adds files to the Agent's environment, the same way S1 adds tools. No
custom agent loop, no harness-side retries, and no custom subagent.

### 5.1 Two layers

| Layer | Form | Why this form |
|---|---|---|
| Diagnostics | a deterministic program in `seismotools/checker/` (CLI) that reads the Agent's picks, events and catalog and writes `checker_report.json` plus figures; rules and ranges only, no case numbers, no references | same status as every other tool; no LLM inside, so it cannot rationalise a symptom away; identical for any Agent |
| Knowledge | an Agent Skill (`SKILL.md` + reference files): method choices, safe parameter ranges, known pitfalls; in S3 also the symptom → likely cause → upstream repair table of 04 §3 | an open format that general Agents load natively (Claude Code skills; Codex skills); progressive disclosure keeps it out of context until relevant |

**Delivery.** The skill is installed in the Agent's runtime skill
directory. An Agent without skill support gets the same files linked from
the prompt, as `prompt_tools.md` does for the tools. The S2 and S3 prompts
add one line naming the skill, just as S1 adds the tools section.

### 5.2 S2 — knowledge

The skill holds what an expert knows before looking at any data:

- the pipeline and when template matching and double-difference relocation
  are expected to add events or precision;
- velocity-model and locator choices, and grid bounds;
- magnitude: units, direct versus chained ML, large-event handling;
- pitfalls observed in the runs and the ladder, e.g. never fix depth
  silently, check the magnitude scale, apply the PhaseNet blinding offset,
  do not let station terms absorb a frame shift.

### 5.3 S3 — checker

The same skill adds the diagnostics tool and the playbook. The contract
adds two items:

- `checker_report.json`, produced by the checker on the submitted catalog;
- one disposition per flag: `fixed` (with what changed) or `justified`
  (with evidence).

The scorer re-runs the checker on the submitted files and verifies the
report. This is the only enforcement, and it is a contract item, not a
loop. Whether and how often the Agent runs the checker before submission
is logged from the transcript and is itself a result.

### 5.4 Why not a subagent

- **Not portable.** Subagent definitions are harness-specific, so the
  "general Agent" claim would hold for one harness only.
- **Adds a confound.** A reviewing subagent is a second LLM context: extra
  compute and a second opinion. A gain could come from the multi-agent
  architecture rather than from the knowledge.
- **Wrong fix for the observed failure.** The Agent's main failure was
  rationalisation: Prague tools explained ML −8 as "ultra-quiet array
  microseismicity". A deterministic flag that must be dispositioned
  addresses that directly; another LLM's opinion may not.

An independent reviewer — a fresh session of the same general Agent given
the checker skill — is a possible later ablation. It is not part of the
ladder.

### 5.5 Constraints

- **Leakage.** Rules are case-agnostic and reference-free, and every use is
  logged.
- **Circularity.** Each rule records the case(s) it was learned from
  (04 §3, *Evidence*). Results are reported both for cases a rule came from
  and for the others (§8).

## 6. Usability criteria (draft — freeze before the first S2 run)

Summary layer over metrics v1 outputs; no metric definition changes. A
case × stage run is **usable** when all hold against the primary
references:

| Dimension | Criterion |
|---|---|
| completion | contract-valid catalog |
| detection | `recall_norm` ≥ 0.9 × final |
| precision | `audited_false_rate` ≤ 2 % |
| absolute location | `shift` ≤ 1 km and ≤ final + 0.5 km |
| depth | \|`dz_median`\| ≤ 0.5 km; `depth_mode_share` ≤ 5 % |
| magnitude | \|median `dmag`\| ≤ 0.2; all M ≥ 4 events present |

Per-case exceptions are allowed only where the final itself fails a
criterion. Example: Kaikōura's frame offset makes the location criteria
relative to the final. Exceptions are written down when the criteria are
frozen. Frozen criteria are added to `03_EVALUATION_METRICS.md` §11 as a
reporting convention.

## 7. Human-in-loop interventions (Phase A, no compute)

Code every intervention in the six `expert/PLAN.md` histories and the
ladder (`evaluation/human_in_loop/expert_ladder.json`) into one of four
classes:

| Class | Example | Automatable by |
|---|---|---|
| execution / tool | fix a tool call, resampling, file handling | tools (S1) |
| method choice | add template matching, EDT, direct ML | knowledge (S2) |
| reference-free diagnosis | depth pile-up, origin-time–depth coupling, coda ghosts | checker (S3) |
| reference-informed diagnosis | Ridgecrest layered frame from Shelly; Magna ML calibration against UUSS | not automatable without references |

The share of each class, weighted by its ladder effect, predicts the
largest gap closure S3 can achieve. The last class is the part of the
final no Agent can reach without references.

## 8. Controls

- **Repeats.** Metrics §6 asks for at least two runs per configuration.
  First pass: one run per case × stage. Second runs go first to S1 and S3
  (the headline contrast), starting with Prague and Magna S1, to measure
  run-to-run spread before deciding the rest.
- **Second model.** Run S1 and S3 on three cases (one per tier) with a
  second model, so the conclusion is about agentic methods rather than one
  model (GLM-5.3 in Claude Code so far).
- **Held-out generalisation (optional).** One Tier B case (00 §2.3; e.g.
  South Napa 2014 or Westmorland 2020) with references and ceiling but no
  human-in-loop final, run under S1 and S3. Neither the knowledge nor the
  checker rules were learned from it.
- **Analyses for every run:** metrics v1, component swap, blind audit.
  The second rater spot-checks 10 per run.

## 9. Work plan

| Phase | Work | Runs | Estimate |
|---|---|---:|---|
| A (now) | finish S0/S1 on six cases (Maple min running; then Maple tools, Kīlauea, Kaikōura, Ridgecrest); score, swap, blind audit, second-rater check. In parallel without compute: tier table (§3), freeze usability criteria (§6), intervention coding (§7) | 7 | ~1 week, single queue, 5–8 h per run |
| B | build the checker CLI and the knowledge skill; skill delivery in the runner; checker contract and scorer verification; debug on pilot runs (not counted) | 0 formal | 3–5 days |
| C | S2 and S3 on six cases; S1 repeats on Prague and Magna; second model S1/S3 on three cases; optional `tools + checker` on three | ~25 | ~7–8 days single queue |
| D | analysis, figures, writing | — | — |

## 10. Paper outline

1. **Introduction** — agentic science; earthquake catalogs as a complete,
   objectively testable task.
2. **Benchmark** — six tiered cases; multiple references and the ceiling;
   the human-in-loop final as the upper bound.
3. **Evaluation** — metrics v1; shift/scatter decomposition; component
   swap; blind audit; usability criteria.
4. **Results I: tools** — S0 vs S1 (necessary, not sufficient).
5. **Results II: knowledge** — S1 vs S2 by dimension and tier.
6. **Results III: human-in-loop iteration** — expert ladder;
   intervention coding.
7. **Results IV: automated validation** — S3; gap closure; checker use and
   dispositions; in-sample vs out-of-sample rules.
8. **Discussion** — which catalog dimensions an Agent can be trusted with,
   in which settings; what still needs a human or a reference.

| Figure | Content |
|---|---|
| 1 | benchmark overview and case map with tiers |
| 2 | heat map: case × stage × dimension, normalised to the final |
| 3 | gap-closure waterfall S1 → S2 → S3 → final per tier |
| 4 | component swap (front end vs back end) |
| 5 | human-in-loop ladder and intervention classes |
| 6 | checker use: flags raised, fixed, justified, missed |

## 11. Open items

- Second model and harness choice (§8).
- Held-out case: whether, and which (§8).
- The task-level `VARIANTS.md` files still list `guided` as the knowledge
  arm (Q3). Update them when S2/S3 task files are added in Phase B.
