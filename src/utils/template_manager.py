import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

class TemplateManager:
    def __init__(self, templates_dir: str = "data/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, Dict] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all templates from the templates directory."""
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, "r") as f:
                    template_data = json.load(f)
                    template_type = template_data.get("template_type")
                    if template_type:
                        self.templates[template_type] = template_data
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")

    def get_template(self, template_type: str) -> Optional[Dict]:
        """Get a template for a specific template type."""
        return self.templates.get(template_type)

    def get_template_section(self, template_type: str, section: str) -> Optional[Any]:
        """Get a specific section from a template."""
        template = self.get_template(template_type)
        if template and "template_sections" in template:
            return template["template_sections"].get(section)
        return None

    def save_template(self, template_type: str, template_sections: Dict, variables: List[str]) -> None:
        """Save a new template with modular sections."""
        template_data = {
            "template_type": template_type,
            "template_sections": template_sections,
            "variables": variables,
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        template_file = self.templates_dir / f"{template_type.lower()}.json"
        with open(template_file, "w") as f:
            json.dump(template_data, f, indent=2)
        
        self.templates[template_type] = template_data

    def list_template_types(self) -> List[str]:
        """List all available template types."""
        try:
            template_files = [f for f in os.listdir(self.templates_dir) if f.endswith('.json')]
            template_types = []
            for file in template_files:
                with open(os.path.join(self.templates_dir, file), 'r') as f:
                    template = json.load(f)
                    if 'template_type' in template:
                        template_types.append(template['template_type'].title())
            
            # Sort templates to ensure 'Outreach' appears first
            template_types.sort(key=lambda x: x.lower() != 'outreach')
            return template_types
        except Exception as e:
            print(f"Error listing template types: {e}")
            return []

    def validate_template(self, template_data: Dict) -> bool:
        """Validate a template's structure."""
        required_fields = ["template_type", "template_sections", "variables", "metadata"]
        metadata_fields = ["last_updated", "version"]
        required_sections = [
            "email_subject", "greeting", "background", "why_choose_us",
            "additional_bullets", "scheduling", "call_to_action",
            "meeting_note_detail", "sign_off"
        ]
        
        # Check required fields
        if not all(field in template_data for field in required_fields):
            return False
            
        # Check metadata fields
        if not all(field in template_data["metadata"] for field in metadata_fields):
            return False
            
        # Check template sections
        if not all(section in template_data["template_sections"] for section in required_sections):
            return False
            
        # Check types
        if not isinstance(template_data["template_type"], str):
            return False
        if not isinstance(template_data["template_sections"], dict):
            return False
        if not isinstance(template_data["variables"], list):
            return False
            
        return True

    def assemble_email(self, template_type: str, variables: Dict[str, str]) -> Optional[str]:
        """Assemble a complete email from template sections and variables."""
        template = self.get_template(template_type)
        if not template:
            return None

        sections = template["template_sections"]
        
        # Start with subject
        email_parts = [f"Subject: {sections['email_subject']}\n"]
        
        # Add greeting
        email_parts.append(f"{sections['greeting']}\n")
        
        # Add background
        email_parts.append(f"{sections['background']}\n")
        
        # Add Why Choose Us section if present
        if 'why_choose_us' in sections:
            why_choose_us = sections['why_choose_us']
            email_parts.append(f"{why_choose_us['title']}\n")
            for bullet in why_choose_us['bullets']:
                email_parts.append(f"• {bullet['title']}: {bullet['content']}\n")
        
        # Add additional bullets if present
        if 'additional_bullets' in sections:
            additional = sections['additional_bullets']
            email_parts.append(f"\n{additional['title']}: {additional['content']}\n")
        
        # Add scheduling section if present
        if 'scheduling' in sections:
            scheduling = sections['scheduling']
            email_parts.append(f"\n{scheduling['title']}:\n")
            for bullet in scheduling['bullets']:
                email_parts.append(f"• {bullet}\n")
        
        # Add call to action if present
        if 'call_to_action' in sections:
            cta = sections['call_to_action']
            email_parts.append(f"\n{cta['title']}\n{cta['content']}\n")
        
        # Add meeting note detail if present
        if 'meeting_note_detail' in sections:
            email_parts.append(f"\n{sections['meeting_note_detail']}\n")
        
        # Add follow-up specific sections if present
        if 'discussion_notes' in sections:
            discussion_notes = sections['discussion_notes']
            email_parts.append(f"\n{discussion_notes['title']}: {discussion_notes['content']}\n")
        if 'pain_points' in sections:
            pain_points = sections['pain_points']
            email_parts.append(f"\n{pain_points['title']}: {pain_points['content']}\n")
        if 'next_steps' in sections:
            next_steps = sections['next_steps']
            email_parts.append(f"\n{next_steps['title']}: {next_steps['content']}\n")
        
        # Add sign off
        if 'sign_off' in sections:
            sign_off = sections['sign_off']
            email_parts.append(f"\n{sign_off['closing']}\n{sign_off['signature']}")
        
        # Replace variables
        email = "".join(email_parts)
        for var_name, var_value in variables.items():
            email = email.replace(f"[{var_name}]", var_value)
        
        return email 