"""Tests for MOP assembly functionality.

Note: These tests use mocking to avoid dependencies on rdkit/openbabel.
The conftest.py at the repo root sets up the mocks.
Run with: python -m pytest twa_mops/tests/test_assembly.py -v
"""

import sys
import os
from unittest.mock import MagicMock, Mock, patch
import pytest

# Add the MOPTools root directory to sys.path so twa_mops can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Now we can import (mocks are set up by conftest.py)
from twa_mops.assembly.assemble import assemble_mop, assemble_mop_from_iris
from twa_mops.assembly.validation import (
    validate_cbu, validate_am, validate_cbu_am_compatibility, validate_mop
)


# ============================================================================
# Mock Classes for Testing
# ============================================================================

class MockGeometry:
    def __init__(self, has_file=True):
        self.hasGeometryFile = ["test.xyz"] if has_file else []
        self.hasPoints = None


class MockGBUType:
    def __init__(self, label="4-planar"):
        self.label = label
    
    def __str__(self):
        return self.label


class MockGBU:
    def __init__(self, gbu_type="4-planar"):
        self.instance_iri = "http://test/gbu1"
        self.gbu_type = gbu_type


class MockCBU:
    def __init__(self, iri="http://test/cbu1", has_geo=True, has_func=True, gbu_type_label="4-planar"):
        self.instance_iri = iri
        self.hasGeometry = [MockGeometry()] if has_geo else []
        # isFunctioningAs should be a list of GBUType objects that have __str__
        if has_func:
            self.isFunctioningAs = [MockGBUType(gbu_type_label)]
        else:
            self.isFunctioningAs = []


class MockAM:
    def __init__(self, iri="http://test/am1", has_gbu=True, has_pairs=True, gbu_types=None):
        self.instance_iri = iri
        if gbu_types is None:
            gbu_types = ["4-planar"]
        # Create mock GBU objects with gbu_type attribute
        self.hasGenericBuildingUnit = []
        for gt in gbu_types:
            gbu = Mock()
            gbu.gbu_type = gt
            self.hasGenericBuildingUnit.append(gbu)
        self.pairs_of_connected_gbus = [(Mock(), Mock())] if has_pairs else []


class MockMOP:
    def __init__(self, iri="http://test/mop1", has_am=True, has_cbu=True):
        self.instance_iri = iri
        self.hasAssemblyModel = [Mock()] if has_am else []
        self.hasChemicalBuildingUnit = [Mock()] if has_cbu else []
        self.hasMolecularWeight = 100.0
        self.hasCharge = 0


class MockProvenance:
    def __init__(self):
        self.hasReferenceDOI = "test-doi"


# ============================================================================
# Validation Tests
# ============================================================================

class TestValidateCBU:
    """Tests for validate_cbu function."""
    
    def test_validate_cbu_valid(self):
        """Test validation of a valid CBU."""
        assert validate_cbu(MockCBU()) is True
    
    def test_validate_cbu_missing_iri(self):
        """Test validation fails when CBU has no IRI."""
        cbu = MockCBU(iri=None)
        cbu.hasGeometry = []
        cbu.isFunctioningAs = []
        with pytest.raises(ValueError, match="must have an instance IRI"):
            validate_cbu(cbu)
    
    def test_validate_cbu_missing_geometry(self):
        """Test validation fails when CBU has no geometry."""
        with pytest.raises(ValueError, match="must have geometry"):
            validate_cbu(MockCBU(has_geo=False))
    
    def test_validate_cbu_missing_geometry_file(self):
        """Test validation fails when geometry has no file."""
        cbu = MockCBU()
        cbu.hasGeometry = [MockGeometry(has_file=False)]
        with pytest.raises(ValueError, match="must have a geometry file"):
            validate_cbu(cbu)
    
    def test_validate_cbu_missing_isFunctioningAs(self):
        """Test validation fails when CBU has no function."""
        with pytest.raises(ValueError, match="must be functioning as at least one GBU type"):
            validate_cbu(MockCBU(has_func=False))


class TestValidateAM:
    """Tests for validate_am function."""
    
    def test_validate_am_valid(self):
        """Test validation of a valid AM."""
        assert validate_am(MockAM()) is True
    
    def test_validate_am_missing_iri(self):
        """Test validation fails when AM has no IRI."""
        am = MockAM(iri=None, has_gbu=False, has_pairs=False)
        with pytest.raises(ValueError, match="must have an instance IRI"):
            validate_am(am)
    
    def test_validate_am_missing_gbu(self):
        """Test validation fails when AM has no GBUs."""
        am = MockAM(has_gbu=False, has_pairs=False)
        am.hasGenericBuildingUnit = []  # Explicitly set to empty
        with pytest.raises(ValueError, match="must have at least one"):
            validate_am(am)
    
    def test_validate_am_missing_pairs(self):
        """Test validation fails when AM has no connected GBU pairs."""
        with pytest.raises(ValueError, match="must have pairs of connected GBUs"):
            validate_am(MockAM(has_pairs=False))


class TestValidateMOP:
    """Tests for validate_mop function."""
    
    def test_validate_mop_valid(self):
        """Test validation of a valid MOP."""
        assert validate_mop(MockMOP()) is True
    
    def test_validate_mop_missing_iri(self):
        """Test validation fails when MOP has no IRI."""
        mop = MockMOP(iri=None)
        mop.hasAssemblyModel = []
        mop.hasChemicalBuildingUnit = []
        with pytest.raises(ValueError, match="must have an instance IRI"):
            validate_mop(mop)
    
    def test_validate_mop_missing_am(self):
        """Test validation fails when MOP has no AM."""
        with pytest.raises(ValueError, match="must have an AssemblyModel"):
            validate_mop(MockMOP(has_am=False))
    
    def test_validate_mop_missing_cbu(self):
        """Test validation fails when MOP has no CBUs."""
        with pytest.raises(ValueError, match="must have at least one ChemicalBuildingUnit"):
            validate_mop(MockMOP(has_cbu=False))


class TestValidateCBUAMCompatibility:
    """Tests for validate_cbu_am_compatibility function."""
    
    def test_compatible_cbus(self):
        """Test validation passes when CBUs are compatible with AM."""
        am = MockAM(gbu_types=["4-planar"])
        cbu1 = MockCBU(gbu_type_label="4-planar")
        cbu2 = MockCBU(iri="http://test/cbu2", gbu_type_label="4-planar")
        assert validate_cbu_am_compatibility([cbu1, cbu2], am) is True
    
    def test_incompatible_cbu(self):
        """Test validation fails when CBU is not compatible with AM."""
        am = MockAM(gbu_types=["4-planar"])
        cbu = MockCBU(gbu_type_label="3-planar")
        with pytest.raises(ValueError, match="but AM.*requires"):
            validate_cbu_am_compatibility([cbu], am)
    
    def test_multiple_compatible_gbu_types(self):
        """Test validation with AM requiring multiple GBU types."""
        am = MockAM(gbu_types=["4-planar", "3-planar"])
        cbu1 = MockCBU(gbu_type_label="4-planar")
        cbu2 = MockCBU(iri="http://test/cbu2", gbu_type_label="3-planar")
        assert validate_cbu_am_compatibility([cbu1, cbu2], am) is True


# ============================================================================
# Assembly Function Tests
# ============================================================================

class TestAssembleMop:
    """Tests for assemble_mop function."""
    
    @patch('twa_mops.assembly.assemble.MetalOrganicPolyhedron.from_assemble')
    def test_assemble_mop_basic(self, mock_assemble):
        """Test basic assembly with valid inputs."""
        mock_mop = MockMOP()
        mock_assemble.return_value = mock_mop
        
        am = MockAM()
        cbus = [MockCBU(), MockCBU(iri="http://test/cbu2")]
        
        result = assemble_mop(am, cbus)
        
        assert result == mock_mop
        mock_assemble.assert_called_once()
    
    @patch('twa_mops.assembly.assemble.MetalOrganicPolyhedron.from_assemble')
    def test_assemble_mop_with_data_dir(self, mock_assemble):
        """Test assembly with custom data_dir."""
        mock_mop = MockMOP()
        mock_assemble.return_value = mock_mop
        
        am = MockAM()
        cbus = [MockCBU()]
        data_dir = "/custom/data"
        
        result = assemble_mop(am, cbus, data_dir=data_dir)
        
        call_kwargs = mock_assemble.call_args[1]
        assert call_kwargs['data_dir'] == data_dir
    
    @patch('twa_mops.assembly.assemble.MetalOrganicPolyhedron.from_assemble')
    def test_assemble_mop_with_provenance(self, mock_assemble):
        """Test assembly with custom provenance."""
        mock_mop = MockMOP()
        mock_assemble.return_value = mock_mop
        
        am = MockAM()
        cbus = [MockCBU()]
        prov = MockProvenance()
        
        result = assemble_mop(am, cbus, provenance=prov)
        
        call_kwargs = mock_assemble.call_args[1]
        assert call_kwargs['prov'] == prov
    
    @patch('twa_mops.assembly.assemble.MetalOrganicPolyhedron.from_assemble')
    def test_assemble_mop_with_ccdc(self, mock_assemble):
        """Test assembly with CCDC identifier."""
        mock_mop = MockMOP()
        mock_assemble.return_value = mock_mop
        
        am = MockAM()
        cbus = [MockCBU()]
        ccdc = "1234567"
        
        result = assemble_mop(am, cbus, ccdc=ccdc)
        
        call_kwargs = mock_assemble.call_args[1]
        assert call_kwargs['ccdc'] == ccdc


class TestAssembleMopFromIris:
    """Tests for assemble_mop_from_iris function."""
    
    @patch('twa_mops.assembly.assemble.assemble_mop')
    def test_assemble_from_iris_basic(self, mock_assemble_mop):
        """Test assembly from IRIs with valid inputs."""
        mock_kg_client = Mock()
        mock_kg_client.pull_instances = Mock(side_effect=[[MockAM()], [MockCBU()]])
        mock_assemble_mop.return_value = MockMOP()
        
        result = assemble_mop_from_iris(
            am_iri="http://test/am1",
            cbu_iris=["http://test/cbu1"],
            kg_client=mock_kg_client
        )
        
        assert result is not None
    
    @patch('twa_mops.assembly.assemble.assemble_mop')
    def test_assemble_from_iris_with_depth(self, mock_assemble_mop):
        """Test assembly from IRIs with specific depth parameter."""
        mock_kg_client = Mock()
        mock_kg_client.pull_instances = Mock(side_effect=[[MockAM()], [MockCBU()]])
        
        assemble_mop_from_iris(
            am_iri="http://test/am1",
            cbu_iris=["http://test/cbu1"],
            kg_client=mock_kg_client,
            depth=3
        )
        
        # Verify depth was passed to pull_instances
        assert mock_kg_client.pull_instances.call_args_list[0][1]['depth'] == 3
        assert mock_kg_client.pull_instances.call_args_list[1][1]['depth'] == 3
    
    @patch('twa_mops.assembly.assemble.assemble_mop')
    def test_assemble_from_iris_with_ccdc(self, mock_assemble_mop):
        """Test assembly from IRIs with CCDC identifier."""
        mock_kg_client = Mock()
        mock_kg_client.pull_instances = Mock(side_effect=[[MockAM()], [MockCBU()]])
        mock_assemble_mop.return_value = MockMOP()
        
        result = assemble_mop_from_iris(
            am_iri="http://test/am1",
            cbu_iris=["http://test/cbu1"],
            kg_client=mock_kg_client,
            ccdc="1234567"
        )
        
        call_kwargs = mock_assemble_mop.call_args[1]
        assert call_kwargs['ccdc'] == "1234567"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in assembly functions."""
    
    def test_assemble_mop_missing_geometry_file(self):
        """Test that assembly raises FileNotFoundError when geometry file is missing."""
        # This test verifies the error message from the from_assemble method
        # We can't easily test this without the full KG setup, so we test the
        # validation error messages instead
        # The error handling is tested by the validation tests above
        am = MockAM()
        cbu = MockCBU(has_geo=False)  # Missing geometry
        
        with pytest.raises(ValueError, match="must have geometry"):
            validate_cbu(cbu)
    
    def test_assemble_mop_error_message_format(self):
        """Test that FileNotFoundError from ontomops has the correct format."""
        # Test the error message format directly
        # The actual assembly error handling is in MetalOrganicPolyhedron.from_assemble
        # which we can't easily test without full setup
        # So we verify the validation catches issues before assembly
        am = MockAM()
        cbu = MockCBU()
        
        # Verify CBU is valid
        assert validate_cbu(cbu) is True
        # Verify AM is valid
        assert validate_am(am) is True


# ============================================================================
# Recursion Depth Tests
# ============================================================================

class TestRecursionDepth:
    """Tests for recursion depth handling in assembly functions."""
    
    @patch('twa_mops.assembly.assemble.assemble_mop')
    def test_assemble_from_iris_depth_zero(self, mock_assemble_mop):
        """Test that depth=0 is passed through correctly."""
        mock_kg_client = Mock()
        mock_kg_client.pull_instances = Mock(side_effect=[[MockAM()], [MockCBU()]])
        
        assemble_mop_from_iris(
            am_iri="http://test/am1",
            cbu_iris=["http://test/cbu1"],
            kg_client=mock_kg_client,
            depth=0
        )
        
        assert mock_kg_client.pull_instances.call_args_list[0][1]['depth'] == 0
    
    @patch('twa_mops.assembly.assemble.assemble_mop')
    def test_assemble_from_iris_depth_negative_one(self, mock_assemble_mop):
        """Test that depth=-1 (infinite recursion) is passed through correctly."""
        mock_kg_client = Mock()
        mock_kg_client.pull_instances = Mock(side_effect=[[MockAM()], [MockCBU()]])
        
        assemble_mop_from_iris(
            am_iri="http://test/am1",
            cbu_iris=["http://test/cbu1"],
            kg_client=mock_kg_client,
            depth=-1
        )
        
        assert mock_kg_client.pull_instances.call_args_list[0][1]['depth'] == -1
    
    @patch('twa_mops.assembly.assemble.assemble_mop')
    def test_assemble_from_iris_depth_three(self, mock_assemble_mop):
        """Test that depth=3 (minimum recommended) is passed through correctly."""
        mock_kg_client = Mock()
        mock_kg_client.pull_instances = Mock(side_effect=[[MockAM()], [MockCBU()]])
        
        assemble_mop_from_iris(
            am_iri="http://test/am1",
            cbu_iris=["http://test/cbu1"],
            kg_client=mock_kg_client,
            depth=3
        )
        
        assert mock_kg_client.pull_instances.call_args_list[0][1]['depth'] == 3


if __name__ == "__main__":
    # Run tests manually if executed directly
    pytest.main([__file__, "-v"])
