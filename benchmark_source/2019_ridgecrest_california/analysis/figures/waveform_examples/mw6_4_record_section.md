# Mw 6.4 record sections

[Response-corrected velocity](mw6_4_record_section_velocity.png) ([PDF](mw6_4_record_section_velocity.pdf)) · [Raw counts](mw6_4_record_section_raw.png) ([PDF](mw6_4_record_section_raw.pdf)).

Event `ci38443183`: 2019-07-04T17:33:49.000000Z, latitude 35.7053333, longitude -117.5038333; source: `analysis/reference_audit.json`, `anchors/mw6_4`. Window: [origin −600 s, origin +600 s). The dashed line is origin time, not a phase arrival.

41 observed stations, each represented by one native vertical channel (HHZ preferred, then EHZ, then HNZ). CI.APL uses HNZ. Stations are ordered by WGS84 epicentral surface distance, nearest at the top. Rows are equally spaced ranks, not a linear distance axis; right-hand values within the channel labels give distances in km. Channel metadata, samples, source paths, per-trace normalization factors and coverage are in [the CSV table](mw6_4_record_section.csv).

Each channel is independently normalized by its maximum absolute amplitude over the displayed 20 minutes, with the same factor for all its segments. Thus waveform heights do not represent relative ground-motion amplitudes between stations; weaker pre-event signals may be visually small at mainshock scale. Positive excursions point upward. Native samples are plotted without temporal decimation; rasterized trace artists keep PDFs compact.

The raw panel only subtracts each channel's displayed-window mean, retaining native counts before normalization. The velocity panel reads 120 s of additional padding on each side, merges only adjacent compatible segments, linearly detrends each contiguous segment and uses ObsPy `remove_response(output='VEL', pre_filt=(0.5,1,15,20), water_level=None, zero_mean=True, taper=True, taper_fraction=0.05)`. The displayed interval is cropped afterwards. No further filter, resampling, rotation, gap interpolation or full-day processed archive is generated. StationXML epoch/rate and vertical orientation must match; corrected samples must be finite. This is an offline diagnostic and the frequency band is not a frozen preprocessing choice.

Gaps remain blank rather than being filled. Summed missing channel-seconds in the displayed interval: 0.296700; summed overlap channel-seconds: 0.000000. The known WRC2 05:15 UTC gap lies outside this plot. For the Mw 7.1 event only, a dagger (†) marks CI.CCC/CI.WRC2, whose HHZ signals were previously flagged as suspected saturation. That event-specific flag is not transferred to Mw 6.4. Unmarked traces have not been individually cleared of saturation. Response removal does not repair distorted input. These plots are for waveform timing and morphology, not validated peak-ground-motion measurements.

Reproduce from the repository root with `python -B benchmark_source/2019_ridgecrest_california/scripts/figures/plot_mainshock_record_section.py --event mw6_4` in the inversionagent environment. Raw waveform files and StationXML are read-only.
