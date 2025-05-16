# Prompts Module

This module contains all the prompt templates used in the Article2Video application.

## Structure

- `__init__.py` - Imports and exposes all prompt functions
- `text_summarization_prompt.py` - Contains the LLM prompt template for article summarization
- `image_generation_prompt.py` - Contains the prompt template for image generation with DALL-E

## Usage

To use these prompts in your code:

```python
from prompts import get_text_summarization_prompt, get_image_generation_prompt

# For text summarization:
prompt = get_text_summarization_prompt(article_text, slidenumber, wordnumber, language)

# For image generation:
prompt = get_image_generation_prompt(headline)
```

## Adding New Prompts

To add a new prompt:

1. Create a new file like `your_new_prompt.py` with a function that returns the prompt text
2. Add the import and export to `__init__.py`
3. Use it in your code with `from prompts import your_new_prompt_function`

## Prompt Design Guidelines

1. Keep variables clearly marked with f-string placeholders
2. Include comments explaining special instructions
3. Maintain consistent formatting for readability 