# Email Templates Library (Scrolls)

This directory contains a curated collection of email templates organized by industry and use case. Each template is designed to provide high-quality examples for the RAG (Retrieval-Augmented Generation) system in Hedwig.

## Directory Structure

```
scrolls/
├── README.md
├── entertainment/          # Entertainment industry templates
│   ├── band/
│   │   └── to_venue/
│   │       └── gig_outreach.yaml
│   └── dj/
│       └── to_venue/
│           └── gig_outreach.yaml
├── general/               # General business templates
│   ├── churn_recovery/
│   │   └── win_back_campaign.yaml
│   ├── event_invitation/
│   │   └── webinar_invite.yaml
│   ├── follow_up/
│   │   └── value_add_followup.yaml
│   ├── introduction/
│   │   └── conference_connection.yaml
│   └── partnership/
│       └── strategic_alliance.yaml
├── healthcare/            # Healthcare industry templates
│   └── sales_rep/
│       ├── to_doctor/
│       │   └── saas_outreach.yaml
│       └── to_patient/
│           └── saas_outreach.yaml
└── tech/                  # Technology industry templates
    └── sales_rep/
        ├── to_enterprise/
        │   └── saas_outreach.yaml
        └── to_startup/
            └── saas_outreach.yaml
```

## Template Format

Each template file follows this YAML structure:

```yaml
metadata:
  tags: ["cold", "SaaS", "formal"]
  use_case: "Cold Intro"
  tone: "Professional"
  industry: "Tech"
  role: "Sales Rep"
  difficulty: "Beginner"
  author: "Hedwig Team"
  date_created: "2024-01-01"
  success_rate: 0.85
  notes: "Effective for B2B SaaS companies"

template: |
  Subject: {{subject}}
  
  Hi {{recipient_name}},
  
  [Email content here with {{variables}} for personalization]
  
  Best regards,
  {{sender_name}}

guidance:
  avoid_phrases:
    - "I hope this email finds you well"
    - "I wanted to reach out"
    - "I'm reaching out because"
  preferred_phrases:
    - "Hi {{recipient_name}}"
    - "I'm {{sender_name}}"
    - "I'd like to"
  writing_tips:
    - "Keep it concise and direct"
    - "Focus on value proposition"
    - "Include a clear call to action"
```

## Template Sections

### Metadata Section
Contains searchable information about the template:

#### Required Fields
- `tags`: Array of relevant tags for search
- `use_case`: Primary use case category
- `tone`: Email tone (Professional, Casual, Friendly, Formal, Natural)
- `industry`: Target industry
- `role`: Sender role (Sales Rep, Manager, etc.)

#### Optional Fields
- `difficulty`: Complexity level (Beginner, Intermediate, Advanced)
- `author`: Template creator
- `date_created`: Creation date (YYYY-MM-DD)
- `success_rate`: Effectiveness score (0.0-1.0)
- `notes`: Additional context or usage notes

### Template Section
Contains the actual email template with variable placeholders:
- Uses `{{variable_name}}` syntax for personalization
- Includes subject line and full email body
- Maintains proper email formatting and structure

### Guidance Section
Provides specific writing instructions for the LLM:

#### Writing Guidance Fields
- `avoid_phrases`: List of phrases to avoid (prevents AI-like language)
- `preferred_phrases`: List of preferred alternatives
- `writing_tips`: General writing advice for the template type

## Template Categories

### By Industry

#### Entertainment
- **Band/DJ Outreach**: Venue booking, gig promotion, collaboration requests
- **Event Management**: Performance opportunities, venue partnerships

#### General Business
- **Churn Recovery**: Customer retention, win-back campaigns
- **Event Invitation**: Webinars, conferences, networking events
- **Follow Up**: Value-add sequences, gentle persistence
- **Introduction**: Networking, conference connections
- **Partnership**: Strategic alliances, collaboration proposals

#### Healthcare
- **B2B Sales**: Medical device sales, software solutions
- **Patient Outreach**: Healthcare services, appointment reminders

#### Technology
- **Enterprise Sales**: Large company outreach, complex sales cycles
- **Startup Outreach**: Early-stage company partnerships, pilot programs

### By Use Case

#### Cold Outreach
- Initial contact emails
- Value proposition focused
- Industry-specific approaches
- Personalization strategies

#### Follow Up
- Multi-touch sequences
- Value-add content
- Gentle persistence
- Call-to-action variations

#### Introduction
- General networking
- Conference connections
- Mutual contact introductions
- Professional networking

#### Churn Recovery
- Customer retention
- Win-back campaigns
- Feedback requests
- Re-engagement strategies

#### Partnership
- Business development
- Collaboration proposals
- Joint venture opportunities
- Strategic alliances

#### Event Invitation
- Webinar invitations
- Conference invites
- Networking events
- Product launches

## Usage in Hedwig

### Automatic Selection
1. **Semantic Search**: Templates are automatically selected based on user input and conversation context
2. **Similarity Matching**: Uses embeddings to find the most relevant templates (threshold: 0.75)
3. **Context Integration**: Selected templates are included in the prompt for style guidance
4. **Guidance Application**: Writing guidance is automatically applied to ensure natural language

### Template Processing
1. **YAML Parsing**: Templates are parsed using `YamlTemplateParser` utility
2. **Text Preprocessing**: Template content is processed using `TextProcessor` utility
3. **Embedding Generation**: Semantic embeddings are created from metadata, notes, and template content
4. **Metadata Filtering**: Optional filters can be applied by industry, tone, or use case
5. **File Operations**: All file reading and YAML parsing is handled by `FileUtils` for safety and consistency
6. **Error Handling**: All file and API errors are managed by the `ErrorHandler` utility for robust operation

### RAG Integration
- Templates are retrieved during email generation based on enhanced conversation context
- Used for style and structure guidance only (specific details are not copied)
- Writing guidance is automatically included in prompts to prevent AI-like language
- Similarity scores are displayed for transparency
- Only the best match above 0.75 similarity is used

## Contributing

To add new templates:
1. Follow the YAML format exactly with `metadata:`, `template:`, and `guidance:` sections
2. Ensure proper categorization by industry and use case
3. Include relevant tags for searchability
4. Add specific writing guidance to prevent AI-like language
5. Test with sample prompts
6. Add to appropriate subdirectory structure

### Template Guidelines
- **Originality**: Write original content, avoid copying from other sources
- **Clarity**: Use clear, professional language
- **Specificity**: Include industry-specific terminology and context
- **Versatility**: Make templates adaptable to different situations
- **Effectiveness**: Focus on proven email strategies
- **Natural Language**: Include guidance to avoid AI-like phrases and promote natural writing

## Performance Notes

- Templates are loaded on app startup by `ScrollRetriever`
- Embeddings are generated using `SimpleEmbeddings` for semantic search
- Caching is implemented for performance optimization
- Memory usage is optimized for large template libraries
- Text preprocessing ensures consistent embedding quality
- YAML parsing is handled efficiently by `YamlTemplateParser`

## Technical Integration

### ScrollRetriever Service
- Loads templates from YAML files using `FileUtils`
- Parses YAML structure with `YamlTemplateParser`
- Handles file and API errors with `ErrorHandler`
- Generates semantic embeddings from metadata, notes, and template content
- Provides similarity search functionality with 0.75 threshold

### YamlTemplateParser Utility
- Parses YAML template structure with metadata, template, and guidance sections
- Extracts and validates template components
- Handles YAML parsing errors gracefully
- Provides clean interface for template access

### TextProcessor Utility
- Standardizes text preprocessing across templates
- Ensures consistent embedding quality
- Maintains important word boundaries (hyphens)
- Normalizes whitespace and special characters

### FileUtils Utility
- Handles all file I/O and YAML parsing for templates
- Ensures safe, consistent file operations
- Provides file discovery and validation

### ErrorHandler Utility
- Manages file and API errors gracefully
- Provides safe execution and retry logic 