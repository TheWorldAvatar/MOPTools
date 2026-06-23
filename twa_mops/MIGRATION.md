# Migration Guide: Old MOPTools to New twa_mops

This guide helps users migrate from the old MOPTools codebase to the new modular `twa_mops` package structure.

## 📚 Table of Contents

- [What Changed](#-what-changed)
- [Folder Structure Changes](#-folder-structure-changes)
- [Import Changes](#-import-changes)
- [Breaking Changes](#-breaking-changes)
- [New Features](#-new-features)
- [Migration Steps](#-migration-steps)
- [Code Examples: Before and After](#-code-examples-before-and-after)

---

## 🔄 What Changed

The MOPTools codebase has been refactored into a modular structure under the `twa_mops` package. This change improves:

- **Maintainability**: Clear separation of concerns
- **Testability**: Independent testing of components
- **Reusability**: Modular imports
- **Documentation**: Better organized code
- **Performance**: Batched queries, caching, optimized error handling

---

## 🗂️ Folder Structure Changes

### Old Structure
```
MOPTools/
├── ontomops.py
├── ontospecies.py
├── geo.py
├── alg1.py
├── alg2.py
├── main.py
├── om.py
├── cavity.py
├── cavity_and_pore_size.py
├── assembly.ipynb
└── fragmops_tutorial.ipynb
```

### New Structure
```
MOPTools/
└── twa_mops/
    ├── __init__.py
    ├── config.py                          # Centralized configuration
    │
    ├── core/                            # Core ontology models
    │   ├── __init__.py
    │   ├── ontomops.py
    │   ├── ontospecies.py
    │   └── geo.py
    │
    ├── kg/                              # Knowledge Graph
    │   ├── __init__.py
    │   ├── client.py                    # KnowledgeGraphClient
    │   ├── compatibility.py
    │   ├── queries/
    │   │   ├── pull.sparql
    │   │   ├── alg1.sparql
    │   │   └── alg2.sparql
    │   └── algorithms/
    │       ├── alg1.py
    │       └── alg2.py
    │
    ├── assembly/                        # Assembly logic
    │   ├── __init__.py
    │   ├── assemble.py
    │   └── validation.py
    │
    ├── utils/                           # Utilities
    │   ├── __init__.py
    │   ├── om.py
    │   └── molecular_fragment_utils.py
    │
    ├── scripts/                         # Scripts
    │   ├── __init__.py
    │   ├── main.py
    │   ├── cavity.py
    │   └── cavity_and_pore_size.py
    │
    ├── tests/                           # Tests
    │   ├── __init__.py
    │   ├── test_kg.py
    │   ├── test_assembly.py
    │   └── test_local_kg_connection.py
    │
    └── tutorials/                       # Tutorials
        ├── __init__.py
        ├── assembly.ipynb
        └── fragmops_tutorial.ipynb
```

---

## 📦 Import Changes

### Core Classes (OntoMOPs)

| Old Import | New Import |
|------------|------------|
| `from ontomops import ChemicalBuildingUnit` | `from twa_mops.core.ontomops import ChemicalBuildingUnit` |
| `from ontomops import AssemblyModel` | `from twa_mops.core.ontomops import AssemblyModel` |
| `from ontomops import MetalOrganicPolyhedron` | `from twa_mops.core.ontomops import MetalOrganicPolyhedron` |
| `from ontomops import GenericBuildingUnit` | `from twa_mops.core.ontomops import GenericBuildingUnit` |
| `from ontomops import GBUCoordinateCenter` | `from twa_mops.core.ontomops import GBUCoordinateCenter` |

### Core Classes (OntoSpecies)

| Old Import | New Import |
|------------|------------|
| `from ontospecies import Geometry` | `from twa_mops.core.ontospecies import Geometry` |
| `from ontospecies import ChemicalSpecies` | `from twa_mops.core.ontospecies import ChemicalSpecies` |

### Geometry Utilities

| Old Import | New Import |
|------------|------------|
| `from geo import Point` | `from twa_mops.core.geo import Point` |
| `from geo import Vector` | `from twa_mops.core.geo import Vector` |
| `from geo import Plane` | `from twa_mops.core.geo import Plane` |

### Knowledge Graph

| Old Import | New Import |
|------------|------------|
| `from twa.kg_operations import PySparqlClient` | `from twa_mops.kg import KnowledgeGraphClient` (recommended) |
| `from twa.kg_operations import PySparqlClient` | `from twa_mops.kg import PySparqlClientCompatibility` (backward compatible) |

### Assembly

| Old Import | New Import |
|------------|------------|
| N/A | `from twa_mops.assembly import assemble_mop` |
| N/A | `from twa_mops.assembly import assemble_mop_from_iris` |
| N/A | `from twa_mops.assembly import validate_cbu, validate_am, validate_mop` |

### Configuration

| Old Import | New Import |
|------------|------------|
| `from twa.conf import config_generic` | `from twa_mops.config import settings` |
| `from mops_conf import DATA_DIR` | `from twa_mops.config import settings; settings.data_dir` |

### Utilities

| Old Import | New Import |
|------------|------------|
| `from om import *` | `from twa_mops.utils.om import *` |
| `from molecular_fragment_utils import *` | `from twa_mops.utils.molecular_fragment_utils import *` |

---

## ⚠️ Breaking Changes

### 1. **Configuration**

**Old:**
```python
from twa.conf import config_generic
endpoint = config_generic.SPARQL_ENDPOINT
data_dir = mops_conf.DATA_DIR
```

**New:**
```python
from twa_mops.config import settings
endpoint = settings.sparql_endpoint
data_dir = settings.data_dir
```

**Migration:**
- Create a `.env` file with your settings:
  ```bash
  SPARQL_ENDPOINT=http://your-endpoint:3838/sparql
  DATA_DIR=./data
  ```
- Or set environment variables before importing

### 2. **SPARQL Client**

**Old:**
```python
from twa.kg_operations import PySparqlClient
sparql_client = PySparqlClient(endpoint, endpoint)
```

**New (Recommended):**
```python
from twa_mops.kg import KnowledgeGraphClient
kg_client = KnowledgeGraphClient(endpoint=settings.sparql_endpoint)
```

**Backward Compatible:**
```python
from twa_mops.kg import PySparqlClientCompatibility
sparql_client = PySparqlClientCompatibility(endpoint, endpoint)
```

### 3. **Pull Methods**

**Old:**
```python
from ontomops import ChemicalBuildingUnit
cbus = ChemicalBuildingUnit.pull_from_kg(iris, sparql_client, recursive_depth=1)
```

**New:**
```python
from twa_mops.core.ontomops import ChemicalBuildingUnit
from twa_mops.kg import KnowledgeGraphClient

kg_client = KnowledgeGraphClient(endpoint=settings.sparql_endpoint)
cbus = kg_client.pull_instances(ChemicalBuildingUnit, iris, depth=1)
```

### 4. **Depth Parameter**

**Old:**
- `recursive_depth=1` (in pull_from_kg)

**New:**
- `depth=1` (in pull_objects, pull_instances, etc.)
- **Recommendation**: Use `depth=3` or `depth=-1` for assembly to ensure all required properties are loaded

---

## ✨ New Features

### 1. **Input Validation**

All inputs are now validated with clear error messages:

```python
from twa_mops.kg import KnowledgeGraphClient

kg_client = KnowledgeGraphClient(endpoint="http://localhost:3838/sparql")

# These will raise ValueError with helpful messages:
kg_client.pull_objects(["invalid-iri"])  # Raises: Invalid IRI format
kg_client.pull_objects([], depth=11)      # Raises: Depth too large
kg_client.execute_query("")              # Raises: Query cannot be empty
```

### 2. **Custom Exceptions**

New exception hierarchy for better error handling:

```python
from twa_mops.kg import KnowledgeGraphError, QueryError, ObjectNotFoundError

try:
    kg_client.pull_objects(iris)
except QueryError as e:
    print(f"Query failed: {e}")
    print(f"Endpoint: {e.endpoint}")
except ObjectNotFoundError as e:
    print(f"Objects not found: {e.iris}")
except KnowledgeGraphError as e:
    print(f"KG error: {e}")
```

### 3. **Performance Optimizations**

#### Batching
```python
# Pull with batching for large IRI lists
kg_client.pull_objects_optimized(large_iri_list, batch_size=50)

# Assembly with batching
kg_client.pull_for_assembly(am_iri, large_cbu_list, batch_size=10)

# Push with batching
kg_client.push_objects(objects, batch_size=10)
```

#### Caching
```python
# LRU caching is automatic (128 entries by default)
kg_client = KnowledgeGraphClient(max_cache_size=256)

# Clear cache when needed
kg_client.clear_cache()

# Prefetch objects into cache
kg_client.prefetch_objects(iris)

# Get cache statistics
stats = kg_client.get_performance_stats()
print(f"Cache hits: {stats['cache_hits']}")
```

#### Retry Logic
```python
# Automatic retries for file operations
kg_client.download_file(remote_path, local_path, max_retries=3, retry_delay=1.0)
kg_client.upload_file(local_path, max_retries=3, retry_delay=1.0)

# Exponential backoff is applied automatically
```

### 4. **Validation Modules**

Use validation functions from the assembly module:

```python
from twa_mops.assembly import validate_cbu, validate_am, validate_mop

validate_cbu(cbu)  # Raises ValueError if invalid
validate_am(am)     # Raises ValueError if invalid
validate_mop(mop)   # Raises ValueError if invalid
```

### 5. **Assembly Convenience Functions**

```python
from twa_mops.assembly import assemble_mop, assemble_mop_from_iris

# Assemble from objects
mop = assemble_mop(am, cbus, provenance, kg_client)

# Assemble directly from IRIs
mop = assemble_mop_from_iris(am_iri, cbu_iris, kg_client, depth=3)
```

---

## 🚀 Migration Steps

### Step 1: Update Imports

Search and replace in your code:

```bash
# Find old imports
find . -name "*.py" -exec grep -l "from ontomops import\|from ontospecies import\|from geo import" {} \;
```

Replace with new imports:
```python
# Old
from ontomops import ChemicalBuildingUnit, AssemblyModel

# New
from twa_mops.core.ontomops import ChemicalBuildingUnit, AssemblyModel
```

### Step 2: Update Configuration

Replace:
```python
# Old
from twa.conf import config_generic
from mops_conf import DATA_DIR

# New
from twa_mops.config import settings

# Use: settings.sparql_endpoint, settings.data_dir, etc.
```

### Step 3: Update SPARQL Client Usage

Replace:
```python
# Old
from twa.kg_operations import PySparqlClient
sparql_client = PySparqlClient(endpoint, endpoint)

# New
from twa_mops.kg import KnowledgeGraphClient
kg_client = KnowledgeGraphClient(endpoint=settings.sparql_endpoint)
```

### Step 4: Update Pull Methods

Replace:
```python
# Old
from ontomops import ChemicalBuildingUnit
cbus = ChemicalBuildingUnit.pull_from_kg(iris, sparql_client, recursive_depth=1)

# New
from twa_mops.core.ontomops import ChemicalBuildingUnit
from twa_mops.kg import KnowledgeGraphClient

kg_client = KnowledgeGraphClient(endpoint=settings.sparql_endpoint)
cbus = kg_client.pull_instances(ChemicalBuildingUnit, iris, depth=1)
```

### Step 5: Update Assembly Calls

Replace:
```python
# Old
from ontomops import MetalOrganicPolyhedron
mop = MetalOrganicPolyhedron.from_assemble(am, cbus, prov, sparql_client=sparql_client)

# New (Option 1: Direct)
from twa_mops.core.ontomops import MetalOrganicPolyhedron
mop = MetalOrganicPolyhedron.from_assemble(am, cbus, prov, sparql_client=kg_client)

# New (Option 2: Using assembly module)
from twa_mops.assembly import assemble_mop
mop = assemble_mop(am, cbus, prov, kg_client=kg_client)

# New (Option 3: From IRIs)
from twa_mops.assembly import assemble_mop_from_iris
mop = assemble_mop_from_iris(am_iri, cbu_iris, kg_client, depth=3)
```

### Step 6: Set Environment Variables

Create a `.env` file in your project root:

```bash
SPARQL_ENDPOINT=http://localhost:3838/sparql
DATA_DIR=./data
FS_URL=http://localhost:8000
```

Or set them in your environment:
```bash
export SPARQL_ENDPOINT=http://localhost:3838/sparql
export DATA_DIR=./data
```

### Step 7: Install Updated Package

```bash
cd /path/to/MOPTools
pip install -e .
```

### Step 8: Run Tests

```bash
# Run all tests
pytest twa_mops/tests/ -v

# Run specific test files
pytest twa_mops/tests/test_kg.py -v
pytest twa_mops/tests/test_assembly.py -v
```

---

## 📝 Code Examples: Before and After

### Example 1: Basic Assembly

**Before:**
```python
from twa.kg_operations import PySparqlClient
from ontomops import AssemblyModel, ChemicalBuildingUnit, MetalOrganicPolyhedron
from twa.conf import config_generic

sparql_client = PySparqlClient(
    config_generic.SPARQL_ENDPOINT,
    config_generic.SPARQL_ENDPOINT
)

am = AssemblyModel.pull_from_kg([am_iri], sparql_client, recursive_depth=1)[0]
cbus = ChemicalBuildingUnit.pull_from_kg(cbu_iris, sparql_client, recursive_depth=1)

mop = MetalOrganicPolyhedron.from_assemble(
    am, cbus, prov, sparql_client=sparql_client
)
```

**After:**
```python
from twa_mops.kg import KnowledgeGraphClient
from twa_mops.core.ontomops import AssemblyModel, ChemicalBuildingUnit, MetalOrganicPolyhedron
from twa_mops.config import settings

kg_client = KnowledgeGraphClient(endpoint=settings.sparql_endpoint)

# Use depth=3 for assembly (recommended)
am = kg_client.pull_instances(AssemblyModel, [am_iri], depth=3)[0]
cbus = kg_client.pull_instances(ChemicalBuildingUnit, cbu_iris, depth=3)

mop = MetalOrganicPolyhedron.from_assemble(
    am, cbus, prov, sparql_client=kg_client
)
```

### Example 2: Using Assembly Module

**Before:**
```python
# No assembly module existed
# Had to use MetalOrganicPolyhedron.from_assemble directly
```

**After:**
```python
from twa_mops.assembly import assemble_mop, assemble_mop_from_iris

# Option 1: From objects
mop = assemble_mop(am, cbus, provenance, kg_client=kg_client)

# Option 2: From IRIs (simpler)
mop = assemble_mop_from_iris(
    am_iri, cbu_iris, kg_client, depth=3
)
```

### Example 3: Error Handling

**Before:**
```python
try:
    cbus = ChemicalBuildingUnit.pull_from_kg(iris, sparql_client)
except Exception as e:
    print(f"Error: {e}")
```

**After:**
```python
from twa_mops.kg import KnowledgeGraphClient, QueryError, ObjectNotFoundError

kg_client = KnowledgeGraphClient(endpoint=settings.sparql_endpoint)

try:
    cbus = kg_client.pull_instances(ChemicalBuildingUnit, iris)
except ObjectNotFoundError as e:
    print(f"Objects not found: {e.iris}")
    print(f"Object type: {e.object_type}")
except QueryError as e:
    print(f"Query failed: {e}")
    print(f"Endpoint: {e.endpoint}")
except Exception as e:
    print(f"Error: {e}")
```

### Example 4: Validation

**Before:**
```python
# No built-in validation
# Had to manually check properties
```

**After:**
```python
from twa_mops.kg import KnowledgeGraphClient
from twa_mops.assembly import validate_cbu, validate_am

kg_client = KnowledgeGraphClient(endpoint=settings.sparql_endpoint)

# Input validation is automatic
cbus = kg_client.pull_instances(ChemicalBuildingUnit, iris, depth=3)

# Explicit validation
validate_cbu(cbus[0])  # Raises ValueError if invalid
validate_am(am)        # Raises ValueError if invalid
```

### Example 5: Performance Optimization

**Before:**
```python
# Multiple separate queries
for iri in iris:
    obj = SomeClass.pull_from_kg([iri], sparql_client)
```

**After:**
```python
from twa_mops.kg import KnowledgeGraphClient

kg_client = KnowledgeGraphClient(endpoint=settings.sparql_endpoint)

# Single batched query (automatic)
objects = kg_client.pull_objects(iris)

# Or with optimization
objects = kg_client.pull_objects_optimized(iris, batch_size=50, prefetch=True)
```

---

## 🎯 Recommendations

### For Assembly Operations

1. **Use depth=3 or depth=-1** for assembly to ensure all required properties are loaded
2. **Use pull_for_assembly()** for pulling AM + CBUs together with proper validation
3. **Use assemble_mop_from_iris()** for the simplest assembly workflow

### For Performance

1. **Enable caching** (enabled by default with max_cache_size=128)
2. **Use batching** for large IRI lists (batch_size=50-100 is good)
3. **Prefetch** objects you know you'll need soon
4. **Reuse kg_client** instances (they maintain cache and connection pools)

### For Error Handling

1. **Catch specific exceptions** (QueryError, ObjectNotFoundError, InvalidObjectError)
2. **Check warnings** for shallow depth and missing IRIs
3. **Validate inputs** early to fail fast

---

## 📞 Support

If you encounter issues during migration:

1. Check the error message - it likely tells you exactly what's wrong
2. Review the examples in this guide
3. Check the updated README.md for more information
4. Run the tests to verify your setup: `pytest twa_mops/tests/ -v`

---

*Migration Guide v1.0 - Last Updated: 2026-06-23*
