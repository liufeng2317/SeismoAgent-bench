# MatchLocatepy

Project-local `matchlocate_runner` package: everything around the native
MatchLocate2 program that a workflow needs — waveform preparation, travel
times and slownesses, the prepared-dataset contract, native job
orchestration and the cross-template merge.

```bash
export PYTHONPATH=/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/match_and_locate/runtime/python/MatchLocatepy:$PYTHONPATH
```

| Module | Purpose | Dependencies |
| --- | --- | --- |
| `prepare` | Filter/resample a channel-day onto the day's sample grid, write continuous SAC, cut templates from the processed data, window SNR | ObsPy |
| `traveltime` | Layered 1-D first arrivals (direct + head waves) with analytic `dT/dDelta`, `dT/dz`; linearisation error of the native moveout | — |
| `dataset` | `templates.csv` / `channels.csv` tables, layout, SAC header validation | — |
| `native` | `INPUT.in`, grid arithmetic and command line, `EventCase.out` / SelectFinal parsing, Python SelectFinal merge | — |
| `runner` | `run_dataset`: (segment, template) jobs, resume, merge, output tables | — |
| `sacheader` | Dependency-free SAC header reader | — |
| `build` | `build_dataset`: MiniSEED + tables + model -> prepared dataset (backs `interface/prepare.py`) | ObsPy |
| `select` | `select_templates`: greedy spatial cover for choosing templates | numpy |

The detailed contract and recommended sequence are in
[docs/MATCHLOCATEPY_CARD.md](docs/MATCHLOCATEPY_CARD.md). The standard
command-line entry point that wraps `run_dataset` is
[`../../../interface/run.py`](../../../interface/run.py). Examples:
[`../../../examples/`](../../../examples).
