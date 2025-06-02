from typing import Dict, Optional, Any
import openai
from src.utils.template_manager import TemplateManager

class EmailGenerator:
    def __init__(self, api_key: str):
        """Initialize the email generator with OpenAI API key."""
        self.client = openai.OpenAI(api_key=api_key)
        self.template_manager = TemplateManager()

    def _create_prompt(self, template_type: str, context: Dict[str, Any]) -> str:
        """Create a prompt for the OpenAI API based on template type and context."""
        # Get the base template
        template = self.template_manager.get_template(template_type)
        if not template:
            return ""

        sections = template["template_sections"]
        
        # Start with the base template structure
        base_prompt = f"""You are an expert email writer. Your task is to write a professional email using the following template structure and context.

Template Structure:
Subject: {sections['email_subject']}

{sections['greeting']}

{sections['background']}

{sections['why_choose_us']['title']}
{chr(10).join(f"• {bullet['title']}: {bullet['content']}" for bullet in sections['why_choose_us']['bullets'])}

{sections['additional_bullets']['title']}: {sections['additional_bullets']['content']}

{sections['scheduling']['title']}:
{chr(10).join(f"• {bullet}" for bullet in sections['scheduling']['bullets'])}

{sections['call_to_action']['title']}
{sections['call_to_action']['content']}

{sections['meeting_note_detail']}

{sections['sign_off']['closing']}
{sections['sign_off']['signature']}

Context Information:
- Sender Name: {context.get('sender_info', {}).get('name', '')}
- Sender Title: {context.get('sender_info', {}).get('title', '')}
- Company Name: {context.get('company_name', '')}
- Recipient Name: {context.get('recipient_info', {}).get('name', '')}
- Recipient Organization: {context.get('recipient_info', {}).get('organization', '')}
- Contact Date: {context.get('contact_date', '')}"""

        # Template-specific context
        if template_type.lower() == "outreach":
            value_props = context.get('value_propositions', [])
            if value_props:
                base_prompt += "\n\nKey Selling Points:"
                for prop in value_props:
                    base_prompt += f"\n- {prop['title']}: {prop['content']}"
            
            call_to_action = context.get('call_to_action')
            if call_to_action:
                base_prompt += f"\n\nCall to Action: {call_to_action}"

        elif template_type.lower() == "follow up":
            discussion = context.get('discussion_points', {})
            if discussion:
                if discussion.get('discussion_notes'):
                    base_prompt += f"\n\nDiscussion Notes: {discussion['discussion_notes']}"
                if discussion.get('pain_points'):
                    base_prompt += f"\n\nPain Points: {discussion['pain_points']}"
                if discussion.get('next_steps'):
                    base_prompt += f"\n\nNext Steps: {discussion['next_steps']}"

        # Additional context (if any)
        additional_context = context.get('additional_context')
        if additional_context:
            base_prompt += f"\n\nAdditional Context: {additional_context}"

        base_prompt += """
Please write a professional email following these guidelines:
1. Use the template structure as a guide, but feel free to modify it to better fit the context
2. Replace all placeholder text (like [Your Company]) with actual values from the context
3. Personalize the content based on the provided context
4. Maintain a professional yet engaging tone
5. Ensure the email flows naturally and is well-structured
6. Include all relevant information from the context
7. Make sure the call to action is clear and compelling"""

        return base_prompt

    def generate_email(self, template_type: str, context: Dict) -> (Optional[str], Optional[str]):
        """Generate a personalized email using OpenAI. Returns (email, error_message)."""
        # Get the base template
        template = self.template_manager.get_template(template_type)
        if not template:
            return None, "Template not found."

        try:
            # Create the prompt
            prompt = self._create_prompt(template_type, context)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert sales email writer who specializes in healthcare communications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract and return the generated email
            generated_email = response.choices[0].message.content
            
            # Replace any remaining variables
            variables = {
                "your_name": context["sender_info"]["name"],
                "company_name": context.get("company_name", "")
            }
            
            for var_name, var_value in variables.items():
                generated_email = generated_email.replace(f"[{var_name}]", var_value)
            
            return generated_email, None
            
        except Exception as e:
            return None, str(e) 