#!/usr/bin/env python3
"""
Demo script for the Hedwig chatbot interface.
This demonstrates the conversational flow without requiring Streamlit.
"""

import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from services.config_service import AppConfig
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder, Profile
from unittest.mock import Mock, patch

def run_demo():
    print("Welcome to Hedwig Demo Chatbot!")
    profile = Profile()
    prompt_builder = PromptBuilder(None, profile)
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"): break
        prompt_builder.add_message(user_input)
        draft = prompt_builder.get_draft_email()
        if draft:
            print(f"Hedwig (draft email):\n{draft}")
        else:
            print("Hedwig: I'm not sure how to respond. Please try again.")
        # Optionally allow profile editing
        if input("Edit profile? (y/N): ").strip().lower() == 'y':
            profile.your_name = input("Your Name: ")
            profile.your_title = input("Your Title: ")
            profile.company_name = input("Your Company: ")

def demo_context_extraction():
    """Demonstrate how context is extracted from conversation."""
    print("\n" + "=" * 50)
    print("🔍 Context Extraction Demo")
    print("=" * 50)
    
    # Mock the context extraction
    mock_context = Mock()
    mock_context.your_name = "John Smith"
    mock_context.your_title = "Sales Manager"
    mock_context.company_name = "TechCorp"
    mock_context.recipient_name = "Sarah Johnson"
    mock_context.recipient_organization = "InnovateTech"
    mock_context.email_type = "cold_outreach"
    mock_context.tone = "professional"
    mock_context.language = "English"
    mock_context.value_propositions = [
        {"title": "Sales Increase", "content": "30% increase in sales"},
        {"title": "Customer Retention", "content": "Reduced customer churn"},
        {"title": "Industry Focus", "content": "Specifically designed for tech companies"}
    ]
    
    print("📋 Extracted Context:")
    print(f"  Your Name: {mock_context.your_name}")
    print(f"  Your Title: {mock_context.your_title}")
    print(f"  Company: {mock_context.company_name}")
    print(f"  Recipient: {mock_context.recipient_name}")
    print(f"  Organization: {mock_context.recipient_organization}")
    print(f"  Email Type: {mock_context.email_type}")
    print(f"  Tone: {mock_context.tone}")
    print(f"  Language: {mock_context.language}")
    print("  Value Propositions:")
    for i, prop in enumerate(mock_context.value_propositions, 1):
        print(f"    {i}. {prop['title']}: {prop['content']}")

if __name__ == "__main__":
    run_demo()
    demo_context_extraction() 