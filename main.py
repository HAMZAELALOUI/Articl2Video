import requests
from bs4 import BeautifulSoup
import re
import json
import urllib.parse
import os
from gtts import gTTS
import shutil
from PIL import Image, ImageDraw, ImageFont
import textwrap
from io import BytesIO
import glob
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, VideoFileClip, CompositeAudioClip
from moviepy.audio.AudioClip import AudioClip
import base64
import google.generativeai as genai
from json import loads
import hashlib
from openai import OpenAI  # Import OpenAI client

# API Keys are expected to be set as environment variables
# by the calling script (e.g., streamlit_app.py using st.secrets)

# Configure Gemini API using environment variable
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    # If running main.py directly, it might fail here.
    # Consider adding a fallback or a specific error message for direct execution.
    print("Warning: GEMINI_API_KEY environment variable not found. Gemini API calls may fail.")
    # raise ValueError("GEMINI_API_KEY not found in environment variables.") # Optional: raise error
else:
    genai.configure(api_key=gemini_api_key)

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY environment variable not found. Image generation calls may fail.")

def scrape_text_from_url(url):

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the URL: {url}")
    soup = BeautifulSoup(response.content, 'html.parser')
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def call_llm_api(article_text, slidenumber, wordnumber, language):
    try:
        prompt = f'''Article scraped text and content and Data: {article_text}
        
        Task: You are an LLM in JSON mode now, you generate directly a JSON, no more, no less, where you summarize this article in {slidenumber} bullet points in a journalist narrative reporting style format that highlight the main key points from the article, and keep the coherence between each bullet point like a story video content, make it in {language} and don't use Unicodes like "u00e9" put a real "é".
        
        NB: Make {slidenumber} short bullet points (around {wordnumber} words max per each) in a narrative style like a reporter and all these bullet points summarize and narrate it in a great way that gives the user a great general idea about the article and don't miss the main ideas but try to keep the flow running and coherence between each bullet point in a way where you can read them and feel like you are reading one article. And there is {slidenumber} bullet points and don't forget that you need to generate a {language} text.
        
        Example: {{"summary": ["Bullet point 1", "Bullet point 2", "Bullet point 3",...], "Total": "x", "Tone": "Tone of the best voice over for it"}}
        
        IMPORTANT: The article text is the only input you have, you can't use any other data or information, you can't use any other source or external data. Don't hallucinate, don't imagine, don't make up, don't add, don't remove, don't change, don't modify, don't do anything else, just summarize the article in bullet points format that highlight the main key points from the article, no Unicodes, and do it in {language} and Focus on Generating the right characters and not giving Unicode like in French use é,à,è,ù... please never generate Unicodes, and for numbers don't put a "." like in "1.600" write directly "1600"; and if mentioned use "S.M. ..." for King Mohammed VI. and generate only the JSON no intro no outro no nothing else, just the JSON, no more, no less.'''
        
        # Create a Gemini model instance
        model = genai.GenerativeModel('gemini-2.0-flash')
                # Generate content
        response = model.generate_content(prompt)
        
        # Extract JSON from the response
        json_text = response.text
        
        # Sometimes the model might output text with markdown code block formatting
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].strip()
            
        # Parse the JSON text
        result = loads(json_text)
        return result
        
    except Exception as e:
        print(f"Error in LLM API call: {str(e)}")
        # Return a fallback response with error message
        return {
            "summary": [f"Error generating summary: {str(e)}"],
            "Total": "0",
            "Tone": "Neutral"
        }


def save_and_clean_json(response, file_path):
    # First, handle the case where response is a string
    if isinstance(response, str):
        response = json.loads(response.replace('\n', '').replace('\\', ''))
    
    # If response is a dict and contains 'response' key
    if isinstance(response, dict) and 'response' in response:
        response = response['response']
        # If response is still a string, parse it
        if isinstance(response, str):
            response = json.loads(response.replace('\n', '').replace('\\', ''))

    # Write the cleaned JSON to file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(response, f, ensure_ascii=False, indent=4)
    
    return response


def fix_unicode(text):
     # Preprocess text - replace common Unicode characters
    # French characters
    text = text.replace('\\u00e9', 'é').replace('\\u00e8', 'è').replace('\\u00ea', 'ê')
    text = text.replace('\\u00e0', 'à').replace('\\u00e2', 'â').replace('\\u00f9', 'ù')
    text = text.replace('\\u00fb', 'û').replace('\\u00ee', 'î').replace('\\u00ef', 'ï')
    text = text.replace('\\u00e7', 'ç').replace('\\u0153', 'œ').replace('\\u00e6', 'æ')
    text = text.replace('\\u20ac', '€').replace('\\u00ab', '«').replace('\\u00bb', '»')
    text = text.replace('\\u2013', '–').replace('\\u2014', '—').replace('\\u2018', ''')
    text = text.replace('\\u2019', ''').replace('\\u201a', '‚').replace('\\u201c', '"')
    text = text.replace('\\u201d', '"').replace('\\u201e', '„').replace('\\u2026', '…')
    text = text.replace('\\u2030', '‰').replace('\\u0152', 'Œ').replace('\\u00a0', ' ')
    text = text.replace('\\u00b0', '°').replace('\\u00a3', '£').replace('\\u00a7', '§')
    text = text.replace('\\u00b7', '·').replace('\\u00bf', '¿').replace('\\u00a9', '©')
    text = text.replace('\\u00ae', '®').replace('\\u2122', '™').replace('\\u00bc', '¼')
    text = text.replace('\\u00bd', '½').replace('\\u00be', '¾').replace('\\u00b1', '±')
    text = text.replace('\\u00d7', '×').replace('\\u00f7', '÷').replace('\\u00a2', '¢')
    text = text.replace('\\u00a5', '¥').replace('\\u00ac', '¬').replace('\\u00b6', '¶')
    text = text.replace('\\u2022', '•')

    # Spanish characters
    text = text.replace('\\u00f1', 'ñ').replace('\\u00ed', 'í').replace('\\u00f3', 'ó')
    text = text.replace('\\u00fa', 'ú').replace('\\u00fc', 'ü').replace('\\u00a1', '¡')
    text = text.replace('\\u00bf', '¿').replace('\\u00e1', 'á').replace('\\u00e9', 'é')
    text = text.replace('\\u00f3', 'ó').replace('\\u00fa', 'ú').replace('\\u00fc', 'ü')
    # German characters
    text = text.replace('\\u00df', 'ß').replace('\\u00e4', 'ä').replace('\\u00f6', 'ö')
    text = text.replace('\\u00fc', 'ü')

    # Italian characters
    text = text.replace('\\u00e0', 'à').replace('\\u00e8', 'è').replace('\\u00e9', 'é')
    text = text.replace('\\u00ec', 'ì').replace('\\u00f2', 'ò').replace('\\u00f9', 'ù')
    text = text.replace('\\u00f9', 'ù')

    # Russian characters
    text = text.replace('\\u0410', 'А').replace('\\u0411', 'Б').replace('\\u0412', 'В')
    text = text.replace('\\u0413', 'Г').replace('\\u0414', 'Д').replace('\\u0415', 'Е')
    text = text.replace('\\u0416', 'Ж').replace('\\u0417', 'З').replace('\\u0418', 'И')
    text = text.replace('\\u0419', 'Й').replace('\\u041a', 'К').replace('\\u041b', 'Л')
    text = text.replace('\\u041c', 'М').replace('\\u041d', 'Н').replace('\\u041e', 'О')
    text = text.replace('\\u041f', 'П').replace('\\u0420', 'Р').replace('\\u0421', 'С')
    text = text.replace('\\u0422', 'Т').replace('\\u0423', 'У').replace('\\u0424', 'Ф')
    text = text.replace('\\u0425', 'Х').replace('\\u0426', 'Ц').replace('\\u0427', 'Ч')
    text = text.replace('\\u0428', 'Ш').replace('\\u0429', 'Щ').replace('\\u042a', 'Ъ')
    text = text.replace('\\u042b', 'Ы').replace('\\u042c', 'Ь').replace('\\u042d', 'Э')
    text = text.replace('\\u042e', 'Ю').replace('\\u042f', 'Я').replace('\\u0430', 'а')
    text = text.replace('\\u0431', 'б').replace('\\u0432', 'в').replace('\\u0433', 'г')
    text = text.replace('\\u0434', 'д').replace('\\u0435', 'е').replace('\\u0436', 'ж')
    text = text.replace('\\u0437', 'з').replace('\\u0438', 'и').replace('\\u0439', 'й')
    text = text.replace('\\u043a', 'к').replace('\\u043b', 'л').replace('\\u043c', 'м')
    text = text.replace('\\u043d', 'н').replace('\\u043e', 'о').replace('\\u043f', 'п')
    text = text.replace('\\u0440', 'р').replace('\\u0441', 'с').replace('\\u0442', 'т')
    text = text.replace('\\u0443', 'у').replace('\\u0444', 'ф').replace('\\u0445', 'х')
    text = text.replace('\\u0446', 'ц').replace('\\u0447', 'ч').replace('\\u0448', 'ш')
    text = text.replace('\\u0449', 'щ').replace('\\u044a', 'ъ').replace('\\u044b', 'ы')
    text = text.replace('\\u044c', 'ь').replace('\\u044d', 'э').replace('\\u044e', 'ю')
    text = text.replace('\\u044f', 'я')
    
    # Arabic characters - generic replacement for common encoding issues
    text = text.replace('\\u0627', 'ا').replace('\\u064a', 'ي').replace('\\u0644', 'ل')
    text = text.replace('\\u062a', 'ت').replace('\\u0646', 'ن').replace('\\u0633', 'س')
    text = text.replace('\\u0645', 'م').replace('\\u0631', 'ر').replace('\\u0648', 'و')
    text = text.replace('\\u0639', 'ع').replace('\\u062f', 'د').replace('\\u0628', 'ب')
    text = text.replace('\\u0649', 'ى').replace('\\u0629', 'ة').replace('\\u062c', 'ج')
    text = text.replace('\\u0642', 'ق').replace('\\u0641', 'ف').replace('\\u062d', 'ح')
    text = text.replace('\\u0635', 'ص').replace('\\u0637', 'ط').replace('\\u0632', 'ز')
    text = text.replace('\\u0634', 'ش').replace('\\u063a', 'غ').replace('\\u062e', 'خ')
    text = text.replace('\\u0623', 'أ').replace('\\u0621', 'ء').replace('\\u0624', 'ؤ')
    text = text.replace('\\u0626', 'ئ').replace('\\u0625', 'إ').replace('\\u0651', 'ّ')
    text = text.replace('\\u0652', 'ْ').replace('\\u064b', 'ً').replace('\\u064c', 'ٌ')
    text = text.replace('\\u064d', 'ٍ').replace('\\u064f', 'ُ').replace('\\u0650', 'ِ')
    text = text.replace('\\u064e', 'َ').replace('\\u0653', 'ٓ').replace('\\u0654', 'ٔ')
    text = text.replace('\\u0670', 'ٰ').replace('\\u0671', 'ٱ').replace('\\u0672', 'ٲ')
    text = text.replace('\\u0673', 'ٳ').replace('\\u0675', 'ٵ').replace('\\u0676', 'ٶ')
    text = text.replace('\\u0677', 'ٷ').replace('\\u0678', 'ٸ').replace('\\u0679', 'ٹ')
    text = text.replace('\\u067a', 'ٺ').replace('\\u067b', 'ٻ').replace('\\u067c', 'ټ')
    text = text.replace('\\u067d', 'ٽ').replace('\\u067e', 'پ').replace('\\u067f', 'ٿ')
    text = text.replace('\\u0680', 'ڀ').replace('\\u0681', 'ځ').replace('\\u0682', 'ڂ')
    text = text.replace('\\u0683', 'ڃ').replace('\\u0684', 'ڄ').replace('\\u0685', 'څ')
    text = text.replace('\\u0686', 'چ').replace('\\u0687', 'ڇ').replace('\\u0688', 'ڈ')
    text = text.replace('\\u0689', 'ډ').replace('\\u068a', 'ڊ').replace('\\u068b', 'ڋ')
    text = text.replace('\\u068c', 'ڌ').replace('\\u068d', 'ڍ').replace('\\u068e', 'ڎ')
    text = text.replace('\\u068f', 'ڏ').replace('\\u0690', 'ڐ').replace('\\u0691', 'ڑ')
    text = text.replace('\\u0692', 'ڒ').replace('\\u0693', 'ړ').replace('\\u0694', 'ڔ')
    text = text.replace('\\u0695', 'ڕ').replace('\\u0696', 'ږ').replace('\\u0697', 'ڗ')
    text = text.replace('\\u0698', 'ژ').replace('\\u0699', 'ڙ').replace('\\u069a', 'ښ')
    text = text.replace('\\u069b', 'ڛ').replace('\\u069c', 'ڜ').replace('\\u069d', 'ڝ')
    text = text.replace('\\u069e', 'ڞ').replace('\\u069f', 'ڟ').replace('\\u06a0', 'ڠ')
    text = text.replace('\\u06a1', 'ڡ').replace('\\u06a2', 'ڢ').replace('\\u06a3', 'ڣ')
    text = text.replace('\\u06a4', 'ڤ').replace('\\u06a5', 'ڥ').replace('\\u06a6', 'ڦ')
    text = text.replace('\\u06a7', 'ڧ').replace('\\u06a8', 'ڨ').replace('\\u06a9', 'ک')
    text = text.replace('\\u06aa', 'ڪ').replace('\\u06ab', 'ګ').replace('\\u06ac', 'ڬ')
    text = text.replace('\\u06ad', 'ڭ').replace('\\u06ae', 'ڮ').replace('\\u06af', 'گ')
    text = text.replace('\\u06b0', 'ڰ').replace('\\u06b1', 'ڱ').replace('\\u06b2', 'ڲ')
    text = text.replace('\\u06b3', 'ڳ').replace('\\u06b4', 'ڴ').replace('\\u06b5', 'ڵ')
    text = text.replace('\\u06b6', 'ڶ').replace('\\u06b7', 'ڷ').replace('\\u06b8', 'ڸ')
    text = text.replace('\\u06b9', 'ڹ').replace('\\u06ba', 'ں').replace('\\u06bb', 'ڻ')

    return text




def print_summary_points(data):

    if 'summary' in data:
        for point in data['summary']:
            point = fix_unicode(point)
            print(f"• {point}")

        print(f"\nTotal points: {data.get('Total', 'N/A')}")
        print(f"Recommended tone: {data.get('Tone', 'N/A')}")


def text_to_speech(text, output_file, language):
    # Map language codes
    language_map = {
        'anglais': 'en',
        'francais': 'fr',
        'espagnol': 'es',
        'arabe': 'ar',
        'allemand': 'de',
        'russe': 'ru',
        'italien': 'it',
        'portugais': 'pt'
    }
    
    # Get the correct language code
    lang_code = language_map.get(language.lower(), 'en')

    text = fix_unicode(text)
    
    try:
        # Initialize gTTS with text and language
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Save to file
        tts.save(output_file)
        print(f"Audio content saved to {output_file}")
        
    except Exception as e:
        print(f"Error generating speech: {str(e)}")



def on_queue_update(update):
    # This function is no longer needed but kept for backwards compatibility
    print(f"Processing update: {update}")



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

def setup_openai_api_key(key=None):
    """
    Set the OpenAI API key in the environment if provided, 
    or try to read it from secrets or environment variables.
    Returns True if successful, False otherwise.
    """
    if key:
        os.environ["OPENAI_API_KEY"] = key
        return True
        
    # Try from .streamlit/secrets.toml first (most direct for Streamlit apps)
    try:
        import toml
        secrets_path = '.streamlit/secrets.toml'
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            if 'OPENAI_API_KEY' in secrets:
                os.environ["OPENAI_API_KEY"] = secrets['OPENAI_API_KEY']
                print("Found OpenAI API key in secrets.toml")
                return True
    except Exception as e:
        print(f"Error reading secrets.toml: {e}")
        
    # Fallback to other methods
    api_key = get_openai_api_key()
    if api_key:
        os.getenv["OPENAI_API_KEY"] = api_key
        print("Found OpenAI API key in environment variables")
        return True
    
    return False

def generate_image(text, output_file):

    text = fix_unicode(text)

    # Use the headline directly
    headline = text
    
    # Exactly as specified by user
    scene_prompt = (
        f"Ultra-realistic 4K editorial photograph press shot illustrating the following topic: {headline}. "
        "Symbolic, in-animate elements that visually convey the story; dramatic cinematic lighting, high contrast, deep shadows, news-photography style, vertical 9:16 composition. "
        "Scene is completely deserted — absolutely no humans, silhouettes or body parts; no written text, no logos, no flags or religious symbols.no public figures. "
    )
 
    print(f"Generating image with user-specified prompt...")

    try:
        # Try to get API key from environment or secrets
        if not setup_openai_api_key():
            raise ValueError("OpenAI API key not found in environment variables or secrets")
            
        # Initialize OpenAI client with API key from environment
        client = OpenAI()
        
        # Call OpenAI's image generation with gpt-image-1 model
        response = client.images.generate(
            model="gpt-image-1",
            prompt=scene_prompt,
            n=1,
            size="1024x1024",  # Use standard size first
            quality="high",
            output_format="png",  
            moderation="auto",
        )
        
        # Check if the response contains valid data
        if not response.data or not hasattr(response.data[0], 'b64_json') or not response.data[0].b64_json:
            raise ValueError("Invalid response from OpenAI API - missing base64 image data")
        
        # Extract base64 data from the response
        image_bytes = base64.b64decode(response.data[0].b64_json)
        
        # Create PIL Image
        img = Image.open(BytesIO(image_bytes))

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

        # Convert back to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG')

        with open(output_file, 'wb') as f:
            f.write(img_byte_arr.getvalue())
        print(f"Image saved to {output_file}")
        
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        # Create a fallback gray image with the text
        fallback_img = Image.new('RGB', (1080, 1920), color=(50, 50, 50))
        draw = ImageDraw.Draw(fallback_img)
        
        # Try to wrap and draw the text on the fallback image
        try:
            font = ImageFont.truetype("Montserrat-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        wrapped_text = textwrap.fill(headline, width=30)
        text_color = (255, 255, 255)
        
        # Calculate text position to center it
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        position = ((1080 - text_width) // 2, (1920 - text_height) // 2)
        
        # Draw the text
        draw.text(position, wrapped_text, font=font, fill=text_color)
        
        # Save the fallback image
        fallback_img.save(output_file)
        print(f"Saved fallback image to {output_file} due to error in image generation")








def add_text_to_image(text, image_path, output_path):

    text = fix_unicode(text)
    
    # Open the image
    img = Image.open(image_path)
    
    # Create a copy of the image
    img_with_overlay = img.copy()
    
    # Create draw object
    draw = ImageDraw.Draw(img_with_overlay)
    
    # Calculate dimensions
    width, height = img.size
    
    # Check if frame exists to adjust content positioning
    frame_exists = False
    frame_path = "cache/custom/frame.png" if os.path.exists("cache/custom/frame.png") else "frame.png"
    frame_border_width = 0
    if os.path.exists(frame_path):
        frame_exists = True
        # Load frame to check its design
        frame = Image.open(frame_path)
        frame_rgba = frame.convert('RGBA')
        
        # More robust frame border detection
        # Check multiple points around the frame edges
        border_samples = []
        
        # Sample points from all four edges
        edge_points = [
            [(i, 5) for i in range(0, width, width//10)],             # Top edge
            [(i, height-5) for i in range(0, width, width//10)],       # Bottom edge
            [(5, i) for i in range(0, height, height//10)],            # Left edge
            [(width-5, i) for i in range(0, height, height//10)]       # Right edge
        ]
        
        # Find border width from each edge
        for edge in edge_points:
            for x, y in edge:
                try:
                    # Check if this point has alpha (part of frame)
                    if x < frame_rgba.width and y < frame_rgba.height:
                        _, _, _, a = frame_rgba.getpixel((x, y))
                        if a > 100:  # If edge pixel has alpha, frame likely has border
                            # Scan inward until we find a transparent/semi-transparent pixel
                            if x <= 5:  # Left edge sample
                                for i in range(20, 150, 5):
                                    if i >= frame_rgba.width:
                                        break
                                    if frame_rgba.getpixel((i, y))[3] < 100:
                                        border_samples.append(i)
                                        break
                            elif x >= width-5:  # Right edge sample
                                for i in range(width-20, width-150, -5):
                                    if i < 0:
                                        break
                                    if frame_rgba.getpixel((i, y))[3] < 100:
                                        border_samples.append(width - i)
                                        break
                            elif y <= 5:  # Top edge sample
                                for i in range(20, 150, 5):
                                    if i >= frame_rgba.height:
                                        break
                                    if frame_rgba.getpixel((x, i))[3] < 100:
                                        border_samples.append(i)
                                        break
                            elif y >= height-5:  # Bottom edge sample
                                for i in range(height-20, height-150, -5):
                                    if i < 0:
                                        break
                                    if frame_rgba.getpixel((x, i))[3] < 100:
                                        border_samples.append(height - i)
                                        break
                except Exception as e:
                    continue  # Skip problematic pixels
        
        # Use the median value for more stability (or minimum 60px if detection fails)
        if border_samples:
            border_samples.sort()
            frame_border_width = border_samples[len(border_samples)//2]  # Median
            # Add safety margin
            frame_border_width += 20
        else:
            frame_border_width = 60  # Conservative default
        
        print(f"Detected frame border width: {frame_border_width}px")
    
    # Add semi-transparent gray overlay over the entire image (with reduced opacity)
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(0, 0), (width, height)], 
                           fill=(50, 50, 50, 140))  # Semi-transparent gray with reduced opacity
    
    # Paste overlay onto the image
    img_with_overlay = Image.alpha_composite(img_with_overlay.convert('RGBA'), overlay)
    
    # Add logo overlay
    try:
        # Check if user wants a logo at all
        use_logo = False  # Default to no logo unless user has explicitly uploaded one
        
        # For video frames: Check for custom uploaded logo only
        video_logo_path = "cache/custom/logo.png"
        
        # Only use a logo if the user has explicitly uploaded one
        if os.path.exists(video_logo_path):
            use_logo = True
        
        if use_logo and os.path.exists(video_logo_path):
            logo = Image.open(video_logo_path)
            # Resize logo to be x of image width, maintaining aspect ratio
            logo_width = int(width * 0.4)  # percentage of image width
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # Calculate position to center logo at the top with some margin
            logo_x = (width - logo_width) // 2
            logo_y = int(height * 0.10)  # distance from the top
            
            # Make sure logo has alpha channel for proper overlay
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
                
            # Paste logo onto the image
            img_with_overlay.paste(logo, (logo_x, logo_y), logo)
            print(f"Added logo from {video_logo_path} to video frame")
        else:
            print("No logo will be added to video frame - user did not upload a logo")
    except Exception as e:
        print(f"Could not add logo to video frame: {e}")
    
    # --- Font Loading START ---
    # Use a specific bundled font file
    bundled_font_path = "Montserrat-Bold.ttf"  # <<< MAKE SURE THIS MATCHES THE FONT FILE YOU ADDED

    # Determine safe margins based on frame existence
    left_margin = int(width * 0.15) if frame_exists else int(width * 0.08)
    right_margin = int(width * 0.20) if frame_exists else int(width * 0.10)  # Increase right margin
    bottom_margin = int(height * 0.15) if frame_exists else int(height * 0.08)
    top_margin = int(height * 0.35)  # Keep more space at top for logo and title

    # If we detected a substantial frame border, use it to inform margins
    if frame_border_width > 0:
        left_margin = max(left_margin, frame_border_width + 30)
        right_margin = max(right_margin, frame_border_width + 50)  # Extra padding on right
        bottom_margin = max(bottom_margin, frame_border_width + 30)

    # Calculate maximum width for text - use a more conservative width
    max_text_width = width - (left_margin + right_margin + 40)  # Extra 40px safety margin

    # Set an upper limit to text height based on remaining vertical space
    max_text_height = height - top_margin - bottom_margin

    # Calculate font size adaptively
    initial_font_size = max(int(width * 0.055), 46)
    font_size = initial_font_size
    font = None

    # More intelligent text wrapping based on actual pixel width
    def smart_wrap_text(text, font, max_width):
        """Wrap text using actual pixel measurements to maximize space usage"""
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            # Calculate width including this word and a space
            word_with_space = word + " " if current_line else word
            word_bbox = draw.textbbox((0, 0), word_with_space, font=font)
            word_width = word_bbox[2] - word_bbox[0]
            
            if current_line and current_width + word_width > max_width:
                # This word doesn't fit, start a new line
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = draw.textbbox((0, 0), word, font=font)[2]
            else:
                # Word fits, add it
                current_line.append(word)
                current_width += word_width
        
        # Add the last line if it contains words
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    # --- End of smart_wrap_text definition ---


    # Try to fit text with current font size, reduce if necessary
    text_too_large = True
    min_font_size = 30  # Don't go smaller than this
    attempt = 0
    final_font_path = None # Keep track of the font path that works

    while text_too_large and font_size > min_font_size and attempt < 5:
        attempt += 1
        try:
            # Try loading the bundled font
            font = ImageFont.truetype(bundled_font_path, font_size)
            final_font_path = bundled_font_path # Font loaded successfully
            print(f"Attempting to use bundled font: {final_font_path} at size {font_size}px")

            # Use smart text wrapping based on pixel measurements
            wrapped_lines = smart_wrap_text(text, font, max_text_width)

            # Calculate total text height with this font
            estimated_text_height = len(wrapped_lines) * font_size * 1.1 + (font_size * 1.2)  # Add padding

            # Check if it fits in allowed vertical space
            if estimated_text_height <= max_text_height:
                text_too_large = False
                print(f"Using font size {font_size}px after {attempt} attempts - text fits")
            else:
                # Reduce font size by 10% and try again
                font_size = int(font_size * 0.9)
                print(f"Reducing font size to {font_size}px - text too large")

        except IOError:
             # If bundled font fails, try a basic default as last resort
            print(f"Error: Bundled font file '{bundled_font_path}' not found or cannot be opened.")
            try:
                print(f"Falling back to Pillow's default font at size {font_size}px")
                font = ImageFont.load_default().font_variant(size=font_size)
                final_font_path = "Pillow Default"

                # Use smart text wrapping based on pixel measurements
                wrapped_lines = smart_wrap_text(text, font, max_text_width)
                estimated_text_height = len(wrapped_lines) * font_size * 1.1 + (font_size * 1.2) # Add padding

                if estimated_text_height <= max_text_height:
                    text_too_large = False
                    print(f"Using default font size {font_size}px - text fits")
                else:
                    font_size = int(font_size * 0.9)
                    print(f"Reducing default font size to {font_size}px - text too large")

            except Exception as e:
                 # This should ideally not happen with load_default
                 print(f"Critical Error: Could not load even the default font. Error: {e}")
                 # Use a minimal font size with default font if possible
                 font_size = min_font_size
                 try:
                     font = ImageFont.load_default().font_variant(size=font_size)
                     final_font_path = "Pillow Default (Minimal)"
                     text_too_large = False # Force exit loop
                 except:
                      # Absolute fallback - render will likely be poor
                      print("ERROR: Unable to load any font.")
                      font = ImageFont.load_default() # Smallest default
                      final_font_path = "Pillow Default (Absolute Fallback)"
                      text_too_large = False # Force exit loop
            # If fallback is attempted, stop trying bundled font sizes
            if final_font_path != bundled_font_path:
                 text_too_large = False # Exit loop after fallback attempt


        except Exception as e:
            print(f"An unexpected error occurred during font loading: {e}")
            # Reduce font size and try again, hoping it was size related
            font_size = int(font_size * 0.9)

    # Ensure font is not None before proceeding
    if font is None:
        print("ERROR: Font object is None. Using absolute default.")
        font = ImageFont.load_default()
        final_font_path = "Pillow Default (Final Fallback)"
        font_size = 20 # Use a small default size


    print(f"Final font used: {final_font_path} at {font_size}px")
    # --- Font Loading END ---

    # Get final text wrapping with the chosen font size
    lines = smart_wrap_text(text, font, max_text_width)
    
    # Find keywords to highlight in green (words in quotes)
    green_words_pattern = r'"([^"]+)"'
    green_word_matches = re.findall(green_words_pattern, text)
    
    # Process text with highlighted parts
    has_highlights = len(green_word_matches) > 0
    
    # Calculate text positioning for left alignment
    text_x = left_margin  # Left margin
    
    # Position in bottom portion with safe margin
    # Adjust position to ensure text doesn't go below safe area
    text_height_total = len(lines) * font_size * 1.1  # Calculate total text height
    
    # Center text vertically in the available space below the logo area
    available_height = height - top_margin - bottom_margin
    text_y = top_margin + (available_height - text_height_total) // 2
    
    # Ensure text stays within bounds
    text_y = max(text_y, top_margin)
    text_y = min(text_y, height - bottom_margin - text_height_total)
    
    print(f"Text positioning: x={text_x}, y={text_y}, width={max_text_width}, height={text_height_total}")
    print(f"Image borders: left={left_margin}, right={right_margin}, top={top_margin}, bottom={bottom_margin}")

    # Add a blurred dark background behind the text for better visibility
    text_height = len(lines) * font_size * 1.1  # Tight line spacing (1.1)
    
    # Calculate text background dimensions with safe margins
    bg_padding_x = int(font_size * 0.6)  # Horizontal padding
    bg_padding_y = int(font_size * 0.6)  # Vertical padding
    
    # Ensure background stays within frame margins
    bg_x0 = max(text_x - bg_padding_x, left_margin - 10)
    bg_y0 = max(text_y - bg_padding_y, top_margin - 10)
    bg_x1 = min(text_x + max_text_width + bg_padding_x, width - right_margin + 10)
    bg_y1 = min(text_y + text_height + bg_padding_y, height - bottom_margin + 10)
    
    # Create a new layer for the text background
    text_bg = Image.new('RGBA', img.size, (0, 0, 0, 0))
    text_bg_draw = ImageDraw.Draw(text_bg)
    
    # Draw a soft, darker semi-transparent background
    corner_radius = int(font_size * 0.3)  # Rounded corners
    
    # Draw the rounded rectangle
    text_bg_draw.rounded_rectangle(
        [bg_x0, bg_y0, bg_x1, bg_y1],
        radius=corner_radius,
        fill=(0, 0, 0, 160)  # Slightly darker for better readability
    )
    
    # Apply a gaussian blur for modern look
    try:
        from PIL import ImageFilter
        text_bg = text_bg.filter(ImageFilter.GaussianBlur(radius=corner_radius/2))
    except:
        pass
    
    # Composite the blurred background
    img_with_overlay = Image.alpha_composite(img_with_overlay, text_bg)
    
    # Re-create draw object after compositing
    draw = ImageDraw.Draw(img_with_overlay)
    
    # Draw text line by line with tight spacing (1.1)
    line_y = text_y
    for line in lines:
        # Force additional text wrap check to catch any lines that might be too long
        if font.getlength(line) > max_text_width:
            # If line is still too long, use our smart wrapping to break it again
            sub_lines = smart_wrap_text(line, font, max_text_width)
            for sub_line in sub_lines:
                # Check if this line contains any words to highlight
                if has_highlights:
                    # Draw highlighted words in green, rest in white
                    current_x = text_x
                    
                    # Split the line into parts that need different colors
                    parts = []
                    last_end = 0
                    
                    for match in re.finditer(green_words_pattern, sub_line):
                        # Add text before the match
                        if match.start() > last_end:
                            parts.append((sub_line[last_end:match.start()], "white"))
                        
                        # Add the quoted text (without quotes) in green
                        parts.append((match.group(1), "green"))
                        
                        last_end = match.end()
                    
                    # Add any remaining text
                    if last_end < len(sub_line):
                        parts.append((sub_line[last_end:], "white"))
                        
                    # Draw each part with its color - ensure it stays within bounds
                    for part_text, color in parts:
                        # Calculate width of this part
                        part_bbox = draw.textbbox((0, 0), part_text, font=font)
                        part_width = part_bbox[2] - part_bbox[0]
                        
                        # Skip if this would go beyond right margin
                        if current_x + part_width > width - right_margin:
                            break
                            
                        # Calculate dynamic shadow based on text size and content type
                        prominence = 1.2 if color == "green" else 1.0  # Highlighted text gets stronger shadow
                        shadow_offset, shadow_opacity = calculate_shadow(font_size, prominence)
                        
                        # Draw dynamic shadow for better readability
                        draw.text((current_x + shadow_offset, line_y + shadow_offset), 
                                 part_text, font=font, fill=(0, 0, 0, shadow_opacity))
                        
                        # Draw the text in the appropriate color
                        if color == "green":
                            draw.text((current_x, line_y), part_text, font=font, fill="#59C532")
                        else:
                            draw.text((current_x, line_y), part_text, font=font, fill="#FFFFFF")
                        
                        # Move x position for next part
                        current_x += part_width
                else:
                    # Skip if this line would be too long
                    if font.getlength(sub_line) > max_text_width:
                        sub_line = sub_line[:int(len(sub_line) * 0.9)] + "..."
                    
                    # Calculate dynamic shadow for regular text
                    shadow_offset, shadow_opacity = calculate_shadow(font_size, 1.0)
                    
                    # No highlights - draw entire line in white with shadow
                    # Dynamic shadow for better readability
                    draw.text((text_x + shadow_offset, line_y + shadow_offset), 
                             sub_line, font=font, fill=(0, 0, 0, shadow_opacity))
                    
                    # Draw the text in white
                    draw.text((text_x, line_y), sub_line, font=font, fill="#FFFFFF")
                
                # Move to next line with tight spacing (1.1)
                line_y += font_size * 1.1
                
                # Safety check - stop if we're getting too close to bottom
                if line_y > height - bottom_margin:
                    break
            
        else:
            # Original handling for lines that fit
            if has_highlights:
                # Process as before
                # Draw highlighted words in green, rest in white
                current_x = text_x
                
                # Split the line into parts that need different colors
                parts = []
                last_end = 0
                
                for match in re.finditer(green_words_pattern, line):
                    # Add text before the match
                    if match.start() > last_end:
                        parts.append((line[last_end:match.start()], "white"))
                    
                    # Add the quoted text (without quotes) in green
                    parts.append((match.group(1), "green"))
                    
                    last_end = match.end()
                
                # Add any remaining text
                if last_end < len(line):
                    parts.append((line[last_end:], "white"))
                    
                # Draw each part with its color
                for part_text, color in parts:
                    # Calculate width of this part
                    part_bbox = draw.textbbox((0, 0), part_text, font=font)
                    part_width = part_bbox[2] - part_bbox[0]
                    
                    # Skip if this would go beyond right margin
                    if current_x + part_width > width - right_margin:
                        break
                    
                    # Calculate dynamic shadow based on text size and content type
                    prominence = 1.2 if color == "green" else 1.0  # Highlighted text gets stronger shadow
                    shadow_offset, shadow_opacity = calculate_shadow(font_size, prominence)
                    
                    # Draw dynamic shadow for better readability
                    draw.text((current_x + shadow_offset, line_y + shadow_offset), 
                             part_text, font=font, fill=(0, 0, 0, shadow_opacity))
                    
                    # Draw the text in the appropriate color
                    if color == "green":
                        draw.text((current_x, line_y), part_text, font=font, fill="#59C532")
                    else:
                        draw.text((current_x, line_y), part_text, font=font, fill="#FFFFFF")
                    
                    # Move x position for next part
                    current_x += part_width
            else:
                # Calculate dynamic shadow for regular text
                shadow_offset, shadow_opacity = calculate_shadow(font_size, 1.0)
                
                # No highlights - draw entire line in white with shadow
                # Dynamic shadow for better readability
                draw.text((text_x + shadow_offset, line_y + shadow_offset), 
                         line, font=font, fill=(0, 0, 0, shadow_opacity))
                
                # Draw the text in white
                draw.text((text_x, line_y), line, font=font, fill="#FFFFFF")
            
            # Move to next line with tight spacing (1.1)
            line_y += font_size * 1.1
            
            # Safety check - stop if we're getting too close to bottom
            if line_y > height - bottom_margin:
                break
    
    # Apply frame overlay if it exists (last step to ensure it's on top of everything)
    try:
        # Check if user wants a frame
        use_frame = False  # Default to no frame unless user has explicitly uploaded one
        
        # Check for custom frame only
        frame_path = "cache/custom/frame.png"
        
        # Only use a frame if the user has explicitly uploaded one
        if os.path.exists(frame_path):
            use_frame = True
        
        if use_frame and os.path.exists(frame_path):
            # Load frame image
            frame = Image.open(frame_path)
            
            # Ensure frame has correct dimensions
            if frame.width != width or frame.height != height:
                frame = frame.resize((width, height), Image.LANCZOS)
            
            # Make sure frame has alpha channel for proper overlay
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')
                
            # Create a new image with the frame overlaid
            img_with_frame = Image.alpha_composite(img_with_overlay, frame)
            img_with_overlay = img_with_frame
            print(f"Added frame overlay from {frame_path} to video frame")
        else:
            print("No frame overlay will be added - user did not upload a frame")
    except Exception as e:
        print(f"Could not add frame overlay to video frame: {e}")
    
    # Save the image
    img_with_overlay.convert('RGB').save(output_path)
    print(f"Collage saved to {output_path}")





def image_audio_to_video(image_dir, audio_dir, output_path, add_voiceover, add_music, frame_durations=None):
        
        print(f"Starting video creation with add_voiceover={add_voiceover}, add_music={add_music}")
        print(f"Reading images from: {image_dir}")
        print(f"Reading audio from: {audio_dir}")
        
        # Get all image and audio files
        image_files = sorted(glob.glob(os.path.join(image_dir, '*.jpg')))
        audio_files = sorted(glob.glob(os.path.join(audio_dir, '*.mp3')))
        
        print(f"Found {len(image_files)} image files")
        print(f"Found {len(audio_files)} audio files")
        
        if len(image_files) > 0:
            print(f"First image file: {image_files[0]}")
        if len(audio_files) > 0:
            print(f"First audio file: {audio_files[0]}")

        if not image_files:
            raise ValueError("No image files found")
        
        # Use default duration if not provided
        if not frame_durations:
            frame_durations = [3.0] * len(image_files)
        
        # Ensure we have enough durations for all images
        while len(frame_durations) < len(image_files):
            frame_durations.append(3.0)
        
        # Log durations for debugging
        for i, duration in enumerate(frame_durations):
            print(f"Frame {i+1}: {duration:.1f} seconds")

        # Check if we should include audio
        if not add_voiceover:  # controlling voiceover
            print("Voiceover disabled - creating video without narration")
            # Create clips without audio
            clips = []
            for i, image_file in enumerate(image_files):
                # Use provided duration
                duration = frame_durations[i] if i < len(frame_durations) else 3.0
                
                # Create image clip with no audio
                image = ImageClip(image_file).set_duration(duration)
                clips.append(image)
                print(f"Added frame {i+1} with duration {duration:.1f}s")
        else:
            print("Voiceover enabled - adding narration to video")
            # Ensure we have audio files if voiceover is enabled
            if not audio_files:
                raise ValueError(f"Voiceover enabled but no audio files found in {audio_dir}")
            
            print(f"Using {len(audio_files)} audio files for voiceover")
            
            # Create video clips with audio
            clips = []
            for i, image_file in enumerate(image_files):
                if i < len(audio_files):
                    audio_file = audio_files[i]
                    print(f"Processing frame {i+1} with audio file: {audio_file}")
                    
                    try:
                        # Load the audio to get its duration
                        audio = AudioFileClip(audio_file)
                        
                        # Decide which duration to use (user-specified or audio duration)
                        # If we have user-specified duration, use that
                        if i < len(frame_durations):
                            duration = frame_durations[i]
                            
                            # If audio is longer than specified duration, trim it
                            if audio.duration > duration:
                                audio = audio.subclip(0, duration)
                                print(f"  Trimmed audio to {duration:.1f}s (original: {audio.duration:.1f}s)")
                            # If audio is shorter, we'll use the specified duration anyway
                        else:
                            # Default to audio duration if no user specification
                            duration = audio.duration
                        
                        # Create image clip with the chosen duration
                        image = ImageClip(image_file).set_duration(duration)
                        
                        # Combine image with audio
                        video_clip = image.set_audio(audio)
                        clips.append(video_clip)
                        print(f"Added frame {i+1} with duration {duration:.1f}s (audio: {audio.duration:.1f}s)")
                    except Exception as e:
                        print(f"Error processing audio for frame {i+1}: {str(e)}")
                        # Fallback: use image without audio
                        duration = frame_durations[i] if i < len(frame_durations) else 3.0
                        image = ImageClip(image_file).set_duration(duration)
                        clips.append(image)
                        print(f"Added frame {i+1} with duration {duration:.1f}s (no audio due to error)")
                else:
                    # Use specified duration if no audio file available
                    duration = frame_durations[i] if i < len(frame_durations) else 3.0
                    image = ImageClip(image_file).set_duration(duration)
                    clips.append(image)
                    print(f"Added frame {i+1} with duration {duration:.1f}s (no audio file available)")

        # Add outro.png as a 3s clip to the end of the video
        # Check for custom outro first, then standard outro
        outro_file = "cache/custom/outro.png" if os.path.exists("cache/custom/outro.png") else "outro.png"
        
        if os.path.exists(outro_file):
            # Create outro clip with same size as frames
            outro = Image.open(outro_file)
            print(f"Using outro from {outro_file}")
            target_width = 1080
            target_height = 1920
            
            # Resize maintaining aspect ratio
            original_aspect = outro.width / outro.height
            target_aspect = target_width / target_height

            if original_aspect > target_aspect:
                # Image is wider than target
                new_width = int(target_height * original_aspect)
                new_height = target_height
                outro = outro.resize((new_width, new_height))
                left = (new_width - target_width) // 2
                outro = outro.crop((left, 0, left + target_width, target_height))
            else:
                # Image is taller than target
                new_height = int(target_width / original_aspect)
                new_width = target_width
                outro = outro.resize((new_width, new_height))
                top = (new_height - target_height) // 2
                outro = outro.crop((0, top, target_width, top + target_height))
            
            # Save resized outro temporarily
            temp_outro = "outro_temp.png"
            outro.save(temp_outro)
            
            # Create clip from resized outro
            outro_clip = ImageClip(temp_outro).set_duration(3.0)
            clips.append(outro_clip)
            print(f"Added outro with duration 3.0s")
            
            # Clean up temp file
            os.remove(temp_outro)

        # Concatenate all clips
        final_video = concatenate_videoclips(clips)
        
        # Calculate total duration
        total_duration = sum(clip.duration for clip in clips)
        print(f"Total video duration: {total_duration:.1f}s")
        
        # Check if the video has audio
        has_audio = False
        if hasattr(final_video, 'audio') and final_video.audio is not None:
            has_audio = True
            print("Final video has voiceover audio track")
        else:
            print("Final video does not have a voiceover audio track")
        
        # MUSIC SELECTION - Only use user-uploaded music, no default fallback
        processed_music_file = "cache/music/processed_background.mp3"
        custom_music_file = "cache/music/background.mp3"
        
        # Add background music if requested AND user music exists
        if add_music:
            # Check for music files in priority order
            processed_exists = os.path.exists(processed_music_file)
            custom_exists = os.path.exists(custom_music_file)
            
            print("====== MUSIC SELECTION DEBUG ======")
            print(f"Processed music file ({processed_music_file}) exists: {processed_exists}")
            print(f"User music file ({custom_music_file}) exists: {custom_exists}")
            print("===================================")
            
            # Only use user-provided music, no default fallback
            if processed_exists:
                music_path = processed_music_file
                print("► Using PRE-PROCESSED user music")
            elif custom_exists:
                music_path = custom_music_file
                print("► Using RAW user-uploaded music")
            else:
                music_path = None
                print("► No user music found - no music will be added")
            
            if music_path and os.path.exists(music_path):
                try:
                    print(f"► Loading music from: {music_path}")
                    # Load background music
                    background_music = AudioFileClip(music_path)
                    
                    # Log music duration
                    print(f"► Background music duration: {background_music.duration:.1f}s")
                    print(f"► Video duration: {final_video.duration:.1f}s")
                    
                    # If not using processed music, we may need to loop or trim
                    if music_path != processed_music_file:
                        # Loop music if it's shorter than the video
                        if background_music.duration < final_video.duration:
                            print(f"► Looping music to match video duration {final_video.duration:.1f}s")
                            background_music = background_music.loop(duration=final_video.duration)
                        else:
                            # Trim if longer than video
                            print(f"► Trimming music to match video duration {final_video.duration:.1f}s")
                            background_music = background_music.subclip(0, final_video.duration)
                        
                        # Reduce volume of background music
                        background_music = background_music.volumex(0.3)
                        print("► Adjusted music volume to 30%")
                    
                    if has_audio and add_voiceover:
                        # Mix background music with existing audio
                        final_audio = CompositeAudioClip([final_video.audio, background_music])
                        final_video = final_video.set_audio(final_audio)
                        print("► Mixed background music with voiceover audio")
                    else:
                        # Just use background music if no voiceover or if voiceover clips didn't have audio
                        final_video = final_video.set_audio(background_music)
                        print("► Added background music without voiceover")
                        
                    print(f"► Successfully added background music from {music_path}")
                except Exception as e:
                    print(f"ERROR adding background music: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print("No user-uploaded music found to add, continuing without music")
        else:
            print("Background music disabled - no music added")
        
        # Write the final video
        print(f"Generating final video at {output_path}...")
        final_video.write_videofile(output_path, fps=30)
        
        # Clean up
        final_video.close()
        for clip in clips:
            clip.close()

        print(f"Video saved to {output_path}")








def clear_cache():
    folders = ["cache/aud", "cache/img", "cache/clg"]
    
    # Keep custom music files by not deleting the music directory
    # Only delete specific folders while preserving user uploads
    for folder in folders:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')




def do_work(data, language, add_voiceover, add_music, frame_durations=None, auto_duration=False, skip_image_generation=False):
    # Create necessary directories
    os.makedirs("cache/aud/", exist_ok=True)
    os.makedirs("cache/img/", exist_ok=True)
    os.makedirs("cache/clg/", exist_ok=True)
    os.makedirs("cache/vid/", exist_ok=True)
    os.makedirs("cache/music/", exist_ok=True)
    
    print(f"DEBUG DO_WORK: add_voiceover={add_voiceover}, language={language}, auto_duration={auto_duration}")

    # Check for user-uploaded background music
    custom_music_file = "cache/music/background.mp3"
    user_music_exists = os.path.exists(custom_music_file)
    
    if user_music_exists:
        print(f"User-uploaded background music found: {custom_music_file}")
    elif add_music:
        print("No user-uploaded background music found. Will use default if available.")

    if 'summary' in data:
        # Initialize frame_durations if it's not provided or auto_duration is True
        if frame_durations is None or len(frame_durations) == 0:
            frame_durations = [3.0] * len(data['summary'])  # Default duration
            
        # Ensure frame_durations has correct length
        while len(frame_durations) < len(data['summary']):
            frame_durations.append(3.0)
            
        # If auto_duration is enabled, we'll measure speech duration for each frame
        if auto_duration and add_voiceover:
            print("Auto duration mode enabled - measuring speech durations")
            total_duration = 0
            
            for i, point in enumerate(data['summary']):
                audio_path = f"cache/aud/point_{i+1}.mp3"
                
                # Generate text-to-speech audio for this frame
                text_to_speech(point, audio_path, language)
                
                # Measure the duration of the generated audio
                if os.path.exists(audio_path):
                    try:
                        audio = AudioFileClip(audio_path)
                        duration = audio.duration
                        audio.close()
                        # Update the frame duration with the actual audio duration
                        frame_durations[i] = duration
                        total_duration += duration
                        print(f"Frame {i+1} auto duration: {duration:.1f}s")
                    except Exception as e:
                        print(f"Error measuring audio duration for frame {i+1}: {e}")
                        # Keep the default duration if there's an error
                        total_duration += frame_durations[i]
            
            # Add outro duration to total
            outro_duration = 3.0  # Standard outro duration
            total_duration += outro_duration
            
            print(f"Total estimated video duration: {total_duration:.1f}s")
            
            # If user uploaded music, prepare it based on total duration
            if user_music_exists and add_music:
                prepare_background_music(custom_music_file, total_duration)
                
        # Otherwise, use the provided frame_durations or generate TTS if needed
        else:
            # Only generate text-to-speech if needed for voiceover
            if add_voiceover:
                print("Generating voiceover audio files...")
                # First clear any existing audio files to avoid conflicts
                for file in os.listdir("cache/aud/"):
                    if file.endswith(".mp3"):
                        os.remove(os.path.join("cache/aud/", file))
                        
                for i, point in enumerate(data['summary']):
                    # IMPORTANT: The naming format must be "point_{i+1}.mp3"
                    audio_path = f"cache/aud/point_{i+1}.mp3"
                    print(f"Generating audio for text: {point[:30]}...")
                    
                    # Always regenerate audio to ensure consistency
                    text_to_speech(point, audio_path, language)
                    
                    # Verify the file was created
                    if os.path.exists(audio_path):
                        print(f"✓ Audio file created: {audio_path}")
                    else:
                        print(f"✗ Failed to create audio file: {audio_path}")
            
            # Calculate total duration from provided frame durations
            if add_music:
                total_duration = sum(frame_durations) + 3.0  # Add outro duration
                print(f"Total estimated video duration: {total_duration:.1f}s")
                
                # If user uploaded music, prepare it based on total duration
                if user_music_exists:
                    prepare_background_music(custom_music_file, total_duration)
        
        # Generate images and add text only if not skipping image generation
        if not skip_image_generation:
            print("Generating images for bullet points...")
            i = 1
            for point in data['summary']:
                print(f"• {point}")
                generate_image(point, f"cache/img/point_{i}.jpg")
                add_text_to_image(point, f"cache/img/point_{i}.jpg", f"cache/clg/point_{i}.jpg")
                i += 1
        else:
            print("Skipping image generation, using existing images...")
            # Verify existing images are in place
            for i, point in enumerate(data['summary'], 1):
                if not os.path.exists(f"cache/clg/point_{i}.jpg"):
                    print(f"Warning: Expected image cache/clg/point_{i}.jpg not found!")
        
        # Create final video
        print(f"Creating video with add_voiceover={add_voiceover}, add_music={add_music}")
        
        # Verify audio files before video creation
        if add_voiceover:
            audio_files = sorted(glob.glob(os.path.join("cache/aud", "*.mp3")))
            print(f"Found {len(audio_files)} audio files: {audio_files}")
            
        image_audio_to_video("cache/clg", "cache/aud", f"cache/vid/final.mp4", add_voiceover, add_music, frame_durations)

def prepare_background_music(music_file, total_duration):
    """
    Prepare background music by trimming or looping to match the estimated video duration.
    This creates a processed version that will be ready to use when generating the final video.
    
    Args:
        music_file: Path to the background music file
        total_duration: Total estimated duration of the video in seconds
    """
    try:
        if not os.path.exists(music_file):
            print(f"Music file not found: {music_file}")
            return
            
        print(f"Preparing background music to match video duration of {total_duration:.1f}s")
        
        # Load the background music
        background_music = AudioFileClip(music_file)
        original_duration = background_music.duration
        print(f"Original music duration: {original_duration:.1f}s")
        
        # Process the music based on video duration
        if original_duration < total_duration:
            # Need to loop the music
            print(f"Music needs looping ({original_duration:.1f}s → {total_duration:.1f}s)")
            processed_music = background_music.loop(duration=total_duration)
        else:
            # Need to trim the music
            print(f"Music needs trimming ({original_duration:.1f}s → {total_duration:.1f}s)")
            processed_music = background_music.subclip(0, total_duration)
        
        # Adjust volume
        processed_music = processed_music.volumex(0.3)
        
        # Save the processed music
        processed_music_path = "cache/music/processed_background.mp3"
        processed_music.write_audiofile(processed_music_path, fps=44100)
        
        # Clean up
        background_music.close()
        processed_music.close()
        
        print(f"Processed background music saved to {processed_music_path}")
        return processed_music_path
        
    except Exception as e:
        print(f"Error preparing background music: {e}")
        return None


# CLI test function
def test_cli():
    print("Article2Video CLI Test")
    url = "https://lematin.ma/economie/pluies-au-maroc-les-avocats-epargnes-hausse-des-prix-en-vue/268054"
    slidenumber = 2
    wordnumber = 10
    language = "francais"
    add_voiceover = False
    add_music = True

    print(f"Processing URL: {url}")
    print(f"Settings: {slidenumber} slides, {wordnumber} words per slide, language: {language}")
    
    # Create necessary directories
    os.makedirs("cache/aud/", exist_ok=True)
    os.makedirs("cache/img/", exist_ok=True)
    os.makedirs("cache/clg/", exist_ok=True)
    os.makedirs("cache/vid/", exist_ok=True)
    
    article_text = scrape_text_from_url(url)
    print(f"Article scraped, length: {len(article_text)} chars")
    
    llm_response = call_llm_api(article_text, slidenumber, wordnumber, language)
    Json = save_and_clean_json(llm_response, "summary.json")
    
    print("\nSummary points:")
    print_summary_points(Json)
    
    print("\nGenerating video...")
    do_work(Json, language, add_voiceover, add_music)
    
    print("\nVideo generation complete!")
    print(f"Output video: cache/vid/final.mp4")


def generate_image_for_text(text, force_regenerate=False):
    """
    Generate an image for the given text and return the path to the created image
    
    Parameters:
    text (str): The text to generate an image for
    force_regenerate (bool): If True, regenerate the image even if it exists
    """
    # Create a unique filename based on the hash of the text
    text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
    output_file = f"cache/img/{text_hash}.jpg"
    
    # Check if the image already exists to avoid regenerating
    if not force_regenerate and os.path.exists(output_file):
        return output_file
    
    # If force_regenerate is True or the file doesn't exist, generate a new image
    generate_image(text, output_file)
    return output_file


# Calculate dynamic shadow parameters based on font size and text prominence
def calculate_shadow(font_size, text_prominence=1.0):
    """Calculate shadow offset and opacity based on font size and text prominence"""
    # Base shadow size scales with font size but not linearly
    base_offset = font_size * 0.04  # Base scaling factor
    
    # Scale offset by prominence factor (bigger for headlines, smaller for body text)
    shadow_offset = max(1, int(base_offset * text_prominence))
    
    # Shadow opacity is inversely related to offset - smaller shadows are more opaque
    # but should never be too light or too dark
    base_opacity = 140  # Base opacity level (out of 255)
    opacity_scale = min(1.0, max(0.6, 1.1 - (shadow_offset / 10)))  # Inverse scaling
    shadow_opacity = int(base_opacity * opacity_scale)
    
    return shadow_offset, shadow_opacity


if __name__ == "__main__":
    test_cli()
