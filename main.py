import os
from web_scraper import scrape_text_from_url
from text_processor import print_summary_points, fix_unicode
from json_utils import save_and_clean_json
from app_controller import do_work, test_cli
from image_generator import generate_image_for_text
from text_overlay import add_text_to_image
from audio_processor import text_to_speech
from video_creator import clear_cache
from openai_client import summarize_with_openai

# Check for necessary API keys
# API Keys are expected to be set as environment variables
# by the calling script (e.g., streamlit_app.py using st.secrets)

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY environment variable not found. Image generation and summarization calls may fail.")

# Check for Gemini API key 
if not os.getenv("GEMINI_API_KEY"):
    print("Warning: GEMINI_API_KEY environment variable not found. Gemini API calls may fail.")

if __name__ == "__main__":
    test_cli()
