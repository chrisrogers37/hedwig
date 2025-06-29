#!/usr/bin/env python3
"""
Backend/dev/test harness for app_chatbot logic.

This script allows you to run and debug the chatbot backend logic (services, prompt building, RAG, etc.) without the Streamlit UI. Useful for development, quick iteration, and log inspection.
"""

import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.services.config_service import AppConfig
from src.services.llm_service import LLMService
from src.services.prompt_builder import PromptBuilder, Profile
from src.services.chat_history_manager import ChatHistoryManager
from unittest.mock import Mock, patch

def run_demo():
    print("Welcome to Hedwig Demo Chatbot!")
    print("Type 'exit' or 'quit' to end the demo.\n")
    
    # Initialize services
    config = AppConfig()
    llm_service = LLMService(config)
    chat_history_manager = ChatHistoryManager()
    profile = Profile()
    prompt_builder = PromptBuilder(llm_service, chat_history_manager, profile, config)
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"): 
            break
            
        # Add user message to chat history
        chat_history_manager.add_message(user_input, chat_history_manager.MessageType.INITIAL_PROMPT)
        
        # Generate draft
        try:
            draft = prompt_builder.generate_draft()
            if draft:
                print(f"\nHedwig (draft email):\n{draft}\n")
            else:
                print("Hedwig: I'm not sure how to respond. Please try again.\n")
        except Exception as e:
            print(f"Hedwig: Sorry, I encountered an error: {e}\n")
        
        # Optionally allow profile editing
        if input("Edit profile? (y/N): ").strip().lower() == 'y':
            profile.name = input("Your Name: ")
            profile.title = input("Your Title: ")
            profile.company = input("Your Company: ")
            print("Profile updated!\n")

def demo_profile_management():
    """Demonstrate profile management functionality."""
    print("\n" + "=" * 50)
    print("👤 Profile Management Demo")
    print("=" * 50)
    
    # Create a profile
    profile = Profile(
        name="John Smith",
        title="Sales Manager", 
        company="TechCorp"
    )
    
    print("📋 Profile Information:")
    print(f"  Name: {profile.name}")
    print(f"  Title: {profile.title}")
    print(f"  Company: {profile.company}")
    
    # Demonstrate profile updates
    print("\n🔄 Updating Profile...")
    profile.name = "John A. Smith"
    profile.title = "Senior Sales Manager"
    
    print("📋 Updated Profile:")
    print(f"  Name: {profile.name}")
    print(f"  Title: {profile.title}")
    print(f"  Company: {profile.company}")

def demo_chat_history():
    """Demonstrate chat history management."""
    print("\n" + "=" * 50)
    print("💬 Chat History Demo")
    print("=" * 50)
    
    chat_manager = ChatHistoryManager()
    
    # Add some messages
    chat_manager.add_message("I need help writing an outreach email", chat_manager.MessageType.INITIAL_PROMPT)
    chat_manager.add_draft("Here's a draft email for you...")
    chat_manager.add_message("Make it more professional", chat_manager.MessageType.FEEDBACK)
    
    print("📝 Chat History:")
    for i, message in enumerate(chat_manager.messages, 1):
        print(f"  {i}. [{message.type.value}] {message.content[:50]}...")
    
    print(f"\n📊 Statistics:")
    print(f"  Total messages: {len(chat_manager.messages)}")
    print(f"  User messages: {len([m for m in chat_manager.messages if m.type == chat_manager.MessageType.INITIAL_PROMPT])}")
    print(f"  Drafts: {len([m for m in chat_manager.messages if m.type == chat_manager.MessageType.DRAFT])}")
    print(f"  Feedback: {len([m for m in chat_manager.messages if m.type == chat_manager.MessageType.FEEDBACK])}")

if __name__ == "__main__":
    print("🦉 Hedwig - Email Outreach Assistant")
    print("=" * 50)
    
    # Run demos
    demo_profile_management()
    demo_chat_history()
    
    print("\n" + "=" * 50)
    print("🚀 Starting Interactive Demo")
    print("=" * 50)
    run_demo() 