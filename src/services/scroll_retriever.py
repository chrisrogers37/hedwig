"""
Scroll Retriever Service for Hedwig

Provides intelligent retrieval of relevant email templates (scrolls) based on user context.
Uses semantic search to find the most appropriate templates for any given situation.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import yaml
import re

from .simple_embeddings import SimpleEmbeddings
from ..utils.logging_utils import log
from ..utils.file_utils import FileUtils
from ..utils.error_utils import ErrorHandler
from .config_service import get_config
from ..utils.text_utils import TextProcessor

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    log("WARNING: sentence-transformers not available, using SimpleEmbeddings", prefix="ScrollRetriever")


@dataclass
class EmailSnippet:
    """Represents a single email template with metadata and content."""
    id: str
    file_path: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    
    @property
    def tags(self) -> List[str]:
        """Get tags from metadata."""
        return self.metadata.get('tags', [])
    
    @property
    def use_case(self) -> str:
        """Get use case from metadata."""
        return self.metadata.get('use_case', '')
    
    @property
    def tone(self) -> str:
        """Get tone from metadata."""
        return self.metadata.get('tone', '')
    
    @property
    def industry(self) -> str:
        """Get industry from metadata."""
        return self.metadata.get('industry', '')
    
    @property
    def role(self) -> str:
        """Get role from metadata."""
        return self.metadata.get('role', '')
    
    @property
    def difficulty(self) -> str:
        """Get difficulty from metadata."""
        return self.metadata.get('difficulty', '')
    
    @property
    def success_rate(self) -> float:
        """Get success rate from metadata."""
        return self.metadata.get('success_rate', 0.0)


class ScrollRetriever:
    """
    Retrieves relevant email snippets using semantic search.
    
    Loads email templates from the scrolls directory, generates embeddings,
    and provides semantic search functionality for RAG implementation.
    """
    
    def __init__(self, 
                 snippets_dir: str = None,
                 embedding_model: str = "all-MiniLM-L6-v2",
                 cache_embeddings: bool = True,
                 max_snippets: int = 1000,
                 use_sentence_transformers: bool = False):
        """
        Initialize the snippet retriever.
        
        Args:
            snippets_dir: Directory containing email snippets
            embedding_model: Sentence transformer model to use (if available)
            cache_embeddings: Whether to cache embeddings in memory
            max_snippets: Maximum number of snippets to load
            use_sentence_transformers: Whether to use sentence-transformers (if available)
        """
        if snippets_dir is None:
            # Always resolve relative to project root (parent of src)
            snippets_dir = Path(__file__).parent.parent.parent / 'scrolls'
        else:
            snippets_dir = Path(snippets_dir)
        self.snippets_dir = snippets_dir
        self.embedding_model_name = embedding_model
        self.cache_embeddings = cache_embeddings
        self.max_snippets = max_snippets
        self.use_sentence_transformers = use_sentence_transformers and SENTENCE_TRANSFORMERS_AVAILABLE
        
        # Initialize components
        self.model = None
        self.simple_embeddings = None
        self.vectorizer = None
        self.snippets: List[EmailSnippet] = []
        self.embeddings: Optional[np.ndarray] = None
        self._loaded = False
        
        log(f"Initialized ScrollRetriever with {'sentence-transformers' if self.use_sentence_transformers else 'SimpleEmbeddings'}")
    
    def load_snippets(self) -> int:
        """
        Load all email snippets from the scrolls directory using FileUtils and ErrorHandler.
        
        Returns:
            Number of snippets loaded
        """
        if self._loaded:
            return len(self.snippets)
        
        log(f"Loading email snippets from: {self.snippets_dir}")
        start_time = time.time()
        
        # Find all markdown files using FileUtils
        markdown_files = FileUtils.find_files_by_extension(self.snippets_dir, '.md')
        markdown_files = [f for f in markdown_files if f.name != "README.md"]  # Exclude README
        
        def load_all_snippets():
            loaded_count = 0
            for file_path in markdown_files:
                if loaded_count >= self.max_snippets:
                    log(f"Reached max snippets limit ({self.max_snippets})", prefix="ScrollRetriever")
                    break
                
                snippet = self._load_snippet(file_path)
                if snippet:
                    self.snippets.append(snippet)
                    loaded_count += 1
            
            log(f"Loaded {loaded_count} snippets in {time.time() - start_time:.2f}s", prefix="ScrollRetriever")
            return loaded_count
        
        loaded_count = ErrorHandler.handle_file_operation(load_all_snippets) or 0
        
        if loaded_count > 0:
            self._generate_embeddings()
            self._loaded = True
        
        return loaded_count
    
    def _load_snippet(self, file_path: Path) -> Optional[EmailSnippet]:
        """Load a single snippet file using FileUtils and ErrorHandler."""
        def load_single_snippet():
            # Read file content using FileUtils
            content = FileUtils.safe_read_file(file_path)
            if content is None:
                return None
            
            # Parse frontmatter and content
            frontmatter, body = FileUtils.parse_yaml_frontmatter(content)
            
            # Process the body text
            processed_body = TextProcessor.preprocess_text(body)
            
            # Create snippet ID from file path
            snippet_id = str(file_path.relative_to(self.snippets_dir)).replace('\\', '/')
            
            # Create metadata
            metadata = frontmatter or {}
            metadata['file_path'] = str(file_path)
            metadata['word_count'] = len(processed_body.split())
            
            # Validate metadata
            if not self._validate_metadata(metadata):
                log(f"WARNING: Invalid metadata in {file_path}", prefix="ScrollRetriever")
                return None
            
            snippet = EmailSnippet(
                id=snippet_id,
                file_path=str(file_path),
                content=body,
                metadata=metadata
            )
            
            log(f"Loaded snippet: {snippet_id} ({metadata['word_count']} words)", prefix="ScrollRetriever")
            return snippet
        
        return ErrorHandler.handle_file_operation(load_single_snippet)
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Validate snippet metadata."""
        required_fields = ['use_case', 'tone', 'industry']
        return all(field in metadata for field in required_fields)
    
    def _generate_embeddings(self) -> None:
        """Generate embeddings for all loaded snippets using ErrorHandler."""
        if not self.snippets:
            log("No snippets to generate embeddings for", prefix="ScrollRetriever")
            return
        
        def generate_embeddings():
            if self.use_sentence_transformers:
                self._generate_sentence_transformer_embeddings()
            else:
                self._generate_simple_embeddings()
        
        ErrorHandler.handle_api_operation(generate_embeddings)
    
    def _generate_sentence_transformer_embeddings(self) -> None:
        """Generate embeddings using sentence-transformers."""
        log("Generating embeddings with sentence-transformers", prefix="ScrollRetriever")
        
        # Initialize model
        self.model = SentenceTransformer(self.embedding_model_name)
        
        # Extract text content for embedding
        texts = [snippet.content for snippet in self.snippets]
        
        # Generate embeddings
        self.embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Store embeddings with snippets
        for i, snippet in enumerate(self.snippets):
            snippet.embedding = self.embeddings[i]
        
        log(f"Generated embeddings for {len(self.snippets)} snippets", prefix="ScrollRetriever")
    
    def _generate_simple_embeddings(self) -> None:
        """Generate embeddings using SimpleEmbeddings."""
        log("Generating embeddings with SimpleEmbeddings", prefix="ScrollRetriever")
        
        # Initialize SimpleEmbeddings
        self.simple_embeddings = SimpleEmbeddings()
        
        # Extract text content for embedding
        texts = [snippet.content for snippet in self.snippets]
        
        # Generate embeddings
        self.embeddings = self.simple_embeddings.embed_documents(texts)
        
        # Store embeddings with snippets
        for i, snippet in enumerate(self.snippets):
            snippet.embedding = self.embeddings[i]
        
        log(f"Generated embeddings for {len(self.snippets)} snippets", prefix="ScrollRetriever")
    
    def query(self, 
              query_text: str, 
              top_k: int = 3, 
              min_similarity: float = 0.3,
              filters: Optional[Dict[str, Any]] = None) -> List[Tuple[EmailSnippet, float]]:
        """
        Query snippets using semantic search with ErrorHandler.
        
        Args:
            query_text: The query text
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold
            filters: Optional filters to apply
            
        Returns:
            List of (snippet, similarity_score) tuples
        """
        if not self._loaded:
            self.load_snippets()
        
        if not self.snippets:
            return []
        
        def perform_query():
            # Get query embedding
            query_embedding = self._get_query_embedding(query_text)
            
            # Calculate similarities
            similarities = self._calculate_similarities(query_embedding)
            
            # Apply filters and threshold
            results = []
            for i, similarity in enumerate(similarities):
                if similarity >= min_similarity:
                    snippet = self.snippets[i]
                    if not filters or self._matches_filters(snippet, filters):
                        results.append((snippet, similarity))
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        
        return ErrorHandler.handle_api_operation(perform_query) or []
    
    def _get_query_embedding(self, query_text: str) -> np.ndarray:
        """Get embedding for query text."""
        if self.use_sentence_transformers and self.model:
            return self.model.encode([query_text])[0]
        elif self.simple_embeddings:
            return self.simple_embeddings.embed_documents([query_text])[0]
        else:
            raise ValueError("No embedding model available")
    
    def _calculate_similarities(self, query_embedding: np.ndarray) -> np.ndarray:
        """Calculate similarities between query and all snippets."""
        if self.embeddings is None:
            return np.zeros(len(self.snippets))
        
        # Calculate cosine similarities
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        return similarities
    
    def _matches_filters(self, snippet: EmailSnippet, filters: Dict[str, Any]) -> bool:
        """Check if snippet matches the given filters."""
        for key, value in filters.items():
            if hasattr(snippet, key):
                snippet_value = getattr(snippet, key)
                if isinstance(value, list):
                    if not any(v in snippet_value for v in value):
                        return False
                else:
                    if snippet_value != value:
                        return False
            else:
                # Check metadata
                snippet_value = snippet.metadata.get(key)
                if snippet_value != value:
                    return False
        return True
    
    def get_snippets_by_category(self, category: str) -> List[EmailSnippet]:
        """Get all snippets in a specific category."""
        return [s for s in self.snippets if s.use_case == category]
    
    def get_snippet_by_id(self, snippet_id: str) -> Optional[EmailSnippet]:
        """Get a specific snippet by ID."""
        for snippet in self.snippets:
            if snippet.id == snippet_id:
                return snippet
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded snippets."""
        if not self.snippets:
            return {"total_snippets": 0}
        
        stats = {
            "total_snippets": len(self.snippets),
            "categories": {},
            "tones": {},
            "industries": {},
            "average_word_count": 0
        }
        
        total_words = 0
        for snippet in self.snippets:
            # Count categories
            stats["categories"][snippet.use_case] = stats["categories"].get(snippet.use_case, 0) + 1
            stats["tones"][snippet.tone] = stats["tones"].get(snippet.tone, 0) + 1
            stats["industries"][snippet.industry] = stats["industries"].get(snippet.industry, 0) + 1
            total_words += snippet.metadata.get('word_count', 0)
        
        stats["average_word_count"] = total_words / len(self.snippets)
        
        return stats 