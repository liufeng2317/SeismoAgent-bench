# TAN2024_JB028735 catalog analysis

S10, S11, associated phases, and S12 mechanisms are separate products.

| Product | Full rows/files | Time-only | Benchmark |
|---|---:|---:|---:|
| `sugar_s10` | 67660 | 9720 | 9720 |
| `sugar_s11` | 46440 | 6973 | 6955 |
| `associated_phase` | 1382337 phase rows / 1165 files | n/a | n/a |
| `focal_mechanisms_s12` | 55 solutions | n/a | n/a |

S10 is the detection/located catalog; S11 is the released GrowClust intermediate. The 41,392 article count must be reconstructed from S11 cluster size >=10. Phase rows and S12 mechanisms are not event rows.

Schemas: `docs/schemas/catalog_event.schema.yaml`; phase product remains product-specific and is not merged into event counts.
