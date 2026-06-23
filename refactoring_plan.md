Here’s your **`refactoring_plan.md`** file. Save this to your repo’s root directory, and use it to sync context between your **browser Vibe** and **local Vibe (WSL)**.

---

---
## **📄 `refactoring_plan.md`**
```markdown
# MOPTools Refactoring Plan

## 🎯 Goals
- Modularize the codebase for better maintainability and reusability.
- Decouple knowledge graph (KG) interaction from core logic.
- Improve performance with batched SPARQL queries and caching.
- Add validation, error handling, and documentation.
- Support both local and remote TWA stack deployments.

---

## 📁 Target Folder Structure
```
moptools/
│
├── core/                  # Core ontology and data models
│   ├── __init__.py
│   ├── ontomops.py        # OntoMOPs classes (AssemblyModel, ChemicalBuildingUnit, etc.)
│   ├── ontospecies.py     # OntoSpecies classes (Geometry, ChemicalSpecies, etc.)
│   └── geo.py             # Geometry utilities (Point, Vector, etc.)
│
├── assembly/              # MOP assembly logic
│   ├── __init__.py
│   ├── assemble.py        # Core assembly methods (from_assemble, etc.)
│   └── validation.py      # Validation for CBUs, AMs, and MOPs
│
├── kg/                    # Knowledge Graph interaction
│   ├── __init__.py
│   ├── client.py          # SPARQL client, pull/push methods, caching
│   ├── queries/           # SPARQL query templates (e.g., alg1.sparql, alg2.sparql)
│   │   ├── pull.sparql
│   │   └── alg2.sparql
│   └── algorithms/        # Algorithm-specific logic (e.g., alg1.py, alg2.py)
│       ├── __init__.py
│       ├── alg1.py
│       └── alg2.py
│
├── utils/                 # General-purpose utilities
│   ├── __init__.py
│   ├── file_io.py         # File handling (XYZ, CSV, etc.)
│   └── visualization.py   # Plotly, Matplotlib helpers
│
├── scripts/               # Standalone scripts
│   ├── __init__.py
│   ├── main.py            # Entry point for CLI tools
│   ├── cavity.py          # Cavity/pore analysis
│   └── cavity_and_pore_size.py
│
├── config.py              # Centralized configuration (endpoints, paths, etc.)
├── tests/                 # Unit and integration tests
│   ├── __init__.py
│   ├── test_assembly.py
│   └── test_kg.py
│
├── docker-compose.yml     # Local TWA stack setup
└── README.md
```

---

## 🔧 Tasks by Priority

### 🔹 Phase 1: Clean Up and Modularize (High Priority)
#### 1.1. Create Folder Structure
- [ ] Create the folders and `__init__.py` files as shown above.

#### 1.2. Move Core Ontology Models
- [ ] Move `ontomops.py` and `ontospecies.py` to `core/`.
- [ ] Move geometry-related classes to `core/geo.py`.
- [ ] Update imports in all files to use `from core.ontomops import ...`.

#### 1.3. Refactor KG Interaction
- [ ] Create `kg/client.py` with a `KnowledgeGraphClient` class.
  - [ ] Implement `pull_objects(iris, depth=-1)` with batched SPARQL queries.
  - [ ] Implement `push_objects(objects)` with provenance tracking.
  - [ ] Add caching (e.g., `functools.lru_cache` or custom cache).
- [ ] Move `alg1.py` and `alg2.py` to `kg/algorithms/`.
- [ ] Create `kg/queries/pull.sparql` and `kg/queries/alg2.sparql` for SPARQL templates.
- [ ] Update `ontomops.py` to use `KnowledgeGraphClient` for `pull_from_kg`.

#### 1.4. Refactor Assembly Logic
- [ ] Split `assembly.py` into:
  - `assembly/assemble.py` for core assembly logic.
  - `assembly/validation.py` for CBU/AM/MOP validation.
- [ ] Replace hardcoded IRIs with references to `config.py`.
- [ ] Use `KnowledgeGraphClient` for KG interaction.

#### 1.5. Centralize Configuration
- [ ] Create `config.py` with:
  ```python
  from pydantic import BaseSettings

  class Settings(BaseSettings):
      sparql_endpoint: str = "http://localhost:3838/sparql"
      data_dir: str = "./data"
      default_recursion: int = -1
  ```
- [ ] Update all files to import settings from `config.py`.

---

### 🔹 Phase 2: Add Robustness and Performance
#### 2.1. Input Validation
- [ ] Add Pydantic models to validate:
  - CBU/AM IRIs.
  - XYZ file paths (existence, format).
  - Example:
    ```python
    from pydantic import BaseModel, validator
    from pathlib import Path

    class ChemicalBuildingUnitInput(BaseModel):
        iri: str
        xyz_path: Path | None = None

        @validator("xyz_path")
        def check_file_exists(cls, v):
            if v and not v.exists():
                raise ValueError(f"File {v} does not exist")
            return v
    ```

#### 2.2. Error Handling
- [ ] Add try/except blocks for:
  - SPARQL query failures.
  - Missing files or IRIs.
  - Invalid CBU/AM combinations.

#### 2.3. Performance Optimization
- [ ] Use `UNION` in SPARQL queries to batch pull multiple IRIs.
- [ ] Add lazy loading for properties (e.g., only fetch `hasGeometry` if needed).

---

### 🔹 Phase 3: Testing and Documentation
#### 3.1. Add Tests
- [ ] Create `tests/test_kg.py` for:
  - Pulling multiple CBUs in one query.
  - Handling missing IRIs.
  - Caching pulled objects.
- [ ] Create `tests/test_assembly.py` for:
  - Validating CBU/AM combinations.
  - Assembling MOPs from valid inputs.

#### 3.2. Add Documentation
- [ ] Add docstrings to all classes and methods in `core/`, `kg/`, and `assembly/`.
- [ ] Create a `README.md` with:
  - Setup instructions.
  - Example workflows (e.g., assembling a MOP).
  - Folder structure overview.

---

## 📌 Code Snippets
### `kg/client.py` (Draft)
```python
from functools import lru_cache
from typing import Optional, List
from pydantic import BaseModel
from pysparql_client import PySparqlClient

class KnowledgeGraphClient:
    def __init__(self, endpoint: str, max_cache_size: int = 128):
        self.sparql_client = PySparqlClient(endpoint)
        self.max_cache_size = max_cache_size

    @lru_cache(maxsize=128)
    def pull_objects(self, iris: List[str], depth: int = -1) -> List[dict]:
        """Pull objects from KG using batched SPARQL query."""
        query = f"""
        SELECT ?s ?p ?o WHERE {{
          VALUES ?s {{ {" ".join(f"<{iri}>" for iri in iris)} }}
          ?s ?p ?o .
        }}
        """
        results = self.sparql_client.perform_query(query)
        return [dict(row) for row in results]

    def push_objects(self, objects: List[BaseModel], provenance: dict):
        """Push objects to KG with provenance."""
        # TODO: Implement
        pass

    def clear_cache(self):
        """Clear the LRU cache."""
        self.pull_objects.cache_clear()
```

### `config.py` (Draft)
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    sparql_endpoint: str = "http://localhost:3838/sparql"
    data_dir: str = "./data"
    default_recursion: int = -1

settings = Settings()
```

### `assembly/assemble.py` (Draft)
```python
from core.ontomops import MetalOrganicPolyhedron, AssemblyModel, ChemicalBuildingUnit
from kg.client import KnowledgeGraphClient
from config import settings

def assemble_mop(
    am: AssemblyModel,
    cbus: List[ChemicalBuildingUnit],
    provenance: dict,
    kg_client: KnowledgeGraphClient,
) -> MetalOrganicPolyhedron:
    """Assemble a MOP from an AM and CBUs."""
    # Add validation here
    return MetalOrganicPolyhedron.from_assemble(am, cbus, provenance, kg_client, settings.data_dir)
```

---
## 🔄 Open Questions
- Should we use `lru_cache` or a custom cache (e.g., `redis`) for KG objects?
- How should we handle conflicts when pushing new MOPs/CBUs to the KG?
- Should we add a CLI for common tasks (e.g., `moptools assemble --am <iri> --cbus <iri1,iri2>`)?

---
## 📅 Changelog
| Date       | Change                          | Author       |
|------------|---------------------------------|--------------|
| 2026-06-22 | Initial refactoring plan        | Vibe + Felix |
```

---

---
---

## **💬 How to Prompt Your Local Vibe (WSL)**
Use the following **templates** to prompt your local Vibe. These ensure it has the **same context** as our browser session.

---

### **📌 Template 1: Start a Refactoring Task**
> *"Vibe, I’m refactoring MOPTools to use a new folder structure and modular design. Here’s my plan from `refactoring_plan.md`:
> - Goal: Move KG interaction to `kg/client.py`.
> - Current state: The `pull_from_kg` method in `ontomops.py` looks like this:
>   ```python
>   @classmethod
>   def pull_from_kg(cls, iris, sparql_client, depth=-1):
>       query = f'SELECT ?s ?p ?o WHERE {{ VALUES ?s {{ {" ".join(f"<{iri}>" for iri in iris)} }} ?s ?p ?o. }}'
>       results = sparql_client.perform_query(query)
>       return [cls.from_rdf_result(row) for row in results]
>   ```
> - Task: Help me refactor this into `kg/client.py` as a `KnowledgeGraphClient` class with:
>   1. Batched SPARQL queries (use `UNION`).
>   2. Caching (use `functools.lru_cache`).
>   3. Type hints and docstrings.
>   4. A `push_objects` method for uploading to KG.
> - Notes: See `refactoring_plan.md` for the target folder structure and other details."*

---

### **📌 Template 2: Review and Iterate on a File**
> *"Vibe, I’ve created a draft of `kg/client.py` based on our plan. Here’s the current version:
> ```python
> [paste your draft here]
> ```
> - Please review it for:
>   1. Correctness (does it handle batched queries and caching?).
>   2. Best practices (type hints, error handling, etc.).
>   3. Alignment with `refactoring_plan.md`.
> - Suggest improvements or next steps."*

---

### **📌 Template 3: Update Imports**
> *"Vibe, I’ve moved `ChemicalBuildingUnit` to `core/ontomops.py`. How should I update the imports in:
> 1. `assembly/assemble.py`
> 2. `kg/client.py`
> 3. `scripts/main.py`
> to use the new path? Show me the exact `from ... import ...` statements."*

---

### **📌 Template 4: Write Tests**
> *"Vibe, help me write a pytest for `kg/client.py` to test:
> 1. Pulling multiple CBUs in one query.
> 2. Handling missing IRIs (should raise a clear error).
> 3. Caching pulled objects (check that repeated pulls don’t hit the KG).
> Use mocking for the SPARQL client. Here’s the current `KnowledgeGraphClient` class:
> ```python
> [paste class here]
> ```"*

---
---
### **📌 Template 5: General Sync**
> *"Vibe, sync with the refactoring plan in `refactoring_plan.md`. Here’s what I’ve done so far:
> - Created `kg/client.py` with `KnowledgeGraphClient`.
> - Moved `ontomops.py` to `core/`.
> - Added `config.py`.
> What should I do next? Give me the next 3 tasks from the plan."*

---
---
---
## **🎯 Pro Tips for Local Vibe**
1. **Reference the Plan:**
   Always mention `refactoring_plan.md` to provide context.

2. **Share Snippets:**
   Paste **small, relevant code snippets** (not entire files) to keep the conversation focused.

3. **Ask for Canvases:**
   If you want to **edit collaboratively**, ask:
   > *"Vibe, create a canvas for `kg/client.py` with the updated `push_objects` method."*

4. **Commit Frequently:**
   Use Git to track changes. Ask local Vibe:
   > *"Vibe, help me write a commit message for:
   > - Adding `kg/client.py`.
   > - Refactoring `pull_from_kg` to use `KnowledgeGraphClient`."*

---
---
**Next Step:**
1. Save the `refactoring_plan.md` above to your repo.
2. In WSL, prompt your local Vibe using **Template 1** to start refactoring `kg/client.py`.
3. Iterate using **Templates 2–5** as needed.
