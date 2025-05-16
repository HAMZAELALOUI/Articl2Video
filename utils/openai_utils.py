import json
import os
import openai
from dotenv import load_dotenv
from prompts.image_generation_prompt import get_image_generation_prompt
from prompts.openai_summarization_prompt import get_openai_summarization_prompt

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_image_prompt(bullet_point, article_text):
    """
    Generate a detailed image prompt for a single bullet point
    
    Args:
        bullet_point (str): The bullet point to generate an image for
        article_text (str): The full article text for context
        
    Returns:
        str: The generated image prompt
    """
    try:
        # Get prompt template for single bullet point
        prompt = get_image_generation_prompt(bullet_point, article_text)
        
        # Call OpenAI API with GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt["messages"],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=4000  # Increased from 3000 to handle more detailed prompts
        )
        
        # Parse the JSON response and extract just the first prompt
        result = json.loads(response.choices[0].message.content)
        if "image_prompts" in result and len(result["image_prompts"]) > 0:
            image_prompt = result["image_prompts"][0]["image_prompt"]
            return image_prompt
        else:
            raise ValueError("Invalid response format from OpenAI API")
    
    except Exception as e:
        print(f"Error generating image prompt: {e}")
        # Return a fallback prompt if there's an error
        return f"Ultra-realistic 4K vertical editorial photograph illustrating: {bullet_point}. Documentary press style in Le Matin du Sahara's North African press photo aesthetic, neutral lighting, natural color palette, moderate saturation, NO TEXT, NO FACES, exclude religious or political symbols."

def generate_batch_image_prompts(bullet_points, article_text):
    """
    Generate image prompts for all bullet points in a batch
    
    Args:
        bullet_points (list): List of bullet points to generate images for
        article_text (str): The full article text for context
        
    Returns:
        list: List of dictionaries containing bullet points and their image prompts
    """
    try:
        # Get prompt template for multiple bullet points
        prompt = get_image_generation_prompt(bullet_points, article_text)
        
        # Call OpenAI API with GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt["messages"],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=10000  # Increased to handle more detailed prompts for multiple bullet points
        )
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        if "image_prompts" in result:
            return result["image_prompts"]
        else:
            raise ValueError("Invalid response format from OpenAI API")
    
    except Exception as e:
        print(f"Error generating batch image prompts: {e}")
        # Return fallback prompts if there's an error
        return [
            {
                "bullet_point": bp,
                "image_prompt": f"Ultra-realistic 4K vertical editorial photograph illustrating: {bp}. Documentary press style in Le Matin du Sahara's North African press photo aesthetic, neutral lighting, natural color palette, moderate saturation, NO TEXT, NO FACES, exclude religious or political symbols.",
                "keywords": []
            } for bp in bullet_points
        ]

def generate_text_summary(article_text, slidenumber, wordnumber, language="English"):
    """
    Generate a text summary of the article
    
    Args:
        article_text (str): The text of the article to summarize
        slidenumber (int): The number of bullet points to generate
        wordnumber (int): The max number of words per bullet point
        language (str): The language to generate the summary in
        
    Returns:
        dict: The generated summary as a JSON object
    """
    try:
        # Get prompt template
        prompt = get_openai_summarization_prompt(article_text, slidenumber, wordnumber, language)
        
        # Call OpenAI API with GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt["messages"],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=4000
        )
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        print(f"Error generating text summary: {e}")
        # Return a fallback summary if there's an error
        return {
            "summary": ["An error occurred while generating the summary."],
            "total": "1",
            "tone": "Error"
        } 