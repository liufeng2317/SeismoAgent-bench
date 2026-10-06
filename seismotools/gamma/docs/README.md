# GaMMA documentation

This directory is organized by reading purpose. The project adapter and its
machine-readable contracts are in [`../interface/`](../interface/); use that
interface for benchmark runs.

## Start here

- [`guides/`](guides/) contains five consolidated workflow guides. Each guide
  combines the example workflow, required files, configuration and diagnostics.
  This is the recommended material for an Agent.
- [`examples/`](examples/) contains the transformed text examples and the
  original notebooks. They show alternative APIs and preprocessing choices;
  they are references, not automatic benchmark launchers.

## Complete reference

- [`reference/deepwiki/`](reference/deepwiki/) contains the full generated
  implementation reference.
- [`reference/retrieval_descriptions.md`](reference/retrieval_descriptions.md)
  contains secondary retrieval-index descriptions and is not an API contract.
- [`reference/assets/`](reference/assets/) and [`reference/figures/`](reference/figures/)
  contain documentation figures.
- [`reference/test_data/`](reference/test_data/) contains retained reference
  figures from the upstream documentation snapshot.

## Reading rule for benchmark runs

Read `guides/` only when the task requires detailed GaMMA usage. Do not use
example case catalogs, published locations or upstream test products as
observations for a new task. Preserve the complete pick table; for large
inputs, use explicit time windows and merge associations rather than keeping a
global top-N subset. A process exit of zero only means that GaMMA ran; inspect
`events.csv` and `assignments.csv` before passing results to a locator.

The source selection and provenance of the transformed material are recorded in
[`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md).
