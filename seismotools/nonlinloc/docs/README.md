# NonLinLoc documentation

This directory contains generic NonLinLoc and Nonlinlocpy usage examples and
Agent-oriented summaries extracted from the local retrieval library.

- `examples/` contains standard workflow examples and configuration templates.
- `core/` contains file, configuration, workflow and validation summaries.
- `../runtime/python/Nonlinlocpy/` contains the executable local Python
  package and its native reference documentation.
- `../interface/` is the project-stable command-line interface.

NonLinLoc is an event locator. Its input must represent an already associated
event or an explicitly defined event observation set; an unassociated global
pick table must not be treated as one event. Check the observation count,
finite RMS, search-limit messages and station geometry before accepting a
location.
