# GrowClust upstream source

`upstream/` holds `SRC/` (Fortran 90 sources and makefile), `license.txt`
(GPL-3.0) and `README.md` from github.com/dttrugman/GrowClust at commit
`53226cf7662ab5bab5db87138d1ae63227d4ba63` (archive sha256
`feec66a06a58fb6761f5a3d63a4e45107084dc735f0a9755aa759583334bcc2c`, kept outside git in
`/liufeng1afs/software/Download/growclust/`, with the upstream `EXAMPLE/` used by
the validation). Not copied: `EXAMPLE/` (18 MB) and the user guide PDF.
Upstream notes the Fortran version is no longer fully maintained in favour of
GrowClust3D.jl.

No local patches. `support/build_native.py --tool growclust` runs the upstream
makefile (`gfortran -O`) into `runtime/bin/growclust`. Array limits
(`grow_params.f90`): 1,000 stations, 100,000 events, 10^6 pairs, 10^7
differential times, event ids < 10^8.
