import json
import os
import openai
from dotenv import load_dotenv
from prompts.image_generation_prompt import get_image_generation_prompt, get_concise_image_generation_prompt
from prompts.openai_summarization_prompt import get_openai_summarization_prompt

# Load environment variables
load_dotenv()

# We'll initialize the client in each function to ensure we get the latest API key
def get_openai_client():
    """
    Get an OpenAI client with the API key from environment
    
    Returns:
        OpenAI: Initialized OpenAI client
    """
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        # Get concise prompt template for single bullet point
        prompt = get_concise_image_generation_prompt(bullet_point, article_text)
        
        # Initialize client
        client = get_openai_client()
        
        # Call OpenAI API with GPT-4.1-mini
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=prompt["messages"],
            response_format=prompt["response_format"],
            temperature=0.5,  # Lower temperature for more focused output
            max_tokens=1000   # Reduced for concise output
        )
        
        # Get the prompt directly from the response content
        image_prompt = response.choices[0].message.content.strip()
        
        # Ensure prompt ends with the correct format
        if not image_prompt.endswith("–ar 9:16 –quality 4k"):
            # Remove any existing aspect ratio markers
            image_prompt = image_prompt.replace("--ar 9:16", "").replace("–ar 9:16", "").strip()
            # Add the standard format
            if image_prompt.endswith("."):
                image_prompt = image_prompt + " –ar 9:16 –quality 4k"
            else:
                image_prompt = image_prompt + ". –ar 9:16 –quality 4k"
        
        return image_prompt
    
    except Exception as e:
        print(f"Error generating image prompt: {e}")
        # Return a concise object-focused fallback prompt with no section headers
        return "Vertical 4K editorial photograph of symbolic objects representing the topic. Ancient manuscripts on wooden desk with brass instruments and old maps. Warm directional lighting highlights textures. Dust particles visible in light beams. Shot with Canon EOS R5, 50mm lens, f/2.8 aperture. –ar 9:16 –quality 4k"

def generate_batch_image_prompts(bullet_points, article_text):
    """
    Generate image prompts for all bullet points in a batch
    
    Args:
        bullet_points (list): List of bullet points to generate images for
        article_text (str): The full article text for context
        
    Returns:
        list: List of dictionaries containing bullet points and their image prompts
    """
    results = []
    
    # Process each bullet point individually using the single prompt generator
    for bp in bullet_points:
        try:
            # Generate image prompt for this bullet point
            image_prompt = generate_image_prompt(bp, article_text)
            
            # Extract keywords in quotes
            import re
            quoted_keywords = re.findall(r'"([^"]*)"', bp)
            
            # Add to results
            results.append({
                "bullet_point": bp,
                "image_prompt": image_prompt,
                "keywords": quoted_keywords
            })
        except Exception as e:
            print(f"Error generating prompt for bullet point '{bp}': {e}")
            # Use concise object-focused fallback prompt with no mention of people
            results.append({
                "bullet_point": bp,
                "image_prompt": "Vertical 4K editorial photograph of a historical library setting. Antique wooden desk with scattered papers and vintage tools under warm golden light. Rich textures of leather-bound books fill wooden shelves in background. Details of paper grain and brass instruments visible in foreground. Shot with Canon EOS R5, 85mm lens, f/2.8 aperture. –ar 9:16 –quality 4k",
                "keywords": []
            })
    
    return results

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
        
        # Initialize client
        client = get_openai_client()
        
        # Call OpenAI API with GPT-4o
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=prompt["messages"],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=12000
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