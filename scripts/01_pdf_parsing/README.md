# PDF parsing with Knowledge_Graph MinerU

`parse_papers_with_mineru.py` calls the existing official parser in
`Knowledge_Graph/KGForge/paper_parse/local_pdf_parser.py`, which in turn uses
the official MinerU v4 API (`/api/v4/file-urls/batch` and
`/api/v4/extract-results/batch/<batch_id>`). This project wrapper does **not**
duplicate the API client and does **not** use the retired `mineru_local` service.

The existing Knowledge_Graph parser reads `MINERU_API_BASE` and
`MINERU_API_KEY` from the SeismoAgentBench `.env` file.

It discovers PDFs under `data/*/references/*/paper/` and writes results beside
the source paper:

```text
paper/
├── SOURCE__paper.pdf
├── SOURCE__paper__mineru.md
└── mineru/SOURCE__paper/
    ├── result.md
    ├── result.json
    ├── mineru_model.json
    ├── task_meta.json
    └── images/
```

List papers without submitting jobs:

```bash
python scripts/01_pdf_parsing/parse_papers_with_mineru.py --list
```

Parse one source:

```bash
python scripts/01_pdf_parsing/parse_papers_with_mineru.py \
  --source COCHRAN2020_GJIGGAA153
```

Parse one case:

```bash
python scripts/01_pdf_parsing/parse_papers_with_mineru.py \
  --case 2011_prague_oklahoma
```

The script skips outputs that already contain both a parsed Markdown file and
MinerU's `*_model.json`; use `--force` to reparse. Official API credentials
are never printed or copied into this repository.
