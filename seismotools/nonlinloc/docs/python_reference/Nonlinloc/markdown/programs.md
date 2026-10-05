# NonLinLoc Programs

NonLinLoc contains core and utility programs. The core programs handle
velocity model setup, travel-time calculation, and earthquake location.
Utility programs cover format conversion, grid manipulation, and related
tasks.

All NonLinLoc core programs and many utiltiy programs use a control file to specify program run parameters.

## Core

Core routines of the NonLinLoc project.

- [programs/core.Vel2Grid](programs/core.Vel2Grid.md)
- [programs/core.Vel2Grid3D](programs/core.Vel2Grid3D.md)
- [programs/core.Grid2Time](programs/core.Grid2Time.md)
- [programs/core.Time2EQ](programs/core.Time2EQ.md)
- [programs/core.NLLoc](programs/core.NLLoc.md)
- [programs/core.LocSum](programs/core.LocSum.md)
- [programs/core.Grid2GMT](programs/core.Grid2GMT.md)
- [programs/core.Loc2ssst](programs/core.Loc2ssst.md)

## Utils

Various utility functions.

- programs/utils.oct2grid

## Control

Control-file reference for the NonLinLoc programs.

- [programs/control.ControlFile](programs/control.ControlFile.md)
