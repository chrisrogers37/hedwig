"""
Profile Manager Service for Hedwig

Manages user profile information and preferences for email generation.
Handles profile CRUD operations and session state management.
"""

from dataclasses import dataclass
from typing import Optional
import streamlit as st
from ..utils.logging_utils import log


@dataclass
class Profile:
    """User profile information for email generation."""
    # Core Identity
    name: str = ""
    alias: str = ""
    title: str = ""
    
    # Organization
    company: str = ""
    
    # Contact Information
    email: str = ""
    phone: str = ""
    website: str = ""


class ProfileManager:
    """
    Manages user profile information and preferences.
    Handles profile CRUD operations and session state persistence.
    """
    
    def __init__(self, session_state_key: str = "user_profile"):
        """
        Initialize ProfileManager.
        
        Args:
            session_state_key: Key for storing profile in session state
        """
        self.session_state_key = session_state_key
        self.profile = Profile()
        self._load_from_session()
        log(f"ProfileManager initialized with session key: {session_state_key}", prefix="ProfileManager")
    
    def _load_from_session(self) -> None:
        """Load profile from session state if available."""
        try:
            if hasattr(st, 'session_state') and self.session_state_key in st.session_state:
                self.profile = st.session_state[self.session_state_key]
                log(f"Profile loaded from session: {self.profile.name}", prefix="ProfileManager")
        except Exception as e:
            log(f"Error loading profile from session: {e}", prefix="ProfileManager")
            # Keep default profile if loading fails
    
    def save_to_session(self) -> None:
        """Save profile to session state."""
        try:
            if hasattr(st, 'session_state'):
                st.session_state[self.session_state_key] = self.profile
                log(f"Profile saved to session: {self.profile.name}", prefix="ProfileManager")
        except Exception as e:
            log(f"Error saving profile to session: {e}", prefix="ProfileManager")
    
    def update_profile(self, **kwargs) -> None:
        """
        Update profile with new information.
        
        Args:
            **kwargs: Profile fields to update (name, alias, title, company, email, phone, website)
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.profile, key):
                    setattr(self.profile, key, value)
                else:
                    log(f"Warning: Unknown profile field '{key}'", prefix="ProfileManager")
            
            self.save_to_session()
            log(f"Profile updated: {kwargs}", prefix="ProfileManager")
        except Exception as e:
            log(f"Error updating profile: {e}", prefix="ProfileManager")
    
    def get_profile(self) -> Profile:
        """
        Get current profile.
        
        Returns:
            Current Profile object
        """
        return self.profile
    
    def get_profile_context(self, include_sensitive: bool = False) -> str:
        """
        Format profile for prompt context.
        
        Args:
            include_sensitive: Whether to include sensitive information (email, phone)
            
        Returns:
            Formatted profile context string
        """
        try:
            profile_lines = []
            
            # Always include non-sensitive info
            if self.profile.name:
                profile_lines.append(f"Name: {self.profile.name}")
            if self.profile.alias:
                profile_lines.append(f"Alias: {self.profile.alias}")
            if self.profile.title:
                profile_lines.append(f"Title: {self.profile.title}")
            if self.profile.company:
                profile_lines.append(f"Company: {self.profile.company}")
            
            # Only include sensitive info if explicitly requested
            if include_sensitive:
                if self.profile.email:
                    profile_lines.append(f"Email: {self.profile.email}")
                if self.profile.phone:
                    profile_lines.append(f"Phone: {self.profile.phone}")
                if self.profile.website:
                    profile_lines.append(f"Website: {self.profile.website}")
            
            context = "\n".join(profile_lines) if profile_lines else ""
            log(f"Profile context generated (sensitive={include_sensitive}): {len(context)} chars", prefix="ProfileManager")
            return context
            
        except Exception as e:
            log(f"Error generating profile context: {e}", prefix="ProfileManager")
            return ""
    
    def has_profile_info(self) -> bool:
        """
        Check if any profile information is provided.
        
        Returns:
            True if any profile field has a value, False otherwise
        """
        return any([
            self.profile.name, self.profile.alias, self.profile.title,
            self.profile.company, self.profile.email, self.profile.phone,
            self.profile.website
        ])
    
    def clear_profile(self) -> None:
        """Clear all profile information and reset to defaults."""
        try:
            self.profile = Profile()
            self.save_to_session()
            log("Profile cleared", prefix="ProfileManager")
        except Exception as e:
            log(f"Error clearing profile: {e}", prefix="ProfileManager")
    
    def get_profile_summary(self) -> str:
        """
        Get a human-readable summary of the profile.
        
        Returns:
            Summary string of profile information
        """
        if not self.has_profile_info():
            return "No profile information provided"
        
        parts = []
        if self.profile.name:
            parts.append(self.profile.name)
        if self.profile.title:
            parts.append(f"({self.profile.title})")
        if self.profile.company:
            parts.append(f"at {self.profile.company}")
        
        return " ".join(parts) if parts else "Profile incomplete" 