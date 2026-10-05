# Time2EQ - travel-time grid to synthetic observations

Given a hypocenter location and a set of travel-time grids, Time2EQ
calculates predicted travel-times.

[Overview](#_overview_) - [Running the program-Input](#_running_)
- [Output](#_output_) - [Processing and Display of results](#_processing_) - [NonLinLoc Home](./index.md)

## Overview

The Time2EQ program calculates predicted travel-times between one or
more synthetic events and one or more stations. Predicted take-off
angles at the source are also calculated if an event mechanism is given
and the corresponidng take-off angles grids are available.

## Running the program - Input

Synopsis: [`Time2EQ InputControlFile`` The Time2EQ program takes a single argument ``InputControlFile`` which specifies the complete path and filename for an `Input Control File](./control.ControlFile.md) with certain required and optional statements
specifying program parameters and input/output file names and locations.
See the [Time2EQ Statements section](./control.ControlFile.md#_Time2EQ_) of the
Input Control File for more details. Note that to run Time2EQ the
[Generic Statements section](./control.ControlFile.md#_generic_) of the Input
Control File must contain the ``CONTROL`` and ``TRANS`` (Geographic
Transformation) statements.

In addition, the Time2EQ program requires:

#. Files containing a 2D or a 3D **Travel-time grids** (and optionally
   **Angles grids**) created by the program
   [Grid2Time](./core.Grid2Time.md) for each phase type at each station.

The names, locations and other information for these files is specified
in the [Time2EQ Statements section](./control.ControlFile.md#_Time2EQ_) of the
Input Control File.

## Output

The predicted travel-times are written to an observation file in
[NonLinLoc phase file format](formats.html#_phase_nlloc_).

## Processing and Display of results

The predicted travel-time files can be used as input phase/observation
files for location with the program [NLLoc](./core.NLLoc.md).

Back to [the NonLinLoc site Home page](./index.md).

*Anthony Lomax*
