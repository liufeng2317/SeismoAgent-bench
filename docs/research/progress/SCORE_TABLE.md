# Score table

Generated 2026-11-04 15:23 UTC by `python -m SeismoAgentBench.scoring.catalog_metrics table` from the tracked score files (catalog metrics v2); do not edit by hand. How each number is computed: [`03_Scoring_Method.md`](../../framework/03_Scoring_Method.md); definitions: [`docs/framework/02_Catalog_Metrics.md`](../../framework/02_Catalog_Metrics.md).

Rows are grouped by case in tier order; the first row of each case is the human-in-loop final, the upper bound every run is compared with (it has no values *against the final*). ✗ marks a value that fails a trusted-catalog criterion (§7a); ✓ / ✗ / … in the verdict table are pass / fail / pending (blind audit not labelled). Each configuration has one run so far.

## 1. Trusted-catalog verdict

The verdict judges whether the events are real and whether their time, space and strength are accurate and stable against the final; completeness is reported in §3 and not judged.

| Case | Run | State | Verdict | Reality | Time | Space | Strength | Failed criteria |
|---|---|---|---|---|---|---|---|---|
| Prague 2011 | backend (claude × glm-5.3, 20261101T000000Z) | scored | not trusted | … | ✓ | ✗ | ✗ | depth_bias, magnitude_offset, magnitude_spread, magnitude_scale |
| Prague 2011 | backend_checker (claude × glm-5.3, 20261101T000024Z) | scored | not trusted | … | ✓ | ✓ | ✗ | magnitude_scale |
| Prague 2011 | backend_knowledge (claude × glm-5.3, 20261101T000047Z) | scored | not trusted | … | ✓ | ✓ | ✗ | magnitude_scale |
| Prague 2011 | min (claude × glm-5.3, 20261028T020935Z) | artifact_invalid | not trusted | — | — | — | — | completed |
| Prague 2011 | min — rescue, reference only | not a formal result | not trusted | ✗ | ✗ | ✗ | ✗ | inside_region, time_bias, after_large_events, depth_bias, horizontal_scatter, magnitude_offset, magnitude_spread, magnitude_scale |
| Prague 2011 | tools (claude × glm-5.3, 20261028T043719Z) | scored | not trusted | ✓ | ✓ | ✗ | ✗ | depth_bias, magnitude_offset |
| Magna 2020 | backend (claude × glm-5.3, 20261101T100247Z) | scored | not trusted | … | ✓ | ✗ | ✗ | horizontal_shift, depth_bias, magnitude_offset, magnitude_spread |
| Magna 2020 | backend_checker (claude × glm-5.3, 20261101T100311Z) | scored | not trusted | … | ✗ | ✗ | ✗ | time_bias, horizontal_shift, magnitude_offset, magnitude_spread |
| Magna 2020 | backend_knowledge (claude × glm-5.3, 20261101T100335Z) | scored | not trusted | … | ✗ | ✗ | ✗ | time_bias, horizontal_shift, horizontal_scatter, magnitude_offset |
| Magna 2020 | min (claude × glm-5.3, 20261028T135859Z) | artifact_invalid | not trusted | — | — | — | — | completed |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | scored | not trusted | ✓ | ✓ | ✗ | ✗ | horizontal_shift, depth_bias, magnitude_offset |
| Maple Creek 2017 | backend (claude × glm-5.3, 20261101T185337Z) | scored | not trusted | … | ✗ | ✗ | ✗ | after_large_events, horizontal_scatter, off_structure, depth_pileup, magnitude_spread, magnitude_scale |
| Maple Creek 2017 | backend_checker (claude × glm-5.3, 20261101T185359Z) | scored | not trusted | … | ✓ | ✗ | ✗ | horizontal_scatter, off_structure, magnitude_spread, magnitude_scale |
| Maple Creek 2017 | backend_knowledge (claude × glm-5.3, 20261101T185422Z) | scored | not trusted | … | ✗ | ✗ | ✗ | time_bias, depth_bias, horizontal_scatter, off_structure, magnitude_scale |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | scored | not trusted | ✗ | ✗ | ✗ | ✗ | inside_region, time_bias, time_spread, after_large_events, horizontal_shift, depth_bias, horizontal_scatter, off_structure, depth_pileup, magnitude_offset, magnitude_spread, magnitude_scale |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | scored | not trusted | … | ✗ | ✗ | ✗ | time_bias, depth_bias, horizontal_scatter, off_structure, magnitude_scale |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261101T050124Z) | scored | not trusted | … | ✓ | ✓ | ✗ | magnitude_offset |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261103T010040Z) | scored | not trusted | … | ✗ | ✗ | ✓ | time_bias, depth_bias, horizontal_scatter |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261101T050148Z) | scored | not trusted | … | ✗ | ✗ | ✗ | time_bias, horizontal_scatter, large_events_present |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261103T010102Z) | scored | not trusted | … | ✗ | ✗ | ✗ | time_bias, depth_bias, horizontal_scatter, large_events_present |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261101T050213Z) | scored | not trusted | … | ✗ | ✗ | ✓ | time_bias, horizontal_scatter |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261103T010127Z) | scored | not trusted | … | ✓ | ✗ | ✓ | depth_pileup |
| Kīlauea 2018 | min (claude × glm-5.3, 20261029T084653Z) | scored | not trusted | … | ✗ | ✗ | ✗ | time_bias, depth_bias, horizontal_scatter, depth_pileup, magnitude_offset |
| Kīlauea 2018 | tools (claude × glm-5.3, 20261029T084718Z) | scored | not trusted | … | ✗ | ✓ | ✓ | time_bias |
| Ridgecrest 2019 | backend (claude × glm-5.3, 20261101T235452Z) | scored | not trusted | … | ✗ | ✗ | ✗ | time_bias, depth_bias, off_structure, magnitude_offset, large_events_present |
| Ridgecrest 2019 | backend_checker (claude × glm-5.3, 20261101T235514Z) | scored | not trusted | … | ✓ | ✗ | ✗ | off_structure, magnitude_spread, large_events_present |
| Ridgecrest 2019 | backend_knowledge (claude × glm-5.3, 20261101T235536Z) | scored | not trusted | … | ✓ | ✗ | ✗ | depth_bias, off_structure, large_events_present |
| Ridgecrest 2019 | min (claude × glm-5.3, 20261029T203728Z) | completed | not trusted | … | ✓ | ✗ | ✗ | horizontal_shift, depth_bias, off_structure, magnitude_offset, magnitude_spread, large_events_present |
| Ridgecrest 2019 | tools (claude × glm-5.3, 20261029T203757Z) | completed | not trusted | … | ✓ | ✗ | ✗ | depth_bias, off_structure, depth_pileup, magnitude_offset, large_events_present |
| Kaikōura 2016 | backend (claude × glm-5.3, 20261102T153500Z) | scored | not trusted | … | ✗ | ✗ | ✗ | time_bias, horizontal_shift, depth_bias, magnitude_scale |
| Kaikōura 2016 | backend_checker (claude × glm-5.3, 20261102T103500Z) | scored | not trusted | … | ✗ | ✗ | ✓ | time_bias, time_spread, horizontal_shift, depth_bias |
| Kaikōura 2016 | backend_knowledge (claude × glm-5.3, 20261102T103527Z) | scored | not trusted | … | ✗ | ✗ | ✓ | time_bias, time_spread, horizontal_shift, depth_bias, off_structure |
| Kaikōura 2016 | min (claude × glm-5.3, 20261029T123602Z) | completed | not trusted | … | ✗ | ✗ | ✗ | time_bias, time_spread, after_large_events, horizontal_shift, horizontal_scatter, off_structure, depth_pileup, large_events_present |
| Kaikōura 2016 | tools (claude × glm-5.3, 20261029T183933Z) | completed | not trusted | … | ✗ | ✗ | ✗ | time_bias, time_spread, horizontal_shift, horizontal_scatter, depth_pileup, magnitude_offset, large_events_present |

## 2. References and ceilings

Roles: D detection, L absolute location, S structure, M magnitude. Matching gates: the case's primary gates (2 s / 5 km; Kaikōura 4 s / 15 km), a reference's own gates where its origin times are coarse, or time only. The ceiling is the best chance-corrected recall another reference reaches; `recall_norm` divides by the primary detection reference's ceiling.

| Case | Tier | Reference | Roles | Events in mask | Matching gates | Ceiling | Ceiling by |
|---|---|---|---|---|---|---|---|
| Prague 2011 | basic | cochran | DLMS | 2,078 | 2 s / 5 km | 0.51 | mcmahon |
| Prague 2011 | basic | mcmahon | DS | 2,343 | 2 s / 5 km | 0.45 | cochran |
| Prague 2011 | basic | isken | L | 6 | 60 s / 5 km (own) | — | — |
| Prague 2011 | basic | comcat | M | 11 | 2 s / 5 km | — | — |
| Magna 2020 | basic | pang | DLMS | 4,169 | 2 s / 5 km | 0.68 | baker |
| Magna 2020 | basic | baker | DS | 3,712 | 2 s / 5 km | 0.77 | pang |
| Magna 2020 | basic | uuss | DLM | 1,432 | 2 s / 5 km | 1.00 | pang |
| Maple Creek 2017 | intermediate | comcat | DLMS | 626 | 2 s / 5 km | 0.98 | shelly |
| Maple Creek 2017 | intermediate | shelly | D | 18,062 | |Δt| ≤ 1 s, time only | 0.03 | comcat |
| Kīlauea 2018 | intermediate | shelly | DLMS | 1,902 | 2 s / 5 km | 0.49 | wei |
| Kīlauea 2018 | intermediate | wei | DLMS | 3,627 | 2 s / 5 km | 0.25 | shelly |
| Kīlauea 2018 | intermediate | matoza | DMS | 1,020 | 2 s / 5 km | 0.76 | wei |
| Kīlauea 2018 | intermediate | comcat | DLM | 496 | 2 s / 5 km | 0.91 | matoza |
| Ridgecrest 2019 | hard | shelly | DLMS | 7,716 | 2 s / 5 km | 0.64 | liu |
| Ridgecrest 2019 | hard | liu | DLS | 6,242 | 2 s / 5 km | 0.79 | shelly |
| Ridgecrest 2019 | hard | ross_relocated | DLS | 6,463 | 2 s / 5 km | 0.72 | shelly |
| Ridgecrest 2019 | hard | awr_hypocenters | D | 5,737 | 2 s / 5 km | 0.84 | shelly |
| Ridgecrest 2019 | hard | official_earthquake | DLM | 6,564 | 2 s / 5 km | 0.70 | shelly |
| Kaikōura 2016 | hard | tan | DMS | 9,720 | 4 s / 15 km | 0.16 | chamberlain |
| Kaikōura 2016 | hard | lanza | LS | 122 | 4 s / 15 km | — | — |
| Kaikōura 2016 | hard | chamberlain | DMS | 2,260 | 4 s / 15 km | 0.69 | tan |
| Kaikōura 2016 | hard | geonet | DM | 1,507 | 4 s / 15 km | 0.94 | tan |

## 3. Completeness (reported, not judged)

`recall_norm` against the primary detection reference (normalised by its ceiling); `recall_tight` the same at 1 s / 3 km; `recall_final` the share of the final's events recovered; `event_ratio_final` events relative to the final; F1 by magnitude class against the magnitude authority.

| Case | Catalog | recall_norm | recall (net) | recall_tight | recall_final | event_ratio_final | F1 M2+ | F1 M3+ | F1 M4+ |
|---|---|---|---|---|---|---|---|---|---|
| Prague 2011 | human-in-loop final | 1.85 | 0.95 | 0.94 | — | — | 0.99 | 1.00 | — |
| Prague 2011 | backend (claude × glm-5.3, 20261101T000000Z) | 1.34 | 0.69 | 0.68 | 0.45 | 0.48 | 0.99 | 1.00 | — |
| Prague 2011 | backend_checker (claude × glm-5.3, 20261101T000024Z) | 1.35 | 0.69 | 0.68 | 0.45 | 0.48 | 0.98 | 1.00 | — |
| Prague 2011 | backend_knowledge (claude × glm-5.3, 20261101T000047Z) | 1.35 | 0.69 | 0.69 | 0.45 | 0.49 | 0.98 | 1.00 | — |
| Prague 2011 | min (claude × glm-5.3, 20261028T020935Z) | 0.00 | 0.00 | 0.00 | 0.00 | — | — | — | — |
| Prague 2011 | min — rescue, reference only | 0.03 | 0.02 | 0.00 | 0.01 | 0.12 | 0.05 | — | — |
| Prague 2011 | tools (claude × glm-5.3, 20261028T043719Z) | 1.38 | 0.71 | 0.70 | 0.46 | 0.50 | 0.97 | 1.00 | — |
| Magna 2020 | human-in-loop final | 1.14 | 0.78 | 0.78 | — | — | 0.96 | 0.99 | 1.00 |
| Magna 2020 | backend (claude × glm-5.3, 20261101T100247Z) | 0.87 | 0.59 | 0.55 | 0.51 | 0.57 | 0.99 | 0.99 | 1.00 |
| Magna 2020 | backend_checker (claude × glm-5.3, 20261101T100311Z) | 0.87 | 0.59 | 0.58 | 0.50 | 0.63 | 0.91 | 0.92 | 1.00 |
| Magna 2020 | backend_knowledge (claude × glm-5.3, 20261101T100335Z) | 0.92 | 0.63 | 0.56 | 0.53 | 0.66 | 0.93 | 0.99 | 1.00 |
| Magna 2020 | min (claude × glm-5.3, 20261028T135859Z) | 0.00 | 0.00 | 0.00 | 0.00 | — | — | — | — |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | 0.87 | 0.59 | 0.52 | 0.51 | 0.57 | 0.98 | 0.99 | 1.00 |
| Maple Creek 2017 | human-in-loop final | 0.99 | 0.98 | 0.95 | — | — | 1.00 | 1.00 | 1.00 |
| Maple Creek 2017 | backend (claude × glm-5.3, 20261101T185337Z) | 0.15 | 0.15 | 0.11 | 0.07 | 0.13 | 0.32 | 0.75 | — |
| Maple Creek 2017 | backend_checker (claude × glm-5.3, 20261101T185359Z) | 0.90 | 0.89 | 0.80 | 0.20 | 0.27 | 0.90 | 0.89 | — |
| Maple Creek 2017 | backend_knowledge (claude × glm-5.3, 20261101T185422Z) | 0.96 | 0.95 | 0.24 | 0.22 | 0.28 | 1.00 | 1.00 | — |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | 0.34 | 0.33 | 0.04 | 0.13 | 0.55 | 0.39 | 0.29 | — |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | 0.96 | 0.94 | 0.43 | 0.22 | 0.27 | 0.99 | 1.00 | 1.00 |
| Kīlauea 2018 | human-in-loop final | 1.22 | 0.59 | 0.57 | — | — | 0.78 | 0.81 | 0.80 |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261101T050124Z) | 0.88 | 0.43 | 0.42 | 0.38 | 0.43 | 0.85 | 0.84 | 0.97 |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261103T010040Z) | 0.88 | 0.43 | 0.40 | 0.37 | 0.45 | 0.81 | 0.83 | 0.94 |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261101T050148Z) | 0.82 | 0.40 | 0.29 | 0.29 | 0.34 | 0.81 | 0.77 | 0.64 |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261103T010102Z) | 0.06 | 0.03 | 0.00 | 0.01 | 0.42 | 0.04 | 0.00 | 0.00 |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261101T050213Z) | 0.88 | 0.43 | 0.40 | 0.38 | 0.44 | 0.86 | 0.84 | 0.93 |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261103T010127Z) | 0.88 | 0.43 | 0.41 | 0.36 | 0.40 | 0.87 | 0.88 | 1.00 |
| Kīlauea 2018 | min (claude × glm-5.3, 20261029T084653Z) | 0.90 | 0.44 | 0.25 | 0.42 | 0.60 | 0.77 | 0.77 | 0.90 |
| Kīlauea 2018 | tools (claude × glm-5.3, 20261029T084718Z) | 0.88 | 0.43 | 0.42 | 0.37 | 0.41 | 0.89 | 0.86 | 1.00 |
| Ridgecrest 2019 | human-in-loop final | 1.38 | 0.88 | 0.86 | — | — | 0.82 | 0.86 | 0.90 |
| Ridgecrest 2019 | backend (claude × glm-5.3, 20261101T235452Z) | 1.24 | 0.79 | 0.76 | 0.43 | 0.68 | 0.80 | 0.82 | 0.84 |
| Ridgecrest 2019 | backend_checker (claude × glm-5.3, 20261101T235514Z) | 1.20 | 0.76 | 0.75 | 0.42 | 0.65 | 0.76 | 0.76 | 0.81 |
| Ridgecrest 2019 | backend_knowledge (claude × glm-5.3, 20261101T235536Z) | 1.22 | 0.78 | 0.73 | 0.42 | 0.68 | 0.80 | 0.83 | 0.86 |
| Ridgecrest 2019 | min (claude × glm-5.3, 20261029T203728Z) | 1.01 | 0.64 | 0.59 | 0.30 | 0.43 | 0.76 | 0.76 | 0.87 |
| Ridgecrest 2019 | tools (claude × glm-5.3, 20261029T203757Z) | 1.15 | 0.73 | 0.65 | 0.39 | 0.68 | 0.76 | 0.79 | 0.82 |
| Kaikōura 2016 | human-in-loop final | 1.17 | 0.81 | 0.32 | — | — | 0.93 | 0.95 | 0.97 |
| Kaikōura 2016 | backend (claude × glm-5.3, 20261102T153500Z) | 0.99 | 0.69 | 0.17 | 0.45 | 0.68 | 0.87 | 0.90 | 0.86 |
| Kaikōura 2016 | backend_checker (claude × glm-5.3, 20261102T103500Z) | 1.00 | 0.70 | 0.22 | 0.45 | 0.68 | 0.82 | 0.84 | 0.85 |
| Kaikōura 2016 | backend_knowledge (claude × glm-5.3, 20261102T103527Z) | 0.97 | 0.68 | 0.20 | 0.43 | 0.67 | 0.81 | 0.74 | 0.86 |
| Kaikōura 2016 | min (claude × glm-5.3, 20261029T123602Z) | 0.13 | 0.09 | 0.00 | 0.04 | 0.11 | 0.26 | 0.15 | 0.11 |
| Kaikōura 2016 | tools (claude × glm-5.3, 20261029T183933Z) | 0.96 | 0.67 | 0.08 | 0.43 | 0.68 | 0.87 | 0.82 | 0.87 |

## 4. Event reality

Share of rows outside the evaluation region, chance-corrected support by any reference or the final, the final's share of the run's events, and the audited false-event rate (blank until the blind review is labelled).

| Case | Catalog | outside region | union_support | precision_final | audited false rate |
|---|---|---|---|---|---|
| Prague 2011 | human-in-loop final | 2.8 % | 0.45 | — | — |
| Prague 2011 | backend (claude × glm-5.3, 20261101T000000Z) | 8.8 % | 0.97 | 0.95 | — |
| Prague 2011 | backend_checker (claude × glm-5.3, 20261101T000024Z) | 8.5 % | 0.96 | 0.95 | — |
| Prague 2011 | backend_knowledge (claude × glm-5.3, 20261101T000047Z) | 8.1 % | 0.97 | 0.95 | — |
| Prague 2011 | min (claude × glm-5.3, 20261028T020935Z) | — | — | — | — |
| Prague 2011 | min — rescue, reference only | 50.3 % | 0.24 | 0.05 | — |
| Prague 2011 | tools (claude × glm-5.3, 20261028T043719Z) | 9.4 % | 0.96 | 0.94 | 0.1 % |
| Magna 2020 | human-in-loop final | 1.7 % | 0.67 | — | — |
| Magna 2020 | backend (claude × glm-5.3, 20261101T100247Z) | 3.3 % | 0.97 | 0.92 | — |
| Magna 2020 | backend_checker (claude × glm-5.3, 20261101T100311Z) | 11.8 % | 0.88 | 0.82 | — |
| Magna 2020 | backend_knowledge (claude × glm-5.3, 20261101T100335Z) | 7.3 % | 0.90 | 0.83 | — |
| Magna 2020 | min (claude × glm-5.3, 20261028T135859Z) | — | — | — | — |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | 2.7 % | 0.97 | 0.92 | 0.2 % |
| Maple Creek 2017 | human-in-loop final | 1.4 % | 0.81 | — | — |
| Maple Creek 2017 | backend (claude × glm-5.3, 20261101T185337Z) | 58.6 % | 0.84 | 0.57 | — |
| Maple Creek 2017 | backend_checker (claude × glm-5.3, 20261101T185359Z) | 12.8 % | 0.99 | 0.78 | — |
| Maple Creek 2017 | backend_knowledge (claude × glm-5.3, 20261101T185422Z) | 12.2 % | 0.93 | 0.91 | — |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | 79.6 % | 0.56 | 0.24 | — |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | 12.7 % | 0.93 | 0.91 | — |
| Kīlauea 2018 | human-in-loop final | 36.4 % | 0.47 | — | — |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261101T050124Z) | 17.3 % | 0.91 | 0.90 | — |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261103T010040Z) | 12.8 % | 0.85 | 0.83 | — |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261101T050148Z) | 34.3 % | 0.89 | 0.87 | — |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261103T010102Z) | 19.8 % | 0.08 | 0.02 | — |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261101T050213Z) | 15.3 % | 0.89 | 0.88 | — |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261103T010127Z) | 24.2 % | 0.95 | 0.94 | — |
| Kīlauea 2018 | min (claude × glm-5.3, 20261029T084653Z) | 45.3 % | 0.73 | 0.70 | — |
| Kīlauea 2018 | tools (claude × glm-5.3, 20261029T084718Z) | 21.2 % | 0.95 | 0.93 | — |
| Ridgecrest 2019 | human-in-loop final | 0.1 % | 0.49 | — | — |
| Ridgecrest 2019 | backend (claude × glm-5.3, 20261101T235452Z) | 13.4 % | 0.72 | 0.65 | — |
| Ridgecrest 2019 | backend_checker (claude × glm-5.3, 20261101T235514Z) | 16.4 % | 0.73 | 0.67 | — |
| Ridgecrest 2019 | backend_knowledge (claude × glm-5.3, 20261101T235536Z) | 11.8 % | 0.69 | 0.63 | — |
| Ridgecrest 2019 | min (claude × glm-5.3, 20261029T203728Z) | 20.9 % | 0.81 | 0.74 | — |
| Ridgecrest 2019 | tools (claude × glm-5.3, 20261029T203757Z) | 12.0 % | 0.64 | 0.58 | — |
| Kaikōura 2016 | human-in-loop final | 3.7 % | 0.42 | — | — |
| Kaikōura 2016 | backend (claude × glm-5.3, 20261102T153500Z) | 3.5 % | 0.75 | 0.66 | — |
| Kaikōura 2016 | backend_checker (claude × glm-5.3, 20261102T103500Z) | 3.5 % | 0.75 | 0.67 | — |
| Kaikōura 2016 | backend_knowledge (claude × glm-5.3, 20261102T103527Z) | 4.6 % | 0.73 | 0.65 | — |
| Kaikōura 2016 | min (claude × glm-5.3, 20261029T123602Z) | 7.6 % | 0.43 | 0.39 | — |
| Kaikōura 2016 | tools (claude × glm-5.3, 20261029T183933Z) | 2.5 % | 0.73 | 0.64 | — |

## 5. Time

Against the final: median signed origin-time difference and its MAD (seconds). Against the primary location reference: median |Δt|. Detection after large events: recall within 1 h after M ≥ 4 relative to all other times.

| Case | Catalog | bias vs final (s) | MAD vs final (s) | \|Δt\| vs ref (s) | after large / other |
|---|---|---|---|---|---|
| Prague 2011 | human-in-loop final | — | — | 0.07 | 0.96 |
| Prague 2011 | backend (claude × glm-5.3, 20261101T000000Z) | -0.11 | 0.04 | 0.07 | 0.78 |
| Prague 2011 | backend_checker (claude × glm-5.3, 20261101T000024Z) | 0.29 | 0.09 | 0.36 | 0.83 |
| Prague 2011 | backend_knowledge (claude × glm-5.3, 20261101T000047Z) | 0.16 | 0.03 | 0.22 | 0.84 |
| Prague 2011 | min (claude × glm-5.3, 20261028T020935Z) | — | — | — | — |
| Prague 2011 | min — rescue, reference only | -0.94 ✗ | 0.23 | 1.56 | 0.00 ✗ |
| Prague 2011 | tools (claude × glm-5.3, 20261028T043719Z) | 0.06 | 0.05 | 0.13 | 0.82 |
| Magna 2020 | human-in-loop final | — | — | 0.13 | 1.15 |
| Magna 2020 | backend (claude × glm-5.3, 20261101T100247Z) | 0.14 | 0.10 | 0.23 | 1.21 |
| Magna 2020 | backend_checker (claude × glm-5.3, 20261101T100311Z) | 0.34 ✗ | 0.17 | 0.43 | 0.96 |
| Magna 2020 | backend_knowledge (claude × glm-5.3, 20261101T100335Z) | 0.38 ✗ | 0.17 | 0.48 | 0.95 |
| Magna 2020 | min (claude × glm-5.3, 20261028T135859Z) | — | — | — | — |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | -0.19 | 0.08 | 0.11 | 1.19 |
| Maple Creek 2017 | human-in-loop final | — | — | 0.09 | 0.98 |
| Maple Creek 2017 | backend (claude × glm-5.3, 20261101T185337Z) | -0.28 | 0.20 | 0.39 | 0.68 ✗ |
| Maple Creek 2017 | backend_checker (claude × glm-5.3, 20261101T185359Z) | -0.05 | 0.16 | 0.23 | 1.01 |
| Maple Creek 2017 | backend_knowledge (claude × glm-5.3, 20261101T185422Z) | 1.18 ✗ | 0.09 | 1.10 | 0.99 |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | 0.39 ✗ | 0.64 ✗ | 0.83 | 0.51 ✗ |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | 1.15 ✗ | 0.16 | 1.01 | 0.99 |
| Kīlauea 2018 | human-in-loop final | — | — | 0.20 | 1.59 |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261101T050124Z) | -0.19 | 0.17 | 0.19 | 1.50 |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261103T010040Z) | -0.59 ✗ | 0.09 | 0.55 | 1.55 |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261101T050148Z) | 0.50 ✗ | 0.20 | 0.60 | 1.38 |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261103T010102Z) | -1.72 ✗ | 0.25 | 1.83 | 1.36 |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261101T050213Z) | -0.40 ✗ | 0.10 | 0.39 | 1.50 |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261103T010127Z) | 0.04 | 0.07 | 0.20 | 1.53 |
| Kīlauea 2018 | min (claude × glm-5.3, 20261029T084653Z) | -0.96 ✗ | 0.26 | 0.90 | 1.48 |
| Kīlauea 2018 | tools (claude × glm-5.3, 20261029T084718Z) | -0.36 ✗ | 0.07 | 0.30 | 1.49 |
| Ridgecrest 2019 | human-in-loop final | — | — | 0.26 | 0.99 |
| Ridgecrest 2019 | backend (claude × glm-5.3, 20261101T235452Z) | -0.36 ✗ | 0.04 | 0.14 | 0.96 |
| Ridgecrest 2019 | backend_checker (claude × glm-5.3, 20261101T235514Z) | -0.25 | 0.09 | 0.10 | 0.97 |
| Ridgecrest 2019 | backend_knowledge (claude × glm-5.3, 20261101T235536Z) | -0.28 | 0.06 | 0.12 | 0.96 |
| Ridgecrest 2019 | min (claude × glm-5.3, 20261029T203728Z) | 0.25 | 0.08 | 0.52 | 0.93 |
| Ridgecrest 2019 | tools (claude × glm-5.3, 20261029T203757Z) | 0.05 | 0.12 | 0.33 | 0.97 |
| Kaikōura 2016 | human-in-loop final | — | — | 0.49 | 1.01 |
| Kaikōura 2016 | backend (claude × glm-5.3, 20261102T153500Z) | 0.79 ✗ | 0.28 | 0.44 | 1.03 |
| Kaikōura 2016 | backend_checker (claude × glm-5.3, 20261102T103500Z) | 0.58 ✗ | 0.34 ✗ | 0.33 | 1.00 |
| Kaikōura 2016 | backend_knowledge (claude × glm-5.3, 20261102T103527Z) | 0.48 ✗ | 0.31 ✗ | 0.23 | 1.01 |
| Kaikōura 2016 | min (claude × glm-5.3, 20261029T123602Z) | 2.57 ✗ | 0.40 ✗ | 2.15 | 0.77 ✗ |
| Kaikōura 2016 | tools (claude × glm-5.3, 20261029T183933Z) | 0.64 ✗ | 0.44 ✗ | 0.43 | 1.02 |

## 6. Space

Against the final: common horizontal shift, scatter about it, median depth difference (km, positive = deeper). Against the primary location reference: shift, scatter and depth difference. Structure: share of epicentres > r_off from every structure reference. Depth pile-up: largest share at one depth value.

| Case | Catalog | shift vs final | scatter vs final | dz vs final | shift vs ref | scatter vs ref | dz vs ref | off structure | depth pile-up |
|---|---|---|---|---|---|---|---|---|---|
| Prague 2011 | human-in-loop final | — | — | — | 0.18 | 0.31 | 0.12 | 0.0 % | 9.1 % |
| Prague 2011 | backend (claude × glm-5.3, 20261101T000000Z) | 0.04 | 0.27 | 1.11 ✗ | 0.19 | 0.29 | 1.27 | 1.6 % | 2.4 % |
| Prague 2011 | backend_checker (claude × glm-5.3, 20261101T000024Z) | 0.04 | 0.22 | -0.02 | 0.14 | 0.19 | 0.11 | 2.4 % | 0.8 % |
| Prague 2011 | backend_knowledge (claude × glm-5.3, 20261101T000047Z) | 0.04 | 0.24 | 0.26 | 0.19 | 0.25 | 0.43 | 1.2 % | 1.1 % |
| Prague 2011 | min (claude × glm-5.3, 20261028T020935Z) | — | — | — | — | — | — | — | — |
| Prague 2011 | min — rescue, reference only | 0.82 | 1.47 ✗ | -3.38 ✗ | 0.86 | 1.01 | -1.59 | 4.9 % | 9.0 % |
| Prague 2011 | tools (claude × glm-5.3, 20261028T043719Z) | 0.03 | 0.26 | 1.10 ✗ | 0.21 | 0.25 | 1.24 | 2.0 % | 1.8 % |
| Magna 2020 | human-in-loop final | — | — | — | 0.95 | 0.47 | 0.09 | 0.3 % | 1.1 % |
| Magna 2020 | backend (claude × glm-5.3, 20261101T100247Z) | 2.11 ✗ | 0.54 | -1.96 ✗ | 2.14 | 0.35 | -1.81 | 0.3 % | 0.8 % |
| Magna 2020 | backend_checker (claude × glm-5.3, 20261101T100311Z) | 1.31 ✗ | 0.82 | 0.56 | 0.87 | 0.74 | 0.50 | 1.9 % | 1.4 % |
| Magna 2020 | backend_knowledge (claude × glm-5.3, 20261101T100335Z) | 1.36 ✗ | 1.02 ✗ | -0.51 | 1.26 | 0.87 | -0.51 | 0.7 % | 1.4 % |
| Magna 2020 | min (claude × glm-5.3, 20261028T135859Z) | — | — | — | — | — | — | — | — |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | 2.35 ✗ | 0.51 | -1.94 ✗ | 2.50 | 0.37 | -1.72 | 0.4 % | 2.0 % |
| Maple Creek 2017 | human-in-loop final | — | — | — | 0.59 | 0.65 | 1.46 | 0.3 % | 3.7 % |
| Maple Creek 2017 | backend (claude × glm-5.3, 20261101T185337Z) | 0.81 | 2.87 ✗ | 0.11 | 0.28 | 1.34 | 3.05 | 28.6 % ✗ | 10.3 % ✗ |
| Maple Creek 2017 | backend_checker (claude × glm-5.3, 20261101T185359Z) | 0.26 | 1.95 ✗ | 0.44 | 0.43 | 1.00 | 2.64 | 23.5 % ✗ | 2.4 % |
| Maple Creek 2017 | backend_knowledge (claude × glm-5.3, 20261101T185422Z) | 0.55 | 1.59 ✗ | -2.50 ✗ | 0.93 | 0.79 | -0.91 | 8.6 % ✗ | 2.3 % |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | 1.02 ✗ | 3.95 ✗ | -3.81 ✗ | 1.62 | 3.08 | -1.84 | 56.1 % ✗ | 27.0 % ✗ |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | 0.91 | 1.90 ✗ | -2.18 ✗ | 0.71 | 1.17 | -0.07 | 11.8 % ✗ | 3.8 % |
| Kīlauea 2018 | human-in-loop final | — | — | — | 0.56 | 0.61 | 0.53 | 0.2 % | 6.0 % |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261101T050124Z) | 0.22 | 0.70 | 0.62 | 0.45 | 0.54 | 1.36 | 0.2 % | 1.1 % |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261103T010040Z) | 0.16 | 1.38 ✗ | 1.11 ✗ | 0.13 | 0.70 | 1.78 | 0.1 % | 0.7 % |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261101T050148Z) | 0.57 | 1.58 ✗ | 0.48 | 0.68 | 0.88 | 0.79 | 0.8 % | 5.1 % |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261103T010102Z) | 0.62 | 1.54 ✗ | 1.62 ✗ | 0.43 | 0.48 | 3.70 | 0.2 % | 0.9 % |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261101T050213Z) | 0.12 | 1.09 ✗ | 0.31 | 0.27 | 0.85 | 1.06 | 0.3 % | 1.8 % |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261103T010127Z) | 0.01 | 0.43 | -0.07 | 0.42 | 0.54 | 0.68 | 0.2 % | 9.0 % ✗ |
| Kīlauea 2018 | min (claude × glm-5.3, 20261029T084653Z) | 0.13 | 1.31 ✗ | 1.29 ✗ | 0.23 | 1.01 | 2.04 | 0.8 % | 16.5 % ✗ |
| Kīlauea 2018 | tools (claude × glm-5.3, 20261029T084718Z) | 0.07 | 0.38 | 0.45 | 0.48 | 0.61 | 1.01 | 0.1 % | 3.7 % |
| Ridgecrest 2019 | human-in-loop final | — | — | — | 0.37 | 0.21 | -0.10 | 0.5 % | 0.5 % |
| Ridgecrest 2019 | backend (claude × glm-5.3, 20261101T235452Z) | 0.43 | 0.49 | 1.31 ✗ | 0.18 | 0.25 | 1.19 | 11.5 % ✗ | 3.0 % |
| Ridgecrest 2019 | backend_checker (claude × glm-5.3, 20261101T235514Z) | 0.36 | 0.41 | 0.82 | 0.14 | 0.28 | 0.64 | 10.5 % ✗ | 0.2 % |
| Ridgecrest 2019 | backend_knowledge (claude × glm-5.3, 20261101T235536Z) | 0.43 | 0.59 | 1.10 ✗ | 0.13 | 0.48 | 1.23 | 14.0 % ✗ | 2.8 % |
| Ridgecrest 2019 | min (claude × glm-5.3, 20261029T203728Z) | 1.01 ✗ | 0.60 | -1.37 ✗ | 0.63 | 0.50 | -1.27 | 9.6 % ✗ | 1.2 % |
| Ridgecrest 2019 | tools (claude × glm-5.3, 20261029T203757Z) | 0.59 | 0.83 | -2.31 ✗ | 0.20 | 0.74 | -2.35 | 17.1 % ✗ | 36.5 % ✗ |
| Kaikōura 2016 | human-in-loop final | — | — | — | 1.37 | 3.06 | -0.32 | 0.8 % | 0.8 % |
| Kaikōura 2016 | backend (claude × glm-5.3, 20261102T153500Z) | 1.97 ✗ | 2.17 | -1.35 ✗ | 0.49 | 1.97 | -1.28 | 4.4 % | 1.0 % |
| Kaikōura 2016 | backend_checker (claude × glm-5.3, 20261102T103500Z) | 3.35 ✗ | 2.60 | 3.34 ✗ | 2.05 | 3.35 | 4.89 | 4.3 % | 4.6 % |
| Kaikōura 2016 | backend_knowledge (claude × glm-5.3, 20261102T103527Z) | 3.45 ✗ | 2.99 | 1.91 ✗ | 2.79 | 3.35 | 2.12 | 5.3 % ✗ | 0.7 % |
| Kaikōura 2016 | min (claude × glm-5.3, 20261029T123602Z) | 2.59 ✗ | 4.45 ✗ | -0.33 | 1.47 | 5.76 | -1.66 | 7.1 % ✗ | 50.1 % ✗ |
| Kaikōura 2016 | tools (claude × glm-5.3, 20261029T183933Z) | 3.69 ✗ | 3.80 ✗ | 0.86 | 2.21 | 4.43 | 2.63 | 4.9 % | 12.5 % ✗ |

## 7. Strength

Against the magnitude authority (the operational catalog; Cochran for Prague): median and spread of the magnitude difference, its slope against magnitude (negative = compressed scale), b-value difference, recall of M ≥ 4 events.

| Case | Catalog | dmag median | dmag std | dmag slope | b difference | recall M4+ |
|---|---|---|---|---|---|---|
| Prague 2011 | human-in-loop final | -0.23 | 0.37 | -0.21 | 0.26 | — |
| Prague 2011 | backend (claude × glm-5.3, 20261101T000000Z) | -1.43 ✗ | 0.48 ✗ | -0.42 ✗ | 0.28 | — |
| Prague 2011 | backend_checker (claude × glm-5.3, 20261101T000024Z) | -0.07 | 0.37 | -0.34 ✗ | 0.33 | — |
| Prague 2011 | backend_knowledge (claude × glm-5.3, 20261101T000047Z) | -0.11 | 0.39 | -0.33 ✗ | 0.28 | — |
| Prague 2011 | min (claude × glm-5.3, 20261028T020935Z) | — | — | — | — | — |
| Prague 2011 | min — rescue, reference only | -1.03 ✗ | 0.77 ✗ | -0.83 ✗ | 0.49 | — |
| Prague 2011 | tools (claude × glm-5.3, 20261028T043719Z) | -2.77 ✗ | 0.37 | -0.28 | 0.26 | — |
| Magna 2020 | human-in-loop final | 0.08 | 0.21 | -0.18 | 0.30 | 1.00 |
| Magna 2020 | backend (claude × glm-5.3, 20261101T100247Z) | 0.67 ✗ | 0.35 ✗ | -0.20 | 0.20 | 1.00 |
| Magna 2020 | backend_checker (claude × glm-5.3, 20261101T100311Z) | 0.63 ✗ | 0.31 ✗ | -0.18 | 0.04 | 1.00 |
| Magna 2020 | backend_knowledge (claude × glm-5.3, 20261101T100335Z) | 0.52 ✗ | 0.19 | -0.12 | 0.07 | 1.00 |
| Magna 2020 | min (claude × glm-5.3, 20261028T135859Z) | — | — | — | — | — |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | 0.67 ✗ | 0.20 | -0.16 | 0.17 | 1.00 |
| Maple Creek 2017 | human-in-loop final | 0.15 | 0.29 | -0.31 | 0.43 | 1.00 |
| Maple Creek 2017 | backend (claude × glm-5.3, 20261101T185337Z) | 0.34 | 0.52 ✗ | -0.51 ✗ | 0.49 | 1.00 |
| Maple Creek 2017 | backend_checker (claude × glm-5.3, 20261101T185359Z) | 0.15 | 0.42 ✗ | -0.50 ✗ | 0.74 | 1.00 |
| Maple Creek 2017 | backend_knowledge (claude × glm-5.3, 20261101T185422Z) | 0.19 | 0.38 | -0.48 ✗ | 0.53 | 1.00 |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | 0.66 ✗ | 0.42 ✗ | -0.54 ✗ | 0.49 | 1.00 |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | 0.19 | 0.37 | -0.44 ✗ | 0.70 | 1.00 |
| Kīlauea 2018 | human-in-loop final | -0.27 | 0.50 | -0.12 | -0.42 | 1.00 |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261101T050124Z) | -0.99 ✗ | 0.35 | -0.12 | -0.16 | 1.00 |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261103T010040Z) | -0.04 | 0.32 | -0.13 | -0.22 | 1.00 |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261101T050148Z) | -0.18 | 0.36 | -0.12 | -0.21 | 0.50 ✗ |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261103T010102Z) | -0.20 | 0.39 | — | -0.24 | 0.00 ✗ |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261101T050213Z) | -0.15 | 0.35 | -0.10 | -0.22 | 1.00 |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261103T010127Z) | -0.16 | 0.34 | -0.08 | -0.24 | 1.00 |
| Kīlauea 2018 | min (claude × glm-5.3, 20261029T084653Z) | -2.43 ✗ | 0.32 | -0.12 | -0.29 | 1.00 |
| Kīlauea 2018 | tools (claude × glm-5.3, 20261029T084718Z) | -0.06 | 0.38 | -0.16 | -0.06 | 1.00 |
| Ridgecrest 2019 | human-in-loop final | -0.09 | 0.16 | 0.01 | -0.09 | 0.90 |
| Ridgecrest 2019 | backend (claude × glm-5.3, 20261101T235452Z) | -0.98 ✗ | 0.26 | -0.05 | -0.10 | 0.88 ✗ |
| Ridgecrest 2019 | backend_checker (claude × glm-5.3, 20261101T235514Z) | 0.06 | 0.44 ✗ | -0.07 | 0.01 | 0.84 ✗ |
| Ridgecrest 2019 | backend_knowledge (claude × glm-5.3, 20261101T235536Z) | -0.08 | 0.15 | -0.00 | -0.01 | 0.88 ✗ |
| Ridgecrest 2019 | min (claude × glm-5.3, 20261029T203728Z) | 0.30 ✗ | 0.31 ✗ | -0.11 | -0.05 | 0.83 ✗ |
| Ridgecrest 2019 | tools (claude × glm-5.3, 20261029T203757Z) | -1.21 ✗ | 0.20 | -0.03 | -0.02 | 0.86 ✗ |
| Kaikōura 2016 | human-in-loop final | -0.12 | 0.41 | -0.03 | -0.41 | 1.00 |
| Kaikōura 2016 | backend (claude × glm-5.3, 20261102T153500Z) | -0.26 | 0.19 | -0.25 ✗ | 0.03 | 1.00 |
| Kaikōura 2016 | backend_checker (claude × glm-5.3, 20261102T103500Z) | -0.21 | 0.18 | -0.14 | -0.12 | 1.00 |
| Kaikōura 2016 | backend_knowledge (claude × glm-5.3, 20261102T103527Z) | -0.12 | 0.23 | -0.12 | -0.20 | 1.00 |
| Kaikōura 2016 | min (claude × glm-5.3, 20261029T123602Z) | -0.26 | 0.18 | -0.15 | -0.27 | 0.08 ✗ |
| Kaikōura 2016 | tools (claude × glm-5.3, 20261029T183933Z) | -0.60 ✗ | 0.23 | -0.01 | -0.24 | 0.92 ✗ |

## 8. Phase picks

Against manual or correlation picks (Magna: Baker; Maple Creek: Shelly): share recovered within 0.5 s and residual MAD (s).

| Case | Catalog | recall P | recall S | MAD P (s) | MAD S (s) |
|---|---|---|---|---|---|
| Magna 2020 | human-in-loop final | 0.89 | 0.85 | 0.03 | 0.06 |
| Magna 2020 | backend (claude × glm-5.3, 20261101T100247Z) | 0.84 | 0.67 | 0.03 | 0.05 |
| Magna 2020 | backend_checker (claude × glm-5.3, 20261101T100311Z) | 0.84 | 0.64 | 0.03 | 0.05 |
| Magna 2020 | backend_knowledge (claude × glm-5.3, 20261101T100335Z) | 0.84 | 0.67 | 0.03 | 0.05 |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | 0.84 | 0.67 | 0.03 | 0.05 |
| Maple Creek 2017 | human-in-loop final | 0.59 | 0.59 | 0.03 | 0.06 |
| Maple Creek 2017 | backend (claude × glm-5.3, 20261101T185337Z) | 0.47 | 0.42 | 0.03 | 0.06 |
| Maple Creek 2017 | backend_checker (claude × glm-5.3, 20261101T185359Z) | 0.57 | 0.54 | 0.03 | 0.06 |
| Maple Creek 2017 | backend_knowledge (claude × glm-5.3, 20261101T185422Z) | 0.57 | 0.54 | 0.03 | 0.06 |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | 0.54 | 0.46 | 0.04 | 0.07 |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | 0.57 | 0.54 | 0.03 | 0.06 |

## 9. Component swap

The run's own picks and associations relocated with the expert's velocity model and locator (no station delays): what remains is the front end (picks, association); what disappears was the back end (model, locator).

| Case | Run | Locations | recall_norm | shift vs final | dz vs final | \|Δt\| vs final | \|Δt\| vs ref | off structure | depth pile-up |
|---|---|---|---|---|---|---|---|---|---|
| Prague 2011 | min — rescue, reference only | Agent's own locations | 0.03 | 0.82 | -3.38 | 0.94 | 1.56 | 0.05 | 0.09 |
| Prague 2011 | min — rescue, reference only | Agent's picks, expert locator | 0.00 | — | — | — | 1.86 | 0.00 | 0.03 |
| Prague 2011 | tools (claude × glm-5.3, 20261028T043719Z) | Agent's own locations | 1.38 | 0.03 | 1.10 | 0.08 | 0.13 | 0.02 | 0.02 |
| Prague 2011 | tools (claude × glm-5.3, 20261028T043719Z) | Agent's picks, expert locator | 1.12 | 0.00 | 0.00 | 0.02 | 0.07 | 0.01 | 0.07 |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | Agent's own locations | 0.87 | 2.35 | -1.94 | 0.20 | 0.11 | 0.00 | 0.02 |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | Agent's picks, expert locator | 0.68 | 1.72 | -0.96 | 0.15 | 0.15 | 0.00 | 0.02 |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | Agent's own locations | 0.34 | 1.02 | -3.81 | 0.85 | 0.83 | 0.56 | 0.27 |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | Agent's picks, expert locator | 0.56 | 0.75 | -2.35 | 0.43 | 0.38 | 0.47 | 0.13 |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | Agent's own locations | 0.96 | 0.91 | -2.18 | 1.15 | 1.01 | 0.12 | 0.04 |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | Agent's picks, expert locator | 0.89 | 0.15 | -0.31 | 0.09 | 0.20 | 0.07 | 0.03 |
| Kīlauea 2018 | min (claude × glm-5.3, 20261029T084653Z) | Agent's own locations | 0.90 | 0.13 | 1.29 | 0.97 | 0.90 | 0.01 | 0.17 |
| Kīlauea 2018 | min (claude × glm-5.3, 20261029T084653Z) | Agent's picks, expert locator | 0.84 | 0.06 | -0.03 | 0.03 | 0.19 | 0.00 | 0.03 |
| Kīlauea 2018 | tools (claude × glm-5.3, 20261029T084718Z) | Agent's own locations | 0.88 | 0.07 | 0.45 | 0.36 | 0.30 | 0.00 | 0.04 |
| Kīlauea 2018 | tools (claude × glm-5.3, 20261029T084718Z) | Agent's picks, expert locator | 0.88 | 0.00 | 0.00 | 0.03 | 0.19 | 0.00 | 0.03 |

## 10. Process and audit

| Case | Run | Wall time (h) | Cost (USD) | Turns | Leakage | Blind audit |
|---|---|---|---|---|---|---|
| Prague 2011 | backend (claude × glm-5.3, 20261101T000000Z) | 4.7 | 22.21 | 327 | no | 50 of 110 unsupported events; not labelled |
| Prague 2011 | backend_checker (claude × glm-5.3, 20261101T000024Z) | 2.6 | 21.59 | 325 | no | 50 of 118 unsupported events; not labelled |
| Prague 2011 | backend_knowledge (claude × glm-5.3, 20261101T000047Z) | 1.2 | 11.34 | 189 | no | 50 of 105 unsupported events; not labelled |
| Prague 2011 | min (claude × glm-5.3, 20261028T020935Z) | 4.7 | 12.65 | 207 | no | — |
| Prague 2011 | tools (claude × glm-5.3, 20261028T043719Z) | 5.8 | 24.02 | 11 | no | 50 of 134 unsupported events; labelled |
| Magna 2020 | backend (claude × glm-5.3, 20261101T100247Z) | 1.7 | 13.92 | 219 | no | 50 of 94 unsupported events; not labelled |
| Magna 2020 | backend_checker (claude × glm-5.3, 20261101T100311Z) | 5.5 | 22.73 | 372 | no | 50 of 357 unsupported events; not labelled |
| Magna 2020 | backend_knowledge (claude × glm-5.3, 20261101T100335Z) | 4.2 | 19.96 | 338 | no | 50 of 322 unsupported events; not labelled |
| Magna 2020 | min (claude × glm-5.3, 20261028T135859Z) | 4.1 | 12.63 | 5 | no | — |
| Magna 2020 | tools (claude × glm-5.3, 20261028T135931Z) | 7.5 | 61.31 | 42 | no | 50 of 91 unsupported events; labelled |
| Maple Creek 2017 | backend (claude × glm-5.3, 20261101T185337Z) | 2.0 | 16.20 | 233 | no | 50 of 219 unsupported events; not labelled |
| Maple Creek 2017 | backend_checker (claude × glm-5.3, 20261101T185359Z) | 2.3 | 18.24 | 296 | no | 39 of 39 unsupported events; not labelled |
| Maple Creek 2017 | backend_knowledge (claude × glm-5.3, 20261101T185422Z) | 1.4 | 15.60 | 235 | no | 50 of 206 unsupported events; not labelled |
| Maple Creek 2017 | min (claude × glm-5.3, 20261028T220720Z) | 10.6 | 30.81 | 400 | no | 50 of 2,662 unsupported events; not labelled |
| Maple Creek 2017 | tools (claude × glm-5.3, 20261028T220746Z) | 2.3 | 21.83 | 335 | no | 50 of 203 unsupported events; not labelled |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261101T050124Z) | 3.2 | 17.14 | 241 | no | 50 of 186 unsupported events; not labelled |
| Kīlauea 2018 | backend (claude × glm-5.3, 20261103T010040Z) | 6.7 | 23.41 | 350 | review | 50 of 347 unsupported events; not labelled |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261101T050148Z) | 2.6 | 21.78 | 320 | no | 50 of 188 unsupported events; not labelled |
| Kīlauea 2018 | backend_checker (claude × glm-5.3, 20261103T010102Z) | 2.2 | 17.13 | 299 | review | 50 of 1,919 unsupported events; not labelled |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261101T050213Z) | 5.0 | 13.73 | 193 | no | 50 of 236 unsupported events; not labelled |
| Kīlauea 2018 | backend_knowledge (claude × glm-5.3, 20261103T010127Z) | 4.0 | 31.08 | 486 | review | 50 of 97 unsupported events; not labelled |
| Kīlauea 2018 | min (claude × glm-5.3, 20261029T084653Z) | 3.6 | 18.39 | 260 | no | 50 of 809 unsupported events; not labelled |
| Kīlauea 2018 | tools (claude × glm-5.3, 20261029T084718Z) | 3.8 | 17.70 | 306 | no | 50 of 112 unsupported events; not labelled |
| Ridgecrest 2019 | backend (claude × glm-5.3, 20261101T235452Z) | 3.7 | 15.30 | 234 | no | 50 of 3,067 unsupported events; not labelled |
| Ridgecrest 2019 | backend_checker (claude × glm-5.3, 20261101T235514Z) | 3.2 | 22.88 | 360 | no | 50 of 2,781 unsupported events; not labelled |
| Ridgecrest 2019 | backend_knowledge (claude × glm-5.3, 20261101T235536Z) | 3.5 | 22.85 | 366 | no | 50 of 3,387 unsupported events; not labelled |
| Ridgecrest 2019 | min (claude × glm-5.3, 20261029T203728Z) | 5.5 | 19.51 | 259 | no | 50 of 1,351 unsupported events; not labelled |
| Ridgecrest 2019 | tools (claude × glm-5.3, 20261029T203757Z) | 9.7 | 28.49 | 16 | no | 50 of 3,974 unsupported events; not labelled |
| Kaikōura 2016 | backend (claude × glm-5.3, 20261102T153500Z) | 2.2 | 22.13 | 249 | no | 50 of 2,110 unsupported events; not labelled |
| Kaikōura 2016 | backend_checker (claude × glm-5.3, 20261102T103500Z) | 3.0 | 34.70 | 552 | no | 50 of 2,104 unsupported events; not labelled |
| Kaikōura 2016 | backend_knowledge (claude × glm-5.3, 20261102T103527Z) | 4.5 | 18.86 | 295 | review | 50 of 2,284 unsupported events; not labelled |
| Kaikōura 2016 | min (claude × glm-5.3, 20261029T123602Z) | 8.0 | 16.14 | 218 | no | 50 of 770 unsupported events; not labelled |
| Kaikōura 2016 | tools (claude × glm-5.3, 20261029T183933Z) | 26.7 | 24.85 | 14 | review | 50 of 2,304 unsupported events; not labelled |

## 11. Excluded runs

Runs stopped by a harness defect, not by the Agent; repeated after the fix (metrics §11).

| Case | Run | Reason |
|---|---|---|
| Prague 2011 | runs/backend/claude/glm-5.3/20261031T184905Z | # Excluded

Stopped by the model provider, not by the Agent: the API returned HTTP 429 "5-hour usage limit reached" (record/execution.log, 2026-10-31 around 20:20 UTC) while nine back-end runs were running at once. Repeated after the quota reset with at most three concurrent runs. In this batch the `backend` arm could also see the catalog checker in the tools directory (the Prague run used it), so the batch would not have isolated the checker factor; the repeat gives that arm a tools view without the checker. |
| Prague 2011 | runs/backend_checker/claude/glm-5.3/20261031T184925Z | # Excluded

Stopped by the model provider, not by the Agent: the API returned HTTP 429 "5-hour usage limit reached" (record/execution.log, 2026-10-31 around 20:20 UTC) while nine back-end runs were running at once. Repeated after the quota reset with at most three concurrent runs. In this batch the `backend` arm could also see the catalog checker in the tools directory (the Prague run used it), so the batch would not have isolated the checker factor; the repeat gives that arm a tools view without the checker. |
| Prague 2011 | runs/backend_knowledge/claude/glm-5.3/20261031T184947Z | # Excluded

Stopped by the model provider, not by the Agent: the API returned HTTP 429 "5-hour usage limit reached" (record/execution.log, 2026-10-31 around 20:20 UTC) while nine back-end runs were running at once. Repeated after the quota reset with at most three concurrent runs. In this batch the `backend` arm could also see the catalog checker in the tools directory (the Prague run used it), so the batch would not have isolated the checker factor; the repeat gives that arm a tools view without the checker. |
| Magna 2020 | runs/backend/claude/glm-5.3/20261031T185642Z | # Excluded

Stopped by the model provider, not by the Agent: after 5 minutes the API returned HTTP 429 (account rate limit) for ten consecutive retries while nine back-end runs were running at once (record/execution.log, 2026-10-31T19:03:32Z). The run is repeated with fewer concurrent runs. |
| Magna 2020 | runs/backend_checker/claude/glm-5.3/20261031T185704Z | # Excluded

Stopped by the model provider, not by the Agent: the API returned HTTP 429 "5-hour usage limit reached" (record/execution.log, 2026-10-31 around 20:20 UTC) while nine back-end runs were running at once. Repeated after the quota reset with at most three concurrent runs. In this batch the `backend` arm could also see the catalog checker in the tools directory (the Prague run used it), so the batch would not have isolated the checker factor; the repeat gives that arm a tools view without the checker. |
| Magna 2020 | runs/backend_knowledge/claude/glm-5.3/20261031T185724Z | # Excluded

Stopped by the model provider, not by the Agent: the API returned HTTP 429 "5-hour usage limit reached" (record/execution.log, 2026-10-31 around 20:20 UTC) while nine back-end runs were running at once. Repeated after the quota reset with at most three concurrent runs. In this batch the `backend` arm could also see the catalog checker in the tools directory (the Prague run used it), so the batch would not have isolated the checker factor; the repeat gives that arm a tools view without the checker. |
| Maple Creek 2017 | runs/backend/claude/glm-5.3/20261101T150405Z | # Excluded

Stopped by the model provider, not by the Agent: HTTP 429 [1310] weekly/monthly usage limit (record/execution.log, 2026-11-01 about 16:00 UTC; reset 2026-11-05 10:38 Beijing time). To be repeated. |
| Maple Creek 2017 | runs/backend_checker/claude/glm-5.3/20261101T150428Z | # Excluded

Stopped by the model provider, not by the Agent: HTTP 429 [1310] weekly/monthly usage limit (record/execution.log, 2026-11-01 about 16:00 UTC; reset 2026-11-05 10:38 Beijing time). To be repeated. |
| Maple Creek 2017 | runs/backend_knowledge/claude/glm-5.3/20261101T150450Z | # Excluded

Stopped by the model provider, not by the Agent: HTTP 429 [1310] weekly/monthly usage limit (record/execution.log, 2026-11-01 about 16:00 UTC; reset 2026-11-05 10:38 Beijing time). To be repeated. |
| Kīlauea 2018 | runs/backend/claude/glm-5.3/20261031T185540Z | # Excluded

Stopped by the model provider, not by the Agent: the API returned HTTP 429 "5-hour usage limit reached" (record/execution.log, 2026-10-31 around 20:20 UTC) while nine back-end runs were running at once. Repeated after the quota reset with at most three concurrent runs. In this batch the `backend` arm could also see the catalog checker in the tools directory (the Prague run used it), so the batch would not have isolated the checker factor; the repeat gives that arm a tools view without the checker. |
| Kīlauea 2018 | runs/backend_checker/claude/glm-5.3/20261031T185601Z | # Excluded

Stopped by the model provider, not by the Agent: the API returned HTTP 429 "5-hour usage limit reached" (record/execution.log, 2026-10-31 around 20:20 UTC) while nine back-end runs were running at once. Repeated after the quota reset with at most three concurrent runs. In this batch the `backend` arm could also see the catalog checker in the tools directory (the Prague run used it), so the batch would not have isolated the checker factor; the repeat gives that arm a tools view without the checker. |
| Kīlauea 2018 | runs/backend_knowledge/claude/glm-5.3/20261031T185621Z | # Excluded

Stopped by the model provider, not by the Agent: the API returned HTTP 429 "5-hour usage limit reached" (record/execution.log, 2026-10-31 around 20:20 UTC) while nine back-end runs were running at once. Repeated after the quota reset with at most three concurrent runs. In this batch the `backend` arm could also see the catalog checker in the tools directory (the Prague run used it), so the batch would not have isolated the checker factor; the repeat gives that arm a tools view without the checker. |
| Kaikōura 2016 | runs/backend/claude/glm-5.3/20261102T052817Z | # Excluded

Stopped by the model provider, not by the Agent: HTTP 429 [1308] 5-hour usage limit after about 2.7 h with three Kaikoura runs at once (record/execution.log; reset 2026-11-02 18:28 Beijing time). Repeated with fewer concurrent runs. |
| Kaikōura 2016 | runs/backend_checker/claude/glm-5.3/20261102T052841Z | # Excluded

Stopped by the model provider, not by the Agent: HTTP 429 [1308] 5-hour usage limit after about 2.7 h with three Kaikoura runs at once (record/execution.log; reset 2026-11-02 18:28 Beijing time). Repeated with fewer concurrent runs. |
| Kaikōura 2016 | runs/backend_knowledge/claude/glm-5.3/20261102T052904Z | # Excluded

Stopped by the model provider, not by the Agent: HTTP 429 [1308] 5-hour usage limit after about 2.7 h with three Kaikoura runs at once (record/execution.log; reset 2026-11-02 18:28 Beijing time). Repeated with fewer concurrent runs. |
| Kaikōura 2016 | runs/tools/claude/glm-5.3/20261029T123626Z | Excluded 2026-10-30: harness defect, not a formal result. The runner passed the task prompt on the Claude process's argv; the tools prompt names MatchLocate2, so the Agent's own `ps | grep MatchLocate2 | ... kill -9` (its last command, 17:01:15 UTC) matched and killed its Claude session (exit -9, state execution_failed, 4.4 h). work/catalog.csv is an intermediate version from 16:19 UTC. The runner now passes the prompt on stdin; the run is repeated with the fixed runner. |

