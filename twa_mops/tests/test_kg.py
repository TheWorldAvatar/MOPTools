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
        """Test that push_objects raises NotImplementedError for Pydantic models."""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
        
        with patch('kg.client.PySparqlClient') as mock_sparql:
            mock_instance = Mock()
            mock_sparql.return_value = mock_instance
            
            client = KnowledgeGraphClient(endpoint="http://test:3838/sparql")
            
            test_model = TestModel(name="test")
            
            with pytest.raises(NotImplementedError, match="Pydantic models is not yet implemented"):
                client.push_objects([test_model])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
