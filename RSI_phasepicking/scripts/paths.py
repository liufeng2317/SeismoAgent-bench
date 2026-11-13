"""All paths of the task, so scripts never hard-code shared storage."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
LOGS = ROOT / "logs"

CATALOGS_RAW = DATA / "catalogs" / "raw"
SCEDC_EVENTS = CATALOGS_RAW / "scedc_events"
NCEDC_EVENTS = CATALOGS_RAW / "ncedc_events"
STATIONS_RAW = DATA / "stations" / "raw"

RIDGECREST_WAVEFORMS = DATA / "waveforms" / "raw" / "ridgecrest_2019"
# SeisBench cache root: models/ links to the TRACE-2.0 pretrained-weight library;
# set seisbench.cache_root to this and load with update=False (offline).
SEISBENCH_ROOT = DATA / "models" / "seisbench"

MODELS = DATA / "models"
HK_MODEL = MODELS / "hk_scsn_1d.txt"  # SCSN Hadley-Kanamori model, Hutton et al. 2010 Table 5

# Upstream tools (PyOcto, HypoInverse) of the SeismoAgentBench repository.
SEISMOTOOLS = ROOT.parent / "seismotools"

# One folder per design part, used alike by scripts/, results/ and logs/.
PART_A = "a_data_labels"
RES_A = RESULTS / PART_A
PART_B = "b_baseline"
RES_B = RESULTS / PART_B
