"""Pytest configuration for MOPTools.

Mocks external dependencies (rdkit, openbabel) that may not be installed.
"""

import sys
from unittest.mock import MagicMock

# Mock external dependencies before any imports
for mod in ['rdkit', 'rdkit.Chem', 'rdkit.Chem.rdmolfiles', 
            'rdkit.Contrib', 'rdkit.Contrib.SA_Score', 'openbabel']:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()
