# Retired variant drafts

Kept for reference only. `run.sh` dispatches `task_<variant>.json` from the
parent directory only, so nothing here is runnable without moving it back up.
Note: the drafts reference `output_contract_v2.json`, which was renamed to
`output_contract_standard.json` during consolidation and later to
`../output_contract.json` when the family was reduced to min/tools/guided.

- **`pubtools`** — public-ecosystem-encouraged tool policy. Retired because the
  neutral policy of `base_standard` already permits public pretrained models,
  making the pubtools-vs-neutral contrast weak; the legacy `tools` variant
  (curated local snapshots, mandated chain) is the strong tools-positive
  endpoint of the axis. Rebuild recipe: copy `../prompt_base_standard.md`,
  swap the `### Tool policy` section with the one in `prompt_base_pubtools.md`.
- **`staged`** — core-window-first staging (Stage A mandatory, Stage B archive
  extension). Retired because its guarantee — complete and checkpoint the core
  window before extending into the archive — is now folded into
  `prompt_base_full.md`'s `### Processing scope` section.

# Retired 2026-10-14: reduction to the min/tools/guided family

The experiment was reduced to three single-factor arms around the research
questions (see `../VARIANTS.md`); everything below lost its role in that
design and was moved here unchanged. Rebuild recipes assume the 2026-10-13
generation of the family (commit `f843a90`).

- **legacy `base`** (`prompt_base.md` + `task.json`) — the original
  knowledge-light baseline with agent-chosen scope. Superseded by `min` as
  the control arm; agent-chosen scope survives as the deliberate no-window
  policy of `min`/`tools`. The 2026-10-13 claude run of this variant
  (completed, 3 h 09 m, 1,760 events) preserves its exact prompt in that
  run's `control/agent_prompt.md`. Rebuild recipe: `min` prompt with the
  legacy prose sections restored from `prompt_base.md`.
- **`base_standard`** (`prompt_base_standard.json` + `prompt_base_standard.md`)
  — professional-guidance control of the retired three-phase matrix. Not an
  arm of any research question; its shared sections live on inside
  `../prompt_guided.md`. Rebuild recipe: `git show f843a90`.
- **`base_notools`** (`task_base_notools.json` + `prompt_base_notools.md`) —
  tool-axis floor. Redundant once `min` (which exposes no tools) became the
  Q2 contrast partner. Rebuild recipe: `git show f843a90`.
- **`base_full`** (`task_base_full.json` + `prompt_base_full.md`) —
  full-archive flagship with core-window-first priority. Outside the current
  research questions; recreate when a full-archive arm is wanted.
  Rebuild recipe: `git show f843a90`.
- **`main.py`** — deterministic infrastructure baseline (two fixed candidate
  events) used to smoke-test the runner and scoring path without an agent.
  Retired from the active interface when the family was reduced; preserved
  here byte-identical, still runnable directly.
- **legacy two-hour `tools`** (`prompt_tools_2h_window.md` +
  `task_tools_2h_window.json`) — fixed two-hour mainshock window, mandated
  tool chain, execution/repair rules. Superseded by `../prompt_tools.md`
  (min + Tools section, no window, no chain mandate) for single-factor
  isolation; its validated tool-usage notes were carried over verbatim.
  Rebuild recipe: diff `prompt_tools_2h_window.md` against `../prompt_tools.md`.
