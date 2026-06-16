# AI Prompt Templates

This folder stores prompt and instruction templates used by the server-side AI workflows.

- `post_generation_prompt.md` builds the final user prompt for Telegram post generation.
- `post_generation_instructions.md` contains the model role instructions for Telegram post generation.
- `venue_research_prompt.md` builds the user prompt for venue research.
- `venue_research_instructions.md` contains the model role instructions for venue research.

Keep templates as plain text with Python `str.format` placeholders. Escape literal braces as `{{` and `}}`.
