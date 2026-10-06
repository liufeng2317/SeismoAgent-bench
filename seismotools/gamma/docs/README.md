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

## Reference archive

- [`reference/rag_examples/`](reference/rag_examples/) contains the original
  transformed RAG examples and notebooks. Consult these only when the core
  guide does not answer a concrete question.
- [`reference/deepwiki/`](reference/deepwiki/) contains the generated full
  implementation reference.
- [`reference/retrieval_descriptions.md`](reference/retrieval_descriptions.md)
  contains retrieval-index descriptions, not an API contract.
- `reference/assets/`, `reference/figures/` and `reference/test_data/` contain
  supporting figures and upstream reference materials.
- [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md) records provenance and any text
  transformations.

Do not use example catalogs, published locations or upstream test products as
observations for a new benchmark case. A successful process exit only means
that GaMMA ran; inspect both `events.csv` and `assignments.csv` before passing
results to a locator.
