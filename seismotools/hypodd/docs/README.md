# hypoDD documentation

The source selection is recorded in [SOURCE_MANIFEST.md](SOURCE_MANIFEST.md).

This directory contains generic hypoDD runner examples and Agent-oriented
summaries extracted from the local retrieval library.

- `examples/` contains the catalog-only, cross-correlation-only and combined
  workflow descriptions.
- `agent_guides/` contains the corresponding input, configuration, workflow,
  output and validation summaries.
- `../runtime/python/HypoDDpy/` contains the local Python interface and its
  detailed interface card.
- `../interface/` is the project-stable native command-line interface.

Use hypoDD only after event association and absolute-location preparation.
Catalog differential times are required for CT mode; waveform cross-correlation
differential times are additionally required for CT+CC or CC-only mode.
Execution success must be checked together with the relocation output and
quality statistics.
