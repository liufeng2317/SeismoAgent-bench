# GaMMA documentation

The documentation is split by purpose so that a run does not need to read the
entire archive.

## Read first

- [`core/`](core/) contains the curated Agent-facing method, input, configuration
  and diagnostic guides. Read the one guide relevant to the current input.
- [`../interface/`](../interface/) contains the project execution entry point and
  machine-readable input/output contracts. Use it to run GaMMA after reading
  the method documentation.

## Runnable examples

- [`../examples/smoke/`](../examples/smoke/) checks the smallest synthetic call.
- [`../examples/workflow/`](../examples/workflow/) is a complete synthetic
  input-to-output workflow for the project adapter.

## Documentation scope

The repository keeps only the curated `core/` guides and the runnable examples
needed to understand and validate this adapter. Historical generated pages,
raw RAG copies, upstream notebooks/tests, retrieval descriptions and their
supporting figures were removed because they were not runtime inputs and often
duplicated or contradicted the curated guides. [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md)
records the provenance of the retained guides.

Do not use example catalogs, published locations or upstream test products as
observations for a new benchmark case. A successful process exit only means
that GaMMA ran; inspect both `events.csv` and `assignments.csv` before passing
results to a locator.
