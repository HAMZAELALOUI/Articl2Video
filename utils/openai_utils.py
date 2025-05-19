import json
import os
import openai
from dotenv import load_dotenv
from prompts.image_generation_prompt import get_image_generation_prompt
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
        # Get prompt template for single bullet point
        prompt = get_image_generation_prompt(bullet_point, article_text)
        
        # Initialize client
        client = get_openai_client()
        
        # Call OpenAI API with GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt["messages"],
            response_format=prompt["response_format"],
            temperature=0.7,
            max_tokens=4000  # Reduced to stay within GPT-4o's limits
        )
        
        # Get the prompt directly from the response content - this should already be
        # entirely object-focused with no humans/faces mentioned
        image_prompt = response.choices[0].message.content.strip()
        
        # Ensure prompt ends with the aspect ratio if it doesn't already
        if not image_prompt.endswith("--ar 9:16"):
            if image_prompt.endswith("."):
                image_prompt = image_prompt[:-1] + ", --ar 9:16"
            else:
                image_prompt += ", --ar 9:16"
        
        return image_prompt
    
    except Exception as e:
        print(f"Error generating image prompt: {e}")
        # Return an object-focused fallback prompt with no mention of people/faces
        return f"detailed close-up of symbolic objects representing {bullet_point}, aged manuscripts on wooden desk with brass instruments, dramatic directional lighting highlighting intricate textures and details, ancient library setting with bookshelves in background, dust particles visible in light beams, captured with Canon EOS R5, 50mm f/1.2 lens, documentary editorial style, hyperrealistic 4K resolution, perfect composition, --ar 9:16"

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
            # Use object-focused fallback prompt with no mention of people
            results.append({
                "bullet_point": bp,
                "image_prompt": f"detailed close-up of symbolic objects representing {bp}, antique wooden desk with scattered papers and vintage tools, warm golden light through window illuminating dust particles, historic library with leather-bound books in background, rich textures and intricate details on all surfaces, captured with Canon EOS R5, 85mm lens at f/2.8, documentary editorial style, extreme detail on materials, perfect composition, --ar 9:16",
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
            model="gpt-4o",
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