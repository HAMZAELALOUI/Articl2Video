"""
Prompt templates for image generation.
"""
import logging
import os
import json
from datetime import datetime

# Set up logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'image_prompts_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("image_generation_prompt")

# =========================================================
#  IMAGE GENERATION PROMPT TEMPLATES — PRESS PHOTO STYLE
# =========================================================

IMAGE_SYSTEM_PROMPT = """
You are an expert prompt engineer. Create concise, detailed prompts for ultra-realistic 4K vertical (9:16) editorial photographs based on the provided bullet point.

KEY REQUIREMENTS:
• Focus on bullet point content with article as context
• Create detailed visual representation that best fits the content type
• NO faces, NO text, NO maps of any kind
• Show locations through landmarks/architecture, never maps
• Keep final prompt between 250-300 words
• AVOID all acronyms and abbreviations - spell out full names
• Choose a specific camera angle and shooting style
• Focus on photorealistic imagery as if taken by professional cameras

CONTENT-BASED APPROACH:
• For financial/economic topics: Focus on OBJECTS (coins, charts, financial instruments, documents)
• For policy/legal topics: Combine OBJECTS with symbolic SETTINGS
• For social/cultural topics: Create meaningful SCENES with environmental context
• For abstract concepts: Use symbolic OBJECTS and visual metaphors
• Always choose the approach that best represents the specific bullet point

TECHNICAL SPECIFICATIONS:
• Classification: Editorial, documentary press photo
• Resolution: 3840 × 2160 px, portrait (9:16)
• Camera body: Choose ONE specific model (Canon EOS R5, Nikon Z9, or Sony A1)
• Lens: Choose ONE specific prime lens (35mm f/1.4, 50mm f/1.2, or 85mm f/1.8)
• Settings: Specify ISO (100-3200), shutter speed, aperture (f/4-f/8 preferred)
• Lighting: Choose ONE specific lighting condition (golden hour, blue hour, overcast daylight, or neutral indoor)
• Composition: Rule of thirds, leading lines, layers for depth

OUTPUT FORMAT:
OBJECTS or SCENE: [Key objects relevant to bullet point] or [Setting with contextual elements]
FOCAL ELEMENTS: [Main objects, actions, symbolic elements]
COMPOSITION: [Detailed composition with angle, perspective, and framing]
TECH: [Specific camera body, lens, ISO, aperture, and lighting]
STYLE: [Style, color palette]
NEGATIVE: faces, text, maps of any kind, map elements
–ar 9:16 –quality 4k
"""

IMAGE_USER_PROMPT_TEMPLATE = """
BULLET POINT: {bullet_point}
KEYWORDS: {quoted_keywords}
ARTICLE CONTEXT: {article_text}

Analyze this bullet point and create a press photography prompt that:
1. Focuses EXCLUSIVELY on this specific bullet point
2. Creates UNIQUE visual elements not present in other article sections
3. Shows NO maps, NO faces, NO text
4. Uses landmarks for locations, never maps
5. Maintains press photography realism and documentary style
6. Stays within 250-300 words
7. AVOIDS all acronyms and abbreviations - spell out full names
8. Specifies a clear camera angle and viewpoint
9. Includes exact technical details (camera, lens, settings)

CONTENT-BASED APPROACH:
• For financial/economic topics: Create OBJECT-FOCUSED images (coins, charts, documents, financial instruments)
• For policy/legal topics: Use symbolic objects in relevant settings
• For cultural/social topics: Create meaningful scenes with environment
• Choose the approach that best fits THIS specific bullet point

Your prompt must include:
OBJECTS or SCENE: [Key objects/elements] or [Setting/environment] - Choose based on content type
FOCAL ELEMENTS: [Key objects/elements]
COMPOSITION: [Detailed layout with specific angle and perspective]
TECH: [Specific camera model, lens, ISO, aperture, lighting condition]
STYLE: [Mood/tone]
NEGATIVE: [Exclude faces, text, maps]
"""

def get_image_generation_prompt(bullet_point, article_text):
    """
    Generate the system prompt for image generation
    
    Args:
        bullet_point (str): The bullet point to generate an image for
        article_text (str): The full article text for context
        
    Returns:
        dict: The formatted system prompt as a dictionary for image generation
    """
    import re
    
    # If the article text is too long, truncate it for the prompt
    max_article_length = 3000
    article_text_truncated = article_text[:max_article_length] + "..." if len(article_text) > max_article_length else article_text
    
    # Extract quoted keywords and key phrases from the bullet point
    quoted_keywords = re.findall(r'"([^"]*)"', bullet_point)
    quoted_keywords_str = ", ".join(quoted_keywords) if quoted_keywords else "None"
    
    # Format the user prompt with all parameters
    user_content = IMAGE_USER_PROMPT_TEMPLATE.format(
        bullet_point=bullet_point,
        quoted_keywords=quoted_keywords_str,
        article_text=article_text_truncated
    )
    
    prompt_data = {
        "messages": [
            {"role": "system", "content": IMAGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "response_format": {"type": "text"}
    }
    
    # Log the input and output for debugging
    log_prompt_data = {
        "timestamp": datetime.now().isoformat(),
        "bullet_point": bullet_point,
        "quoted_keywords": quoted_keywords_str,
        "article_length": len(article_text),
        "truncated_article_length": len(article_text_truncated),
        "prompt_messages": prompt_data["messages"]
    }
    
    logger.info(f"Generated image prompt for bullet point: {bullet_point[:50]}...")
    
    try:
        # Log the full prompt data to a JSON file for detailed analysis
        prompt_log_file = os.path.join(log_dir, f'prompt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(prompt_log_file, 'w') as f:
            json.dump(log_prompt_data, f, indent=2)
        logger.info(f"Full prompt data logged to {prompt_log_file}")
    except Exception as e:
        logger.error(f"Error logging prompt data: {str(e)}")
    
    return prompt_data

def log_image_generation_response(bullet_point, prompt_response, image_url=None):
    """
    Log the response from the image generation model
    
    Args:
        bullet_point (str): The original bullet point
        prompt_response (str): The response from the prompt engineer
        image_url (str, optional): URL to the generated image if available
    """
    try:
        response_data = {
            "timestamp": datetime.now().isoformat(),
            "bullet_point": bullet_point,
            "prompt_response": prompt_response,
            "image_url": image_url
        }
        
        # Log to the main log file
        logger.info(f"Image prompt response received for bullet point: {bullet_point[:50]}...")
        
        # Save detailed response to JSON file
        response_log_file = os.path.join(log_dir, f'response_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(response_log_file, 'w') as f:
            json.dump(response_data, f, indent=2)
        logger.info(f"Full response data logged to {response_log_file}")
        
        return True
    except Exception as e:
        logger.error(f"Error logging response data: {str(e)}")
        return False

def get_concise_image_generation_prompt(bullet_point, article_text):
    """
    Generate a concise version of the image generation prompt
    
    Args:
        bullet_point (str): The bullet point to generate an image for
        article_text (str): The full article text for context
        
    Returns:
        dict: The formatted system prompt as a dictionary for image generation with concise format
    """
    import re
    
    # If the article text is too long, truncate it further for the concise prompt
    max_article_length = 1500
    article_text_truncated = article_text[:max_article_length] + "..." if len(article_text) > max_article_length else article_text
    
    # Extract quoted keywords and key phrases from the bullet point
    quoted_keywords = re.findall(r'"([^"]*)"', bullet_point)
    quoted_keywords_str = ", ".join(quoted_keywords) if quoted_keywords else "None"
    
    # Simplified concise prompt template
    concise_system_prompt = """
    You are an expert prompt engineer. Create a detailed press photography prompt for a 4K vertical (9:16) editorial photograph based on the bullet point.
    
    KEY POINTS:
    • Focus only on the bullet point content
    • NO faces, NO text, NO maps of any kind
    • For geographic content, use landmarks not maps
    • Keep prompt between 200-250 words
    • AVOID all acronyms and abbreviations - spell out full names
    • Choose a specific camera angle and shooting perspective
    
    CONTENT APPROACH:
    • For financial/economic topics: Focus on OBJECTS (coins, charts, documents)
    • For social/cultural topics: Create meaningful SCENES
    • Choose the approach that best fits the specific content
    
    TECHNICAL SPECIFICATIONS:
    • Classification: Editorial, documentary press photo
    • Resolution: 3840 × 2160 px, portrait (9:16)
    • Camera body: Specify ONE (Canon EOS R5, Nikon Z9, or Sony A1)
    • Lens: Specify ONE prime lens (35mm f/1.4, 50mm f/1.2, or 85mm f/1.8)
    • Settings: ISO (100-3200), aperture (f/4-f/8 preferred)
    • Lighting: Specify ONE (golden hour, blue hour, overcast daylight, neutral indoor)
    • Composition: Rule of thirds, leading lines, layers for depth
    
    FORMAT:
    OBJECTS or SCENE: [Key objects with clear descriptions] or [Setting with specific details]
    FOCAL ELEMENTS: [Key objects/elements]
    COMPOSITION: [Layout with specific angle and perspective]
    TECH: [Specific camera model, lens, settings, lighting]
    STYLE: [Mood with realistic color profile]
    NEGATIVE: faces, text, maps
    –ar 9:16 –quality 4k
    """
    
    # Simplified concise user prompt
    concise_user_prompt = f"""
    BULLET POINT: {bullet_point}
    ARTICLE CONTEXT: {article_text_truncated}
    
    Create a press photo prompt that:
    1. Focuses on this bullet point only
    2. Shows no maps, faces, or text
    3. Uses landmarks for locations
    4. Stays under 250 words
    5. AVOIDS all acronyms and abbreviations
    6. Specifies exact camera equipment and settings
    7. Includes a specific camera angle and perspective
    
    APPROACH:
    • For financial/economic topics: Focus on OBJECTS (coins, charts, documents)
    • For social/cultural topics: Create meaningful SCENES
    • Choose what best represents this specific content
    
    Include: OBJECTS or SCENE, FOCAL ELEMENTS, COMPOSITION, TECH, STYLE, NEGATIVE
    """
    
    prompt_data = {
        "messages": [
            {"role": "system", "content": concise_system_prompt},
            {"role": "user", "content": concise_user_prompt}
        ],
        "response_format": {"type": "text"}
    }
    
    # Log the concise prompt generation
    logger.info(f"Generated concise image prompt for bullet point: {bullet_point[:50]}...")
    
    return prompt_data