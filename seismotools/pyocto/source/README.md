# PyOcto upstream source

`upstream/` is a subset of the PyOcto 0.1.9 sdist (PyPI `pyocto-0.1.9.tar.gz`,
sha256 `6f985b92dc5a83b14e6744ce74e1b498a96fadeaf4eb6f7be35408ad3b736d19`,
equal to the PyPI digest; archive kept outside git in
`/liufeng1afs/software/Download/pyocto/`): `src/` (C++ core, pybind11 bindings,
Python package), `CMakeLists.txt`, `pyproject.toml`, `LICENSE` (MIT, Jannes
Münchmeyer) and `README.md`. Not copied: the vendored `extern/pybind11`
(9.6 MB), benchmarks, notebooks, docs and tests.

| Patch | File | Change |
|---|---|---|
| `0001-cmake-find-pybind11.patch` | `CMakeLists.txt` | `find_package(pybind11 CONFIG REQUIRED)` instead of `add_subdirectory(extern/pybind11)`: pybind11 comes from the declared build requirements |

`support/build_native.py --tool pyocto` copies `upstream/` to
`runtime/build/src`, applies the patch, builds a wheel offline from the build
requirements in `/liufeng1afs/software/Download/pyocto/build_requirements`
(override with `PYOCTO_BUILD_REQUIREMENTS`; scikit-build-core 1.1.1,
pybind11 3.1.0, system CMake, Unix Makefiles) and installs it into
`runtime/build/site`. The Python environment is not modified.
