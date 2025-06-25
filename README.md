# 🦉 OutboundOwl - AI-Powered Conversational Email Assistant

## Overview

OutboundOwl is an intelligent email assistant that creates personalized outreach emails through natural conversation. Instead of filling out rigid forms, simply chat with the AI about your goals, and it will guide you to create compelling, personalized emails for any use case.

## ✨ Key Features

- **🎯 Conversational Interface**: Chat naturally with the AI to describe your email goals
- **🧠 Context-Aware**: The AI remembers your conversation and builds context progressively
- **🔄 Session Persistence**: Your conversation state is maintained across interactions
- **🎨 Multiple Tones**: Choose from professional, casual, friendly, formal, or natural tones
- **🌍 Multi-Language**: Support for English, Spanish, French, and German
- **📋 One-Click Copy**: Copy generated emails directly to your clipboard
- **🔄 Regenerate**: Easily regenerate emails with different approaches
- **📊 Conversation Stats**: Track your conversation progress and history

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### 1. Clone and Install
```bash
git clone <repository-url>
cd outbound-owl
pip install -r requirements.txt
```

### 2. Set Up Your API Key
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Application
```bash
cd src
streamlit run app_chatbot.py
```

The app will open in your browser at `http://localhost:8501`

## 💬 How It Works

### Conversational Flow

1. **Start Chatting**: Describe what kind of email you want to create
2. **AI Guides You**: The AI asks for missing information naturally
3. **Get Your Email**: Receive a personalized, professional email draft
4. **Iterate**: Provide feedback to refine the email further

### Example Conversation

```
You: I need help writing an outreach email for getting DJ gigs in NYC

AI: I'd be happy to help you create an outreach email for DJ gigs! To make this 
    compelling, I need a few details:
    
    - Your name and what you do as a DJ
    - What types of venues or events you're targeting
    - What makes you unique or special
    - What you're offering (rates, availability, etc.)

You: I'm DJ Alex, I do electronic and hip-hop. I'm targeting nightclubs and 
     corporate events. I have 5 years experience and can work any night.

AI: Perfect! Here's a draft outreach email for you:

    [Generated personalized email]

    Would you like me to adjust the tone or add any specific details?
```

## 🏗️ Architecture

OutboundOwl is built with a modular, service-oriented architecture:

### Core Services

- **`ChatHistoryManager`**: Manages conversation state and message history
- **`PromptBuilder`**: Constructs context-aware prompts from conversation history
- **`LLMService`**: Handles communication with language models
- **`ConfigService`**: Manages application configuration and settings

### Key Design Principles

- **Separation of Concerns**: Each service has a single responsibility
- **Session State Management**: Persistent conversation state across Streamlit reruns
- **Conversational-First**: Built around natural conversation flow
- **Extensible**: Easy to add new LLM providers or features

## ⚙️ Configuration

### Sidebar Settings

- **Provider**: Currently supports OpenAI (extensible for other providers)
- **Model**: Choose from GPT-4, GPT-4 Turbo, or GPT-3.5 Turbo
- **API Key**: Enter your OpenAI API key (or set in .env file)
- **Default Tone**: Set your preferred email tone (natural, professional, casual, friendly, formal)
- **Language**: Choose the email language

### Conversation Management

- **Show Conversation Stats**: View detailed conversation analytics
- **Clear Conversation**: Start fresh with a new conversation
- **Regenerate**: Create a new version of the current email

## 🧪 Testing

OutboundOwl includes comprehensive test coverage. See [Testing Guide](src/tests/README.md) for detailed information.

### Quick Test Commands

```bash
# Run all tests
cd src
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_prompt_builder.py -v
python -m pytest tests/test_chat_history_manager.py -v
python -m pytest tests/test_llm_service.py -v

# Run with coverage
python -m pytest tests/ --cov=services --cov-report=html
```

## 📁 Project Structure

```
outbound-owl/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── src/
│   ├── app_chatbot.py          # Main Streamlit application
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_history_manager.py  # Conversation state management
│   │   ├── config_service.py        # Configuration management
│   │   ├── llm_service.py           # LLM integration
│   │   ├── prompt_builder.py        # Context-aware prompt construction
│   │   └── logging_utils.py         # Logging utilities
│   └── tests/
│       ├── README.md            # Testing guide
│       ├── conftest.py          # Pytest configuration
│       ├── test_chat_history_manager.py
│       ├── test_config_service.py
│       ├── test_llm_service.py
│       ├── test_prompt_builder.py
│       └── test_chatbot_app.py
└── venv/                        # Virtual environment (not in repo)
```

## 🔧 Development

### Setting Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov
```

### Running Tests

```bash
cd src
python -m pytest tests/ -v --cov=services --cov-report=term-missing
```

### Code Style

The project follows PEP 8 guidelines. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

## 🚧 Known Limitations

- **Provider Support**: Currently only supports OpenAI (other providers planned)
- **Session Persistence**: Session state clears on browser refresh (persistent storage planned)
- **Internet Required**: Requires active internet connection for API calls
- **Token Limits**: Long conversations may hit LLM token limits (auto-summarization implemented)

## 🎯 Use Cases

OutboundOwl is perfect for:

- **Sales Outreach**: Cold emails to potential clients
- **Networking**: Follow-up emails after meetings or events
- **Job Applications**: Professional outreach to hiring managers
- **Partnership Proposals**: Business development emails
- **Event Promotion**: Outreach to venues, sponsors, or attendees
- **Content Collaboration**: Reaching out to potential collaborators

## 🔮 Roadmap

### Short Term
- [ ] Persistent conversation storage
- [ ] Email template library
- [ ] A/B testing suggestions
- [ ] Email performance analytics

### Medium Term
- [ ] Multi-provider support (Anthropic, Google, etc.)
- [ ] Team collaboration features
- [ ] Integration with email clients
- [ ] Advanced tone customization

### Long Term
- [ ] AI-powered email optimization
- [ ] Multi-language conversation support
- [ ] Voice interface
- [ ] Mobile app

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow the existing code style
- Update documentation as needed
- Ensure all tests pass before submitting

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Powered by [OpenAI](https://openai.com/) for language model capabilities
- Inspired by the need for more natural, conversational AI tools

---

**Ready to create amazing emails through conversation? Start chatting with OutboundOwl today!** 🦉 