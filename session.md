# MOPTools: Stack Switching Diagnostic & Refactoring Scaffold

**Updated for `local-twa-integration` Branch**
**Last Updated: 2026-07-03**

---

## **Quick Status Summary**

| Item | Status | Notes | Priority |
|------|--------|-------|----------|
| Stack switching | ✅ Implemented | `switch_stack('local')` or `switch_stack('remote')` | Done |
| Namespace config | ✅ Fixed | Both stacks use `ontomops` for ontology IRIs | Done |
| Assembly notebook | ✅ Updated | Example 1 & 2 use stack switching | Done |
| **ForwardRef fix** | **✅ Implemented** | **Monkey-patch for Pydantic v2 ForwardRef in twa package** | **Done** |
| Remote timeout fix | ❌ Open | `from_assemble()` times out on remote | **P0** |
| GBU/AM visualization | ⏳ Open | Need separate visualization in Example 1 | **P1** |
| Interactive viewing | ⏳ Open | Add `orient()` from xyzrender | **P1** |
| Code cleanup | ⏳ Open | Remove redundant `get_iri_for_stack()` | **P2** |

---

## **Plan for Tomorrow (2026-07-04)**

**Goal:** Fix remote timeout, enhance visualization, clean up code, push to remote

**P0 - CRITICAL (Do first):**
1. Diagnose and fix remote stack timeout in Example 1 `from_assemble()`
   - Add logging/timing to identify bottleneck
   - Test connectivity to remote Blazegraph
   - Implement timeout/retry if needed

**P1 - HIGH (Do next):**
2. Enhance Example 1 visualization
   - Add GBU (GenericBuildingUnit) visualization
   - Add AM (AssemblyModel) visualization  
   - Add interactive `orient()` viewing

**P2 - MEDIUM (Do last):**
3. Code cleanup for lean library
   - Remove redundant `get_iri_for_stack()` calls
   - Simplify stack_utils.py
   - Verify all imports are used
4. Push to `local-twa-integration` branch

---

## **Objective**

Diagnose and resolve issues when switching between **local** and **remote** stacks in `assembly.ipynb`, with a focus on:

- **Timeouts** during MOP assembly on the remote stack.
- **Data download failures** from the remote stack.
- **Seamless switching** between stacks, leveraging the refactored codebase (PySparqlClient, Pydantic OGM, unified config).

---

## **1. Current Context (local-twa-integration Branch)**

### **Key Refactoring Changes**

- **Client**: Migrated to `PySparqlClient` for SPARQL operations, with Pydantic models for OGM validation.
- **Configuration**: Centralized in `mops.env` (SPARQL endpoint, file server URL, auth).
- **OGM**: Pydantic-based classes for schema compliance and synchronization with local/remote KG.
- **Networking**: Local stack uses `localhost:3838`; remote uses `68.183.227.15:3838` and `mops.theworldavatar.io:3838`.
- **Reverse Proxy**: Nginx forwards `80/443` to `3838` for local testing with domain aliases (e.g., `mops.theworldavatar.io` → `127.0.0.1`).

### **Relevant Files**


| File/Module                          | Purpose                                   | Notes                              |
| ------------------------------------ | ----------------------------------------- | ---------------------------------- |
| `twa_mops/mops.env`                  | Environment variables for endpoints, auth | Updated for local/remote switching |
| `twa/kg_operations/sparql_client.py` | SPARQL client (PySparqlClient)            | Timeout/retry logic needed         |
| `twa_mops/ontomops.py`               | OGM for MOPs (Pydantic)                   | `pull_from_kg`, `push_to_kg`       |
| `twa_mops/ontospecies.py`            | OGM for species                           | Geometry file downloads            |
| `assembly.ipynb`                     | Tutorial for MOP assembly                 | Needs stack-switching logic        |


---

## **2. Diagnostic Goals**

### **A. Verify Stack Connectivity**

- **Local Stack**: Test SPARQL query and file download.
- **Remote Stack**: Test SPARQL query and file server access.
- **Nginx/Proxy**: Confirm local domain alias (`mops.theworldavatar.io`) resolves to `127.0.0.1`.

**Test SPARQL Query:**

```sparql
SELECT * WHERE {
  ?cbu a <https://www.theworldavatar.com/kg/ontomops/ChemicalBuildingUnit> .
  ?cbu ?p ?o .
} LIMIT 5
```

**Test File Download:**

```bash
curl -v http://mops.theworldavatar.io:3838/file-server/<example_geometry_file>
```

---

### **B. Diagnose Timeout Issues**

- **Check Timeout Settings**:
  - `sparql_client.py`: Look for `requests.get(..., timeout=...)` or PySparqlClient timeout config.
  - `ontomops.py`: Check `pull_from_kg` and `push_to_kg` for batch/async operations.
- **Log Queries**: Add logging to print SPARQL queries and execution time.
- **Test with Smaller Data**: Try assembling a MOP with fewer CBUs.

**Example Logging Addition:**

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In sparql_client.py or ontomops.py
logger.info(f"Executing SPARQL query: {query}")
start_time = time.time()
response = client.query(query)
logger.info(f"Query executed in {time.time() - start_time:.2f}s")
```

---

### **C. Diagnose Data Download Failures**

- **File Server Access**: Verify remote file server (`FS_URL`) is reachable.
- **Authentication**: Check if `FS_USERNAME`/`FS_PASSWORD` are set in `mops.env`.
- **File Paths**: Ensure KG file paths match remote file server structure.

**Example Download Logic (ontospecies.py):**

```python
def download_geometry_file(self, file_url, local_path):
    auth = (os.getenv("FS_USERNAME"), os.getenv("FS_PASSWORD")) if os.getenv("FS_USERNAME") else None
    try:
        response = requests.get(file_url, auth=auth, timeout=30)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {file_url}: {e}")
        raise
```

---

## **3. Stack Switching Implementation**

### **A. Centralized Configuration**

- **Location**: `twa_mops/config.py` (new) or `mops.env`.
- **Action**: Add a `StackConfig` class to manage stack-specific settings.

**Example:**

```python
# twa_mops/config.py
from pydantic import BaseSettings

class StackConfig(BaseSettings):
    stack_name: str = "remote"  # or "local"
    sparql_endpoint: str
    fs_url: str
    fs_username: str = None
    fs_password: str = None
    timeout: int = 30

    class Config:
        env_file = "mops.env"

stack_config = StackConfig()
```

### **B. Stack Switching Utility**

- **Location**: `twa_mops/stack_utils.py` (new).
- **Action**: Add functions to switch and validate stacks.

**Example:**

```python
# twa_mops/stack_utils.py
from twa_mops.config import stack_config

def switch_stack(stack_name: str):
    if stack_name == "local":
        stack_config.stack_name = "local"
        stack_config.sparql_endpoint = "http://localhost:3838/blazegraph/namespace/ontomops/sparql"
        stack_config.fs_url = "http://localhost:8000/"
    elif stack_name == "remote":
        stack_config.stack_name = "remote"
        stack_config.sparql_endpoint = "http://68.183.227.15:3838/blazegraph/namespace/ontomops_ogm_dummy/sparql"
        stack_config.fs_url = "http://mops.theworldavatar.io:3838/file-server/"
    else:
        raise ValueError(f"Unknown stack: {stack_name}")
    validate_stack_connectivity()

def validate_stack_connectivity():
    # Test SPARQL endpoint
    from twa.kg_operations.sparql_client import SPARQLClient
    client = SPARQLClient(stack_config.sparql_endpoint)
    test_query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"
    try:
        client.query(test_query)
        logger.info(f"SPARQL endpoint {stack_config.sparql_endpoint} is reachable.")
    except Exception as e:
        logger.error(f"SPARQL endpoint {stack_config.sparql_endpoint} failed: {e}")
        raise
```

---

### **C. Update OGM for Stack Awareness**

- **Location**: `ontomops.py`, `ontospecies.py`.
- **Action**: Use `stack_config` for endpoints and timeouts.

**Example (ontomops.py):**

```python
from twa_mops.config import stack_config

class MOP(BaseClass):
    @classmethod
    def pull_from_kg(cls, iri: str):
        client = SPARQLClient(stack_config.sparql_endpoint, timeout=stack_config.timeout)
        # ... rest of the logic
```

---

## **4. Timeout and Retry Logic**

### **A. Configurable Timeouts**

- **Location**: `sparql_client.py`, `ontospecies.py`.
- **Action**: Add timeout parameters to all network calls.

**Example (sparql_client.py):**

```python
class SPARQLClient:
    def __init__(self, endpoint, timeout=30):
        self.endpoint = endpoint
        self.timeout = timeout

    def query(self, query):
        response = requests.post(
            self.endpoint,
            data={"query": query},
            headers={"Content-Type": "application/sparql-query"},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.text
```

### **B. Retry Logic**

- **Library**: Use `tenacity` for retries.
- **Action**: Add retry decorators to network calls.

**Example:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def query_with_retry(self, query):
    return self.query(query)
```

---

## **5. Testing Plan**

### **A. Unit Tests**

- **SPARQL Client**: Test query execution and timeout handling.
- **File Download**: Test download from both stacks.
- **Stack Switching**: Test `switch_stack()` and `validate_stack_connectivity()`.

### **B. Integration Tests**

- **Assembly Workflow**: Run `assembly.ipynb` with both stacks.
  - Log time for each step.
  - Capture errors/warnings.
  - Verify MOP assembly success.

---

## **6. Expected Outcomes**

- **Root Cause**: Identify why remote stack times out (network, auth, query complexity).
- **Fixes**: Implement timeouts, retries, and better error messages.
- **Configuration**: Centralize and validate stack configurations.
- **Documentation**: Update `LOCAL_STACK_SETUP.md` with troubleshooting steps.

---

## **7. CLI Vibe Session Questions**

1. How can I integrate `PySparqlClient` with configurable timeouts and retries?
2. Where should I add logging to track SPARQL queries and file downloads?
3. How do I centralize configuration for both stacks using Pydantic?
4. What’s the best way to validate stack connectivity programmatically?
5. Should I add a fallback mechanism to the local stack if the remote fails?
6. How do I ensure the OGM (Pydantic models) stays in sync with both stacks?

---

## **8. Resources**

- [MOPTools GitHub (local-twa-integration)](https://github.com/TheWorldAvatar/MOPTools/tree/local-twa-integration/)
- [PySparqlClient Docs](https://github.com/TheWorldAvatar/pysparqlclient)
- [Pydantic Docs](https://pydantic-docs.helpmanual.io/)
- [Tenacity (Retry) Docs](https://tenacity.readthedocs.io/)
- [Local Stack Setup Guide](docs/LOCAL_STACK_SETUP.md)

---

## **9. Completed Work**

### **Stack Utilities Enhanced** (`twa_mops/stack_utils.py`)
- Added `namespace` field to stack configurations (local: `ontomops`, remote: `ontomops`)
- Added `get_current_namespace()` function to get the current stack's namespace
- Added `convert_iri_namespace(iri, target_namespace)` function to convert IRIs between namespaces
- Added `get_iri_for_stack(iri, stack_name)` function to get IRIs for a specific stack
- Added `discover_available_iris(stack_name, limit)` function to discover available IRIs from a stack
- **FIXED**: Changed remote stack namespace from `ontomops_ogm_dummy` to `ontomops` (Blazegraph DB namespace in URL remains `ontomops_ogm_dummy`, but ontology data uses `ontomops`)

### **Pydantic v2 ForwardRef Fix** (`twa_mops/core/__init__.py`)
- **PROBLEM**: Pydantic v2 uses ForwardRef for class definitions that reference types defined later in the file. The twa package's `BaseClass.get_object_properties()` and `get_data_properties()` methods didn't handle these, causing `pull_from_kg()` to return incomplete data (only `instance_iri`)
- **SOLUTION**: Added monkey-patch functions that:
  - Evaluate ForwardRef annotations in the class's module namespace
  - Handle `types.GenericAlias` (Python 3.9+ annotations like `HasPolyhedralShape[PolyhedralShape]`)
  - Handle `typing._UnionGenericAlias` (Optional types like `Optional[HasBindingSite[BindingSite]]`)
  - Extract inner types from Optional wrappers to properly detect ObjectProperties and DatatypeProperties
- **RESULT**: `pull_from_kg()` now correctly returns complete objects with all fields populated for both AssemblyModel and ChemicalBuildingUnit

### **Assembly Notebook Updated** (`twa_mops/tutorials/assembly.ipynb`)
- Added stack switching at the beginning with `STACK_NAME` variable (users can change to 'remote')
- Updated imports in Cell 4 to include: `switch_stack, get_client_for_stack, list_stacks, get_current_namespace, get_iri_for_stack`
- Replaced hardcoded KnowledgeGraphClient creation with `get_client_for_stack()`
- Updated Example 1 and Example 2 to use `get_iri_for_stack()` for namespace-aware IRIs
- Added helper function `discover_iris_from_stack()` to allow users to discover available IRIs
- Added stack info printing to show which stack is being used

### **Configuration Files Updated**
- `twa_mops/envs/mops_remote.env`: FS_URL updated to use IP address `http://68.183.227.15:3838/file-server/`
- `twa_mops/stack_utils.py`: Remote fs_url matches the env file

### **Bug Fixes Applied**
- **FIXED**: Remote namespace mismatch - remote stack's ontology data uses `ontomops` namespace, not `ontomops_ogm_dummy`
- **FIXED**: `ObjectNotFoundError` for AssemblyModel by using correct namespace
- **FIXED**: `NameError` for `get_iri_for_stack` by adding complete imports to Cell 4
- **FIXED**: Python bytecode cache cleared to ensure updated code is loaded

----

## **10. Known Issues & Considerations**

### **Namespace Behavior**
- **Blazegraph namespace** (in URL): `ontomops_ogm_dummy` for remote, `ontomops` for local
- **Ontology namespace** (for IRIs): `ontomops` for **both** stacks
- This means `get_iri_for_stack()` is currently redundant (returns same IRI for both stacks)
- Kept for future-proofing if namespace configurations diverge

### **FragMOPs Tutorial**
- `fragmops_tutorial.ipynb` uses separate system with namespace `ontomops_ogm_fragmops`
- This is a different ontology (FragMOPs vs OntoMOPs) and does not need stack switching updates

----

## **11. Testing Status**

- ✅ Stack switching logic implemented and tested
- ✅ Namespace configuration corrected (remote uses `ontomops` for ontology data)
- ✅ IRI conversion functions available and tested
- ✅ Assembly notebook updated with stack switching
- ✅ **ForwardRef monkey-patch implemented and tested** - `pull_from_kg` now returns complete objects
- ✅ **Example 1 assembly works with remote stack** - User verified
- ⏳ Remote stack timeout in `from_assemble()`: Still needs diagnosis

----

## **12. Legacy Next Steps (Original)**

1. Test with remote stack: Restart Jupyter kernel and run all cells in `assembly.ipynb` with `STACK_NAME = 'remote'`
2. Verify AssemblyModel found: The IRI should now be found
3. Optional: Add logging to `sparql_client.py` and `ontomops.py` if debugging is needed
4. Optional: Implement timeout/retry logic for production use

---

**Note**: Update this scaffold with findings, code snippets, and test results as you progress.

---

## **13. Code Cleanup Goals**

**Make Library Lean:**
- **REDUNDANT**: `get_iri_for_stack()` - both stacks use same `ontomops` namespace
- **ACTION**: Remove from stack_utils.py and notebook, use direct IRIs
- **REASON**: Eliminates unnecessary function calls, simplifies code

---

## **14. Open Issues & Tomorrow's Priorities**

### **🔴 P0: Remote Stack Timeout in from_assemble()**
**Issue:** Example 1 works on local stack but fails on remote with timeout during `MetalOrganicPolyhedron.from_assemble()`

**Diagnosis Plan:**
1. Add logging to `ontomops.py` in `from_assemble()` method
2. Check if SPARQL query timeout or file download timeout
3. Test with smaller data to isolate issue
4. Check network connectivity to remote stack
5. Verify remote Blazegraph endpoint response times

**Potential Fixes:**
- Add configurable timeout parameters to `from_assemble()`
- Add retry logic using `tenacity`
- Optimize query patterns (reduce depth, batch requests)
- Implement progressive loading for large assemblies

### **🟡 P1: Enhance Example 1 Visualization**
**Goal:** Highlight GBU and AM visualization separately from MOP/CBU visualization

**Requirements:**
- Add visualization of GBUs from AssemblyModel
- Add visualization of AMs
- Add interactive viewing using `orient()` from xyzrender
- Allow viewing from different angles

**Implementation:**
```python
# After pulling AM and CBUs:
# Visualize each GBU
for gbu_iri in am.hasGenericBuildingUnit:
    gbu = ...  # Retrieve GBU
    display(gbu.visualise())

# Visualize the AM
am_vis = am.visualise()
display(am_vis)

# For final MOP
from xyzrender import orient
mop_vis = new_mop.visualise()
orient(mop_vis)  # Interactive rotation
```

### **🟡 P2: Code Cleanup**
**Goal:** Remove redundant code
- Remove `get_iri_for_stack()` calls from notebook
- Simplify stack_utils.py
- Ensure all imports are used

---

## **15. Commit & Push Strategy**

**Status:** ✅ **Committed** on 2026-07-03

**Commit:** `32c2898` - "Fix Pydantic v2 ForwardRef issues and add stack switching"

**Changes included:**
- ✅ Monkey-patch for BaseClass.get_object_properties() and get_data_properties()
- ✅ Stack switching implementation (stack_utils.py)
- ✅ Updated assembly.ipynb with stack switching
- ✅ Enhanced visualization utilities
- ✅ Updated configuration files

**Next commit targets:**
1. After fixing remote stack timeout in `from_assemble()`
2. After adding GBU/AM visualization
3. After code cleanup

**Push:** To `local-twa-integration` after setting up SSH keys (currently blocked by authentication)

----

## **16. Next Session Action Items**

### **Immediate (2026-07-04):**
1. ✅ **Done:** Diagnose timeout - ForwardRef fix implemented and verified working
2. ⏳ Diagnose remaining timeout: Run Example 1 `from_assemble()` with `STACK_NAME = 'remote'`
3. ⏳ Check connectivity to remote stack
4. ⏳ Add logging to identify bottleneck

### **Short-term:**
1. Fix remote timeout in `from_assemble()`
2. Add GBU/AM visualization to Example 1
3. Add interactive `orient()` viewing
4. Clean up code (remove redundant `get_iri_for_stack()`)
5. Set up SSH keys and push to remote

### **Long-term:**
1. Add comprehensive tests
2. Document stack switching
3. PR to main branch

----

**Note:** Update this scaffold with findings and test results.
