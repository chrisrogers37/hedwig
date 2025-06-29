#!/usr/bin/env python3
"""
Test script to evaluate ScrollRetriever performance on specific queries.
"""

import sys
import os
sys.path.append('src')

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
from datetime import datetime
import yaml

from src.services.scroll_retriever import ScrollRetriever

def test_queries():
    """Test the two example queries."""
    
    # Initialize retriever
    retriever = ScrollRetriever(snippets_dir='scrolls')
    loaded_count = retriever.load_snippets()
    print(f"Loaded {loaded_count} snippets")
    print()
    
    # Test query 1: DJ sets
    print('=== QUERY 1: DJ Sets ===')
    query1 = 'I would like to create an email outreach to local clubs and venues for getting DJ sets'
    print(f"Query: {query1}")
    print()
    
    results1 = retriever.query(query1, top_k=3, min_similarity=0.75)
    if results1:
        for i, (snippet, score) in enumerate(results1, 1):
            print(f'{i}. Score: {score:.3f}')
            print(f'   Use Case: {snippet.use_case}')
            print(f'   Industry: {snippet.industry}')
            print(f'   Role: {snippet.metadata.get("role", "")}')
            print(f'   Content: {snippet.content[:150]}...')
            print()
    else:
        print("No relevant templates found!")
    print()
    
    # Test query 2: Band gigs
    print('=== QUERY 2: Band Gigs ===')
    query2 = 'I would like to create an email outreach to local venues to get my band booked for a live gig'
    print(f"Query: {query2}")
    print()
    
    results2 = retriever.query(query2, top_k=3, min_similarity=0.75)
    if results2:
        for i, (snippet, score) in enumerate(results2, 1):
            print(f'{i}. Score: {score:.3f}')
            print(f'   Use Case: {snippet.use_case}')
            print(f'   Industry: {snippet.industry}')
            print(f'   Role: {snippet.metadata.get("role", "")}')
            print(f'   Content: {snippet.content[:150]}...')
            print()
    else:
        print("No relevant templates found!")
    print()
    
    # Test query 3: SaaS dietician
    print('=== QUERY 3: SaaS Dietician ===')
    query3 = 'I would like to create an outreach to send to doctors to try and convince them to sign up for Nourish, a SaaS dietician company that patients can sign up for for online consulting'
    print(f"Query: {query3}")
    print()
    
    results3 = retriever.query(query3, top_k=3, min_similarity=0.75)
    if results3:
        for i, (snippet, score) in enumerate(results3, 1):
            print(f'{i}. Score: {score:.3f}')
            print(f'   Use Case: {snippet.use_case}')
            print(f'   Industry: {snippet.industry}')
            print(f'   Role: {snippet.metadata.get("role", "")}')
            print(f'   Content: {snippet.content[:150]}...')
            print()
    else:
        print("No relevant templates found!")

if __name__ == "__main__":
    test_queries() 