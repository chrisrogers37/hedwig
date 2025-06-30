"""
Tests for ProfileManager service.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.services.profile_manager import ProfileManager, Profile


class TestProfile:
    """Test Profile dataclass."""
    
    def test_profile_defaults(self):
        """Test Profile has correct default values."""
        profile = Profile()
        assert profile.name == ""
        assert profile.alias == ""
        assert profile.title == ""
        assert profile.company == ""
        assert profile.email == ""
        assert profile.phone == ""
        assert profile.website == ""
    
    def test_profile_custom_values(self):
        """Test Profile with custom values."""
        profile = Profile(
            name="John Doe",
            alias="Johnny",
            title="Manager",
            company="TechCorp",
            email="john@techcorp.com",
            phone="+1-555-123-4567",
            website="https://techcorp.com"
        )
        assert profile.name == "John Doe"
        assert profile.alias == "Johnny"
        assert profile.title == "Manager"
        assert profile.company == "TechCorp"
        assert profile.email == "john@techcorp.com"
        assert profile.phone == "+1-555-123-4567"
        assert profile.website == "https://techcorp.com"


class TestProfileManager:
    """Test ProfileManager class."""
    
    def test_profile_manager_initialization(self):
        """Test ProfileManager initializes correctly."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            assert profile_manager.session_state_key == "user_profile"
            assert isinstance(profile_manager.profile, Profile)
            assert not profile_manager.has_profile_info()
    
    def test_profile_manager_custom_session_key(self):
        """Test ProfileManager with custom session state key."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager("custom_key")
            
            assert profile_manager.session_state_key == "custom_key"
    
    def test_load_from_session_with_existing_profile(self):
        """Test loading profile from session state."""
        existing_profile = Profile(name="Jane Doe", title="Developer")
        
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {"user_profile": existing_profile}
            profile_manager = ProfileManager()
            
            assert profile_manager.profile.name == "Jane Doe"
            assert profile_manager.profile.title == "Developer"
            assert profile_manager.has_profile_info()
    
    def test_load_from_session_no_profile(self):
        """Test loading when no profile exists in session."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            assert not profile_manager.has_profile_info()
            assert profile_manager.profile.name == ""
    
    def test_load_from_session_error_handling(self):
        """Test error handling when loading from session fails."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = None  # This will cause an error
            profile_manager = ProfileManager()
            
            # Should not raise exception, should use default profile
            assert isinstance(profile_manager.profile, Profile)
            assert not profile_manager.has_profile_info()
    
    def test_save_to_session(self):
        """Test saving profile to session state."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            # Update profile
            profile_manager.profile.name = "Test User"
            profile_manager.save_to_session()
            
            assert mock_st.session_state["user_profile"].name == "Test User"
    
    def test_save_to_session_error_handling(self):
        """Test error handling when saving to session fails."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = None  # This will cause an error
            profile_manager = ProfileManager()
            
            # Should not raise exception
            profile_manager.save_to_session()
    
    def test_update_profile_valid_fields(self):
        """Test updating profile with valid fields."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            profile_manager.update_profile(
                name="John Doe",
                title="Manager",
                company="TechCorp",
                email="john@techcorp.com"
            )
            
            assert profile_manager.profile.name == "John Doe"
            assert profile_manager.profile.title == "Manager"
            assert profile_manager.profile.company == "TechCorp"
            assert profile_manager.profile.email == "john@techcorp.com"
            assert mock_st.session_state["user_profile"].name == "John Doe"
    
    def test_update_profile_invalid_field(self):
        """Test updating profile with invalid field."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            # Should not raise exception, should log warning
            profile_manager.update_profile(invalid_field="value")
            
            # Profile should remain unchanged
            assert profile_manager.profile.name == ""
    
    def test_update_profile_error_handling(self):
        """Test error handling when updating profile fails."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = None  # This will cause an error on save
            profile_manager = ProfileManager()
            
            # Should not raise exception
            profile_manager.update_profile(name="Test")
    
    def test_get_profile(self):
        """Test getting current profile."""
        profile_manager = ProfileManager()
        profile = profile_manager.get_profile()
        
        assert isinstance(profile, Profile)
        assert profile.name == ""
    
    def test_get_profile_context_no_info(self):
        """Test getting profile context with no profile information."""
        profile_manager = ProfileManager()
        context = profile_manager.get_profile_context()
        
        assert context == ""
    
    def test_get_profile_context_basic_info(self):
        """Test getting profile context with basic information."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            profile_manager.update_profile(
                name="John Doe",
                title="Manager",
                company="TechCorp"
            )
            
            context = profile_manager.get_profile_context()
            expected_lines = [
                "Name: John Doe",
                "Title: Manager", 
                "Company: TechCorp"
            ]
            
            for line in expected_lines:
                assert line in context
    
    def test_get_profile_context_with_sensitive_info(self):
        """Test getting profile context including sensitive information."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            profile_manager.update_profile(
                name="John Doe",
                email="john@techcorp.com",
                phone="+1-555-123-4567",
                website="https://techcorp.com"
            )
            
            # Without sensitive info
            context = profile_manager.get_profile_context(include_sensitive=False)
            assert "Name: John Doe" in context
            assert "Email: john@techcorp.com" not in context
            assert "Phone: +1-555-123-4567" not in context
            assert "Website: https://techcorp.com" not in context
            
            # With sensitive info
            context = profile_manager.get_profile_context(include_sensitive=True)
            assert "Name: John Doe" in context
            assert "Email: john@techcorp.com" in context
            assert "Phone: +1-555-123-4567" in context
            assert "Website: https://techcorp.com" in context
    
    def test_get_profile_context_error_handling(self):
        """Test error handling when generating profile context fails."""
        profile_manager = ProfileManager()
        
        # Mock profile to cause an error
        profile_manager.profile = None
        
        # Should not raise exception, should return empty string
        context = profile_manager.get_profile_context()
        assert context == ""
    
    def test_has_profile_info_empty(self):
        """Test has_profile_info with empty profile."""
        profile_manager = ProfileManager()
        assert not profile_manager.has_profile_info()
    
    def test_has_profile_info_with_data(self):
        """Test has_profile_info with profile data."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            # Should be False initially
            assert not profile_manager.has_profile_info()
            
            # Add some data
            profile_manager.update_profile(name="John Doe")
            assert profile_manager.has_profile_info()
            
            # Clear and check again
            profile_manager.clear_profile()
            assert not profile_manager.has_profile_info()
    
    def test_clear_profile(self):
        """Test clearing profile."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            # Add some data
            profile_manager.update_profile(
                name="John Doe",
                title="Manager",
                company="TechCorp"
            )
            assert profile_manager.has_profile_info()
            
            # Clear profile
            profile_manager.clear_profile()
            assert not profile_manager.has_profile_info()
            assert profile_manager.profile.name == ""
            assert profile_manager.profile.title == ""
            assert profile_manager.profile.company == ""
    
    def test_clear_profile_error_handling(self):
        """Test error handling when clearing profile fails."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = None  # This will cause an error
            profile_manager = ProfileManager()
            
            # Should not raise exception
            profile_manager.clear_profile()
    
    def test_get_profile_summary_no_info(self):
        """Test getting profile summary with no information."""
        profile_manager = ProfileManager()
        summary = profile_manager.get_profile_summary()
        assert summary == "No profile information provided"
    
    def test_get_profile_summary_with_info(self):
        """Test getting profile summary with profile information."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            # Test with name only
            profile_manager.update_profile(name="John Doe")
            summary = profile_manager.get_profile_summary()
            assert summary == "John Doe"
            
            # Test with name and title
            profile_manager.update_profile(title="Manager")
            summary = profile_manager.get_profile_summary()
            assert summary == "John Doe (Manager)"
            
            # Test with name, title, and company
            profile_manager.update_profile(company="TechCorp")
            summary = profile_manager.get_profile_summary()
            assert summary == "John Doe (Manager) at TechCorp"
    
    def test_get_profile_summary_incomplete(self):
        """Test getting profile summary with incomplete information."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager()
            
            # Test with only title (no name)
            profile_manager.update_profile(title="Manager")
            summary = profile_manager.get_profile_summary()
            assert summary == "(Manager)"
            
            # Test with only company (no name)
            profile_manager.clear_profile()
            profile_manager.update_profile(company="TechCorp")
            summary = profile_manager.get_profile_summary()
            assert summary == "at TechCorp"
    
    def test_profile_manager_integration(self):
        """Test complete ProfileManager workflow."""
        with patch('src.services.profile_manager.st') as mock_st:
            mock_st.session_state = {}
            profile_manager = ProfileManager("test_profile")
            
            # Initial state
            assert not profile_manager.has_profile_info()
            assert profile_manager.get_profile_context() == ""
            assert profile_manager.get_profile_summary() == "No profile information provided"
            
            # Update profile
            profile_manager.update_profile(
                name="Jane Smith",
                alias="Jane",
                title="Senior Developer",
                company="Innovation Corp",
                email="jane@innovationcorp.com",
                phone="+1-555-987-6543",
                website="https://janesmith.dev"
            )
            
            # Check updated state
            assert profile_manager.has_profile_info()
            assert profile_manager.profile.name == "Jane Smith"
            assert profile_manager.profile.alias == "Jane"
            
            # Check context generation
            basic_context = profile_manager.get_profile_context(include_sensitive=False)
            assert "Name: Jane Smith" in basic_context
            assert "Alias: Jane" in basic_context
            assert "Title: Senior Developer" in basic_context
            assert "Company: Innovation Corp" in basic_context
            assert "Email: jane@innovationcorp.com" not in basic_context
            
            sensitive_context = profile_manager.get_profile_context(include_sensitive=True)
            assert "Email: jane@innovationcorp.com" in sensitive_context
            assert "Phone: +1-555-987-6543" in sensitive_context
            assert "Website: https://janesmith.dev" in sensitive_context
            
            # Check summary
            summary = profile_manager.get_profile_summary()
            assert summary == "Jane Smith (Senior Developer) at Innovation Corp"
            
            # Check session state
            assert mock_st.session_state["test_profile"].name == "Jane Smith"
            
            # Clear and verify
            profile_manager.clear_profile()
            assert not profile_manager.has_profile_info()
            assert profile_manager.get_profile_context() == "" 