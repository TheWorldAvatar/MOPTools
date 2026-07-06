# MOPTools - Metal-Organic Polyhedron Assembly Tools

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

**MOPTools** is a Python library for assembling and analyzing Metal-Organic Polyhedrons (MOPs) using ontology-based knowledge graphs. It provides tools for working with the OntoMOPs ontology and integrating with the World Avatar Knowledge Graph (TWA KG).

## 📚 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Usage Examples](#-usage-examples)
- [Configuration](#-configuration)
- [Error Handling](#-error-handling)
- [Input Validation](#-input-validation)
- [Testing](#-testing)
- [Recursion Depth Guidelines](#-recursion-depth-guidelines)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Features

- **Knowledge Graph Integration**: Pull and push data from/to TWA KG using SPARQL
- **Modular Assembly**: Assemble MOPs from Assembly Models (AMs) and Chemical Building Units (CBUs)
- **Batched Queries**: Optimized batched SPARQL queries for performance
- **Caching**: LRU caching for KG objects to reduce redundant queries
- **Input Validation**: Comprehensive validation of IRIs, depths, endpoints, and file paths
- **Error Handling**: Custom exceptions with detailed error messages
- **Performance Metrics**: Track query execution times and statistics

---

## 💻 Installation

### Prerequisites

- Python 3.12 is recommended for the tutorials
- pip package manager
- Java 17, used by the TWA/Py4J gateway
- Conda or Miniforge, if using the conda setup below
- Access to a TWA Knowledge Graph endpoint (local or remote)

### Install from source

The tutorials are intended to be run from an editable source install so that notebook imports use the local checkout.

```bash
# Clone the repository
git clone https://github.com/your-org/MOPTools.git
cd MOPTools

# Create and activate a conda environment
conda create -n twa python=3.12
conda activate twa

# Install MOPTools with notebook support
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[notebook]"

# Register the environment as a Jupyter kernel
python -m ipykernel install --user --name twa --display-name "twa conda"
```

If `conda` is not available, install Miniforge or use a standard Python virtual environment with the same `pip install -e ".[notebook]"` command.

When opening a tutorial notebook in VS Code, select the `twa conda` kernel. The first notebook cells check that the editable install, Java version, KG endpoint, and required local files are available.

### Required Dependencies

- Runtime dependencies are listed in the root `requirements.txt`.
- Notebook dependencies are installed via the `notebook` extra in `setup.py`.
- Development/test dependencies are installed via the `dev` extra:

```bash
python -m pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### Basic Usage

```python
from twa_mops.kg import KnowledgeGraphClient

# Initialize the KG client
kg_client = KnowledgeGraphClient(
    endpoint="http://localhost:3838/sparql",
    max_cache_size=128
)

# Pull objects from KG
am_iri = "https://www.theworldavatar.com/kg/ontomops/AssemblyModel_123"
cbu_iris = [
    "https://www.theworldavatar.com/kg/ontomops/ChemicalBuildingUnit_456",
    "https://www.theworldavatar.com/kg/ontomops/ChemicalBuildingUnit_789"
]

# Pull with validation and depth recommendation
am, cbus = kg_client.pull_for_assembly(am_iri, cbu_iris, depth=3)

# Assemble a MOP
from twa_mops.core import MetalOrganicPolyhedron
provenance = {"created_by": "user@example.com", "method": "manual"}
mop = MetalOrganicPolyhedron.from_assemble(
    am, cbus, provenance, 
    sparql_client=kg_client
)
```

### Using Environment Configuration

Create a `.env` file:

```bash
# .env
SPARQL_ENDPOINT=http://localhost:3838/sparql
DATA_DIR=./data
FS_URL=http://localhost:8000
```

Then in Python:

```python
from twa_mops.config import settings
from twa_mops.kg import KnowledgeGraphClient

# settings are automatically loaded from .env
kg_client = KnowledgeGraphClient(endpoint=settings.sparql_endpoint)
print(f"Using data directory: {settings.data_dir}")
```

---

## 🗂️ Project Structure

```
twa_mops/
├── __init__.py                    # Package initialization
├── config.py                      # Centralized configuration (Pydantic settings)
│
├── core/                          # Core ontology and data models
│   ├── __init__.py
│   ├── ontomops.py               # OntoMOPs classes (AssemblyModel, ChemicalBuildingUnit, etc.)
│   ├── ontospecies.py            # OntoSpecies classes (Geometry, ChemicalSpecies, etc.)
│   └── geo.py                    # Geometry utilities (Point, Vector, etc.)
│
├── kg/                            # Knowledge Graph interaction
│   ├── __init__.py
│   ├── client.py                 # KnowledgeGraphClient with validation and error handling
│   ├── compatibility.py           # PySparqlClient compatibility layer
│   ├── queries/                  # SPARQL query templates
│   │   ├── __init__.py
│   │   ├── pull.sparql
│   │   ├── alg1.sparql
│   │   └── alg2.sparql
│   └── algorithms/               # Algorithm-specific logic
│       ├── __init__.py
│       ├── alg1.py
│       └── alg2.py
│
├── assembly/                     # MOP assembly logic
│   └── __init__.py
│
├── utils/                        # General-purpose utilities
│   ├── __init__.py
│   ├── om.py
│   └── molecular_fragment_utils.py
│
├── scripts/                      # Standalone scripts
│   ├── __init__.py
│   ├── main.py
│   ├── cavity.py
│   └── cavity_and_pore_size.py
│
├── tests/                        # Unit and integration tests
│   ├── __init__.py
│   ├── test_kg.py                # KG client tests (22 tests)
│   └── test_local_kg_connection.py
│
└── tutorials/                    # Jupyter notebook tutorials
    ├── __init__.py
    ├── assembly.ipynb
    └── fragmops_tutorial.ipynb
```

---

## 📖 Usage Examples

### Example 1: Pulling Objects from KG

```python
from twa_mops.kg import KnowledgeGraphClient

# Initialize client
kg_client = KnowledgeGraphClient(
    endpoint="http://localhost:3838/sparql",
    max_cache_size=256,
    enable_performance_timing=True
)

# Pull single object
iri = "https://www.theworldavatar.com/kg/ontomops/ChemicalBuildingUnit_abc123"
cbu_data = kg_client.pull_single_object(iri)

# Pull multiple objects (batched query)
iris = ["iri1", "iri2", "iri3"]
objects = kg_client.pull_objects(iris)

# Get performance stats
stats = kg_client.get_performance_stats()
print(f"Total queries: {stats['total_queries']}")
print(f"Average time: {stats['avg_time']:.3f}s")
```

### Example 2: MOP Assembly

```python
from twa_mops.kg import KnowledgeGraphClient
from twa_mops.core import MetalOrganicPolyhedron, AssemblyModel, ChemicalBuildingUnit

# Initialize client
kg_client = KnowledgeGraphClient(endpoint="http://localhost:3838/sparql")

# Pull AM and CBUs with recommended depth=3
am_iri = "https://www.theworldavatar.com/kg/ontomops/AssemblyModel_xyz"
cbu_iris = ["CBU_iri_1", "CBU_iri_2"]

# This will warn if depth < 3 (too shallow for assembly)
am, cbus = kg_client.pull_for_assembly(am_iri, cbu_iris, depth=3)

# Define provenance
provenance = {
    "created_by": "researcher@example.com",
    "method": "automated_assembly",
    "timestamp": "2026-06-23"
}

# Assemble MOP
mop = MetalOrganicPolyhedron.from_assemble(
    am, cbus, provenance,
    sparql_client=kg_client,
    data_dir="./data"
)
```

### Example 3: Using Validation Models Directly

```python
from twa_mops.kg.client import IRIInput, DepthInput, EndpointInput

# Validate an IRI
validated_iri = IRIInput(iri="https://example.com/kg/resource").iri

# Validate depth
validated_depth = DepthInput(depth=3).depth

# Validate endpoint
validated_endpoint = EndpointInput(endpoint="http://localhost:3838/sparql").endpoint
```

---

## ⚙️ Configuration

### Environment Variables

MOPTools uses environment variables for configuration. Create a `.env` file in your project root:

```bash
# SPARQL Endpoint
SPARQL_ENDPOINT=http://localhost:3838/sparql

# Data directory for geometry files
DATA_DIR=./data

# File server configuration (optional)
FS_URL=http://localhost:8000
FS_USERNAME=your_username
FS_PASSWORD=your_password

# KG authentication (optional)
KG_USERNAME=your_username
KG_PASSWORD=your_password
```

Or set them directly in your environment:

```bash
export SPARQL_ENDPOINT=http://localhost:3838/sparql
export DATA_DIR=./my_data
```

### Using Settings in Code

```python
from twa_mops.config import settings

# Access configuration values
print(settings.sparql_endpoint)  # "http://localhost:3838/sparql"
print(settings.data_dir)          # "./data"
```

---

## ⚠️ Error Handling

MOPTools provides custom exceptions for better error handling:

### Custom Exceptions

```python
from twa_mops.kg import (
    KnowledgeGraphError,    # Base exception for all KG errors
    QueryError,             # SPARQL query failures
    ObjectNotFoundError,    # Objects not found in KG
    InvalidObjectError,    # Invalid object data/structure
)
```

### Handling Errors

```python
from twa_mops.kg import KnowledgeGraphClient, QueryError, ObjectNotFoundError

kg_client = KnowledgeGraphClient(endpoint="http://localhost:3838/sparql")

try:
    # This might fail if the KG is unreachable
    data = kg_client.pull_objects(["http://example.com/iri"])
except QueryError as e:
    print(f"Query failed: {e}")
    print(f"Endpoint: {e.endpoint}")
    print(f"Original error: {e.original_error}")
except ObjectNotFoundError as e:
    print(f"Objects not found: {e.iris}")
except KnowledgeGraphError as e:
    print(f"KG error occurred: {e}")
```

---

## ✅ Input Validation

MOPTools validates all inputs to prevent errors and provide clear error messages:

### Validated Parameters

| Parameter | Validation | Valid Range/Format |
|-----------|------------|-------------------|
| `endpoint` | HTTP/HTTPS URL | Must start with `http://` or `https://` |
| `iris` | IRI format | HTTP/HTTPS URL or URN format |
| `depth` | Numeric bounds | -1 to 10 (inclusive) |
| `max_cache_size` | Numeric bounds | 1 to 10000 (inclusive) |
| `fs_url` | HTTP/HTTPS URL | Must start with `http://` or `https://` |
| `queries` | Non-empty string | Cannot be empty or None |
| `file paths` | Existence check | Must exist on disk (for upload) |

### Depth Recommendations for Assembly

| Depth | Description | Recommended? |
|-------|-------------|--------------|
| -1 | Infinite recursion (full object resolution) | ✅ Yes (most reliable) |
| 0 | No recursion (IRIs only, not loaded objects) | ❌ No (will fail) |
| 1 | Direct properties only | ⚠️ Maybe (may miss nested objects) |
| 2 | Two-level recursion | ⚠️ Maybe (may miss GBUConnectingPoint) |
| 3 | Three-level recursion | ✅ Yes (minimum for assembly) |
| 4-10 | Deeper recursion | ✅ Yes (safe, more complete) |

**For MOP assembly, use depth=3 or depth=-1 to ensure all required properties are loaded.**

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest twa_mops/tests/ -v

# Run specific test file
pytest twa_mops/tests/test_kg.py -v

# Run with coverage
pytest --cov=twa_mops --cov-report=html twa_mops/tests/
```

### Test Structure

- `test_kg.py`: Unit tests for KnowledgeGraphClient (22 tests)
  - Initialization tests
  - Input validation tests (12 new tests)
  - Pull/push operation tests
  - Cache tests
- `test_local_kg_connection.py`: Integration tests with local KG

---

## 📝 Recursion Depth Guidelines

When working with the Knowledge Graph, the recursion depth parameter controls how deeply related objects are loaded:

```python
# depth=-1: Load everything (infinite recursion)
#   Pros: Most reliable, won't miss any data
#   Cons: Slowest, may load unnecessary data
#   Use: When you need complete objects and performance is not critical

# depth=0: Load only direct properties as IRIs
#   Pros: Fastest
#   Cons: Properties are IRIs (strings), not loaded objects - WILL FAIL for assembly
#   Use: Never for assembly, only for metadata inspection

# depth=1: Load direct properties
#   Pros: Fast
#   Cons: May miss nested objects like GBUConnectingPoint
#   Use: Not recommended for assembly

# depth=2: Load two levels of properties
#   Pros: Faster than -1
#   Cons: May miss GBUConnectingPoint, Modularity - WILL FAIL for assembly
#   Use: Not recommended for assembly

# depth=3: Load three levels of properties
#   Pros: Loads all required objects for assembly
#   Cons: Slightly slower than depth=1
#   Use: RECOMMENDED for assembly (minimum safe depth)

# depth=4-10: Load deeper properties
#   Pros: More complete data
#   Cons: Slower as depth increases
#   Use: For complex structures or when depth=3 is insufficient
```

---

## 🤝 Contributing

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/MOPTools.git
cd MOPTools

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install in development mode
pip install -e .[dev]

# Run tests
pytest twa_mops/tests/ -v
```

### Code Style

- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Add docstrings to all classes and public methods
- Use Pydantic models for input validation
- Write unit tests for new functionality

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests (`pytest twa_mops/tests/ -v`)
5. Commit your changes (`git commit -m "Add your feature"`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

## 📞 Support

For questions, issues, or feature requests:

- Open an issue on GitHub
- Contact the maintainers

---

*Documentation last updated: 2026-06-23*
