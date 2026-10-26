# HypoInverse upstream source

`upstream/source/` is the complete Fortran source and makefile of HypoInverse
1.40 (Fred Klein, USGS) from `hyp1.40.tar`
(https://escweb.wr.usgs.gov/content/software/HYPOINVERSE/hyp1.40.tar, 6,964,224
bytes, last modified 2022-03-01, sha256
`c7ef454f45df4c4f04eed599cd464e03223ffd69e6efc9aa8be0611fe7411006`; archive kept
outside git in `/liufeng1afs/software/Download/hypoinverse/` with the manual
`doc/hyp1.40.pdf` and the `testone/` example used by the validation), plus
`hyp1.40-release-notes.txt`. The archive contains no license file; HypoInverse
is USGS software (a U.S. Government work).

No source patches. The upstream makefile targets g77;
`support/build_native.py --tool hypoinverse` compiles the 47 objects of its
`hyp1.40` target with gfortran (`-O1 -std=legacy -fno-automatic
-finit-local-zero -ffixed-line-length-none -fallow-argument-mismatch`) into
`runtime/bin/hyp1.40`. With this build the `testone` summary and archive
outputs are identical to the shipped ones.

gfortran note: a list-directed read that runs out of values raises an
end-of-file error that hyp1.40 does not trap, so commands must carry all
their values (e.g. `LET 5 2 3 0 0`, `ZTR 5 F`); the adapter writes them so.
