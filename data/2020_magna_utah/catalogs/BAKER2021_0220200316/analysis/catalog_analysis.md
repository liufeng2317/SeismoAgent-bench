# BAKER2021_0220200316 catalog analysis

Baker is a pick-level release. Event counts are after collapsing repeated pick rows by `event_number`; pick rows remain a separate denominator.

| Product | Full | Time-only | Benchmark |
|---|---:|---:|---:|
| Event collapse | 5885 | 3782 | 3712 |
| Pick rows | 329,611 | n/a | 161,567 |

Phase rows: `{'P': 141972, 'S': 187639}`; stations: `207`. Schema: `docs/schemas/catalog_event.schema.yaml`.
