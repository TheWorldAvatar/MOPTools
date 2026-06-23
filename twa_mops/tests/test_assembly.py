"""Tests for MOP assembly functionality.

Note: These tests use mocking to avoid dependencies on rdkit/openbabel.
The conftest.py at the repo root sets up the mocks.
Run with: python -m pytest twa_mops/tests/test_assembly.py -v
"""

import sys
import os
from unittest.mock import MagicMock, Mock, patch

# Add the MOPTools root directory to sys.path so twa_mops can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Now we can import (mocks are set up by conftest.py)
from twa_mops.assembly.validation import validate_cbu, validate_am, validate_mop


# Mock classes
class MockGeometry:
    def __init__(self):
        self.hasGeometryFile = ["test.xyz"]


class MockCBU:
    def __init__(self, iri="http://test/cbu1", has_geo=True, has_func=True):
        self.instance_iri = iri
        self.hasGeometry = [MockGeometry()] if has_geo else []
        self.isFunctioningAs = [Mock()] if has_func else []


class MockGBU:
    def __init__(self):
        self.instance_iri = "http://test/gbu1"


class MockAM:
    def __init__(self, iri="http://test/am1", has_gbu=True, has_pairs=True):
        self.instance_iri = iri
        self.hasGenericBuildingUnit = [MockGBU()] if has_gbu else []
        self.pairs_of_connected_gbus = [(Mock(), Mock())] if has_pairs else []


class MockMOP:
    def __init__(self, iri="http://test/mop1", has_am=True, has_cbu=True):
        self.instance_iri = iri
        self.hasAssemblyModel = [Mock()] if has_am else []
        self.hasChemicalBuildingUnit = [Mock()] if has_cbu else []
        self.hasMolecularWeight = 100.0
        self.hasCharge = 0


# Tests
def test_validate_cbu_valid():
    assert validate_cbu(MockCBU()) is True


def test_validate_cbu_missing_iri():
    cbu = MockCBU(iri=None)
    cbu.hasGeometry = []
    cbu.isFunctioningAs = []
    try:
        validate_cbu(cbu)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must have an instance IRI" in str(e)


def test_validate_cbu_missing_geometry():
    try:
        validate_cbu(MockCBU(has_geo=False))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must have geometry" in str(e)


def test_validate_am_valid():
    assert validate_am(MockAM()) is True


def test_validate_am_missing_gbu():
    try:
        validate_am(MockAM(has_gbu=False))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must have at least one GenericBuildingUnit" in str(e)


def test_validate_mop_valid():
    assert validate_mop(MockMOP()) is True


def test_validate_mop_missing_am():
    try:
        validate_mop(MockMOP(has_am=False))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must have an AssemblyModel" in str(e)


if __name__ == "__main__":
    # Run tests manually if executed directly
    import pytest
    pytest.main([__file__, "-v"])
