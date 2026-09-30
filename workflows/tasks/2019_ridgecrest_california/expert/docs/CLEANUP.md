# Expert output cleanup

Completed after the expert handoff. This is storage/navigation maintenance, not a new scientific stage or experiment. The current candidate, baseline, flags and closing decision remain unchanged.

## Completed actions

| Action | Result |
| --- | ---: |
| Remove byte-identical NonLinLoc `last.*` copies | 112,418 files deleted |
| Replace byte-identical `time.P/S.mod.buf` copies with local relative links to retained `model.P/S.mod.buf` | 33 copies replaced |
| Total redundant file content removed | 5,595,022,800 bytes (5.21 GiB) |
| Original allocated file blocks removed, excluding retained hard links | 8,508,833,792 bytes (7.92 GiB; new short symlinks/manifest add a small overhead) |

Candidates were inventoried across physical output groups without following directory aliases. Existing symlink targets and structured run-record references were checked. Every deleted/replaced file was compared byte-for-byte with its retained counterpart, then both hashes were checked again immediately before mutation. All retained counterparts were regular files. Post-cleanup checks verified retained files, deletion of the intended copies and the new grid links.

Only matched duplicate `last.hyp`, `last.hdr`, `last.scat`, `last.in`, `last.stat`, `last.stat_totcorr` and `last.stations` files were removed. Named event solutions, posterior samples, controls and station/statistics outputs remain at their canonical paths. Nothing was deleted merely because a method failed an acceptance gate. No unique scientific information, raw observations, catalog records or model values were discarded.

The single compressed audit [duplicate_cleanup.csv.gz](../export/_provenance/duplicate_cleanup.csv.gz) records each former path, retained path, action, byte counts and shared SHA256. Paths are relative to the expert root. It is approximately 3 MB, not one metadata file per deletion. These hashes document duplicate identity; they do not introduce a new waveform checksum requirement.

Post-cleanup delivery verification passed: 52 stage directories/aliases, all 729 pre-existing symlinks, 177 frozen source identities and four fitted-result hashes. Current documentation links also resolve.

## Navigation after cleanup

Use the [expert overview](../README.md) for the seven effective steps and current products, and [EXPERT_DELIVERY.md](EXPERT_DELIVERY.md) for replay instructions. Historical diagrams moved to EVOLUTION; the overview now includes the requested operational parameter table. The complete 52-stage index is collapsed by default in the export README.

Keep the existing stage IDs and six output groups: their names are dependency/provenance identities, not 52 active tasks. Scientific scripts and frozen input paths were not renamed. Legacy flat directory aliases remain for compatibility. Failed branches can still supply grids, observations or comparison evidence to later stages, so wholesale deletion would require changing the declared reproduction scope.

## Reproduction and restoration

Current artifact verification and cached stage-52 replay retain the same inputs and fitted results. Run `python 01_pipeline/check_export_layout.py --full` from the expert root for the delivery checks. No picker, locator or grid generator was run during cleanup.

Native NonLinLoc can regenerate its `last.*` convenience files on a new run; they are not required by the retained case scripts, which consume named solutions. If an external consumer needs one, copy the audit row's retained file back to its former path and verify the recorded digest.

**Before deliberately regenerating any of the 33 deduplicated model-grid outputs with Grid2Time, restore independent output files.** Do not let a generator write through an output symlink into the retained model input. For a `link_duplicate_grid` audit row, copy `retained_path` to a new temporary regular file, then atomically replace the symlink at `path` with that temporary file. Never copy directly into the symlink. This is only necessary for rebuilding those historical grids; the current frozen application reads them without regeneration.

The historical unique velocity/time grids remain the dominant storage use (roughly 150 GiB before this cleanup across velocity experiments). They were not labeled useless solely because their associated method was not adopted. Future deletion of unique reconstruction inputs would narrow reproducibility and is outside this completed duplicate cleanup.
