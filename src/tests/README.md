# 🧪 Testing Guide for OutboundOwl

This guide covers the comprehensive testing strategy for OutboundOwl, including how to run tests, understand test coverage, and contribute new tests.

## 📋 Test Overview

OutboundOwl uses **pytest** for testing with comprehensive coverage across all core services:

- **62 total tests** across 5 test modules
- **100% test coverage** for critical functionality
- **Modular test design** matching the service architecture
- **Mock-based testing** for external dependencies

## 🏗️ Test Architecture

### Test Structure
```
src/tests/
├── README.md                    # This file
├── conftest.py                  # Pytest configuration and shared fixtures
├── test_chat_history_manager.py # Chat history and conversation management
├── test_config_service.py       # Configuration management
├── test_llm_service.py          # LLM integration and API calls
├── test_prompt_builder.py       # Prompt construction and context building
└── test_chatbot_app.py          # Streamlit app integration
```

### Test Categories

#### 1. **ChatHistoryManager Tests** (25 tests)
Tests conversation state management, message handling, and persistence.

**Key Test Areas:**
- Message creation and storage
- Conversation context building
- Message type filtering
- Conversation summarization
- Import/export functionality
- Session state management

**Example Test:**
```python
def test_add_message(self):
    """Test adding messages."""
    manager = ChatHistoryManager()
    manager.start_conversation("test_conv")
    
    msg_id = manager.add_message(
        content="Test draft",
        message_type=MessageType.DRAFT,
        metadata={"tone": "professional"}
    )
    
    assert len(manager.messages) == 1
    assert manager.messages[0].content == "Test draft"
    assert manager.messages[0].type == MessageType.DRAFT
```

#### 2. **PromptBuilder Tests** (18 tests)
Tests prompt construction, context building, and conversation flow.

**Key Test Areas:**
- Prompt generation from conversation history
- Tone-specific instructions
- Profile integration
- Latest message extraction
- Feedback handling

**Example Test:**
```python
def test_build_llm_prompt_latest_user_message_only(prompt_builder, chat_history_manager):
    """Test that only the latest user message is used in the prompt."""
    chat_history_manager.add_message("First request", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_message("Second request", MessageType.INITIAL_PROMPT)
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "Second request" in prompt  # Latest message
    assert "First request" not in prompt  # Earlier message not included
```

#### 3. **LLMService Tests** (4 tests)
Tests LLM integration, API communication, and error handling.

**Key Test Areas:**
- Service initialization
- API key validation
- Response generation
- Error handling

#### 4. **ConfigService Tests** (5 tests)
Tests configuration management and environment handling.

**Key Test Areas:**
- Default configuration
- Environment variable loading
- File-based configuration
- Configuration validation

#### 5. **ChatbotApp Tests** (3 tests)
Tests Streamlit app integration and service initialization.

**Key Test Areas:**
- App import and initialization
- Service setup with valid/invalid config
- Streamlit integration

## 🚀 Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Ensure you're in the src directory
cd src
```

### Basic Test Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=services --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_prompt_builder.py -v

# Run specific test function
python -m pytest tests/test_prompt_builder.py::test_build_llm_prompt_with_empty_history -v

# Run tests matching a pattern
python -m pytest tests/ -k "placeholder" -v
```

### Coverage Reports

```bash
# Generate HTML coverage report
python -m pytest tests/ --cov=services --cov-report=html

# Generate XML coverage report (for CI/CD)
python -m pytest tests/ --cov=services --cov-report=xml

# Generate detailed coverage report
python -m pytest tests/ --cov=services --cov-report=term-missing --cov-report=html
```

### Test Output Examples

**Successful Test Run:**
```
============================================== test session starts ===============================================
platform darwin -- Python 3.11.12, pytest-8.0.2, pluggy-1.6.0
collected 62 items

src/tests/test_chat_history_manager.py::TestChatMessage::test_chat_message_creation PASSED
src/tests/test_chat_history_manager.py::TestChatMessage::test_chat_message_to_dict PASSED
...
src/tests/test_prompt_builder.py::test_custom_profile_initialization PASSED

=============================================== 62 passed in 1.73s ===============================================
```

**With Coverage:**
```
---------- coverage: platform darwin, python 3.11.12-final-0 -----------
Name                                    Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
services/__init__.py                        0      0   100%
services/chat_history_manager.py          150      0   100%
services/config_service.py                 99      0   100%
services/llm_service.py                    45      0   100%
services/logging_utils.py                   2      0   100%
services/prompt_builder.py                205      0   100%
-------------------------------------------------------------------------
TOTAL                                     501      0   100%
```

## 🧩 Test Fixtures

### Shared Fixtures (conftest.py)

```python
@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = AppConfig(load_env=False)
    config.set("OPENAI_API_KEY", "test-api-key")
    config.set("OPENAI_MODEL", "gpt-4")
    config.set("DEFAULT_TONE", "professional")
    config.set("DEFAULT_LANGUAGE", "English")
    return config

@pytest.fixture
def chat_history_manager():
    """Create a fresh ChatHistoryManager instance for testing."""
    return ChatHistoryManager()

@pytest.fixture
def prompt_builder(mock_llm_service, chat_history_manager, mock_config):
    """Create a fresh PromptBuilder instance for testing."""
    return PromptBuilder(mock_llm_service, chat_history_manager, config=mock_config)
```

### Using Fixtures

```python
def test_example(prompt_builder, chat_history_manager):
    """Example test using fixtures."""
    # Use the fixtures directly
    chat_history_manager.add_message("Test message", MessageType.INITIAL_PROMPT)
    prompt = prompt_builder.build_llm_prompt()
    assert "Test message" in prompt
```

## 🔧 Mocking Strategy

### External Dependencies

**LLM API Calls:**
```python
with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
    mock_generate.return_value = "Mock response"
    result = prompt_builder.generate_draft()
    assert result == "Mock response"
```

**File System Operations:**
```python
with patch('builtins.open', mock_open(read_data='test data')):
    # Test file operations
    pass
```

**Environment Variables:**
```python
with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
    # Test environment-dependent code
    pass
```

## 📊 Test Coverage Goals

### Current Coverage: 100%
- **ChatHistoryManager**: 100% (150/150 statements)
- **PromptBuilder**: 100% (205/205 statements)
- **LLMService**: 100% (45/45 statements)
- **ConfigService**: 100% (99/99 statements)

### Coverage Targets
- **Critical Paths**: 100% coverage required
- **Error Handling**: 100% coverage required
- **Edge Cases**: 90%+ coverage
- **Integration Points**: 100% coverage required

## 🐛 Debugging Tests

### Common Issues

**Import Errors:**
```bash
# Ensure you're in the src directory
cd src

# Check Python path
python -c "import sys; print(sys.path)"

# Run with explicit path
PYTHONPATH=src python -m pytest tests/
```

**Mock Issues:**
```python
# Use patch.object for instance methods
with patch.object(instance, 'method_name') as mock_method:
    mock_method.return_value = expected_value

# Use patch for module-level functions
with patch('module.function_name') as mock_function:
    mock_function.return_value = expected_value
```

**Session State Issues:**
```python
# Mock Streamlit session state
with patch('streamlit.session_state') as mock_session:
    mock_session.get.return_value = expected_value
```

### Debug Mode

```bash
# Run with debug output
python -m pytest tests/ -v -s

# Run single test with debug
python -m pytest tests/test_prompt_builder.py::test_specific -v -s --pdb
```

## 📝 Writing New Tests

### Test Naming Convention

```python
def test_[function_name]_[scenario]_[expected_behavior]():
    """Test description."""
    pass

# Examples:
def test_build_llm_prompt_with_empty_history():
    """Test building prompt with empty conversation history."""
    
def test_add_message_with_metadata():
    """Test adding message with custom metadata."""
    
def test_generate_response_api_error():
    """Test generate_response handles API errors."""
```

### Test Structure

```python
def test_example():
    """Test description."""
    # Arrange - Set up test data and mocks
    mock_service = Mock()
    test_data = "test input"
    
    # Act - Execute the function being tested
    result = function_under_test(test_data, mock_service)
    
    # Assert - Verify the expected behavior
    assert result == "expected output"
    mock_service.method.assert_called_once_with(test_data)
```

### Best Practices

1. **One Assertion Per Test**: Each test should verify one specific behavior
2. **Descriptive Names**: Test names should clearly describe what's being tested
3. **Arrange-Act-Assert**: Structure tests with clear sections
4. **Mock External Dependencies**: Don't rely on external services in tests
5. **Test Edge Cases**: Include tests for error conditions and boundary cases
6. **Use Fixtures**: Reuse common setup code through fixtures

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          cd src
          python -m pytest tests/ --cov=services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Mock Documentation](https://pytest-mock.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)

---

**Happy Testing! 🧪✨** 