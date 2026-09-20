# Non-PDF supplementary processing

`convert_nonpdf_supplements.py` handles DOCX, XLSX, TXT, XML, CSV, and TSV
files. It converts them to searchable Markdown and identifies possible event
tables. PDF supplements are handled separately by
`../01_pdf_parsing/parse_supplement_pdfs_with_mineru.py`.

```bash
python scripts/02_supplement_processing/convert_nonpdf_supplements.py
```

Original files remain unchanged. Catalog migration is opt-in and must be
verified against the paper before use.
