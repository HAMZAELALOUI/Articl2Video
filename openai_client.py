import os
import json
import re
import unicodedata
from openai import OpenAI
from json_utils import fix_json_quotes, additional_json_cleanup
from prompts import get_openai_summarization_prompt

# Define our own version of clean_encoding_issues to avoid circular imports
def clean_encoding_issues(text):
    """
    Clean text with encoding issues like replacement characters
    
    Args:
        text (str): The text with potential encoding issues
        
    Returns:
        str: Cleaned text
    """
    # Replace replacement character with space
    text = text.replace('\ufffd', ' ')
    
    # Try to normalize unicode characters
    try:
        text = unicodedata.normalize('NFKD', text)
    except Exception as e:
        print(f"Warning: Unicode normalization failed: {e}")
    
    # Manually fix some common encoding issues in French text
    text = text.replace('fractur\ufffd', 'fracturée')
    text = text.replace('pr\ufffd', 'pré')
    text = text.replace('\ufffdchanges', 'échanges')
    text = text.replace('\ufffd', 'é')
    
    # Remove any remaining control characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    return text

def get_openai_api_key():
    """
    Get the OpenAI API key from environment variables or secrets
    
    Returns:
        str: The OpenAI API key
    """
    # First try environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Then check os.environ in case it was set differently
    if not api_key and 'OPENAI_API_KEY' in os.environ:
        api_key = os.environ['OPENAI_API_KEY']
    
    # Finally try to read from .streamlit/secrets.toml
    if not api_key:
        try:
            import toml
            secrets_path = '.streamlit/secrets.toml'
            if os.path.exists(secrets_path):
                secrets = toml.load(secrets_path)
                if 'OPENAI_API_KEY' in secrets:
                    api_key = secrets['OPENAI_API_KEY']
        except Exception as e:
            print(f"Error reading secrets.toml: {e}")
    
    return api_key

def safely_parse_json(json_str):
    """
    Safely parse a JSON string with multiple fallback mechanisms
    
    Args:
        json_str (str): The JSON string to parse
        
    Returns:
        tuple: (parsed_json, error_message)
    """
    # First try direct parsing
    try:
        result = json.loads(json_str)
        return result, None
    except json.JSONDecodeError as e:
        print(f"Initial JSON parsing failed: {e}")
        
        # Try with basic cleanup (remove whitespace)
        try:
            cleaned = ' '.join(json_str.replace('\n', ' ').split())
            result = json.loads(cleaned)
            return result, None
        except json.JSONDecodeError:
            pass
            
        # Try with quote fixing
        try:
            fixed = fix_json_quotes(json_str)
            result = json.loads(fixed)
            return result, None
        except json.JSONDecodeError as e:
            print(f"Quote fixing failed to parse: {e}")
            
        # Try aggressive cleanup
        try:
            cleaned = additional_json_cleanup(json_str)
            result = json.loads(cleaned)
            return result, None
        except json.JSONDecodeError as e:
            error_msg = str(e)
            print(f"All JSON parsing attempts failed: {error_msg}")
            return None, error_msg

def summarize_with_openai(article_text, slidenumber, wordnumber, language):
    """
    Summarize an article using OpenAI's API with logical narrative flow
    
    Args:
        article_text (str): The text of the article to summarize
        slidenumber (int): The number of bullet points to generate
        wordnumber (int): The max number of words per bullet point
        language (str): The language to generate the summary in
        
    Returns:
        dict: The generated summary data
    """
    try:
        # Clean the article text to fix encoding issues
        cleaned_article_text = clean_encoding_issues(article_text)
        
        # Get API key
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        # Initialize client
        client = OpenAI(api_key=api_key)
        
        # Get prompt
        prompt_data = get_openai_summarization_prompt(cleaned_article_text, slidenumber, wordnumber, language)
        
        # Call OpenAI API
        print(f"Calling OpenAI API for text summarization in {language}...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=prompt_data["messages"],
            response_format=prompt_data["response_format"],
            temperature=0.7,
            max_tokens=6000,
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content
        
        # Safe parsing with fallback mechanisms
        result, error = safely_parse_json(response_content)
        
        if result:
            print(f"Successfully generated summary with {len(result.get('summary', []))} slides")
            return result
        else:
            # If all parsing attempts failed, we'll create a fallback response
            error_message = error or "Unknown JSON parsing error"
            print(f"All JSON parsing attempts failed: {error_message}")
            
            return {
                "summary": [f"Error parsing summary: {error_message}. Please try again."],
                "total": "0",
                "tone": "Neutral"
            }
                
    except Exception as e:
        print(f"Error in OpenAI summarization: {str(e)}")
        # Return a fallback response with error message
        return {
            "summary": [f"Error generating summary: {str(e)}"],
            "total": "0",
            "tone": "Neutral"
        } 