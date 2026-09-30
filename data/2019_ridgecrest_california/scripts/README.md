# Ridgecrest case scripts

Only case-specific workflows live here. Reusable source parsers remain in `SeismoAgentBench/utils/source_prepare/`.

| Directory | Responsibility | Entry points |
| --- | --- | --- |
| `catalogs/` | Reference catalog parsing and comparison audit | `audit_references.py` |
| `figures/` | Catalog, station and legacy waveform figures | `plot_catalog_comparison.py`, `plot_station_distribution.py`, `inspect_existing_waveforms.py` |
| `observations/` | Station metadata, waveform inventory, missing-data assessment and acquisition | `prepare_station_metadata.py`, `inventory_waveforms.py`, `audit_waveform_download_needs.py`, `download_observations.py`, `run_download.sh`, `run_download_missing_stations.sh` |

Scripts resolve the case from their own location. Data remain in the external archive reached through `../data/waveforms`; code, figures and metadata are not downloaded into this scripts tree. Old flat script paths have been replaced, including imports, documentation and test entry paths.

## Download workflow

Requires Python 3.9+, ObsPy, requests and PyYAML. Existing metadata preparation also requires pandas; plotting requires matplotlib/numpy. The locally verified environment is `inversionagent` (Python 3.10, ObsPy 1.5); run `conda activate inversionagent`, or set `PYTHON_BIN=/path/to/python`. No hard-coded conda environment, user identity or date appears in the Bash runner.

The Shell entry defaults to downloading over a direct connection; neither `--action download` nor `--direct` is required. The Python entry still defaults to plan mode. From the repository root, inspect a plan without network requests:

```bash
bash data/2019_ridgecrest_california/scripts/observations/run_download.sh --action plan --scope existing
```

Execute the same selection:

```bash
bash data/2019_ridgecrest_california/scripts/observations/run_download.sh \
  --action download --scope existing --max-requests 1
```

Omit `--max-requests 1` to execute the complete plan. The Shell entry already uses `--direct`; use `--use-proxy` to restore environment proxy settings. Providers are tried sequentially (`SCEDC,EARTHSCOPE`); `--providers EARTHSCOPE` restricts the choice. There is one active HTTP request per process, and a directory lock prevents concurrent downloader runs on the same archive. SCEDC permits at most three concurrent sessions across all jobs.

Dates come from `analysis/processing.yaml`'s candidate window. Do not change the scope by editing shell dates. The window and station policy remain provisional; running this tool does not freeze a benchmark.

### Selection

- `--scope existing` targets stations represented in the current candidate inventory within the requested channel families (default). An HN-only station is not treated as missing HH data.
- `--scope liu` uses the 41 metadata-present Liu candidates; `--scope shelly` uses the auxiliary subset; `--scope ross` uses rule-based candidates, not a confirmed paper list.
- `--stations CI.EDW2,CI.FUR` overrides the scope with exact stations.
- `--channels EH,HH` is the default family selection. HN is opt-in and remains acceleration data; no conversion or synthetic components are generated.
- `--locations=--` selects the blank location code. If omitted, all matching metadata locations are considered independently. Do not combine or mislabel 100 Hz and 200 Hz HN variants.
- Stations without a matching active channel appear in `unmatched_station_ids`; they are not silently treated as complete.

For example, plan the five missing HH stations, or the APL acceleration channels separately:

```bash
bash data/2019_ridgecrest_california/scripts/observations/run_download.sh \
  --action plan --stations CI.EDW2,CI.FUR,CI.HYS,CI.LDR,CI.SPG2 --channels HH --locations=--
bash data/2019_ridgecrest_california/scripts/observations/run_download.sh \
  --action plan --stations CI.APL --channels HN --locations=--
```

### Station metadata

`prepare_station_metadata.py` retains the existing regional discovery and paper-selection workflow. The new downloader can explicitly refresh response snapshots for selected, already known channel epochs:

```bash
bash data/2019_ridgecrest_california/scripts/observations/run_download.sh \
  --action plan --kind stations --stations CI.APL --channels HN --locations=--
```

Remove `--action plan` (or set `--action download`) to retrieve StationXML. This is an explicit response refresh, not a waveform request. It saves validated snapshots under external `stations/downloads/`; subsequent download plans read these alongside the existing channel index. Unknown stations must first be discovered with the regional metadata preparation workflow; the downloader does not invent channel configurations. Existing metadata/index snapshots are preserved, not silently replaced.

### Integrity, resuming and records

Waveform plans are calculated from actual local MiniSEED segment headers by exact NSLC and rate, including cross-file gaps, then clipped to channel epochs and split at UTC midnight. The default minimum gap is 1 second; use `--min-gap-seconds 0` to include sample-sized gaps. Sub-sample timing offsets at file boundaries do not require a download. A file on HHZ never makes HHN complete.

Plans represent missing local observations, not confirmed remote availability. Download mode directly requests those intervals; `204/404` is recorded as `no_data`. Network/server failures have bounded retries and provider fallback. Returned data must decode and match the requested channel, rate and bounds. Native gaps remain gaps. All waveform files use the original daily naming format: `data/<NET.STA>/<NSLC>__YYYYMMDDT000000Z__YYYYMMDDT000000Z.mseed`, where the second date is the following UTC day. No microsecond or hash suffix is added. Supplemental samples are inserted into that same daily file: existing samples remain unchanged, identical incoming overlaps are skipped, and missing intervals remain separate segments without zero-filling or interpolation. Conflicting overlapping values, rates or sample grids stop the write. The combined file is written to a temporary file, decoded and checked, then atomically replaces the previous daily file. MiniSEED bytes may change while sample values and times are retained; previous/updated file hashes and the response hash are recorded in `download_runs`. New samples at the following midnight are excluded from the current day. StationXML evidence snapshots retain their separate metadata naming convention. Re-running recalculates residual gaps, including incomplete earlier responses. A partial response from one provider is saved; rerun to request its remaining holes, potentially from the fallback provider.

The existing `waveform_inventory.json` stores `download_plan` and `download_runs`; no separate plan/result JSON files are generated. Plans are replaced on each run; execution history is retained. Completed and interrupted downloads remain discoverable from their files. Unavailable, failed or partial responses cause exit code 2; a request limit means only that prefix was attempted, not that all data are complete. Metadata-only refresh requests are repeated intentionally when explicitly run.

After downloading, refresh the header inventory and assessment **sequentially**, not concurrently with acquisition:

```bash
python -B data/2019_ridgecrest_california/scripts/observations/inventory_waveforms.py
python -B data/2019_ridgecrest_california/scripts/observations/audit_waveform_download_needs.py
```

The inventory refresh preserves download history and drops obsolete plans/assessments. The assessment uses the original shared metadata index; newly downloaded response snapshots may need incorporation through the metadata preparation workflow before that separate assessment reflects them. All code in `observations/` preserves raw waveform samples.

## Legacy implementation reviewed

The implementation was informed by TRACE's `Science2019_Hierarchical_interlocked_orthogonal_faulting_in_the_2019_ridgecrest/v2/02_waveform_download_station.py` and station-inventory notebook. It retains station/day requests and bounded retries, but replaces the station-wide “any file exists” skip with channel-specific coverage. The legacy shell's 2026 dates, environment activation and broad channel-priority fallback were not carried over.

Service references: [SCEDC dataselect](https://service.scedc.caltech.edu/fdsnws/dataselect/1/) and [EarthScope station](https://service.earthscope.org/fdsnws/station/1/). The latter confirms that channel metadata is distinct from waveform availability.

### Progress and troubleshooting

The Shell runner prints the log path and saves full stdout/stderr to `scripts/observations/logs/download_<UTC timestamp>_<unique suffix>.log`, while showing it in the terminal. The Python exit status is preserved. Earlier execution records were exported to `scripts/observations/logs/download_history_summary.log`; this is a summary, not a recovered terminal transcript. Direct Python invocation does not use the Shell logging wrapper.

Download mode prints the request index, channel, provider, attempt, HTTP status, transferred MB and validation outcome. While bytes are arriving, transfer progress is printed at roughly five-second intervals; connection waits are bounded by the displayed timeout. Failures retain the exception type, message, code location and stage in `download_runs`. URL credentials are redacted. The active request is saved before the network call, so an interrupted run can be distinguished from one that never started. Each run records its Python version.

Python 3.9 is supported: hashing uses a streaming implementation rather than `hashlib.file_digest`. The documented `--locations=--` option is normalized before parsing to avoid older argparse behavior. If the environment proxy fails, use `--direct`; this changes transport only and does not change the requested data.

## Add the six missing Liu-window stations

```bash
conda activate inversionagent
bash data/2019_ridgecrest_california/scripts/observations/run_download_missing_stations.sh
```

This runs two explicit batches: CI.EDW2/CI.FUR/CI.HYS/CI.LDR/CI.SPG2 with HH channels, followed by CI.APL with HN channels. The APL batch tries `SCEDC_CLOUD,SCEDC,EARTHSCOPE` to avoid slow HN streaming from FDSN. Both use blank location codes and the case candidate window; current metadata specifies 100 Hz. HN remains acceleration data, identified by its native channel code. The expected initial requests are 45 HH channel-days and 9 HN channel-days. Existing coverage is checked on each run. Ross-only rule candidates are not added.

Each batch writes its own console log under `scripts/observations/logs/`. An unsuccessful batch does not prevent the other from being attempted; the wrapper retains a nonzero exit status if either fails. Additional flags are forwarded to both batches: `--action plan` previews both without network access; `--max-requests` limits each batch separately. After execution, refresh the waveform inventory and assessment using the commands above.

### SCEDC cloud adapter

`--providers SCEDC_CLOUD,SCEDC,EARTHSCOPE` can use the [SCEDC official public cloud archive](https://scedc.caltech.edu/data/cloud.html). The current adapter supports full UTC-day waveform requests for CI channels with blank location codes. Other requests skip this adapter and try the subsequent providers. Objects are validated by the same waveform checks and saved with the same local daily filenames; the remote object naming never appears in the local payload layout. `download_runs` records the provider and source URL. Missing cloud objects fall back to FDSN. This adapter is not a StationXML downloader or an arbitrary sub-day slicer.

## Candidate waveform quality review

```bash
conda activate inversionagent
OPENBLAS_NUM_THREADS=1 python -B data/2019_ridgecrest_california/scripts/figures/analyze_waveform_quality.py
```

This case-specific, read-only workflow decodes every candidate-window MiniSEED file and generates coverage, sample-quality and exploratory preprocessing figures under `analysis/figures/waveform_quality/`. Its focused README describes definitions, parameters and limitations; CSV tables hold the derived statistics without duplicating the external inventory JSON. It uses existing local data and does not download, alter raw samples or save a processed waveform archive. Run after downloads and inventory refresh have finished; file size and modification time are checked for concurrent changes. Console progress is printed every 20 files.

## Instrument response audit and removal trial

```bash
OPENBLAS_NUM_THREADS=1 python -B data/2019_ridgecrest_california/scripts/figures/analyze_instrument_response.py
```

Audits the already downloaded StationXML against all observed candidate channels, then applies ObsPy response removal to three representative vertical-channel windows. Exact epoch/rate matching and numerical response evaluation must pass. Results, figures, an audit CSV and one small derived NPZ bundle go to `analysis/figures/instrument_response/`; raw files remain untouched. The report records physical units, frequency taper, ObsPy version and saturation limitations. Missing responses should be refreshed with the existing `observations/run_download.sh --kind stations` entry and exact station/channel selection; there is no second downloader implementation.

## Station metadata layout

`data/waveforms/stations/station_inventory.json` (schema 2) is the single station JSON: `channel_epochs`, `stations`, `catalogs`, `requests`, `metadata_conflicts` and `ross_channel_candidates`. Catalog choices remain separate keys; Ross references shared channel rows instead of copying them. Regional and catalog-subset StationXML files remain available for ObsPy. The preparation, download-planning, gap-assessment and station-plot scripts all use this consolidated index. See `data/waveforms/stations/README.md` for field definitions.

## Mainshock record section

```bash
OPENBLAS_NUM_THREADS=1 python -B data/2019_ridgecrest_california/scripts/figures/plot_mainshock_record_section.py
```

Plots both Mw 6.4 and Mw 7.1 events ±10 minutes by default (`--event mw6_4` or `--event mw7_1` selects one) for each observed station's native vertical channel, ordered by epicentral distance. Raw-count and response-corrected-velocity figures are saved under `analysis/figures/waveform_examples/`, with one CSV and a focused figure description. Traces are independently normalized for readability; vertical spacing represents station rank, with distances labeled explicitly. Original waveforms are unchanged.

Record-section artifacts use `mw6_4_record_section_*` and `mw7_1_record_section_*`. The short two-event example is `mw6_4_mw7_1_raw_examples`, and the historical archive comparison is `legacy_waveform_directory_comparison`.

## Minimal raw-waveform shape screen

`python -B data/2019_ridgecrest_california/scripts/figures/screen_waveform_shapes.py` scans candidate raw counts for near-flat elevated platforms and isolated increments. It writes only a per-channel ranking CSV, seven-window diagnostic figure (PNG/PDF), and a short methods note under `analysis/figures/waveform_quality/`. This internal source check does not label ground truth, remove responses, repair data or prescribe agent preprocessing.
