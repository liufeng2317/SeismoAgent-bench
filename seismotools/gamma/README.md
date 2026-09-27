
# GaMMA

Local TRACE GaMMA source snapshot; `source/setup.py` reports distribution name `GMMA`, version `1.2.17`. The runtime import is `gamma`. Copied source identity is recorded separately from this version because the local implementation may differ from an upstream release.

Input: picks, station coordinates, coordinate projection, velocity settings and association configuration. Output: associated events and event/pick membership. Keep unassociated picks separately. The Ridgecrest run uses arrival-only BGMM and omits the local placeholder magnitude and unreliable returned assignment scores.

Use `source/` on the Python import path; dependencies are in [requirements.txt](source/requirements.txt) and the observed environment record. [Bundled documentation](docs/README.md) is copied from the same local library. Run the root tool check with `--imports` to verify local module import without association or network calls.

[Case usage](../../tasks/2019_ridgecrest_california/expert/01_pipeline/03_associate_gamma.py) defines projection, time blocking, eikonal grids and association thresholds. Keep those case choices out of the reusable source.

## Documentation map

| Material                        | Entry                                                                                                                                                                                                       | Status and use                                                                                  |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Source-distributed introduction | [Original docs README](docs/README.md)                                                                                                                                                                       | Copied with its available images and tutorial notebooks                                         |
| Expanded local documentation    | [DeepWiki index](docs/deepwiki-document/README.md)                                                                                                                                                           | All 30 local Markdown pages; secondary documentation, check claims against this source snapshot |
| Association API                 | [Core association functions](docs/deepwiki-document/Core-Association-Functions.md)                                                                                                                           | API/parameter explanation                                                                       |
| Velocity and travel times       | [Custom velocity models](docs/deepwiki-document/Custom-Velocity-Models.md), [travel-time calculation](docs/deepwiki-document/Travel-Time-Calculation.md)                                                      | Forward-model assumptions and configuration                                                     |
| Usage notebooks                 | [PhaseNet](docs/example_phasenet.ipynb), [NCEDC](docs/example_phasenet_ncedc.ipynb), [SeisBench](docs/example_seisbench.ipynb), [synthetic](docs/example_synthetic.ipynb), [FastAPI](docs/example_fastapi.ipynb) | Code/Markdown cells retained; outputs cleared; external data/environment requirements remain    |
| Original examples/tests         | [Synthetic example](source/tests/synthetic_example.py), [GaMMA notebook](source/tests/GaMMA.ipynb)                                                                                                            | Historical examples, not a newly validated benchmark or automatically run test suite            |
| Retrieval tool descriptions     | [Extracted descriptions](docs/retrieval_descriptions.md)                                                                                                                                                     | Text from the existing local retrieval index; embedding vectors omitted                         |

The previous transfer omitted the DeepWiki directory, notebooks and image assets; those gaps are now filled. The source-distributed docs also contain example waveforms, picks and generated catalogs: these are deliberately excluded, so data-dependent notebooks require their documented inputs and are not promised to run unchanged. No evidence establishes which individual document was read during each historical agent turn.
