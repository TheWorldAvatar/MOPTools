# CLI Vibe Session Guide: Adding xyzrender Visualization for GBUs and AssemblyModels

---
**Context:**
You are working in the `local-twa-integration` branch of [MOPTools](https://github.com/TheWorldAvatar/MOPTools).
The goal is to **reuse the existing `xyzrender` visualization** (currently used for `MetalOrganicPolyhedra` and `ChemicalBuildingUnits`) for **GeometricBuildingUnits (GBUs)** and **AssemblyModels (AMs)**.

---

---

## **🎯 Objectives**
1. **Analyze** how `xyzrender` is currently implemented for `MetalOrganicPolyhedra`/`ChemicalBuildingUnits`.
2. **Extend** `xyzrender` support to `GeometricBuildingUnit` and `AssemblyModel` classes.
3. **Test** the changes with real data from your Knowledge Graph (KG).

---

---

## **📌 Prerequisites**
- Your repo is cloned and up-to-date:
  ```bash
  git checkout local-twa-integration
  git pull origin local-twa-integration
