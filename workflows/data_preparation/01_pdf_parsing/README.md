# PDF parsing with Knowledge_Graph MinerU

`parse_papers_with_mineru.py` calls the existing official parser in `Knowledge_Graph/KGForge/paper_parse/local_pdf_parser.py`, which in turn uses the official MinerU v4 API (`/api/v4/file-urls/batch` and `/api/v4/extract-results/batch/<batch_id>`). This project wrapper does **not** duplicate the API client and does **not** use the retired `mineru_local` service.

The existing Knowledge_Graph parser reads `MINERU_API_BASE` and `MINERU_API_KEY` from the SeismoAgentBench `.env` file.

It discovers PDFs under `data/*/references/*/paper/` and writes results beside the source paper:

```text
paper/
└── SOURCE__paper.pdf

parsed/paper/
├── SOURCE__paper__mineru.md
└── mineru/SOURCE__paper/
    ├── full.md
    ├── *_content_list*.json
    ├── *_model.json
    ├── layout.json
    └── images/
```

List papers without submitting jobs:

```bash
python workflows/data_preparation/01_pdf_parsing/parse_papers_with_mineru.py --list
```

Parse one source:

```bash
python workflows/data_preparation/01_pdf_parsing/parse_papers_with_mineru.py \
  --source COCHRAN2020_GJIGGAA153
```

Parse one case:

```bash
python workflows/data_preparation/01_pdf_parsing/parse_papers_with_mineru.py \
  --case 2011_prague_oklahoma
```

The script skips outputs that already contain both a parsed Markdown file and MinerU's `*_model.json`; use `--force` to reparse. To create the stable `parsed/paper/<stem>__mineru.md` derivatives from already downloaded local bundles without contacting MinerU, run:

```bash
python workflows/data_preparation/01_pdf_parsing/parse_papers_with_mineru.py --sync-stable
```

Audit existing outputs without submitting new MinerU jobs:

```bash
python workflows/data_preparation/01_pdf_parsing/audit_mineru_outputs.py \
  --report docs/data/preparation/03_MinerU_Parsing_Audit.md
```

The audit checks task success, page-count agreement between MinerU model and content-list outputs, HTML tables, image links, OCR replacement characters, and stable Markdown derivatives. It intentionally does not treat a successful paper parse as proof that supplementary catalog products were parsed.

Official API credentials are never printed or copied into this repository. The parser covers source paper PDFs; supplementary PDFs/DOCX/XLSX/XML must be audited separately because their thresholds and catalog schemas can be essential to reproducing a reference catalog.


## Supplementary PDFs

Supplementary-information PDFs use the same official MinerU service but are discovered under `references/*/supplement/`:

```bash
python workflows/data_preparation/01_pdf_parsing/parse_supplement_pdfs_with_mineru.py --list
python workflows/data_preparation/01_pdf_parsing/parse_supplement_pdfs_with_mineru.py \
  --case 2016_kaikoura_new_zealand
```

Outputs are written under `parsed/supplement/mineru/<stem>/` and `parsed/supplement/<stem>__mineru.md`. DOCX/XLSX/TXT/XML processing remains in `02_supplement_processing/`.

## Reading the audit (notes kept by hand, 2026-10-30)

The generated report is [`docs/data/preparation/03_MinerU_Parsing_Audit.md`](../../../docs/data/preparation/03_MinerU_Parsing_Audit.md); regenerate it with the command above and keep notes here, because the script rewrites the whole report.

- Successful outputs preserve text and figures; HTML tables appear in the Markdown where MinerU detected them, so downstream extraction must parse HTML tables rather than assume pipe tables.
- The concatenated Markdown has no page boundaries. Quantitative claims need an anchor from the source PDF or the page-indexed `*_model.json` / `*_content_list_v2.json`.
- Unicode replacement characters mark OCR or encoding uncertainty; confirm those passages visually before recording exact symbols, signs, units or numbers. `LENGLINE2021_EPSL116653` and `AWR2025_CALTECHDATA` also need a control-character and broken-formula check, although they contain no U+FFFD.
- A successful parse is necessary but not sufficient for extraction: the reading record still has to separate article-reported counts from local-file audits and identify the catalog lineage.
- `MAPLE_RELATED_OPEN` is about the Sheldon, Nevada sequence: context only, not Maple Creek evidence. Of the two `QUAKEFLOW_GJI_GGAC355` PDFs, the 10-page article is method context and the 62-page deck is QC context, not a Kīlauea catalog.
- The script discovers only `paper/*.pdf`; supplementary PDF/DOCX/XLSX/XML products must be checked separately.
- Unparsed sources: `MCMAHON2017_DISSERTATION` (MinerU failed; it is a method source, and its extraction JSON was written from the PDF directly); `HVO2002_OFR02157` (Kīlauea) and `BJARNASON_PECHMANN_1989_BSSA` (Magna, kept locally and git-ignored) were added later for velocity models (`data/<case>/data/models/velocity_models.json`) and were not sent to MinerU.
