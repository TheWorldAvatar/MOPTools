# MOP Synthesis Prediction

This is a collection of tools that supports the synthesis of novel MOPs that have been suggested via The World Avatar.

## Prerequisites
The TWA library needs to be installed via `pip install twa`. This requires an installation of Python version >= 3.8 and the latest version of Java (e.g., via OpenJDK).
Running the example notebook for geometry retrieval also requires installation of jupyter and pandas library. Fill out credentials file with endpoints and paths.


## Synthesis prediction
- The initial script selectCandidates.py generates a list of synthesis candidates based on reproduced known MOPs, ranking the tuples according to 3 strong and 4 weak criteria.
- The final script predictSynthesis.py predicts a synthesis procedure for a novel MOP based on three known MOPs and their synthesis conditions.


## Measurement analysis
- The analysis script ir_analysis.py plots a measured FTIR spectrum of a MOP against the references of involved materials as the known peaks associated with the MOP for comparison.

## MOP structure retrieval
This is a minimal software package to retrieve metal-organic polyhedra information from the TWA knowledge graph:
- The synthesis retrieval script (retrieve_synthesis.py) transforms the OntoSyn graph for a certain procedure into human readable text and lays out step-by-step synthesis instructions.
- The Jupyter notebook (retrieve_structures.ipynb) establishes a connection to TWA, retrieves a number of MOPs based on specific criteria, and downloads the related geometry files.