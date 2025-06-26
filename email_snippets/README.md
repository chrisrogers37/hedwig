# Email Snippets Library

This directory contains a curated collection of email templates organized by use case and industry. Each template is designed to provide high-quality examples for the RAG (Retrieval-Augmented Generation) system.

## Directory Structure

```
email_snippets/
├── cold_outreach/          # Initial outreach emails
├── follow_up/             # Follow-up sequences
├── introduction/          # General introductions
├── churn_recovery/        # Customer retention emails
├── partnership/           # Partnership proposals
└── event_invitation/      # Event invitations
```

## Template Format

Each template file follows this structure:

```markdown
---
tags: ["cold", "SaaS", "formal"]
use_case: "Cold Intro"
tone: "Professional"
industry: "Tech"
difficulty: "Beginner"
author: "OutboundOwl Team"
date_created: "2024-01-01"
success_rate: 0.85
notes: "Effective for B2B SaaS companies"
---

[Email content here with {{variables}} for personalization]
```

## Metadata Fields

### Required Fields
- `tags`: Array of relevant tags for search
- `use_case`: Primary use case category
- `tone`: Email tone (Professional, Casual, Friendly, Formal, Enthusiastic)
- `industry`: Target industry
- `difficulty`: Complexity level (Beginner, Intermediate, Advanced)

### Optional Fields
- `author`: Template creator
- `date_created`: Creation date (YYYY-MM-DD)
- `success_rate`: Effectiveness score (0.0-1.0)
- `notes`: Additional context or usage notes

## Template Categories

### Cold Outreach
- Initial contact emails
- Value proposition focused
- Industry-specific approaches
- Personalization strategies

### Follow Up
- Multi-touch sequences
- Value-add content
- Gentle persistence
- Call-to-action variations

### Introduction
- General networking
- Conference connections
- Mutual contact introductions
- Professional networking

### Churn Recovery
- Customer retention
- Win-back campaigns
- Feedback requests
- Re-engagement strategies

### Partnership
- Business development
- Collaboration proposals
- Joint venture opportunities
- Strategic alliances

### Event Invitation
- Webinar invitations
- Conference invites
- Networking events
- Product launches

## Usage Guidelines

1. **Template Selection**: Templates are automatically selected based on user input and context
2. **Personalization**: Use {{variables}} for dynamic content insertion
3. **Adaptation**: Templates serve as examples and should be adapted to specific situations
4. **Quality**: All templates are reviewed for effectiveness and relevance

## Contributing

To add new templates:
1. Follow the metadata format exactly
2. Ensure proper categorization
3. Include relevant tags for searchability
4. Test with sample prompts
5. Add to appropriate subdirectory

## Performance Notes

- Templates are loaded on app startup
- Embeddings are generated for semantic search
- Caching is implemented for performance
- Memory usage is optimized for large libraries 