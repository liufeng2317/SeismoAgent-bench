# REAL upstream source

`upstream/` holds `src/REAL/REAL.c` and `Makefile`, `LICENSE` (MIT, Miao Zhang),
`README.md` and `Modified_History` from github.com/Dal-mzhang/REAL at commit
`6435ace552d1efe72e633e8f82a5f9d8467f1049` (archive
`REAL-6435ace552d1efe72e633e8f82a5f9d8467f1049.zip`, sha256
`47ea30bd04d89a95de22f0f360e95a2d840b058b0c3c2db32c57c4a7f0a5b605`, kept outside git in
`/liufeng1afs/software/Download/real/`). Not copied: the bundled x86 binaries,
VELEST, pick2real, demos and the user guide PDF.

No local patches. `support/build_native.py --tool real` compiles
`gcc -O2 -fopenmp -ffp-contract=off REAL.c -lm` into `runtime/bin/REAL`.
