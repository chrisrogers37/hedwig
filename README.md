# 🦉 OutboundOwl - AI Email Assistant

## Overview

OutboundOwl features a **conversational chatbot interface** that makes creating personalized sales emails as easy as having a conversation. No more filling out forms - just chat naturally with the AI!

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
2. **Answer questions** - The AI will ask for missing information naturally
3. **Get your email** - Once enough context is gathered, your personalized email is generated

### Example Conversation

```
You: Hi, I want to write a cold outreach email to a potential client.

AI: I'd be happy to help! To create a personalized email, I need some information:
    - Your name and title
    - Your company name
    - The recipient's name and company
    - What you're offering
    - Any specific benefits
    - Your preferred tone

You: I'm John Smith, a sales manager at TechCorp. I want to reach out to Sarah Johnson at InnovateTech about our new CRM solution.

AI: Great! Now I need a bit more information to make this compelling:
    - What specific benefits does your CRM offer?
    - What makes it relevant for InnovateTech?
    - What tone would you prefer?

You: Our CRM helps companies increase sales by 30% and reduce customer churn. It's specifically designed for tech companies like theirs. I'd like a professional but friendly tone.

AI: Perfect! Here's your personalized cold outreach email:
    [Generated email content]
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
- **Progressive Context Building**: Information is gathered through conversation
- **Interactive Questioning**: AI asks for missing information when needed
- **Real-time Configuration**: Change settings without restarting
- **Context Visualization**: See what the AI understands about your request
- **Copy to Clipboard**: One-click email copying
- **Conversation Management**: Clear, regenerate, or restart conversations

### 🔧 Technical Features

- **Provider-Agnostic**: Built to support multiple LLM providers (OpenAI first)
- **Session Management**: Maintains conversation state during your session
- **Error Handling**: Graceful handling of API errors and missing configuration
- **Responsive Design**: Works on desktop and mobile devices

## 🧪 Testing

Run the demo to see the chatbot in action:
```bash
cd src
python demo_chatbot.py
```

Run tests to ensure everything works:
```bash
PYTHONPATH=src pytest src/tests/
```

## 📁 File Structure

```
src/
├── app_chatbot.py          # Main chatbot Streamlit app
├── demo_chatbot.py         # Demo script showing conversation flow
├── services/
│   ├── config_service.py   # Configuration management
│   ├── llm_service.py      # LLM integration
│   └── prompt_builder.py   # Conversational context building
└── tests/
    └── test_chatbot_app.py # Chatbot app tests
```

## 🔄 Migration from Old Interface

The old form-based interface has been completely replaced with this new conversational chatbot interface:

- **Old**: Fill out forms → Generate email
- **New**: Chat naturally → AI guides you → Generate email

The new interface provides a much better user experience with natural conversation flow and intelligent context building.

## 🚧 Known Limitations

- Currently only supports OpenAI (other providers coming soon)
- Session state is ephemeral (clears on page refresh)
- Requires internet connection for API calls

## 🎉 Benefits

1. **User-Friendly**: No learning curve - just chat naturally
2. **Flexible**: No rigid form fields - provide information in any order
3. **Intelligent**: AI guides you to provide the right information
4. **Efficient**: Faster than filling out forms
5. **Personalized**: Context-aware email generation

## 🔮 Future Enhancements

- Multi-provider support (Anthropic, Google, etc.)
- Conversation history persistence
- Email templates and variations
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