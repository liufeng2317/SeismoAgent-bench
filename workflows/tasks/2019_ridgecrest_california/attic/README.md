# Retired variant drafts

Kept for reference only. `run.sh` dispatches `task_<variant>.json` from the
parent directory only, so nothing here is runnable without moving it back up.
Note: the drafts reference `output_contract_v2.json`, which was renamed to
`../output_contract_standard.json` during consolidation.

- **`pubtools`** — public-ecosystem-encouraged tool policy. Retired because the
  neutral policy of `base_standard` already permits public pretrained models,
  making the pubtools-vs-neutral contrast weak; the legacy `tools` variant
  (curated local snapshots, mandated chain) is the strong tools-positive
  endpoint of the axis. Rebuild recipe: copy `../prompt_base_standard.md`,
  swap the `### Tool policy` section with the one in `prompt_base_pubtools.md`.
- **`staged`** — core-window-first staging (Stage A mandatory, Stage B archive
  extension). Retired because its guarantee — complete and checkpoint the core
  window before extending into the archive — is now folded into
  `../prompt_base_full.md`'s `### Processing scope` section.
