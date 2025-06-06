import os
import base64
from PIL import Image, ImageDraw, ImageFont
import textwrap
from io import BytesIO
import hashlib
import re
import shutil
from openai import OpenAI
from text_processor import fix_unicode
from image_utils import calculate_shadow, smart_wrap_text
from prompts import get_image_generation_prompt
from prompts.image_generation_prompt import get_image_generation_prompt
from utils.openai_utils import generate_image_prompt, generate_batch_image_prompts

def get_openai_api_key():
    """
    Try multiple approaches to get the OpenAI API key.
    Returns the API key if found, None otherwise.
    """
    # Method 1: Try to get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Method 2: Check in streamlit secrets via os.environ
    if not api_key and 'OPENAI_API_KEY' in os.environ:
        api_key = os.environ['OPENAI_API_KEY']
    
    # Method 3: Try to read from .streamlit/secrets.toml directly
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

def setup_openai_api_key():
    """
    Set up the OpenAI API key from environment variables or secrets
    
    Returns:
        bool: True if API key was successfully set up, False otherwise
    """
    try:
        # Check if OPENAI_API_KEY is already in the environment
        api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key:
            # API key already exists in environment, nothing to do
            return True
        else:
            # Try to read from secrets.toml
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
                    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
                    return True
            except ImportError:
                # Streamlit not available, cannot use st.secrets
                pass
                
            # If we got here, we couldn't find the API key
            print("OpenAI API key not found in environment variables or secrets")
            return False
    except Exception as e:
        print(f"Error setting up OpenAI API key: {e}")
        return False

def generate_images_for_bullet_points(bullet_points, article_text, output_dir="cache/img/"):
    """
    Generate images for all bullet points in a batch
    
    Args:
        bullet_points (list): List of bullet point texts
        article_text (str): The full article text for context
        output_dir (str): Directory to save the generated images
        
    Returns:
        list: List of paths to the generated images
    """
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    
    try:
        # Generate all image prompts in one batch API call
        print(f"Generating image prompts for {len(bullet_points)} bullet points...")
        image_prompts_data = generate_batch_image_prompts(bullet_points, article_text)
        
        # Process each image prompt
        for i, prompt_data in enumerate(image_prompts_data):
            bullet_point = prompt_data["bullet_point"]
            image_prompt = prompt_data["image_prompt"]
            keywords = prompt_data.get("keywords", [])
            
            print(f"Generating image {i+1}/{len(bullet_points)}: {bullet_point[:30]}...")
            
            # Create a unique filename based on the hash of the bullet point
            text_hash = hashlib.md5(bullet_point.encode()).hexdigest()[:10]
            output_file = os.path.join(output_dir, f"{text_hash}.jpg")
            
            # Generate the image using the optimized prompt
            try:
                generate_image_with_prompt(image_prompt, output_file)
                image_paths.append(output_file)
            except Exception as e:
                print(f"Error generating image for bullet point {i+1}: {e}")
                # Create fallback image
                fallback_file = create_fallback_image(bullet_point, output_dir)
                image_paths.append(fallback_file)
    
    except Exception as e:
        print(f"Error in batch image generation: {e}")
        # Create fallback images for all bullet points
        for i, bullet_point in enumerate(bullet_points):
            fallback_file = create_fallback_image(bullet_point, output_dir)
            image_paths.append(fallback_file)
    
    return image_paths

def generate_image_with_prompt(prompt, output_file):
    """
    Generate an image using OpenAI's DALL-E model with a specific prompt
    
    Args:
        prompt (str): The detailed image prompt 
        output_file (str): Path to save the generated image
        
    Returns:
        None
    """
    print(f"Generating image with prompt: {prompt[:10000]}...")

    try:
        # Try to get API key from environment or secrets
        if not setup_openai_api_key():
            print("Warning: OpenAI API key not found or invalid")
            raise ValueError("OpenAI API key not found in environment variables or secrets")
            
        # Initialize OpenAI client with API key from environment
        client = OpenAI()
        
        # Use a try-except block specifically for the API call
        try:
            # Call OpenAI's image generation with gpt-image-1 model
            response = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                n=1,
                size="1024x1024",  # Use standard size first
                quality="high",
                output_format="png",  
                moderation="auto",
                background="auto",
            )
            
            print("API call completed successfully")
            
            # Check if the response contains valid data
            if not response.data or not hasattr(response.data[0], 'b64_json') or not response.data[0].b64_json:
                print("Error: API response missing base64 data")
                raise ValueError("Invalid response from OpenAI API - missing base64 image data")
            
            # Extract base64 data from the response
            image_bytes = base64.b64decode(response.data[0].b64_json)
            print(f"Decoded {len(image_bytes)} bytes of image data")
            
            # Create PIL Image from bytes
            try:
                img = Image.open(BytesIO(image_bytes))
                print(f"Successfully opened image: {img.format}, {img.size}")
            except Exception as img_open_error:
                print(f"Error opening image from bytes: {img_open_error}")
                raise ValueError(f"Failed to create image from API response: {img_open_error}")
            
            # Create a new image with desired dimensions
            target_width = 1080
            target_height = 1920

            # Calculate dimensions to maintain aspect ratio
            original_aspect = img.width / img.height
            target_aspect = target_width / target_height

            if original_aspect > target_aspect:
                # Original image is wider than target
                new_width = int(target_height * original_aspect)
                new_height = target_height
                img = img.resize((new_width, new_height))
                left = (new_width - target_width) // 2
                img = img.crop((left, 0, left + target_width, target_height))
            else:
                # Original image is taller than target
                new_height = int(target_width / original_aspect)
                new_width = target_width
                img = img.resize((new_width, new_height))
                top = (new_height - target_height) // 2
                img = img.crop((0, top, target_width, top + target_height))

            print(f"Resized image to {target_width}x{target_height}")
            
            # Convert back to bytes
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='JPEG')
            
            # Make sure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            # Write the image to file
            try:
                with open(output_file, 'wb') as f:
                    f.write(img_byte_arr.getvalue())
                print(f"Image saved to {output_file}")
                
                # Verify that the file was created and is a valid image
                if os.path.exists(output_file):
                    with Image.open(output_file) as verify_img:
                        # Just checking that we can open it
                        img_size = verify_img.size
                        print(f"Verified saved image: {verify_img.format}, {img_size}")
                else:
                    print(f"Warning: File {output_file} was not created")
                    raise IOError(f"File not created: {output_file}")
                    
            except Exception as save_error:
                print(f"Error saving image: {save_error}")
                raise IOError(f"Failed to save image to {output_file}: {save_error}")
                
        except Exception as api_error:
            print(f"OpenAI API error: {api_error}")
            raise ValueError(f"OpenAI API error: {api_error}")
        
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        raise e

def create_fallback_image(text, output_dir):
    """
    Create a fallback image with the given text
    
    Args:
        text (str): The text to display on the fallback image
        output_dir (str): Directory to save the fallback image
        
    Returns:
        str: Path to the created fallback image
    """
    text = fix_unicode(text)
    text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
    fallback_file = os.path.join(output_dir, f"fallback_{text_hash}.jpg")
    
    try:
        fallback_img = Image.new('RGB', (1080, 1920), color=(50, 50, 50))
        draw = ImageDraw.Draw(fallback_img)
        
        try:
            # First try with our custom font
            font = ImageFont.truetype("fonts/Leelawadee Bold.ttf", 40)
        except Exception as font_error:
            print(f"Error loading custom font: {font_error}, using default font")
            # Fall back to default font
            font = ImageFont.load_default()
            
        wrapped_text = textwrap.fill(text, width=30)
        text_color = (255, 255, 255)
        
        # Calculate text position to center it
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        position = ((1080 - text_width) // 2, (1920 - text_height) // 2)
        
        # Draw the text
        draw.text(position, wrapped_text, font=font, fill=text_color)
        
        # Save the fallback image
        fallback_img.save(fallback_file)
        print(f"Created fallback image: {fallback_file}")
        
        return fallback_file
    except Exception as fallback_error:
        print(f"Critical error creating fallback image: {fallback_error}")
        # Last resort: try one more time with absolute minimal approach
        try:
            print("Attempting emergency fallback image creation...")
            simple_img = Image.new('RGB', (1080, 1920), color=(0, 0, 0))
            simple_img.save(fallback_file)
            return fallback_file
        except:
            print("CRITICAL FAILURE: Could not create even a simple fallback image")
            # Return the path anyway, let the caller handle missing file
            return fallback_file

def generate_image(text, output_file):
    """
    Generate an image for the given text using OpenAI's DALL-E model
    
    Args:
        text (str): The text to visualize in the image
        output_file (str): Path to save the generated image
        
    Returns:
        None
    """
    text = fix_unicode(text)

    # Use the headline directly
    headline = text
    
    # Get a dedicated image prompt for this text
    try:
        # Generate a specific image prompt for this text
        image_prompt = generate_image_prompt(headline, headline)
        print(f"Generated image prompt: {image_prompt[:100]}...")
        generate_image_with_prompt(image_prompt, output_file)
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        # Create a fallback gray image with the text
        fallback_file = create_fallback_image(headline, os.path.dirname(output_file))
        
        # If fallback file is different from requested output file, copy it
        if fallback_file != output_file:
            try:
                shutil.copy(fallback_file, output_file)
            except Exception as copy_error:
                print(f"Error copying fallback image: {copy_error}")


def generate_image_for_text(text, force_regenerate=False):
    """
    Generate an image for the given text and return the path to the created image
    
    Args:
        text (str): The text to generate an image for
        force_regenerate (bool): If True, regenerate the image even if it exists
        
    Returns:
        str: Path to the generated image
    """
    try:
        # Ensure cache directory exists
        os.makedirs("cache/img/", exist_ok=True)
        
        # Create a unique filename based on the hash of the text
        text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
        output_file = f"cache/img/{text_hash}.jpg"
        
        # Check if the image already exists to avoid regenerating
        if not force_regenerate and os.path.exists(output_file):
            print(f"Using cached image: {output_file}")
            # Verify the file is a valid image
            try:
                with Image.open(output_file) as img:
                    # Just checking if we can open it
                    img_format = img.format
                    img_size = img.size
                    if img_size[0] < 100 or img_size[1] < 100:
                        print(f"Cached image is too small ({img_size}), regenerating...")
                        # Force regeneration
                        force_regenerate = True
                    else:
                        print(f"Verified cached image: {img_format}, {img_size}")
                        return output_file
            except Exception as img_error:
                print(f"Error verifying cached image: {img_error}, regenerating...")
                force_regenerate = True
        
        # If force_regenerate is True or the file doesn't exist or is invalid, generate a new image
        if force_regenerate or not os.path.exists(output_file):
            print(f"Generating new image for text: {text[:50]}...")
            
            try:
                # Try to generate image with OpenAI
                generate_image(text, output_file)
                
                # Verify the image was created and is valid
                if os.path.exists(output_file):
                    try:
                        with Image.open(output_file) as img:
                            # Check if the image is valid
                            img_format = img.format
                            img_size = img.size
                            print(f"Successfully generated image: {output_file} ({img_format}, {img_size})")
                            return output_file
                    except Exception as img_verify_error:
                        print(f"Error verifying generated image: {img_verify_error}, creating fallback...")
                        raise Exception(f"Invalid image generated: {img_verify_error}")
                else:
                    raise FileNotFoundError(f"Image generation failed - file not created: {output_file}")
            except Exception as gen_error:
                print(f"Error in image generation: {str(gen_error)}, creating fallback image...")
                # Let it continue to the fallback
                raise gen_error
    except Exception as e:
        print(f"Error in generate_image_for_text: {str(e)}")
        # Create a fallback image
        return create_fallback_image(text, "cache/img/") 