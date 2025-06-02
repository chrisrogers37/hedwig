# OutboundOwl

```
   ,_,
  (O,O)   OutboundOwl
  (   )   Smart, AI-powered outreach & follow-up
   " "
```

Generate personalized sales outreach and follow-up emails for any industry or audience using AI and customizable templates.

## Features

- **Streamlit Web App**: User-friendly interface for generating professional emails.
- **Template System**: Modular, JSON-based templates for different email types (e.g., Outreach, Follow Up).
- **Dynamic Forms**: The form adapts to the selected template, showing only relevant fields.
- **Key Selling Points**: Add, remove, and customize value propositions for each outreach.
- **Call to Action**: For outreach emails, specify a custom call to action.
- **Follow Up Support**: (Beta) Follow Up template supports discussion notes, pain points, and next steps.
- **Preview Pane**: Instantly preview the assembled email template with example data.
- **OpenAI Integration**: Uses GPT-4 to generate high-quality, context-aware emails.
- **Extensible**: Add new templates by dropping JSON files into `data/templates/`.

## How It Works

1. **Select a Template**: Choose "Outreach" (default) or "Follow Up". More templates can be added.
2. **Fill Out the Form**: The form adapts to your template selection:
   - **Outreach**: Enter your info, recipient info, value propositions, and a call to action.
   - **Follow Up**: Enter your info, recipient info, discussion notes, pain points, and next steps.
   - **Both**: Add any additional context.
3. **Preview**: See a live preview of the email structure in the sidebar.
4. **Generate Email**: Click to generate a personalized email using OpenAI's GPT-4.
5. **Copy & Use**: Copy the generated email for your outreach or follow-up needs.

## Project Structure

```
/ (project root)
├── data/templates/         # JSON templates for each email type
│   ├── outreach.json
│   └── followup.json
├── src/
│   ├── app.py              # Streamlit app
│   └── utils/
│       ├── template_manager.py
│       └── email_generator.py
├── README.md
└── ...
```

## Setup

1. **Clone the repository**
2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set your OpenAI API key**
   - Add it to a `.env` file as `OPENAI_API_KEY=sk-...`
   - Or enter it in the Streamlit sidebar
5. **Run the app**
   ```bash
   streamlit run src/app.py
   ```

## Adding/Editing Templates
- Add new JSON files to `data/templates/` following the structure of `outreach.json` or `followup.json`.
- Templates are auto-discovered and selectable in the UI.
- Placeholders (e.g., `[Your Name]`, `[Recipient Organization]`) are replaced with form input values.

## Current Capabilities
- **Outreach**: Fully functional. Supports custom value propositions and call to action.
- **Follow Up**: (Beta) Form adapts to show only relevant fields. Not fully tested.
- **Preview**: Sidebar shows a live preview of the selected template with example data.
- **Error Handling**: UI displays detailed error messages if email generation fails.

## Extending OutboundOwl
- Add new templates for other email types (e.g., "Thank You", "Re-Engagement") by adding new JSON files.
- Update the form logic in `src/app.py` to support new template-specific fields as needed.

## Known Issues
- Only "Outreach" template is fully tested.
- "Follow Up" template is available but may need further validation.
- Some browser extensions may cause harmless console errors (can be ignored).

## License
MIT 