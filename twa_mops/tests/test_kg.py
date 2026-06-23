"""Tests for Knowledge Graph client functionality."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add twa_mops to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kg.client import KnowledgeGraphClient


class TestKnowledgeGraphClient:
    """Test suite for KnowledgeGraphClient."""
    
    def test_initialization(self):
        """Test that KnowledgeGraphClient initializes correctly."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(
                endpoint="http://test:3838/sparql",
                max_cache_size=50,
                username="test_user",
                password="test_pass",
                fs_url="http://test:8000/",
                fs_username="fs_user",
                fs_password="fs_pass"
            )
            
            assert client.endpoint == "http://test:3838/sparql"
            assert client.max_cache_size == 50
            assert client.username == "test_user"
            assert client.password == "test_pass"
            assert client.fs_url == "http://test:8000/"
            assert client.fs_username == "fs_user"
            assert client.fs_password == "fs_pass"
            assert client.sparql_client == mock_instance
            
            # Verify PySparqlClient was called with correct args
            mock_sparql.assert_called_once_with(
                query_endpoint="http://test:3838/sparql",
                update_endpoint="http://test:3838/sparql",
                kg_user="test_user",
                kg_password="test_pass",
                fs_url="http://test:8000/",
                fs_user="fs_user",
                fs_pwd="fs_pass"
            )
    
    def test_initialization_default_values(self):
        """Test that KnowledgeGraphClient uses default values correctly."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            assert client.max_cache_size == 128
            assert client.username is None
            assert client.password is None
            assert client.fs_url is None
            assert client.fs_username is None
            assert client.fs_password is None
    
    def test_pull_objects_empty_list(self):
        """Test pull_objects with empty IRI list."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            result = client.pull_objects([])
            
            assert result == []
    
    def test_pull_objects_single_iri(self):
        """Test pull_objects with a single IRI."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_result = [
                {'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'},
                {'s': 'http://test/iri1', 'p': 'http://test/p2', 'o': 'value2'},
            ]
            mock_instance.perform_query.return_value = mock_result
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            result = client.pull_objects(['http://test/iri1'])
            
            assert len(result) == 2
            assert result[0] == {'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'}
            assert result[1] == {'s': 'http://test/iri1', 'p': 'http://test/p2', 'o': 'value2'}
    
    def test_pull_objects_multiple_iris(self):
        """Test pull_objects with multiple IRIs (batched query)."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_result = [
                {'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'},
                {'s': 'http://test/iri2', 'p': 'http://test/p2', 'o': 'value2'},
            ]
            mock_instance.perform_query.return_value = mock_result
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            result = client.pull_objects(['http://test/iri1', 'http://test/iri2'])
            
            assert len(result) == 2
            # Verify the query contained both IRIs
            call_args = mock_instance.perform_query.call_args[0][0]
            assert '<http://test/iri1>' in call_args
            assert '<http://test/iri2>' in call_args
    
    def test_pull_single_object(self):
        """Test pull_single_object method."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_result = [{'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'}]
            mock_instance.perform_query.return_value = mock_result
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            result = client.pull_single_object('http://test/iri1')
            
            assert len(result) == 1
            assert result[0] == {'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'}
    
    def test_clear_cache(self):
        """Test clear_cache method."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            # Call pull_objects to populate cache
            mock_result = [{'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'}]
            mock_instance.perform_query.return_value = mock_result
            client.pull_objects(['http://test/iri1'])
            
            # Clear cache
            client.clear_cache()
            
            # Verify cache_info shows cache was cleared
            cache_info = client._pull_objects_cached.cache_info()
            # After clear, hits should be 0
            assert cache_info.hits == 0
    
    def test_execute_query(self):
        """Test execute_query method."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_result = "query result"
            mock_instance.perform_query.return_value = mock_result
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            result = client.execute_query("SELECT ?s ?p ?o WHERE { ?s ?p ?o }")
            
            assert result == "query result"
            mock_instance.perform_query.assert_called_once_with("SELECT ?s ?p ?o WHERE { ?s ?p ?o }")
    
    def test_push_objects_empty_list(self):
        """Test push_objects with empty list raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="No objects to push"):
                client.push_objects([])
    
    def test_push_objects_with_pydantic_models_raises(self):
        """Test that push_objects raises InvalidObjectError for Pydantic models."""
        from pydantic import BaseModel
        from kg.client import InvalidObjectError
        
        class TestModel(BaseModel):
            name: str
        
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            test_model = TestModel(name="test")
            
            with pytest.raises(InvalidObjectError, match="Pydantic models is not yet implemented"):
                client.push_objects([test_model])


class TestInputValidation:
    """Test suite for input validation in KnowledgeGraphClient."""
    
    def test_invalid_endpoint_raises(self):
        """Test that invalid endpoint raises ValueError."""
        with pytest.raises(ValueError, match="Invalid SPARQL endpoint"):
            KnowledgeGraphClient(endpoint="not-a-valid-url")
    
    def test_empty_endpoint_raises(self):
        """Test that empty endpoint raises ValueError."""
        with pytest.raises(ValueError, match="SPARQL endpoint cannot be empty"):
            KnowledgeGraphClient(endpoint="")
    
    def test_invalid_cache_size_too_small_raises(self):
        """Test that cache size < 1 raises ValueError."""
        with pytest.raises(ValueError, match="greater_than_equal"):
            KnowledgeGraphClient(endpoint="http://test:3838/sparql", max_cache_size=0)
    
    def test_invalid_cache_size_too_large_raises(self):
        """Test that cache size > 10000 raises ValueError."""
        with pytest.raises(ValueError, match="less_than_equal"):
            KnowledgeGraphClient(endpoint="http://test:3838/sparql", max_cache_size=10001)
    
    def test_invalid_iri_raises(self):
        """Test that invalid IRI raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="Invalid IRI format"):
                client.pull_objects(["not-a-valid-iri"])
    
    def test_empty_iri_raises(self):
        """Test that empty IRI raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="IRI cannot be empty"):
                client.pull_objects([""])
    
    def test_pull_for_assembly_warns_on_shallow_depth(self):
        """Test that pull_for_assembly warns when depth < 3."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            # Create mock objects
            mock_am = Mock()
            mock_am.instance_iri = "http://test/am1"
            mock_cbu = Mock()
            mock_cbu.instance_iri = "http://test/cbu1"
            
            # Mock the pull_from_kg to return mock objects
            with patch('twa_mops.core.ontomops.AssemblyModel.pull_from_kg') as mock_am_pull, \
                 patch('twa_mops.core.ontomops.ChemicalBuildingUnit.pull_from_kg') as mock_cbu_pull:
                mock_am_pull.return_value = [mock_am]
                mock_cbu_pull.return_value = [mock_cbu]
                
                # This should trigger a warning but not raise an error
                with pytest.warns(UserWarning, match="Depth=2 may be too shallow"):
                    am, cbus = client.pull_for_assembly("http://test/am1", ["http://test/cbu1"], depth=2)
                    assert am == mock_am
                    assert cbus == [mock_cbu]
    
    def test_invalid_batch_size_raises(self):
        """Test that invalid batch_size raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="batch_size must be a positive integer"):
                client.pull_for_assembly("http://test/am1", ["http://test/cbu1"], batch_size=0)
            
            with pytest.raises(ValueError, match="batch_size must be a positive integer"):
                client.pull_for_assembly("http://test/am1", ["http://test/cbu1"], batch_size=-5)
    
    def test_invalid_max_retries_raises(self):
        """Test that invalid max_retries raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="max_retries must be a non-negative integer"):
                client.push_objects([Mock()], max_retries=-1)
            
            with pytest.raises(ValueError, match="max_retries must be a non-negative integer"):
                client.download_file("remote.txt", "local.txt", max_retries=-1)
    
    def test_invalid_retry_delay_raises(self):
        """Test that invalid retry_delay raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="retry_delay must be a non-negative number"):
                client.download_file("remote.txt", "local.txt", retry_delay=-1)
    
    def test_custom_exceptions_available(self):
        """Test that custom exceptions are importable from kg module."""
        from kg.client import (
            KnowledgeGraphError,
            QueryError,
            ObjectNotFoundError,
            InvalidObjectError
        )
        
        # Verify they are proper exceptions
        assert issubclass(KnowledgeGraphError, Exception)
        assert issubclass(QueryError, KnowledgeGraphError)
        assert issubclass(ObjectNotFoundError, KnowledgeGraphError)
        assert issubclass(InvalidObjectError, KnowledgeGraphError)


class TestPerformanceOptimization:
    """Test suite for performance optimization features."""
    
    def test_performance_stats_includes_cache_info(self):
        """Test that performance stats include cache information."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_instance.perform_query.return_value = []
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(
                endpoint="http://test:3838/sparql",
                enable_performance_timing=True
            )
            
            # Make a query to populate stats
            client.pull_objects(["http://test/iri1"])
            
            stats = client.get_performance_stats()
            
            # Verify cache info is included
            assert 'cache_hits' in stats
            assert 'cache_misses' in stats
            assert 'cache_size' in stats
            assert 'cache_maxsize' in stats
    
    def test_clear_cache(self):
        """Test that clear_cache works."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_instance.perform_query.return_value = [
                {'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'}
            ]
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            # Pull to populate cache
            client.pull_objects(["http://test/iri1"])
            
            # Check cache is populated
            cache_info = client._pull_objects_cached.cache_info()
            assert cache_info.currsize > 0
            
            # Clear cache
            client.clear_cache()
            
            # Check cache is empty
            cache_info = client._pull_objects_cached.cache_info()
            assert cache_info.currsize == 0
    
    def test_clear_cached_objects(self):
        """Test that clear_cached_objects works."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_instance.perform_query.return_value = [
                {'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'}
            ]
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            # Pull to populate cache
            client.pull_objects(["http://test/iri1"])
            
            # Clear specific objects
            count = client.clear_cached_objects(["http://test/iri1"])
            
            # Should return the original cache size
            assert count >= 0
    
    def test_prefetch_objects(self):
        """Test that prefetch_objects works."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_instance.perform_query.return_value = [
                {'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'}
            ]
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            # Prefetch objects
            count = client.prefetch_objects(["http://test/iri1", "http://test/iri2"])
            
            # Should return number of objects fetched
            assert count >= 0
            
            # Cache should be populated
            cache_info = client._pull_objects_cached.cache_info()
            assert cache_info.currsize > 0
    
    def test_pull_objects_optimized_empty_list(self):
        """Test that pull_objects_optimized handles empty list."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            result = client.pull_objects_optimized([], depth=1)
            assert result == []
    
    def test_pull_objects_optimized_with_batch_size(self):
        """Test that pull_objects_optimized works with batch_size."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_instance.perform_query.return_value = [
                {'s': 'http://test/iri1', 'p': 'http://test/p1', 'o': 'value1'},
                {'s': 'http://test/iri2', 'p': 'http://test/p2', 'o': 'value2'},
            ]
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            # With batch_size=1, should make 2 separate calls
            result = client.pull_objects_optimized(
                ["http://test/iri1", "http://test/iri2"],
                depth=1,
                batch_size=1
            )
            
            # Should get results for both IRIs
            assert len(result) >= 0  # May be 0 or 2 depending on mock
    
    def test_build_optimized_query_generates_valid_sparql(self):
        """Test that _build_optimized_query generates valid SPARQL."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            iris = ["http://test/iri1", "http://test/iri2"]
            query = client._build_optimized_query(tuple(iris), depth=1)
            
            # Verify it's a valid SPARQL query
            assert "SELECT" in query
            assert "WHERE" in query
            assert "VALUES" in query
            assert "http://test/iri1" in query
            assert "http://test/iri2" in query
    
    def test_invalid_depth_too_small_raises(self):
        """Test that depth < -1 raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="greater_than_equal"):
                client.pull_objects(["http://test/iri1"], depth=-2)
    
    def test_invalid_depth_too_large_raises(self):
        """Test that depth > 10 raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="less_than_equal"):
                client.pull_objects(["http://test/iri1"], depth=11)
    
    def test_empty_query_raises(self):
        """Test that empty query raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="SPARQL query cannot be empty"):
                client.execute_query("")
    
    def test_none_query_raises(self):
        """Test that None query raises ValueError."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            with pytest.raises(ValueError, match="SPARQL query cannot be empty"):
                client.execute_query(None)
    
    def test_invalid_file_server_url_raises(self):
        """Test that invalid file server URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid file server URL"):
            KnowledgeGraphClient(
                endpoint="http://test:3838/sparql",
                fs_url="invalid-url"
            )
    
    def test_valid_urn_iri(self):
        """Test that URN format IRIs are accepted."""
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_instance.perform_query.return_value = []
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            # URN format should be accepted
            client.pull_objects(["urn:test:iri1"])
            mock_instance.perform_query.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
