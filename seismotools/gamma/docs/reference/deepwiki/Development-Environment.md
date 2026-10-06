# Development Environment

> **Relevant source files**
> * [.devcontainer/devcontainer.json](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/.devcontainer/devcontainer.json)
> * [.gitignore](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/.gitignore)

This document provides guidance for setting up a development environment for contributing to the GaMMA project. It covers development container setup, local development configuration, and understanding the project structure for effective contribution.

For information about the CI/CD pipeline and deployment processes, see [CI/CD Pipeline](/AI4EPS/GaMMA/7.2-cicd-pipeline). For documentation building and maintenance, see [Documentation System](/AI4EPS/GaMMA/7.3-documentation-system).

## Development Container Setup

GaMMA provides a preconfigured development container that ensures a consistent development environment across different machines and platforms. The development container is configured to automatically install dependencies and set up the necessary tools.

### Container Configuration

The development environment uses Microsoft's Universal DevContainer image with the following specifications:

```mermaid
flowchart TD

A["devcontainer.json"]
B["mcr.microsoft.com/devcontainers/universal:2"]
C["4 CPU cores minimum"]
D["Python 3 with pip"]
E["VS Code Extensions"]
F["ms-toolsai.jupyter"]
G["ms-python.python"]
H["updateContentCommand"]
I["python3 -m pip install -e ./"]

A --> B
B --> C
B --> D
B --> E
E --> F
E --> G
A --> H
H --> I
```

The container automatically executes `python3 -m pip install -e ./` during the update phase, installing GaMMA in editable mode for development work.

**Sources:** [.devcontainer/devcontainer.json L1-L22](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/.devcontainer/devcontainer.json#L1-L22)

### Required Resources

| Resource | Specification | Purpose |
| --- | --- | --- |
| CPU Cores | 4 minimum | Support parallel processing in association algorithms |
| Memory | Standard (4GB+) | Handle seismic data processing workloads |
| Extensions | Jupyter, Python | Interactive development and notebook support |

### Setup Process

1. **Container Initialization**: The container uses `waitFor: "onCreateCommand"` to ensure proper setup sequencing
2. **Dependency Installation**: Automatically runs `python3 -m pip install -e ./` to install GaMMA in development mode
3. **Extension Loading**: Installs Jupyter and Python extensions for VS Code integration

**Sources:** [.devcontainer/devcontainer.json L6-L8](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/.devcontainer/devcontainer.json#L6-L8)

## Local Development Setup

For developers who prefer local development without containers, GaMMA can be installed directly on the host system.

### Installation Process

```mermaid
flowchart TD

A["Clone Repository"]
B["Create Virtual Environment"]
C["Activate Environment"]
D["pip install -e ./"]
E["Development Ready"]
F["setup.py"]
G["requirements"]

A --> B
B --> C
C --> D
D --> E
F --> D
G --> D
```

### Environment Requirements

* **Python**: 3.8 or higher
* **Dependencies**: Automatically handled by `setup.py`
* **Development Tools**: pytest, jupyter, git

**Sources:** [.devcontainer/devcontainer.json L7](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/.devcontainer/devcontainer.json#L7-L7)

## Project Structure Overview

Understanding the GaMMA project structure is essential for effective development. The codebase follows a modular architecture with clear separation of concerns.

### Core Directory Layout

```mermaid
flowchart TD

A["GaMMA Repository"]
B["gamma/"]
C["tests/"]
D["docs/"]
E[".devcontainer/"]
F[".github/"]
G["app.py"]
H["setup.py"]
B1["utils.py"]
B2["seismic_ops.py"]
B3["_bayesian_mixture.py"]
B4["_gaussian_mixture.py"]
B5["_base.py"]
C1["comparison/"]
C2["test_*.py files"]
D1["*.ipynb notebooks"]
D2["README.md"]
F1["workflows/"]

A --> B
A --> C
A --> D
A --> E
A --> F
A --> G
A --> H
B --> B1
B --> B2
B --> B3
B --> B4
B --> B5
C --> C1
C --> C2
D --> D1
D --> D2
F --> F1
```

### Key Development Files

| Path | Purpose | Importance for Development |
| --- | --- | --- |
| `gamma/utils.py` | Main association workflow | Primary development target |
| `gamma/seismic_ops.py` | Seismic calculations | Physics and math implementations |
| `gamma/_base.py` | EM algorithm foundation | Core statistical methods |
| `app.py` | FastAPI service | Web API development |
| `tests/` | Test suite | Validation and regression testing |

**Sources:** [.gitignore L1-L19](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/.gitignore#L1-L19)

## Development Workflow

### File Exclusions

The development environment automatically excludes certain files and directories from version control:

```mermaid
flowchart TD

A["Source Files"]
B["Git Tracking"]
C["pycache"]
D["Excluded"]
E["*.egg-info"]
F["build/"]
G[".DS_Store"]
H[".ipynb_checkpoints"]
I["test_data"]
J["Repository"]
K["Local Only"]

A --> B
C --> D
E --> D
F --> D
G --> D
H --> D
I --> D
B --> J
D --> K
```

### Ignored File Categories

* **Python Artifacts**: `__pycache__`, `*.egg-info`, `build/`
* **IDE Files**: `.DS_Store`, `.ipynb_checkpoints`
* **Test Data**: `test_data`, `test_data.zip`
* **Output Files**: `figures`, `results`, `timetable_*`

**Sources:** [.gitignore L1-L19](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/.gitignore#L1-L19)

### Development Cycle

1. **Environment Setup**: Use dev container or local installation
2. **Code Modification**: Edit source files in `gamma/` directory
3. **Testing**: Run tests to validate changes
4. **Documentation**: Update relevant documentation
5. **Integration**: Ensure compatibility with existing workflows

## Testing Integration

The development environment integrates with GaMMA's comprehensive testing framework. Tests are organized to support both unit testing and integration validation.

### Test Organization

```mermaid
flowchart TD

A["tests/"]
B["Unit Tests"]
C["Integration Tests"]
D["Comparison Tools"]
B1["test_*.py files"]
C1["End-to-end workflows"]
D1["comparison/ notebooks"]
E["Development Environment"]
F["pytest execution"]

A --> B
A --> C
A --> D
B --> B1
C --> C1
D --> D1
E --> F
F --> B
F --> C
```

### Test Data Management

Test data files are automatically excluded from the repository but can be generated or downloaded as needed during development:

* `test_data.zip` and extracted `test_data/` directories
* Generated `figures` and `results` directories
* Temporary `timetable_*` files

**Sources:** [.gitignore L9-L14](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/.gitignore#L9-L14)

## IDE Integration

The development container includes specific VS Code extensions optimized for GaMMA development:

| Extension | Purpose | Development Benefit |
| --- | --- | --- |
| `ms-toolsai.jupyter` | Jupyter notebook support | Interactive data analysis and examples |
| `ms-python.python` | Python language support | Code completion, debugging, linting |

These extensions enable seamless development of both the core Python library and the accompanying Jupyter notebook examples.

**Sources:** [.devcontainer/devcontainer.json L14-L19](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/.devcontainer/devcontainer.json#L14-L19)