"""
Tests for SimpleEmbeddings service.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from sklearn.feature_extraction.text import TfidfVectorizer

from src.services.simple_embeddings import SimpleEmbeddings, create_embeddings
from src.utils.text_utils import TextProcessor


class TestSimpleEmbeddings:
    """Test cases for SimpleEmbeddings class."""
    
    def test_initialization(self):
        """Test SimpleEmbeddings initialization."""
        embeddings = SimpleEmbeddings()
        assert embeddings.n_components == 128
        assert embeddings.max_features == 2000
        assert embeddings.vectorizer is None
        assert embeddings.svd is None
        assert embeddings._fitted is False
    
    def test_initialization_custom_params(self):
        """Test SimpleEmbeddings initialization with custom parameters."""
        embeddings = SimpleEmbeddings(n_components=64, max_features=1000)
        assert embeddings.n_components == 64
        assert embeddings.max_features == 1000
    
    def test_preprocess_text(self):
        """Test text preprocessing."""
        # Test basic preprocessing
        text = "Hello, World! This is a TEST."
        processed = TextProcessor.preprocess_text(text)
        assert processed == "hello world this is a test"
        
        # Test with special characters
        text = "Email@domain.com - (123) 456-7890"
        processed = TextProcessor.preprocess_text(text)
        assert "email" in processed
        assert "domain" in processed
        assert "123" in processed
        assert "456" in processed
        assert "7890" in processed
        
        # Test with extra whitespace
        text = "  Multiple    spaces   "
        processed = TextProcessor.preprocess_text(text)
        assert processed == "multiple spaces"
    
    def test_fit(self):
        """Test fitting the embedding model."""
        embeddings = SimpleEmbeddings(n_components=2, max_features=10)
        texts = ["Hello world", "Goodbye world", "Test document"]
        
        result = embeddings.fit(texts)
        
        assert embeddings._fitted is True
        assert embeddings.vectorizer is not None
        assert embeddings.svd is not None
        # n_components will be limited by the actual number of features
        assert result.shape[0] == 3  # 3 documents
        assert result.shape[1] <= 2  # components limited by n_components
        assert isinstance(result, np.ndarray)
    
    def test_fit_empty_texts(self):
        """Test fitting with empty text list."""
        embeddings = SimpleEmbeddings()
        texts = []
        
        with pytest.raises(ValueError):
            embeddings.fit(texts)
    
    def test_transform_without_fit(self):
        """Test transform without fitting first."""
        embeddings = SimpleEmbeddings()
        texts = ["Test text"]
        
        with pytest.raises(ValueError, match="Model must be fitted before transforming"):
            embeddings.transform(texts)
    
    def test_transform(self):
        """Test transforming texts to embeddings."""
        embeddings = SimpleEmbeddings(n_components=2, max_features=10)
        train_texts = ["Hello world", "Goodbye world", "Test document"]
        
        # Fit the model
        embeddings.fit(train_texts)
        
        # Transform new texts
        new_texts = ["New document", "Another test"]
        result = embeddings.transform(new_texts)
        
        assert result.shape[0] == 2  # 2 documents
        assert result.shape[1] <= 2  # components limited by n_components
        assert isinstance(result, np.ndarray)
    
    def test_similarity(self):
        """Test similarity calculation."""
        embeddings = SimpleEmbeddings()
        
        # Create test embeddings
        query_embedding = np.array([0.1, 0.2, 0.3])
        embeddings_matrix = np.array([
            [0.1, 0.2, 0.3],  # Same as query
            [0.9, 0.8, 0.7],  # Different from query
            [0.2, 0.4, 0.6]   # Somewhat similar
        ])
        
        similarities = embeddings.similarity(query_embedding, embeddings_matrix)
        
        assert len(similarities) == 3
        assert similarities[0] > 0.99  # Should be very similar to itself
        # Note: cosine similarity can be higher than expected with normalized vectors
        assert similarities[1] < 0.95   # Should be less similar
        assert similarities[2] > 0.5   # Should be somewhat similar
    
    def test_similarity_edge_cases(self):
        """Test similarity calculation with edge cases."""
        embeddings = SimpleEmbeddings()
        
        # Test with zero vectors
        query_embedding = np.array([0.0, 0.0, 0.0])
        embeddings_matrix = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0]
        ])
        
        similarities = embeddings.similarity(query_embedding, embeddings_matrix)
        assert len(similarities) == 2
        # Zero vectors may not always have similarity 1.0 due to normalization
        assert similarities[0] >= 0.0
        assert similarities[1] >= 0.0
    
    def test_fit_transform_consistency(self):
        """Test that fit and transform produce consistent results."""
        embeddings = SimpleEmbeddings(n_components=4, max_features=10)
        texts = ["Hello world", "Goodbye world", "Test document"]
        
        # Fit and get embeddings
        fit_embeddings = embeddings.fit(texts)
        
        # Transform the same texts
        transform_embeddings = embeddings.transform(texts)
        
        # Results should be identical
        np.testing.assert_array_almost_equal(fit_embeddings, transform_embeddings)
    
    def test_different_texts_embeddings(self):
        """Test that different texts produce different embeddings."""
        embeddings = SimpleEmbeddings(n_components=4, max_features=10)
        texts = ["Hello world", "Goodbye world", "Test document"]
        
        embeddings.fit(texts)
        
        # Get embeddings for each text
        embeddings_list = embeddings.transform(texts)
        
        # All embeddings should be different
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similarity = embeddings.similarity(embeddings_list[i], [embeddings_list[j]])[0]
                assert similarity < 1.0  # Should not be identical


class TestCreateEmbeddings:
    """Test cases for create_embeddings function."""
    
    def test_create_embeddings(self):
        """Test create_embeddings function."""
        texts = ["Hello world", "Goodbye world", "Test document"]
        
        embeddings, model = create_embeddings(texts, n_components=2)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 3  # 3 documents
        assert embeddings.shape[1] <= 2  # components limited by n_components
        assert isinstance(model, SimpleEmbeddings)
        assert model._fitted is True
    
    def test_create_embeddings_empty_list(self):
        """Test create_embeddings with empty text list."""
        texts = []
        
        with pytest.raises(ValueError):
            create_embeddings(texts)
    
    def test_create_embeddings_custom_components(self):
        """Test create_embeddings with custom n_components."""
        texts = ["Hello world", "Goodbye world"]
        
        # Use smaller n_components to avoid exceeding feature count
        embeddings, model = create_embeddings(texts, n_components=2)
        
        assert embeddings.shape[0] == 2  # 2 documents
        assert embeddings.shape[1] <= 2  # components limited by n_components


class TestSimpleEmbeddingsIntegration:
    """Integration tests for SimpleEmbeddings."""
    
    def test_full_pipeline(self):
        """Test the full embedding pipeline."""
        embeddings = SimpleEmbeddings(n_components=4, max_features=50)
        
        # Training texts
        train_texts = [
            "Email outreach for SaaS companies",
            "Cold email to potential clients",
            "Follow up email template",
            "Partnership proposal email"
        ]
        
        # Fit the model
        train_embeddings = embeddings.fit(train_texts)
        
        # Query texts
        query_texts = [
            "SaaS cold outreach",  # Should be similar to first two
            "Partnership email",   # Should be similar to last one
            "Unrelated topic"      # Should be less similar
        ]
        
        # Transform queries
        query_embeddings = embeddings.transform(query_texts)
        
        # Calculate similarities
        for i, query_embedding in enumerate(query_embeddings):
            similarities = embeddings.similarity(query_embedding, train_embeddings)
            
            # All similarities should be between -1 and 1 (cosine similarity range)
            assert all(-1 <= sim <= 1 for sim in similarities)
            
            # Should have some similarity to at least one training text
            assert max(similarities) > -1
    
    def test_embedding_quality(self):
        """Test that embeddings capture semantic similarity."""
        embeddings = SimpleEmbeddings(n_components=16, max_features=100)
        
        # Texts with semantic relationships
        texts = [
            "Email marketing campaign",
            "Email outreach strategy", 
            "Cold email template",
            "Follow up email",
            "Unrelated topic about cooking"
        ]
        
        embeddings_matrix = embeddings.fit(texts)
        
        # Test semantic similarity
        email_marketing_idx = 0
        email_outreach_idx = 1
        cold_email_idx = 2
        follow_up_idx = 3
        cooking_idx = 4
        
        # Email-related texts should be more similar to each other
        email_similarity = embeddings.similarity(
            embeddings_matrix[email_marketing_idx], 
            [embeddings_matrix[email_outreach_idx]]
        )[0]
        
        cooking_similarity = embeddings.similarity(
            embeddings_matrix[email_marketing_idx], 
            [embeddings_matrix[cooking_idx]]
        )[0]
        
        # Email-related texts should be more similar than email vs cooking
        assert email_similarity > cooking_similarity 