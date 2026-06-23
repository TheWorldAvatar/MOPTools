import os
alg1_fpath = os.path.join(os.path.dirname(__file__), "..", "queries", "alg1.sparql")
with open(alg1_fpath, "r") as file:
    alg1 = file.read()
