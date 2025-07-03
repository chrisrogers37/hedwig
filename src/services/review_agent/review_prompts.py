"""
Review Prompts for Review Agent

Provides prompt templates and prompt-building functions for the review agent LLM calls.
Requests conversational critique with structured actionable feedback for UI interaction.
"""
from typing import Dict, Optional
import textwrap

REVIEW_PROMPT_TEMPLATE = textwrap.dedent("""
You are an experienced reviewer of outreach emails with industry knowledge of {recipient_industry}.

You have just used an LLM system to generate an outreach email. Please provide a rigorous critique of this generated email:

{email_content}

Review the email for:
1. **Authenticity**: Does this sound like it was written by a real person, not AI?
2. **Template Adherence**: If a template was used, does the email follow its structure and guidelines?
3. **Forbidden Phrases**: Are there any marketing buzzwords or forbidden phrases used?
4. **Writing Guidelines**: Does the email follow the provided writing tips and preferred language?
5. **Completeness**: Are there any template placeholders or missing context that need more information?
6. **Tone Appropriateness**: Is the tone appropriate for the industry and relationship?
7. **Effectiveness**: Will this email achieve its intended purpose?

Please provide your review in the following format:

## CRITIQUE
[Provide your detailed, conversational critique of the email. Be specific about what works and what doesn't. This should be 2-4 paragraphs of nuanced analysis.]

## FEEDBACK
Provide 3-5 specific, actionable suggestions for improvement. Each suggestion should be:
- Specific and concrete
- Something the user can easily implement
- Focused on one aspect of the email
- Written as a clear instruction

Format your feedback as a bulleted list:

 - [*TAGLINE*: [first specific suggestion]
 - [*TAGLINE*: [second specific suggestion]
 - [*TAGLINE*: [third specific suggestion]

## RECOMMENDATION
[Either "KEEP" if the email is good enough to use, or "REGENERATE" if it needs significant improvement]

{template_context}
""")

def build_review_prompt(
    email_content: str,
    template_info: Optional[Dict] = None,
    user_context: Optional[str] = None,
    recipient_industry: Optional[str] = None,
    extra_metadata: Optional[Dict] = None
) -> str:
    """
    Build the review prompt for the LLM, requesting conversational critique with structured feedback.
    
    Args:
        email_content: The generated email to review
        template_info: Metadata about the template used (may include forbidden phrases, writing tips, etc.)
        user_context: The original user request/context
        recipient_industry: The industry of the recipient (if available)
        extra_metadata: Any additional context to include
        
    Returns:
        The formatted review prompt string requesting critique and actionable feedback
    """
    # Fallbacks for missing info
    industry = recipient_industry or (template_info.get('industry') if template_info else 'the recipient industry')
    
    # Build template context section
    template_context = ""
    if template_info:
        template_context += "\n\n## TEMPLATE CONTEXT\n"
        
        if 'forbidden_phrases' in template_info and template_info['forbidden_phrases']:
            template_context += f"**Forbidden phrases to avoid:** {', '.join(template_info['forbidden_phrases'])}\n"
        
        if 'writing_tips' in template_info and template_info['writing_tips']:
            template_context += f"**Writing guidelines:** {', '.join(template_info['writing_tips'])}\n"
        
        if 'preferred_phrases' in template_info and template_info['preferred_phrases']:
            template_context += f"**Preferred language:** {', '.join(template_info['preferred_phrases'])}\n"
        
        if 'structure' in template_info and template_info['structure']:
            template_context += f"**Template structure:** {template_info['structure']}\n"
    
    # Add user context if available
    if user_context:
        template_context += f"\n**User request context:** {user_context}\n"
    
    # Add extra metadata if available
    if extra_metadata:
        template_context += "\n**Additional context:**\n"
        for k, v in extra_metadata.items():
            template_context += f"- {k}: {v}\n"
    
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        recipient_industry=industry,
        email_content=email_content,
        template_context=template_context
    )
    
    return prompt 