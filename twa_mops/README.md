# MOPTools

Tools for working with Metal-Organic Polyhedra (MOPs) using the TWA Knowledge Graph.

## Installation

```bash
# Install in development mode (recommended)
pip install -e .

# Or install as a package
pip install .
```

## Quick Start

```python
from twa_mops.kg import KnowledgeGraphClient
from twa_mops.core import ontomops
from twa_mops.config import settings

# Create a client
client = KnowledgeGraphClient(settings.sparql_endpoint)

# Pull objects from KG
cbu_iri = "https://www.theworldavatar.com/kg/ontomops/ChemicalBuildingUnit_..."
cbus = ontomops.ChemicalBuildingUnit.pull_from_kg([cbu_iri], client, recursive_depth=1)

# Or use the new assembly module
from twa_mops.assembly import assemble_mop_from_iris
mop = assemble_mop_from_iris(am_iri, [cbu1_iri, cbu2_iri], client)
```

## Package Structure

```
twa_mops/
├── core/                  # Core ontology and data models
│   ├── ontomops.py        # OntoMOPs classes
│   ├── ontospecies.py     # OntoSpecies classes
│   └── geo.py             # Geometry utilities
├── kg/                    # Knowledge Graph interaction
│   ├── client.py          # KnowledgeGraphClient
│   ├── compatibility.py   # PySparqlClient compatibility layer
│   ├── queries/           # SPARQL query templates
│   └── algorithms/        # Algorithm-specific logic
├── assembly/              # MOP assembly logic
│   ├── assemble.py        # Assembly functions
│   └── validation.py      # Validation functions
├── utils/                 # General-purpose utilities
│   └── om.py              # Ontology of Units
├── scripts/               # Standalone scripts
├── tests/                 # Unit and integration tests
└── tutorials/             # Example notebooks
```
