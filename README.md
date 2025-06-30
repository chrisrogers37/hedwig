# 🦉 Hedwig - AI Email Assistant

## Overview

Hedwig features a **conversational chatbot interface** that makes creating personalized sales emails as easy as having a conversation. No more filling out forms - just chat naturally with the AI!

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Your API Key
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Chatbot
```bash
cd src
streamlit run app_chatbot.py
```

The app will open in your browser at `http://localhost:8501`

## 💬 How to Use

### Basic Conversation Flow

1. **Start the conversation** - Tell the AI what kind of email you want to write
2. **Get your email** - The AI generates a personalized email based on your request
3. **Provide feedback** - Ask for changes or improvements naturally
4. **Refine and finalize** - The AI incorporates your feedback and maintains conversation context

### Example Conversation

```
You: I want to create an outreach email for reaching out to venues in NYC to get DJ gigs. I am a local DJ in NYC

AI: [Generates a professional DJ outreach email with venue-appropriate tone and structure]

You: This is very good! Please fill in placeholders with my contact info: CROG, 5082597980, crogmusic@gmail.com, https://soundcloud.com/notcrog

AI: [Updates the email with your contact information]

You: Please format the contact info better - put each on a separate line

AI: [Reformats the contact information as requested]
```

## ⚙️ Configuration

### Sidebar Settings

- **Model Provider**: Currently supports OpenAI
- **Model Selection**: Choose from GPT-4, GPT-4 Turbo, or GPT-3.5 Turbo
- **API Key**: Enter your OpenAI API key (or set in .env file)
- **Default Tone**: Set your preferred email tone
- **Language**: Choose the email language

### Context Display

Toggle "Show Extracted Context" in the sidebar to see what information the AI has extracted from your conversation.

## 🎯 Features

### ✅ What's New (vs. Old Form Interface)

- **Natural Conversation**: No more rigid forms - chat naturally
- **Intelligent RAG**: Automatically finds relevant email templates for your use case
- **Enhanced Context**: Maintains full conversation history for better email generation
- **Real-time Configuration**: Change settings without restarting
- **Context Visualization**: See what the AI understands about your request
- **Copy to Clipboard**: One-click email copying
- **Conversation Management**: Clear, regenerate, or restart conversations

### 🔧 Technical Features

- **Provider-Agnostic**: Built to support multiple LLM providers (OpenAI first)
- **Session Management**: Maintains conversation state during your session
- **Error Handling**: Graceful handling of API errors and missing configuration
- **Responsive Design**: Works on desktop and mobile devices
- **RAG Integration**: Retrieves relevant YAML templates with guidance for better generation
- **Modular Architecture**: Clean separation of concerns with utilities and services
- **YAML Templates**: Structured template format with metadata, content, and writing guidance

## 🧪 Testing

Run tests to ensure everything works:
```bash
python -m pytest
```

## 🗂️ File Structure

```
hedwig/
├── src/
│   ├── app_chatbot.py              # Main chatbot Streamlit app
│   ├── services/                   # Core business logic services
│   │   ├── __init__.py
│   │   ├── chat_history_manager.py # Conversation state and history management
│   │   ├── config_service.py       # Configuration and environment management
│   │   ├── llm_service.py          # Language model interface (OpenAI, etc.)
│   │   ├── profile_manager.py      # User profile management and session state
│   │   ├── prompt_builder.py       # Prompt construction with RAG context
│   │   ├── scroll_retriever.py     # YAML template retrieval and embedding
│   │   └── simple_embeddings.py    # Lightweight semantic embeddings
│   ├── utils/                      # Shared utilities and helpers
│   │   ├── __init__.py
│   │   ├── logging_utils.py        # Centralized logging with prefixes
│   │   ├── text_utils.py           # Text preprocessing and normalization
│   │   ├── file_utils.py           # Safe file I/O and YAML parsing
│   │   ├── error_utils.py          # Error handling and safe execution
│   │   ├── config_utils.py         # Environment and config management
│   │   └── yaml_template_parser.py # YAML template structure parsing
│   └── tests/                      # Comprehensive test suite
│       ├── conftest.py             # Pytest configuration and fixtures
│       ├── test_app_chatbot.py     # Main app integration tests
│       ├── test_services/          # Service-specific tests
│       │   ├── __init__.py
│       │   ├── test_chat_history_manager.py
│       │   ├── test_chatbot_app.py
│       │   ├── test_config_service.py
│       │   ├── test_llm_service.py
│       │   ├── test_prompt_builder.py
│       │   ├── test_scroll_retriever.py
│       │   ├── test_simple_embeddings.py
│       │   └── test_snippet_retriever_queries.py
│       └── test_utils/             # Utility-specific tests
│           ├── __init__.py
│           ├── test_logging_utils.py
│           ├── test_text_utils.py
│           ├── test_file_utils.py
│           ├── test_error_utils.py
│           ├── test_config_utils.py
│           └── test_yaml_template_parser.py
├── scrolls/                        # Email templates in YAML format
│   ├── README.md                   # Template documentation
│   ├── entertainment/              # Entertainment industry templates
│   │   ├── band/
│   │   │   └── to_venue/
│   │   │       └── gig_outreach.yaml
│   │   └── dj/
│   │       └── to_venue/
│   │           └── gig_outreach.yaml
│   ├── general/                    # General business templates
│   │   ├── churn_recovery/
│   │   │   └── win_back_campaign.yaml
│   │   ├── event_invitation/
│   │   │   └── webinar_invite.yaml
│   │   ├── follow_up/
│   │   │   └── value_add_followup.yaml
│   │   ├── introduction/
│   │   │   └── conference_connection.yaml
│   │   └── partnership/
│   │       └── strategic_alliance.yaml
│   ├── healthcare/                 # Healthcare industry templates
│   │   └── sales_rep/
│   │       ├── to_doctor/
│   │       │   └── saas_outreach.yaml
│   │       └── to_patient/
│   │           └── saas_outreach.yaml
│   └── tech/                       # Technology industry templates
│       └── sales_rep/
│           ├── to_enterprise/
│           │   └── saas_outreach.yaml
│           └── to_startup/
│               └── saas_outreach.yaml
├── planning_docs/                  # Project planning and documentation
│   ├── architecture.md             # System architecture overview
│   ├── refactor_plan.md            # Refactoring progress and status
│   ├── tasks.md                    # Development tasks and roadmap
│   ├── rag_feature_overview.md     # RAG system documentation
│   ├── yaml_migration_plan.md      # YAML template migration planning
│   ├── yaml_migration_summary.md   # YAML migration completion summary
│   └── yaml_implementation_work_plan.md # Detailed YAML implementation work
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Project configuration and metadata
└── README.md                       # This file
```

## 🛠️ Utilities Overview

Hedwig uses a comprehensive set of shared utility modules to ensure DRY principles, clean separation of concerns, and robust error handling throughout the application:

### Core Utilities

- **logging_utils.py**: Centralized logging system with support for log levels, prefixes, and structured output. Provides consistent logging across all services with configurable verbosity.

- **text_utils.py**: Text preprocessing and normalization utilities. Handles whitespace cleanup, special character processing, and text standardization for consistent embedding generation.

- **file_utils.py**: Safe file I/O operations including reading, writing, YAML parsing, and file discovery. Provides robust error handling for file operations and supports multiple file formats.

- **error_utils.py**: Comprehensive error handling system with safe execution decorators, retry logic, and standardized error formatting. Includes context-aware error messages and graceful failure handling.

- **config_utils.py**: Environment variable and configuration file management. Handles loading, validation, masking of sensitive data, and merging of configuration sources (defaults, environment, files).

- **yaml_template_parser.py**: Specialized YAML template parsing for the scrolls system. Extracts metadata, template content, and writing guidance from structured YAML files with validation.

### Utility Integration

These utilities are used throughout the services layer to ensure:
- **Maintainability**: Consistent patterns and centralized functionality
- **Reliability**: Robust error handling and safe operations
- **Performance**: Optimized file operations and text processing
- **Security**: Proper handling of sensitive configuration data
- **Testability**: Isolated, well-defined utility functions

### Key Features

- **Error Recovery**: Automatic retry logic for transient failures
- **Safe Operations**: Decorators for safe execution with fallback values
- **Configuration Management**: Environment-aware configuration loading
- **File Safety**: Protected file operations with proper error handling
- **Text Processing**: Standardized text normalization for embeddings
- **Logging**: Structured logging with prefixes and levels

## 🔄 Recent Updates

### YAML Template Format
- **Structured Templates**: All templates now use YAML format with `metadata:`, `template:`, and `guidance:` sections
- **Writing Guidance**: Templates include specific phrases to avoid and preferred alternatives
- **Enhanced RAG**: Templates are embedded based on metadata tags, notes, and content for better matching
- **Guidance Integration**: Writing guidance is automatically included in prompts for better email quality

### Simplified Conversation Flow
- **No Message Classification**: All user messages are treated as initial prompts for simplicity
- **Enhanced Context**: Full conversation history is maintained and used for RAG retrieval
- **Feedback Integration**: User feedback is naturally incorporated into subsequent generations
- **Context Preservation**: All previous messages are included in enhanced RAG context

### Improved Architecture
- **Utility Layer**: Comprehensive utilities for text processing, file I/O, error handling, and configuration
- **Service Separation**: Clean separation of concerns with focused service responsibilities
- **Test Organization**: Tests organized by service and utility categories
- **Error Handling**: Robust error handling throughout the application

## 🚧 Known Limitations

- Currently only supports OpenAI (other providers coming soon)
- Session state is ephemeral (clears on page refresh)
- Requires internet connection for API calls

## 🎉 Benefits

1. **User-Friendly**: No learning curve - just chat naturally
2. **Intelligent**: AI automatically finds relevant templates and guidance
3. **Contextual**: Maintains full conversation history for better results
4. **Flexible**: No rigid form fields - provide information in any order
5. **High-Quality**: Writing guidance ensures natural, effective emails

## 🔮 Future Enhancements

- Multi-provider support (Anthropic, Google, etc.)
- Conversation history persistence
- Template rating and feedback system
- A/B testing suggestions
- Integration with email clients
- Team collaboration features

## 🗺️ ROADMAP

### RAG System Enhancements

#### High Priority (Complete the MVP)
- **Template Visibility**: Add sidebar showing "Relevant Email Templates Used" in the UI
- **RAG Toggle**: Add UI toggle to disable/enable RAG functionality
- **Template Preview**: Let users see the retrieved templates before generation

#### Medium Priority (Enhance UX)
- **Template Rating**: Let users rate how helpful templates were
- **Manual Template Selection**: Allow users to choose specific templates from UI
- **Template Categories**: Organize templates by industry/use case in the interface

#### Low Priority (Future Enhancements)
- **FAISS Integration**: Replace in-memory storage with FAISS for larger template libraries
- **User Memory**: Add user-specific template memory when authentication is implemented
- **Advanced Interpolation**: Add "copy structure but rephrase" feature for template adaptation

### Technical Improvements
- **Performance Optimization**: Implement caching for frequently used templates
- **Template Analytics**: Track which templates are most effective
- **Dynamic Thresholds**: Industry-specific similarity thresholds for better template matching

## 🏗️ Architecture

### Services Layer
- **ChatHistoryManager**: Manages conversation state, message history, and conversation context. Handles message types, conversation summarization, and history trimming for performance.

- **ConfigService**: Handles configuration and environment variables with validation, masking of sensitive data, and support for multiple configuration sources (defaults, environment, files).

- **LLMService**: Interfaces with language models (OpenAI, etc.) with error handling, retry logic, and response processing. Supports multiple providers and models.

- **PromptBuilder**: Constructs prompts with RAG context and writing guidance. Manages enhanced conversation context, template retrieval, and prompt optimization for natural language generation.

- **ScrollRetriever**: Retrieves relevant YAML email templates using semantic search. Handles template loading, embedding generation, similarity matching, and template caching.

- **SimpleEmbeddings**: Lightweight semantic embeddings using TF-IDF and SVD. Provides fallback embedding functionality when sentence-transformers is unavailable.

### Utilities Layer
- **LoggingUtils**: Standardized logging across the application with configurable levels, prefixes, and structured output for debugging and monitoring.

- **TextUtils**: Text preprocessing and normalization utilities for consistent embedding generation, including whitespace cleanup and special character handling.

- **FileUtils**: Safe file I/O and YAML parsing with robust error handling, file discovery, and support for multiple file formats and encodings.

- **ErrorUtils**: Error handling and safe execution with decorators, retry logic, context-aware error messages, and graceful failure handling.

- **ConfigUtils**: Configuration management and validation with environment variable loading, file-based config support, and sensitive data masking.

- **YamlTemplateParser**: YAML template parsing and structure extraction for the scrolls system, with validation and metadata extraction.

### Testing Architecture
- **Comprehensive Test Suite**: 259+ tests covering all functionality with high coverage
- **Service Tests**: Isolated testing of business logic with mocked dependencies
- **Utility Tests**: Testing of shared utilities with edge cases and error conditions
- **Integration Tests**: End-to-end functionality testing including YAML template integration
- **Test Organization**: Clear separation between service and utility tests for maintainability 