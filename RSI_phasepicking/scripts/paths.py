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

# One folder per design part, used alike by scripts/, results/ and logs/.
PART_A = "a_data_labels"
RES_A = RESULTS / PART_A
