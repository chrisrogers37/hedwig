import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
import pyperclip
from src.utils.template_manager import TemplateManager
from src.utils.email_generator import EmailGenerator

# Load environment variables
load_dotenv()

# Initialize template manager
template_manager = TemplateManager()

def format_date(date):
    """Format date for display."""
    return date.strftime("%B %d, %Y")

def copy_to_clipboard(text: str) -> None:
    """Copy text to clipboard and show success message."""
    try:
        pyperclip.copy(text)
        st.toast("Email copied to clipboard!", icon="✅")
    except Exception as e:
        st.error(f"Failed to copy to clipboard: {e}")

def main():
    st.title("Sales Outreach and Follow Up Generator")
    st.write("Generate personalized sales outreach and follow-up emails for any industry or audience.")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Your OpenAI API key. You can also set this in the .env file."
        )
        
        # Template preview section
        st.header("Template Preview")
        selected_template_type = st.selectbox(
            "Select Template Type to Preview",
            template_manager.list_template_types() or ["No templates available"]
        )
        
        if selected_template_type != "No templates available":
            template = template_manager.get_template(selected_template_type)
            if template:
                st.subheader("Template Sections")
                sections = template["template_sections"]
                
                # Display template sections in an expandable section
                with st.expander("View Template Structure"):
                    st.json(sections)
                
                # Preview the assembled email
                st.subheader("Preview Assembled Email")
                preview_variables = {
                    "your_name": "Your Name",
                    "your_title": "Your Title",
                    "company_name": "Example Company",
                    "recipient_name": "Recipient Name",
                    "recipient_organization": "Recipient Org"
                }
                preview_email = template_manager.assemble_email(selected_template_type, preview_variables)
                if preview_email:
                    st.text_area("Preview", preview_email, height=300)
                else:
                    st.error("Failed to assemble preview email.")
    
    # Main content area
    st.header("Email Generation")
    if "generated_email" not in st.session_state:
        st.session_state["generated_email"] = None
    if "value_propositions" not in st.session_state:
        st.session_state.value_propositions = [{"title": "", "content": ""}]
    if "step" not in st.session_state:
        st.session_state["step"] = 1
    if "selected_template_type" not in st.session_state:
        st.session_state["selected_template_type"] = None

    # Step 1: Template Type Selection
    if st.session_state["step"] == 1:
        st.subheader("Step 1: Select Template Type")
        template_types = template_manager.list_template_types() or ["No templates available"]
        selected_template_type = st.selectbox("Template Type", template_types, key="main_template_type_select")
        if st.button("Continue"):
            if selected_template_type == "No templates available":
                st.error("No templates available. Please add templates first.")
            else:
                st.session_state["selected_template_type"] = selected_template_type
                st.session_state["step"] = 2
                st.experimental_rerun()

    # Step 2: Show tailored form
    elif st.session_state["step"] == 2:
        template_type = st.session_state["selected_template_type"]
        st.subheader(f"Step 2: {template_type} Details")
        with st.form("email_generation_form"):            
            # Basic Information
            st.subheader("Basic Information")
            contact_date = st.date_input("Contact Date")
            # Your information
            st.subheader("Your Information")
            your_name = st.text_input("Your Name")
            your_title = st.text_input("Your Title")
            company_name = st.text_input("Company Name", placeholder="e.g. Capsule")
            # Recipient Information
            st.subheader("Recipient Information")
            recipient_name = st.text_input("Recipient Name")
            recipient_organization = st.text_input("Recipient Organization (Company, Practice, Store, etc.)")

            # Outreach-specific fields
            call_to_action = None
            if template_type.lower() == "outreach":
                st.markdown("---")
                st.subheader("Key Selling Points")
                st.write("Add your main value propositions and selling points. These will be used to customize the 'Why Choose Us' section of the email.")
                st.info("Use the buttons just above to add or remove value propositions.")
                for i, prop in enumerate(st.session_state.value_propositions):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.session_state.value_propositions[i]["title"] = st.text_input(
                            f"Value Proposition {i+1}",
                            value=prop["title"],
                            key=f"prop_title_{i}",
                            placeholder="e.g., Price Transparency, Individualized Care"
                        )
                    with col2:
                        st.session_state.value_propositions[i]["content"] = st.text_area(
                            f"Description {i+1}",
                            value=prop["content"],
                            key=f"prop_content_{i}",
                            placeholder="Describe this value proposition in detail..."
                        )
                st.markdown("---")
                call_to_action = st.text_area(
                    "Call to Action",
                    placeholder="What action do you want the recipient to take? (e.g., Schedule a meeting, reply to this email, etc.)"
                )

            # Follow Up-specific fields
            discussion_notes = pain_points = next_steps = None
            if template_type.lower() == "follow up":
                st.markdown("---")
                st.subheader("Discussion Notes")
                st.write("Add key points from your discussion to personalize the email")
                discussion_notes = st.text_area(
                    "Discussion Notes",
                    placeholder="Summarize the main points from your discussion..."
                )
                pain_points = st.text_area(
                    "Recipient Pain Points",
                    placeholder="What challenges did the recipient mention?"
                )
                next_steps = st.text_area(
                    "Agreed Next Steps",
                    placeholder="What follow-up actions were discussed?"
                )

            # Additional context (always shown)
            st.subheader("Additional Context")
            additional_notes = st.text_area(
                "Additional Notes",
                placeholder="Any other relevant information from the discussion..."
            )

            submitted = st.form_submit_button("Generate Email")
            if submitted:
                # Validate required fields
                required_fields = {
                    "Basic": {
                        "your_name": your_name,
                        "your_title": your_title,
                        "company_name": company_name,
                        "recipient_name": recipient_name,
                        "recipient_organization": recipient_organization
                    }
                }

                # Template-specific required fields
                if template_type.lower() == "outreach":
                    required_fields["Outreach"] = {
                        "call_to_action": call_to_action
                    }
                    # Validate at least one value proposition
                    if not any(prop["title"] and prop["content"] for prop in st.session_state.value_propositions):
                        st.error("Please add at least one value proposition for the Outreach template.")
                        return
                elif template_type.lower() == "follow up":
                    required_fields["Follow Up"] = {
                        "discussion_notes": discussion_notes,
                        "pain_points": pain_points,
                        "next_steps": next_steps
                    }

                # Check all required fields
                missing_fields = []
                for section, fields in required_fields.items():
                    for field_name, value in fields.items():
                        if not value:
                            missing_fields.append(f"{section}: {field_name.replace('_', ' ').title()}")
                
                if missing_fields:
                    st.error("Please fill in all required fields:\n" + "\n".join(f"- {field}" for field in missing_fields))
                    return

                # Prepare context for OpenAI
                context = {
                    "sender_info": {
                        "name": your_name,
                        "title": your_title
                    },
                    "recipient_info": {
                        "name": recipient_name,
                        "organization": recipient_organization
                    },
                    "company_name": company_name,
                    "contact_date": format_date(contact_date),
                    "additional_context": additional_notes
                }

                # Add template-specific context
                if template_type.lower() == "outreach":
                    context["value_propositions"] = [
                        prop for prop in st.session_state.value_propositions 
                        if prop["title"] and prop["content"]
                    ]
                    context["call_to_action"] = call_to_action
                elif template_type.lower() == "follow up":
                    context["discussion_points"] = {
                        "discussion_notes": discussion_notes,
                        "pain_points": pain_points,
                        "next_steps": next_steps
                    }

                # Initialize email generator
                api_key = os.getenv("OPENAI_API_KEY", "")
                email_generator = EmailGenerator(api_key)
                with st.spinner("Generating personalized email..."):
                    generated_email, error_message = email_generator.generate_email(template_type.lower(), context)
                    if generated_email:
                        st.session_state["generated_email"] = generated_email
                        st.success("Email generated successfully!")
                    else:
                        st.error(f"Failed to generate email. {error_message if error_message else 'Please try again.'}")
                with st.expander("View Context Used for Generation"):
                    st.json(context)
        # Add/Remove value proposition buttons (just above the value proposition fields, outside the form)
        if template_type.lower() == "outreach":
            st.markdown("---")
            st.info("Use these buttons to add or remove value propositions.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add Value Proposition"):
                    st.session_state.value_propositions.append({"title": "", "content": ""})
                    st.experimental_rerun()
            with col2:
                if len(st.session_state.value_propositions) > 1:
                    if st.button("➖ Remove Last Value Proposition"):
                        st.session_state.value_propositions.pop()
                        st.experimental_rerun()
            st.markdown("---")
        if st.button("⬅️ Back"):
            st.session_state["step"] = 1
            st.session_state["generated_email"] = None
            st.experimental_rerun()

    # After the form, use session state to display and copy
    if st.session_state.get("generated_email"):
        st.subheader("Generated Email")
        st.text_area(
            "Email Content",
            st.session_state["generated_email"],
            height=400,
            key="email_content"
        )
        if st.button("📋 Copy to Clipboard"):
            copy_to_clipboard(st.session_state["generated_email"])

if __name__ == "__main__":
    main() 