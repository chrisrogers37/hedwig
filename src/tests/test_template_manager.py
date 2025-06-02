import pytest
from pathlib import Path
import json
from src.utils.template_manager import TemplateManager

@pytest.fixture
def template_manager(tmp_path):
    """Create a template manager with a temporary directory."""
    return TemplateManager(templates_dir=str(tmp_path))

@pytest.fixture
def sample_template_sections():
    """Create sample template sections for testing."""
    return {
        "email_subject": "Test Subject",
        "greeting": "Hello!",
        "background": "Test background",
        "why_choose_us": {
            "title": "Why Choose Us",
            "bullets": [
                {
                    "title": "Feature 1",
                    "content": "Description 1"
                }
            ]
        },
        "additional_bullets": {
            "title": "Additional Info",
            "content": "More details"
        },
        "scheduling": {
            "title": "Scheduling",
            "bullets": ["Point 1", "Point 2"]
        },
        "call_to_action": {
            "title": "Let's Connect",
            "content": "Contact us"
        },
        "meeting_note_detail": "When can we meet?",
        "sign_off": {
            "closing": "Best regards",
            "signature": "[Your Name]"
        }
    }

def test_save_and_load_template(template_manager, tmp_path, sample_template_sections):
    """Test saving and loading a template."""
    # Create a test template
    specialty = "TestSpecialty"
    variables = ["var1", "var2"]
    
    # Save the template
    template_manager.save_template(specialty, sample_template_sections, variables)
    
    # Verify the file was created
    template_file = tmp_path / f"{specialty.lower()}.json"
    assert template_file.exists()
    
    # Verify the content
    with open(template_file, "r") as f:
        saved_data = json.load(f)
        assert saved_data["specialty"] == specialty
        assert saved_data["template_sections"] == sample_template_sections
        assert saved_data["variables"] == variables
        assert "metadata" in saved_data

def test_get_template(template_manager, sample_template_sections):
    """Test retrieving a template."""
    # Save a test template
    specialty = "TestSpecialty"
    variables = ["var1", "var2"]
    template_manager.save_template(specialty, sample_template_sections, variables)
    
    # Get the template
    retrieved = template_manager.get_template(specialty)
    assert retrieved is not None
    assert retrieved["specialty"] == specialty
    assert retrieved["template_sections"] == sample_template_sections
    assert retrieved["variables"] == variables

def test_get_template_section(template_manager, sample_template_sections):
    """Test retrieving a specific template section."""
    specialty = "TestSpecialty"
    variables = ["var1", "var2"]
    template_manager.save_template(specialty, sample_template_sections, variables)
    
    # Get specific sections
    assert template_manager.get_template_section(specialty, "email_subject") == "Test Subject"
    assert template_manager.get_template_section(specialty, "greeting") == "Hello!"
    assert template_manager.get_template_section(specialty, "nonexistent") is None

def test_validate_template():
    """Test template validation."""
    template_manager = TemplateManager()
    
    # Valid template
    valid_template = {
        "specialty": "Test",
        "template_sections": {
            "email_subject": "Test",
            "greeting": "Hello",
            "background": "Test",
            "why_choose_us": {"title": "Test", "bullets": []},
            "additional_bullets": {"title": "Test", "content": "Test"},
            "scheduling": {"title": "Test", "bullets": []},
            "call_to_action": {"title": "Test", "content": "Test"},
            "meeting_note_detail": "Test",
            "sign_off": {"closing": "Test", "signature": "Test"}
        },
        "variables": ["var1"],
        "metadata": {
            "last_updated": "2024-03-19T00:00:00",
            "version": "1.0"
        }
    }
    assert template_manager.validate_template(valid_template)
    
    # Invalid template (missing fields)
    invalid_template = {
        "specialty": "Test",
        "template_sections": {}
    }
    assert not template_manager.validate_template(invalid_template)

def test_assemble_email(template_manager, sample_template_sections):
    """Test assembling a complete email from template sections."""
    specialty = "TestSpecialty"
    variables = {
        "your_name": "John Doe"
    }
    template_manager.save_template(specialty, sample_template_sections, list(variables.keys()))
    
    email = template_manager.assemble_email(specialty, variables)
    assert email is not None
    assert "Subject: Test Subject" in email
    assert "Hello!" in email
    assert "John Doe" in email
    assert "[your_name]" not in email 