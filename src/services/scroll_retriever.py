"""
Scroll Retriever Service for Hedwig

Provides semantic search and retrieval of email templates for RAG (Retrieval-Augmented Generation).
Uses SimpleEmbeddings (TF-IDF + SVD) for semantic search, with fallback to basic TF-IDF.
"""

import os
import yaml
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

from .logging_utils import log
from .simple_embeddings import SimpleEmbeddings

# Try to import sentence-transformers, but don't fail if not available
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    log("WARNING: sentence-transformers not available, using SimpleEmbeddings")


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
        Load all email snippets from the snippets directory.
        
        Returns:
            Number of snippets loaded
        """
        if self._loaded:
            log(f"Snippets already loaded: {len(self.snippets)} snippets")
            return len(self.snippets)
        
        log(f"Loading email snippets from: {self.snippets_dir}")
        start_time = time.time()
        
        # Find all markdown files
        md_files = list(self.snippets_dir.rglob("*.md"))
        md_files = [f for f in md_files if f.name != "README.md"]  # Exclude README
        
        log(f"Found {len(md_files)} markdown files (excluding README.md)")
        for file_path in md_files:
            log(f"  - {file_path}")
        
        if not md_files:
            log("WARNING: No markdown files found in snippets directory")
            return 0
        
        # Load snippets
        loaded_count = 0
        failed_count = 0
        for file_path in md_files[:self.max_snippets]:
            try:
                snippet = self._load_snippet(file_path)
                if snippet:
                    self.snippets.append(snippet)
                    loaded_count += 1
                    log(f"✓ Loaded snippet: {snippet.id} ({snippet.use_case} for {snippet.industry} {snippet.role})")
                else:
                    failed_count += 1
                    log(f"✗ Failed to load snippet: {file_path}")
            except Exception as e:
                failed_count += 1
                log(f"ERROR loading snippet {file_path}: {e}")
        
        # Generate embeddings if caching is enabled
        if self.cache_embeddings and self.snippets:
            log(f"Generating embeddings for {len(self.snippets)} snippets...")
            self._generate_embeddings()
        else:
            log("Skipping embedding generation (cache_embeddings=False or no snippets)")
        
        load_time = time.time() - start_time
        log(f"Loaded {loaded_count} snippets, failed {failed_count} in {load_time:.2f}s")
        
        self._loaded = True
        return loaded_count
    
    def _load_snippet(self, file_path: Path) -> Optional[EmailSnippet]:
        """
        Load a single snippet from a markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            EmailSnippet object or None if loading fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML frontmatter
            metadata, content = self._parse_frontmatter(content)
            
            log(f"Parsed metadata for {file_path}: {metadata}")
            
            # Validate required metadata
            if not self._validate_metadata(metadata):
                missing_fields = []
                required_fields = ['use_case', 'tone', 'industry']
                for field in required_fields:
                    if field not in metadata or not metadata[field]:
                        missing_fields.append(field)
                log(f"WARNING: Invalid metadata in {file_path} - missing fields: {missing_fields}")
                return None
            
            # Create snippet ID
            snippet_id = f"{file_path.parent.name}_{file_path.stem}"
            
            snippet = EmailSnippet(
                id=snippet_id,
                file_path=str(file_path),
                content=content.strip(),
                metadata=metadata
            )
            
            log(f"Successfully created snippet: {snippet_id}")
            return snippet
            
        except Exception as e:
            log(f"ERROR loading snippet {file_path}: {e}")
            return None
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Tuple of (metadata, content)
        """
        lines = content.split('\n')
        
        if not lines or not lines[0].strip().startswith('---'):
            return {}, content
        
        # Find frontmatter boundaries
        start_idx = 0
        end_idx = None
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                end_idx = i
                break
        
        if end_idx is None:
            return {}, content
        
        # Extract and parse frontmatter
        frontmatter_lines = lines[1:end_idx]
        frontmatter_text = '\n'.join(frontmatter_lines)
        
        try:
            metadata = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError as e:
            log(f"ERROR parsing YAML frontmatter: {e}")
            metadata = {}
        
        # Extract content after frontmatter
        content_lines = lines[end_idx + 1:]
        content = '\n'.join(content_lines)
        
        return metadata, content
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate that required metadata fields are present.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['use_case', 'tone', 'industry']
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                return False
        return True
    
    def _generate_embeddings(self) -> None:
        """Generate embeddings for all loaded snippets."""
        if not self.snippets:
            return
        
        log("Generating embeddings...")
        start_time = time.time()
        
        if self.use_sentence_transformers:
            self._generate_sentence_transformer_embeddings()
        else:
            self._generate_simple_embeddings()
        
        embed_time = time.time() - start_time
        log(f"Generated embeddings in {embed_time:.2f}s")
    
    def _generate_sentence_transformer_embeddings(self) -> None:
        """Generate embeddings using sentence-transformers."""
        # Initialize model if not already done
        if self.model is None:
            self.model = SentenceTransformer(self.embedding_model_name)
        
        # Prepare texts for embedding
        texts = []
        for snippet in self.snippets:
            # Combine metadata and content for embedding
            text_parts = [
                snippet.content,
                ' '.join(snippet.tags),
                snippet.use_case,
                snippet.tone,
                snippet.industry,
                snippet.role
            ]
            texts.append(' '.join(text_parts))
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Store embeddings
        self.embeddings = embeddings
        
        # Attach embeddings to snippets
        for i, snippet in enumerate(self.snippets):
            snippet.embedding = embeddings[i]
    
    def _generate_simple_embeddings(self) -> None:
        """Generate embeddings using SimpleEmbeddings."""
        # Prepare texts for embedding
        texts = []
        for snippet in self.snippets:
            # Combine metadata and content for embedding
            text_parts = [
                snippet.content,
                ' '.join(snippet.tags),
                snippet.use_case,
                snippet.tone,
                snippet.industry,
                snippet.role
            ]
            texts.append(' '.join(text_parts))
        
        # Initialize and fit SimpleEmbeddings
        self.simple_embeddings = SimpleEmbeddings(n_components=128, max_features=2000)
        embeddings = self.simple_embeddings.fit(texts)
        
        # Store embeddings
        self.embeddings = embeddings
        
        # Attach embeddings to snippets
        for i, snippet in enumerate(self.snippets):
            snippet.embedding = embeddings[i]
    
    def query(self, 
              query_text: str, 
              top_k: int = 3, 
              min_similarity: float = 0.3,
              filters: Optional[Dict[str, Any]] = None) -> List[Tuple[EmailSnippet, float]]:
        """
        Query for relevant snippets using semantic search.
        
        Args:
            query_text: Query text to search for
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold
            filters: Optional filters for metadata (e.g., {'tone': 'Professional'})
            
        Returns:
            List of (snippet, similarity_score) tuples
        """
        log(f"Querying snippets for: '{query_text}' (top_k={top_k}, min_similarity={min_similarity}, filters={filters})")
        
        # Ensure snippets are loaded
        if not self._loaded:
            log("Snippets not loaded, loading now...")
            self.load_snippets()
        
        if not self.snippets:
            log("No snippets available for query")
            return []
        
        log(f"Loaded {len(self.snippets)} snippets for query")
        
        # Generate query embedding
        query_embedding = self._get_query_embedding(query_text)
        log(f"Generated query embedding with shape: {query_embedding.shape}")
        
        # Calculate similarities
        if self.use_sentence_transformers and self.model:
            log("Using sentence-transformers for similarity calculation")
            similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        elif self.simple_embeddings:
            log("Using SimpleEmbeddings for similarity calculation")
            similarities = self.simple_embeddings.similarity(query_embedding, self.embeddings)
        else:
            log("Using TF-IDF fallback for similarity calculation")
            similarities = self._calculate_tfidf_similarity(query_text)
        
        log(f"Calculated similarities: min={similarities.min():.3f}, max={similarities.max():.3f}, mean={similarities.mean():.3f}")
        
        # Apply filters if provided
        filtered_snippets = []
        filtered_similarities = []
        
        for i, snippet in enumerate(self.snippets):
            similarity = similarities[i]
            
            # Apply similarity threshold
            if similarity < min_similarity:
                log(f"Snippet '{snippet.id}' filtered out due to low similarity: {similarity:.3f} < {min_similarity}")
                continue
            
            # Apply metadata filters
            if filters and not self._matches_filters(snippet, filters):
                log(f"Snippet '{snippet.id}' filtered out due to metadata filters: {filters}")
                continue
            
            filtered_snippets.append(snippet)
            filtered_similarities.append(similarity)
            log(f"Snippet '{snippet.id}' passed filters: similarity={similarity:.3f}, use_case='{snippet.use_case}', industry='{snippet.industry}', role='{snippet.role}'")
        
        log(f"After filtering: {len(filtered_snippets)} snippets remain")
        
        # Sort by similarity and return top_k
        sorted_pairs = sorted(
            zip(filtered_snippets, filtered_similarities),
            key=lambda x: x[1],
            reverse=True
        )
        
        result = sorted_pairs[:top_k]
        log(f"Returning {len(result)} top results")
        
        for i, (snippet, score) in enumerate(result):
            log(f"Result {i+1}: '{snippet.id}' (score={score:.3f}) - {snippet.use_case} for {snippet.industry} {snippet.role}")
        
        return result
    
    def _get_query_embedding(self, query_text: str) -> np.ndarray:
        """Get embedding for query text."""
        if self.use_sentence_transformers and self.model:
            return self.model.encode([query_text])[0]
        elif self.simple_embeddings:
            return self.simple_embeddings.transform([query_text])[0]
        else:
            # Fallback: return zero vector
            return np.zeros(self.embeddings.shape[1] if self.embeddings is not None else 1000)
    
    def _calculate_tfidf_similarity(self, query_text: str) -> np.ndarray:
        """Calculate TF-IDF similarity as fallback."""
        if self.vectorizer is None:
            # Create vectorizer from snippets
            texts = []
            for snippet in self.snippets:
                text_parts = [
                    snippet.content,
                    ' '.join(snippet.tags),
                    snippet.use_case,
                    snippet.tone,
                    snippet.industry,
                    snippet.role
                ]
                texts.append(' '.join(text_parts))
            
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.9
            )
            self.vectorizer.fit(texts)
        
        # Transform query and calculate similarity
        query_vector = self.vectorizer.transform([query_text])
        snippet_vectors = self.vectorizer.transform([
            ' '.join([
                snippet.content,
                ' '.join(snippet.tags),
                snippet.use_case,
                snippet.tone,
                snippet.industry,
                snippet.role
            ]) for snippet in self.snippets
        ])
        
        return cosine_similarity(query_vector, snippet_vectors)[0]
    
    def _matches_filters(self, snippet: EmailSnippet, filters: Dict[str, Any]) -> bool:
        """
        Check if snippet matches the given filters.
        
        Args:
            snippet: Email snippet to check
            filters: Filter criteria
            
        Returns:
            True if snippet matches filters, False otherwise
        """
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
        """
        Get all snippets in a specific category.
        
        Args:
            category: Category name (use_case, tone, industry, etc.)
            
        Returns:
            List of snippets in the category
        """
        if not self._loaded:
            self.load_snippets()
        
        return [s for s in self.snippets if getattr(s, category, None)]
    
    def get_snippet_by_id(self, snippet_id: str) -> Optional[EmailSnippet]:
        """
        Get a specific snippet by ID.
        
        Args:
            snippet_id: Snippet ID
            
        Returns:
            EmailSnippet object or None if not found
        """
        if not self._loaded:
            self.load_snippets()
        
        for snippet in self.snippets:
            if snippet.id == snippet_id:
                return snippet
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded snippets.
        
        Returns:
            Dictionary with statistics
        """
        if not self._loaded:
            self.load_snippets()
        
        stats = {
            'total_snippets': len(self.snippets),
            'industries': {},
            'use_cases': {},
            'tones': {},
            'roles': {}
        }
        
        for snippet in self.snippets:
            # Count industries
            industry = snippet.industry
            stats['industries'][industry] = stats['industries'].get(industry, 0) + 1
            
            # Count use cases
            use_case = snippet.use_case
            stats['use_cases'][use_case] = stats['use_cases'].get(use_case, 0) + 1
            
            # Count tones
            tone = snippet.tone
            stats['tones'][tone] = stats['tones'].get(tone, 0) + 1
            
            # Count roles
            role = snippet.role
            if role:
                stats['roles'][role] = stats['roles'].get(role, 0) + 1
        
        return stats 