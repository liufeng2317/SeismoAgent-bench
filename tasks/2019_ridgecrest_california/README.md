# Ridgecrest task package

This package defines the first real case task for SeismoAgentBench. The
current version is a smoke task only. It uses three CI.CCC waveform components
and one StationXML file from the approved external data store.

The bundled reference contains only the M6.4 and M7.1 mainshocks copied from
the USGS/SCSN operational catalog. It verifies the task and scoring path; it is
not a complete Ridgecrest benchmark reference and must not be used to claim
full-sequence performance.

The waveform files are referenced through the input manifest and are not
copied into Git.
