"""
Simple Embedding Service for Hedwig

Provides lightweight semantic embeddings using a simple but effective approach
that doesn't require heavy dependencies like PyTorch.
"""

import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from ..utils.text_utils import TextProcessor

class SimpleEmbeddings:
    """
    A lightweight embedding service that combines TF-IDF with dimensionality reduction
    to create semantic embeddings without heavy ML dependencies.
    """
    
    def __init__(self, n_components: int = 128, max_features: int = 2000):
        """
        Initialize the simple embedding service.
        
        Args:
            n_components: Number of dimensions for the final embeddings
            max_features: Maximum number of features for TF-IDF
        """
        self.n_components = n_components
        self.max_features = max_features
        self.vectorizer = None
        self.svd = None
        self._fitted = False
        
    def fit(self, texts: List[str]) -> np.ndarray:
        """
        Fit the embedding model on a list of texts.
        
        Args:
            texts: List of text strings to fit on
            
        Returns:
            Embeddings matrix
        """
        # Preprocess texts using TextProcessor
        processed_texts = [TextProcessor.preprocess_text(text) for text in texts]
        
        # Create TF-IDF vectors
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.9,
            lowercase=True
        )
        
        tfidf_matrix = self.vectorizer.fit_transform(processed_texts)
        
        # Reduce dimensionality using SVD for semantic compression
        self.svd = TruncatedSVD(n_components=self.n_components, random_state=42)
        embeddings = self.svd.fit_transform(tfidf_matrix)
        
        self._fitted = True
        return embeddings
    
    def transform(self, texts: List[str]) -> np.ndarray:
        """
        Transform texts to embeddings using the fitted model.
        
        Args:
            texts: List of text strings to transform
            
        Returns:
            Embeddings matrix
        """
        if not self._fitted:
            raise ValueError("Model must be fitted before transforming")
        
        processed_texts = [TextProcessor.preprocess_text(text) for text in texts]
        tfidf_matrix = self.vectorizer.transform(processed_texts)
        embeddings = self.svd.transform(tfidf_matrix)
        
        return embeddings
    
    def similarity(self, query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between query and embeddings.
        
        Args:
            query_embedding: Query embedding vector
            embeddings: Matrix of embeddings to compare against
            
        Returns:
            Array of similarity scores
        """
        return cosine_similarity([query_embedding], embeddings)[0]

def create_embeddings(texts: List[str], n_components: int = 128) -> tuple:
    """
    Create embeddings for a list of texts.
    
    Args:
        texts: List of text strings
        n_components: Number of dimensions for embeddings
        
    Returns:
        Tuple of (embeddings, model)
    """
    model = SimpleEmbeddings(n_components=n_components)
    embeddings = model.fit(texts)
    return embeddings, model 