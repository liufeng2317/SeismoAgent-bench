# Data directory migration

- `563f1bc`: moved the tracked source documentation, metadata and scripts from `benchmark_source/` to `data/`. Bulk catalogs, waveforms, generated figures/statistics and large extracted tables remain local and are ignored. All 507 formerly tracked source files were confirmed present at their new disk paths before committing.
- The accompanying path-update commit changes repository references to `data/`, including source scripts, expert configuration and documentation.
- Validation: 89 regression tests passed; 25 modified Python files passed syntax checks; 24 modified JSON files parsed successfully; no old directory references remain in tracked files other than this historical migration record.
- Next: use `data/` as the source tree for subsequent work; no framework behavior or scientific method was changed.
