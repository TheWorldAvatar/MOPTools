"""Tests for visualization module functionality."""

import pytest
from unittest.mock import Mock, patch
import sys
import os
import importlib.util

# Get the path to the visualization module
VISUALIZATION_PATH = os.path.join(os.path.dirname(__file__), "..", "utils", "visualization.py")


def load_visualization_module():
    """Load the visualization module, mocking twa.data_model to avoid conflicts."""
    spec = importlib.util.spec_from_file_location("visualization_test", VISUALIZATION_PATH)
    visualization = importlib.util.module_from_spec(spec)
    
    # Mock the problematic imports
    mock_twa_data_model = Mock()
    mock_kg = Mock()
    mock_twa_data_model.KnowledgeGraph = mock_kg
    mock_twa_data_model.get_object_from_lookup = Mock(return_value=Mock())
    
    with patch.dict('sys.modules', {
        'twa.data_model': mock_twa_data_model,
        'twa.data_model.base_ontology': mock_twa_data_model
    }):
        spec.loader.exec_module(visualization)
    
    return visualization


class TestVisualizationImports:
    """Test that visualization module imports correctly."""
    
    def test_visualization_module_imports(self):
        """Test that visualisation module can be imported."""
        viz = load_visualization_module()
        
        assert hasattr(viz, 'visualise_mop')
        assert hasattr(viz, 'visualise_cbu')
        assert hasattr(viz, 'visualise_am')
        assert hasattr(viz, 'VisualizationError')
        assert hasattr(viz, 'BackendNotAvailableError')
        assert hasattr(viz, 'InvalidGeometryError')
    
    def test_backend_availability_flags(self):
        """Test that backend availability flags are set correctly."""
        viz = load_visualization_module()
        assert viz.XYZRENDER_AVAILABLE or viz.PLOTLY_AVAILABLE


class TestVisualizationExceptions:
    """Test custom exceptions."""
    
    def test_visualization_error_hierarchy(self):
        """Test exception hierarchy."""
        viz = load_visualization_module()
        assert issubclass(viz.BackendNotAvailableError, viz.VisualizationError)
        assert issubclass(viz.InvalidGeometryError, viz.VisualizationError)
    
    def test_exception_messages(self):
        """Test exception messages."""
        viz = load_visualization_module()
        
        error1 = viz.BackendNotAvailableError("Test message")
        assert str(error1) == "Test message"
        
        error2 = viz.InvalidGeometryError("Test geometry error")
        assert str(error2) == "Test geometry error"


class TestBackendSelection:
    """Test backend selection logic."""
    
    def test_check_backend_availability_with_backend(self):
        """Test _check_backend_availability when backend is available."""
        viz = load_visualization_module()
        if viz.XYZRENDER_AVAILABLE or viz.PLOTLY_AVAILABLE:
            viz._check_backend_availability()
    
    def test_check_backend_availability_raises_when_none(self):
        """Test _check_backend_availability raises when no backend is available."""
        viz = load_visualization_module()
        with patch.object(viz, 'XYZRENDER_AVAILABLE', False):
            with patch.object(viz, 'PLOTLY_AVAILABLE', False):
                with pytest.raises(viz.BackendNotAvailableError):
                    viz._check_backend_availability()


class TestDataExtraction:
    """Test data extraction helper functions using proper classes."""
    
    def test_extract_atoms_data_no_geometry(self):
        """Test _extract_atoms_data raises error when object has no geometry."""
        viz = load_visualization_module()
        
        class MockObj:
            hasGeometry = []
        
        with pytest.raises(viz.InvalidGeometryError):
            viz._extract_atoms_data(MockObj())
    
    def test_extract_atoms_data_none_points(self):
        """Test _extract_atoms_data raises error when geometry has no points."""
        viz = load_visualization_module()
        
        class MockGeometry:
            hasPoints = None
        
        class MockObj:
            hasGeometry = [MockGeometry()]
        
        with pytest.raises(viz.InvalidGeometryError):
            viz._extract_atoms_data(MockObj())
    
    def test_extract_atoms_data_success(self):
        """Test _extract_atoms_data extracts atom data correctly."""
        viz = load_visualization_module()
        
        class MockPoint:
            def __init__(self, label, x, y, z):
                self.label = label
                self.x = x
                self.y = y
                self.z = z
        
        class MockGeometry:
            def __init__(self, points):
                self.hasPoints = points
        
        class MockObj:
            def __init__(self):
                self.hasGeometry = [MockGeometry([
                    MockPoint('C', 1.0, 2.0, 3.0),
                    MockPoint('O', 4.0, 5.0, 6.0)
                ])]
                self.instance_iri = 'test_iri'
        
        atoms = viz._extract_atoms_data(MockObj())
        
        assert len(atoms) == 2
        assert atoms[0] == {'label': 'C', 'x': 1.0, 'y': 2.0, 'z': 3.0}
        assert atoms[1] == {'label': 'O', 'x': 4.0, 'y': 5.0, 'z': 6.0}
    
    def test_extract_binding_sites_data_no_binding_sites(self):
        """Test _extract_binding_sites_data returns empty list when no binding sites."""
        viz = load_visualization_module()
        
        class MockObj:
            hasBindingSite = []
        
        result = viz._extract_binding_sites_data(MockObj())
        assert result == []
    
    def test_extract_binding_sites_data_success(self):
        """Test _extract_binding_sites_data extracts binding site data correctly."""
        viz = load_visualization_module()
        
        class MockCoordinates:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        class MockBindingSite:
            def __init__(self, coords):
                self.binding_coordinates = coords
        
        class MockObj:
            hasBindingSite = []
        
        mock_obj = MockObj()
        mock_obj.hasBindingSite = [MockBindingSite(MockCoordinates(1.0, 2.0, 3.0))]
        
        result = viz._extract_binding_sites_data(mock_obj)
        
        assert len(result) == 1
        assert result[0] == {'label': 'BindingSite', 'x': 1.0, 'y': 2.0, 'z': 3.0}
    
    def test_extract_assembly_center_success(self):
        """Test _extract_assembly_center extracts center data correctly."""
        viz = load_visualization_module()
        
        class MockCoordinates:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        class MockObj:
            def __init__(self, center):
                self.assembly_center = center
        
        result = viz._extract_assembly_center(MockObj(MockCoordinates(0.0, 0.0, 0.0)))
        
        assert result == {'label': 'AssemblyCenter', 'x': 0.0, 'y': 0.0, 'z': 0.0}
    
    def test_extract_assembly_center_no_center(self):
        """Test _extract_assembly_center returns None when no center."""
        viz = load_visualization_module()
        
        class MockObj:
            pass
        
        result = viz._extract_assembly_center(MockObj())
        assert result is None
    
    def test_extract_pore_data_no_pores(self):
        """Test _extract_pore_data returns empty list when no pores."""
        viz = load_visualization_module()
        
        class MockObj:
            pass
        
        result = viz._extract_pore_data(MockObj())
        assert result == []
    
    def test_extract_pore_data_with_pore_ring(self):
        """Test _extract_pore_data extracts pore ring data correctly."""
        viz = load_visualization_module()
        
        class MockCoordinates:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        class MockValue:
            def __init__(self, value):
                self.hasNumericalValue = value
        
        class MockDiameter:
            def __init__(self, value):
                self.hasValue = [MockValue(value)]
        
        class MockPoreRing:
            def __init__(self, center, diameter):
                self.hasPoreRingCenter = [center]
                self.hasPoreDiameter = [diameter]
        
        class MockObj:
            hasCavity = None
            hasPoreRing = None
        
        mock_obj = MockObj()
        mock_obj.hasPoreRing = [MockPoreRing(MockCoordinates(1.0, 2.0, 3.0), MockDiameter(8.0))]
        
        result = viz._extract_pore_data(mock_obj)
        
        assert len(result) == 1
        assert result[0]['label'] == 'PoreRing'
        assert result[0]['x'] == 1.0
        assert result[0]['radius'] == 4.0


class TestBackendSelection:
    """Test backend selection in main functions."""
    
    def test_invalid_backend_raises_error(self):
        """Test that invalid backend raises ValueError."""
        viz = load_visualization_module()
        
        class MockObj:
            pass
        
        with pytest.raises(ValueError, match="Unknown backend"):
            viz.visualise_mop(MockObj(), backend='invalid')


class TestModuleExports:
    """Test that all expected exports are available."""
    
    def test_all_exports_available(self):
        """Test that all exports in __all__ are available."""
        viz = load_visualization_module()
        
        for export in viz.__all__:
            assert hasattr(viz, export), f"Missing export: {export}"
    
    def test_visualization_in_all(self):
        """Test that key visualization functions are in __all__."""
        viz = load_visualization_module()
        
        expected_exports = [
            'VisualizationError',
            'BackendNotAvailableError',
            'InvalidGeometryError',
            'visualise_mop',
            'visualise_cbu',
            'visualise_am',
            'visualise_mop_xyzrender',
            'visualise_mop_plotly',
            'visualise_cbu_xyzrender',
            'visualise_cbu_plotly',
            'visualise_am_xyzrender',
            'visualise_am_plotly',
            'visualise_with_xyzrender',
            'visualise_with_plotly',
        ]
        
        for export in expected_exports:
            assert export in viz.__all__, f"Missing expected export: {export}"
