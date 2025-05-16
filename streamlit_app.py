import streamlit as st
import os
import shutil
import time
import random
import uuid
import hashlib

# Load secrets and set environment variables FIRST
try:
    # Validate secrets existence
    required_secrets = ["OPENAI_API_KEY", "GEMINI_API_KEY"]
    missing_secrets = [key for key in required_secrets if key not in st.secrets]
    
    if missing_secrets:
        st.error(f"Missing secrets: {', '.join(missing_secrets)}. Please add them to your .streamlit/secrets.toml file.")
        st.stop()
        
    # Get secrets
    openai_key = st.secrets["OPENAI_API_KEY"]
    gemini_key = st.secrets["GEMINI_API_KEY"]
    
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["GEMINI_API_KEY"] = gemini_key
    
except Exception as e:
    st.error(f"Error loading secrets: {e}. Ensure .streamlit/secrets.toml exists and is correctly formatted.")
    st.stop()

# Now import main functions (which will use the environment variables)
from web_scraper import scrape_text_from_url
from text_processor import fix_unicode, clean_encoding_issues
from json_utils import save_and_clean_json
from app_controller import do_work
from video_creator import clear_cache
from image_generator import generate_image_for_text, generate_images_for_bullet_points
from text_overlay import add_text_to_image
from audio_processor import text_to_speech
from openai_client import summarize_with_openai
from PIL import Image
from io import BytesIO
import music_api  # Import the music API module

# Read an image from disk and return a PIL Image object
def read_image(file_path):
    if os.path.exists(file_path):
        try:
            return Image.open(file_path)
        except Exception as e:
            print(f"Error loading image {file_path}: {e}")
            return None
    return None

def check_session_state_integrity():
    """
    Checks and fixes session state to ensure arrays are properly aligned
    Returns True if any repairs were made
    """
    repairs_made = False
    
    # Check if arrays exist
    required_arrays = ['bullet_points', 'frame_images', 'frame_image_bytes', 'frame_durations', 'frame_audio']
    for array_name in required_arrays:
        if array_name not in st.session_state:
            print(f"Creating missing session state array: {array_name}")
            st.session_state[array_name] = []
            repairs_made = True
    
    # Determine the expected length based on bullet_points
    if len(st.session_state.bullet_points) > 0:
        expected_length = len(st.session_state.bullet_points)
        
        # Check if frame_images matches the length of bullet_points
        if len(st.session_state.frame_images) != expected_length:
            print(f"Session state mismatch: frame_images length ({len(st.session_state.frame_images)}) != bullet_points length ({expected_length})")
            # If we have more frame_images than bullet_points, trim the excess
            if len(st.session_state.frame_images) > expected_length:
                st.session_state.frame_images = st.session_state.frame_images[:expected_length]
                print(f"Trimmed frame_images to {expected_length} items")
            # If we have fewer frame_images than bullet_points, add placeholder values
            else:
                st.session_state.frame_images.extend([None] * (expected_length - len(st.session_state.frame_images)))
                print(f"Extended frame_images to {expected_length} items")
            repairs_made = True
        
        # Check if frame_image_bytes matches the length of bullet_points
        if len(st.session_state.frame_image_bytes) != expected_length:
            print(f"Session state mismatch: frame_image_bytes length ({len(st.session_state.frame_image_bytes)}) != bullet_points length ({expected_length})")
            # If we have more frame_image_bytes than bullet_points, trim the excess
            if len(st.session_state.frame_image_bytes) > expected_length:
                st.session_state.frame_image_bytes = st.session_state.frame_image_bytes[:expected_length]
                print(f"Trimmed frame_image_bytes to {expected_length} items")
            # If we have fewer frame_image_bytes than bullet_points, add None values
            else:
                st.session_state.frame_image_bytes.extend([None] * (expected_length - len(st.session_state.frame_image_bytes)))
                print(f"Extended frame_image_bytes to {expected_length} items")
            repairs_made = True
        
        # Check if frame_durations matches the length of bullet_points
        if len(st.session_state.frame_durations) != expected_length:
            print(f"Session state mismatch: frame_durations length ({len(st.session_state.frame_durations)}) != bullet_points length ({expected_length})")
            # If we have more frame_durations than bullet_points, trim the excess
            if len(st.session_state.frame_durations) > expected_length:
                st.session_state.frame_durations = st.session_state.frame_durations[:expected_length]
                print(f"Trimmed frame_durations to {expected_length} items")
            # If we have fewer frame_durations than bullet_points, add default values
            else:
                st.session_state.frame_durations.extend([5.0] * (expected_length - len(st.session_state.frame_durations)))
                print(f"Extended frame_durations to {expected_length} items")
            repairs_made = True
    
    # Check for missing image bytes
    if len(st.session_state.frame_images) > 0 and len(st.session_state.frame_image_bytes) == len(st.session_state.frame_images):
        for i, (image_path, image_bytes) in enumerate(zip(st.session_state.frame_images, st.session_state.frame_image_bytes)):
            if image_path and not image_bytes and os.path.exists(image_path):
                try:
                    print(f"Loading missing image bytes for frame {i} from {image_path}")
                    with open(image_path, "rb") as f:
                        st.session_state.frame_image_bytes[i] = f.read()
                    repairs_made = True
                except Exception as e:
                    print(f"Error loading image bytes for frame {i}: {e}")
    
    return repairs_made

def main():
    # Set page config for better appearance
    st.set_page_config(
        page_title="Générateur de Vidéos - Le Matin",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Ensure Leelawadee Bold font is available
    check_leelawadee_font()
    
    # Apply custom CSS
    st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem;}
    h1, h2, h3 {margin-bottom: 0.5rem !important;}
    .stButton button {padding: 0.3rem 1rem; border-radius: 0.5rem;}
    .stProgress .st-bo {height: 1rem; border-radius: 1rem;}
    .stTextArea textarea {min-height: 100px;}
    .step-container {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f0f8ff;
        margin-bottom: 1.5rem;
    }
    .highlight {
        background-color: #e6f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {padding-top: 1rem;}
    .progress-bar {padding: 0.5rem 0;}

    /* Control media display sizes */
    /* Remove specific video sizing - let column layout control it */
    /* .main .block-container video { */
    /*    max-width: 25%; */
    /*    max-height: 350px; */
    /*    margin: auto; */
    /*    display: block; */
    /* } */

    /* Ensure this doesn't affect image size too much */
    .stImage img {
        max-height: 600px !important;
        width: auto !important;
        margin: 0 auto;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state variables if they don't exist
    if 'initialized' not in st.session_state:
        # First time loading app - clear cache and initialize
        reset_project()
        st.session_state.initialized = True
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
        
    if 'bullet_points' not in st.session_state:
        st.session_state.bullet_points = []
    if 'article_text' not in st.session_state:
        st.session_state.article_text = ""
    if 'frame_images' not in st.session_state:
        st.session_state.frame_images = []
    if 'frame_image_bytes' not in st.session_state:
        st.session_state.frame_image_bytes = []
    if 'frame_audio' not in st.session_state:
        st.session_state.frame_audio = []
    if 'frame_durations' not in st.session_state:
        st.session_state.frame_durations = []
    if 'current_frame' not in st.session_state:
        st.session_state.current_frame = 0
    if 'generated_summary' not in st.session_state:
        st.session_state.generated_summary = {}
    if 'auto_duration' not in st.session_state:
        st.session_state.auto_duration = False
    if 'editing_mode' not in st.session_state:
        st.session_state.editing_mode = False
    if 'needs_refresh' not in st.session_state:
        st.session_state.needs_refresh = False
    if 'outro_image_data' not in st.session_state:
        st.session_state.outro_image_data = None
    if 'outro_timestamp' not in st.session_state:
        st.session_state.outro_timestamp = 0
    if 'frame_image_data' not in st.session_state:
        st.session_state.frame_image_data = None
    if 'frame_timestamp' not in st.session_state:
        st.session_state.frame_timestamp = 0
    if 'logo_image_data' not in st.session_state:
        st.session_state.logo_image_data = None
    if 'logo_timestamp' not in st.session_state:
        st.session_state.logo_timestamp = 0
    if 'refresh_counter' not in st.session_state:
        st.session_state.refresh_counter = 0
    
    # Load existing images from cache if available and frames are empty
    if len(st.session_state.frame_images) == 0:
        try:
            # Look for images in the cache/clg/ directory
            image_files = sorted([f for f in os.listdir("cache/clg/") if f.endswith(".jpg")])
            
            if image_files:
                print(f"Found {len(image_files)} existing images in cache/clg/")
                
                # Load the images into session state
                for img_file in image_files:
                    file_path = os.path.join("cache/clg/", img_file)
                    st.session_state.frame_images.append(file_path)
                    
                    # Also load the image bytes
                    with open(file_path, "rb") as f:
                        st.session_state.frame_image_bytes.append(f.read())
                    
                    # Set default durations
                    st.session_state.frame_durations.append(5.0)
                
                # If we loaded images, but don't have bullet points, try to extract them
                if len(st.session_state.bullet_points) == 0:
                    # Create default bullet points based on image count
                    for i in range(len(image_files)):
                        st.session_state.bullet_points.append(f"Point {i+1}")
                
                print(f"Successfully loaded {len(st.session_state.frame_images)} images into session state")
        except Exception as e:
            print(f"Error loading cached images: {e}")
    
    # Check session state integrity and repair if needed
    if check_session_state_integrity():
        print("Session state was repaired, forcing refresh")
        st.session_state.needs_refresh = True
    
    # Force refresh if needed
    if st.session_state.needs_refresh:
        st.session_state.needs_refresh = False
        st.rerun()
    
    # Settings in sidebar
    with st.sidebar:
        # Always use the fixed project logo (not the custom one)
        st.image("project logo.png", width=200)
        st.title("Paramètres")
        
        language = st.selectbox(
            "Langue",
            ["Anglais", "Francais", "Espagnol", "Arabe", "Allemand", "Russe", "Italien", "Portugais"],
            index=1,
            key="language_select"
        )
        st.session_state.language = language
        
        # Clean cache/restart button
        if st.button("🔄 Nouveau projet", use_container_width=True):
            reset_project()
            st.rerun()
            
        slidenumber = st.slider(
            "Nombre de points",
            min_value=2,
            max_value=12,
            value=10,
            key="slidenumber_slider"
        )
        st.session_state.slidenumber = slidenumber

        wordnumber = st.slider(
            "Mots par point",
            min_value=10,
            max_value=30,
            value=15,
            key="wordnumber_slider"
        )
        st.session_state.wordnumber = wordnumber

        st.session_state.add_music = st.checkbox(
            "Ajouter musique de fond",
            value=True,
            help="Ajouter une musique de fond à la vidéo générée"
        )
        
        st.session_state.add_voiceover = st.checkbox(
            "Ajouter voix",
            value=False,
            help="Ajouter une voix off à la vidéo générée"
        )
        
        st.session_state.auto_duration = st.checkbox(
            "Durée automatique",
            value=True,
            help="Synchroniser la durée des slides avec le temps de lecture"
        )
        
        # Display progress
        step_titles = {
            1: "1. Entrée article",
            2: "2. Édition points", 
            3: "3. Visualisation slides",
            4: "4. Musique & Audio",
            5: "5. Génération vidéo"
        }
        
        st.write("### Progression")
        current_step = st.session_state.current_step
        progress_value = current_step / len(step_titles)
        st.progress(progress_value)
        
        for step, title in step_titles.items():
            if step == current_step:
                st.markdown(f"**➡️ {title}**")
            elif step < current_step:
                st.markdown(f"✅ {title}")
            else:
                st.markdown(f"⬜ {title}")
    
    # Main content area - display the appropriate step
    display_step(current_step)

def display_step(step):
    """Display the appropriate step content based on the current step"""
    
    # Main title
    st.title("Génerateur des Vidéos Pour Le Matin 🎬")
    
    if step == 1:
        display_input_interface()
    elif step == 2:
        display_editing_interface()
    elif step == 3:
        display_frame_interface()
    elif step == 4:
        display_audio_interface()
    elif step == 5:
        display_video_generation()

def display_input_interface():
    """Step 1: Article Input"""
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    st.subheader("Étape 1: Entrez votre article")
    st.write("Fournissez un article pour générer une vidéo")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        input_method = st.radio("Méthode d'entrée:", ["URL", "Texte direct"])
        
    with col2:
        if input_method == "URL":
            url = st.text_input("URL de l'article:")
            if st.button("Analyser l'article", use_container_width=True):
                if not url or url.strip() == "":
                    st.error("Veuillez entrer une URL valide")
                else:
                    with st.spinner("Récupération de l'article..."):
                        try:
                            article_text = scrape_text_from_url(url)
                            st.session_state.article_text = article_text
                            process_article_text()
                        except Exception as e:
                            st.error(f"Erreur lors de la récupération: {str(e)}")
        else:
            article_text = st.text_area("Texte de l'article:", height=200)
            if st.button("Générer résumé", use_container_width=True):
                if not article_text or article_text.strip() == "":
                    st.error("Veuillez entrer du texte")
                else:
                    st.session_state.article_text = article_text
                    process_article_text()
    
    st.markdown('</div>', unsafe_allow_html=True)

def process_article_text():
    """Process the article text and generate a summary using OpenAI"""
    with st.spinner("Génération du résumé avec OpenAI..."):
        try:
            # Clean the text to fix encoding issues
            cleaned_text = clean_encoding_issues(st.session_state.article_text)
            
            # Use OpenAI for summarization
            Json = summarize_with_openai(
                cleaned_text, 
                st.session_state.slidenumber, 
                st.session_state.wordnumber, 
                st.session_state.language
            )
            save_and_clean_json(Json, "summary.json")
            st.session_state.generated_summary = Json
            
            if 'summary' in Json:
                st.session_state.bullet_points = [fix_unicode(point) for point in Json['summary']]
                st.success("Résumé généré avec succès avec OpenAI!")
                
                # Move to the next step
                st.session_state.current_step = 2
                st.rerun()
            else:
                st.error("Le résumé n'a pas été généré correctement. Veuillez réessayer.")
        except Exception as e:
            st.error(f"Erreur lors de la génération: {str(e)}")

def display_editing_interface():
    """Step 2: Edit bullet points"""
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    st.subheader("Étape 2: Édition des points")
    
    # Information about keyword highlighting
    st.info("💡 Les mots ou phrases clés entre guillemets (\"comme ceci\") seront mis en évidence en vert dans la vidéo finale.")
    
    # Get the edited points
    edited_points = []
    for i, point in enumerate(st.session_state.bullet_points):
        edited_point = st.text_area(
            f"Point {i+1}",
            value=point,
            key=f"point_{i}",
            height=100
        )
        edited_points.append(edited_point)
    
    # Create columns for the continue button
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col3:
        if st.button("Continuer ➡️", use_container_width=True):
            # Update the bullet points
            st.session_state.bullet_points = edited_points
            
            # Update the summary in generated_summary
            if 'summary' in st.session_state.generated_summary:
                st.session_state.generated_summary['summary'] = edited_points
            
            # Clear previous frame data
            st.session_state.frame_images = []
            st.session_state.frame_image_bytes = []
            st.session_state.frame_durations = []
            st.session_state.frame_audio = []
            
            # Process bullet points to generate images and frames
            process_bullet_points()
            
            # Move to the next step
            st.session_state.current_step = 3
            st.rerun()
    
    with col1:
        if st.button("⬅️ Retour", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_frame_interface():
    """Step 3: Frame/Slide Interface"""
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    # Get current frame index and total frames
    current_frame = st.session_state.current_frame
    total_frames = len(st.session_state.bullet_points)
    
    st.subheader(f"Étape 3: Visualisation des slides ({current_frame + 1}/{total_frames})")
    
    # Information about font
    st.info("💡 La police Leelawadee Bold est utilisée pour le texte, avec les mots clés entre guillemets mis en évidence en vert (#79C910). Le texte sera ajouté aux images lors de la génération de la vidéo finale.")
    
    # Display debug information in a collapsible section
    with st.expander("Informations de débogage (cliquez pour voir)", expanded=False):
        st.write(f"Nombre de points: {len(st.session_state.bullet_points)}")
        st.write(f"Nombre d'images: {len(st.session_state.frame_images)}")
        st.write(f"Nombre d'images en mémoire: {len(st.session_state.frame_image_bytes)}")
        st.write(f"Nombre de durées: {len(st.session_state.frame_durations)}")
        
        if len(st.session_state.frame_images) > 0:
            st.write("Chemins des images:")
            for i, path in enumerate(st.session_state.frame_images):
                st.write(f"Image {i+1}: {path} (existe: {os.path.exists(path)})")
        
        if current_frame < len(st.session_state.frame_images):
            current_image_path = st.session_state.frame_images[current_frame]
            st.write(f"Image actuelle: {current_image_path}")
            st.write(f"L'image existe: {os.path.exists(current_image_path)}")
            
            if current_frame < len(st.session_state.frame_image_bytes):
                st.write(f"Données d'image en mémoire: {'Présentes' if st.session_state.frame_image_bytes[current_frame] else 'Absentes'}")
    
    # Display current frame
    # Ensure we have paths AND bytes data
    if (current_frame < total_frames and
        current_frame < len(st.session_state.frame_images) and
        current_frame < len(st.session_state.frame_image_bytes) and
        st.session_state.frame_image_bytes[current_frame] is not None):

        col1, col2 = st.columns([2, 3])

        with col1:
            # --- Load image from bytes stored in session state --- 
            try:
                image_data = st.session_state.frame_image_bytes[current_frame]
                img = Image.open(BytesIO(image_data))
                st.image(img, caption=f"Slide {current_frame + 1} (prévisualisation sans texte)", use_container_width=True, width=300)
            except Exception as e:
                st.error(f"Erreur affichage image depuis cache mémoire: {e}")
                # Fallback: try loading from path if bytes failed
                image_path = st.session_state.frame_images[current_frame]
                if os.path.exists(image_path):
                    img_fallback = read_image(image_path)
                    if img_fallback:
                        st.image(img_fallback, caption=f"Slide {current_frame + 1} (depuis fichier)", use_container_width=True, width=300)
                    else:
                        st.warning(f"Image non disponible (fichier corrompu?) {image_path}")
                else:
                     st.warning(f"Image non disponible (fichier non trouvé?) {image_path}")
            # --- End image loading --- 

            # Create a preview of text overlay for reference, but don't save it
            with st.expander("Aperçu avec texte (cliquez pour voir)", expanded=False):
                try:
                    # Simply call our implementation from text_overlay.py to get consistent results
                    from text_overlay import add_text_to_image
                    from PIL import Image
                    import io
                    from io import BytesIO
                    
                    # Get image and text from state
                    text = st.session_state.bullet_points[current_frame]
                    image_data = st.session_state.frame_image_bytes[current_frame]
                    
                    # Create temporary files for the preview
                    temp_input = f"cache/temp_preview_input_{current_frame}.jpg"
                    temp_output = f"cache/temp_preview_output_{current_frame}.jpg"
                    
                    # Save the input image
                    with open(temp_input, "wb") as f:
                        f.write(image_data)
                    
                    # Generate the preview using the same function that will be used in video generation
                    # This will automatically include logo and frame if they exist
                    add_text_to_image(text, temp_input, temp_output)
                    
                    # Display the preview
                    preview_img = Image.open(temp_output)
                    st.image(preview_img, caption="Aperçu avec texte et logo (si présent)", use_container_width=True)
                    
                    # Add info about custom features
                    logo_path = "cache/custom/logo.png"
                    frame_path = "cache/custom/frame.png"
                    
                    features = []
                    if os.path.exists(logo_path):
                        features.append("✅ Logo")
                    else:
                        features.append("❌ Logo (non configuré)")
                        
                    if os.path.exists(frame_path):
                        features.append("✅ Cadre")
                    else:
                        features.append("❌ Cadre (non configuré)")
                    
                    if features:
                        st.caption("Éléments personnalisés: " + ", ".join(features))
                    
                    # Clean up temp files
                    try:
                        os.remove(temp_input)
                        os.remove(temp_output)
                    except:
                        pass
                    
                except Exception as preview_error:
                    st.warning(f"Impossible de générer l'aperçu avec texte: {preview_error}")

            # Add option to upload custom image
            st.markdown("---")
            st.markdown("#### Remplacer l'image")
            uploaded_image = st.file_uploader(
                "Télécharger votre propre image", 
                type=["jpg", "jpeg", "png"], 
                key=f"image_upload_{current_frame}",
                on_change=None  # No automatic callback
            )
            
            # Process uploaded image with a button instead of automatic processing
            if uploaded_image is not None:
                if st.button("Appliquer l'image", use_container_width=True, key=f"apply_image_{current_frame}"):
                    try:
                        # Create directory if it doesn't exist
                        os.makedirs("cache/custom_img/", exist_ok=True)
                        
                        # Save the uploaded image
                        custom_image_path = f"cache/custom_img/frame_{current_frame}.jpg"
                        with open(custom_image_path, "wb") as f:
                            f.write(uploaded_image.getbuffer())
                        
                        # Process the uploaded image - resize to match format
                        img = Image.open(custom_image_path)
                        
                        # Resize to match the standard size (1080x1920)
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
                        
                        # Save the resized image
                        img.save(custom_image_path)
                        
                        # Update the frame image path in session state
                        st.session_state.frame_images[current_frame] = custom_image_path

                        # Read the final image and update bytes in session state
                        try:
                            with open(custom_image_path, "rb") as f:
                                st.session_state.frame_image_bytes[current_frame] = f.read()
                            print(f"Updated image bytes for frame {current_frame} from custom upload.")
                        except Exception as read_error:
                            st.error(f"Failed to read processed custom image for state update: {read_error}")

                        # Success message
                        st.success("✅ Image téléchargée et appliquée avec succès!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Erreur lors du traitement de l'image: {str(e)}")

        with col2:
            # Show editable text and duration
            st.markdown(f"#### Texte du slide {current_frame + 1}")
            edited_text = st.text_area(
                "Texte:",
                value=st.session_state.bullet_points[current_frame],
                height=100,
                key=f"frame_text_{current_frame}"
            )
            
            # Duration control
            if st.session_state.auto_duration:
                # Show estimated duration based on text
                words = len(edited_text.split())
                estimated_duration = max(2.0, words / 2.5)  # ~2.5 words per second
                st.session_state.frame_durations[current_frame] = estimated_duration
                st.info(f"⏱️ Durée estimée: **{estimated_duration:.1f}s** ({words} mots)")
            else:
                # Manual duration control
                frame_duration = st.slider(
                    "⏱️ Durée (secondes):",
                    min_value=1.0,
                    max_value=10.0,
                    value=st.session_state.frame_durations[current_frame],
                    step=0.5,
                    key=f"duration_slider_{current_frame}"
                )
                st.session_state.frame_durations[current_frame] = frame_duration
            
            # Custom image actions
            st.markdown("---")
            
            # Two columns for actions
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                # Regenerate image button
                if st.button("🔄 Régénérer l'image", use_container_width=True, key=f"regenerate_{current_frame}"):
                    with st.spinner("Génération d'une nouvelle image..."):
                        # Save the edited text first
                        st.session_state.bullet_points[current_frame] = edited_text

                        # Generate a specific image for this single bullet point
                        try:
                            # Generate an optimized image prompt for this specific bullet point
                            from utils.openai_utils import generate_image_prompt
                            from image_generator import generate_image_with_prompt
                            
                            # Get the full article text for context
                            article_text = st.session_state.article_text
                            
                            # Generate a specific image prompt
                            image_prompt = generate_image_prompt(edited_text, article_text)
                            
                            # Create a unique filename based on hash
                            text_hash = hashlib.md5(edited_text.encode()).hexdigest()[:10]
                            new_image_path = f"cache/img/{text_hash}_{int(time.time())}.jpg"
                            
                            # Generate the image with the optimized prompt
                            generate_image_with_prompt(image_prompt, new_image_path)
                            
                            # Update session state with raw image path (no text overlay)
                            st.session_state.frame_images[current_frame] = new_image_path
                            
                            # Update the image bytes in session state
                            try:
                                with open(new_image_path, "rb") as f:
                                    st.session_state.frame_image_bytes[current_frame] = f.read()
                                print(f"Updated image bytes for frame {current_frame} from regeneration.")
                            except Exception as read_error:
                                st.error(f"Failed to read regenerated image for state update: {read_error}")
                            
                        except Exception as e:
                            st.error(f"Error regenerating image: {e}")
                            # Fall back to the simpler approach
                            new_image_path = generate_image_for_text(edited_text, force_regenerate=True)
                            st.session_state.frame_images[current_frame] = new_image_path
                            
                            # Update the image bytes in session state
                            try:
                                with open(new_image_path, "rb") as f:
                                    st.session_state.frame_image_bytes[current_frame] = f.read()
                            except Exception as read_error:
                                st.error(f"Failed to read regenerated image bytes: {read_error}")
                        
                        st.rerun()
            
            with action_col2:
                # Reset to original image
                if os.path.exists(f"cache/custom_img/frame_{current_frame}.jpg"):
                    if st.button("⚠️ Retirer image custom", use_container_width=True, key=f"remove_custom_{current_frame}"):
                        # Regenerate the AI image
                        with st.spinner("Restauration de l'image générée..."):
                            # Save the edited text first
                            st.session_state.bullet_points[current_frame] = edited_text

                            # Remove custom image file reference if needed (optional)
                            # os.remove(f"cache/custom_img/frame_{current_frame}.jpg")

                            # Regenerate the image (force_regenerate=True needed)
                            new_image_path = generate_image_for_text(edited_text, force_regenerate=True)
                            st.session_state.frame_images[current_frame] = new_image_path # Update path

                            # --- Read the new image and update bytes in session state ---
                            try:
                                with open(new_image_path, "rb") as f:
                                    st.session_state.frame_image_bytes[current_frame] = f.read()
                                print(f"Updated image bytes for frame {current_frame} after removing custom.")
                            except Exception as read_error:
                                st.error(f"Failed to read restored image for state update: {read_error}")
                            # --- End update bytes ---

                            st.rerun()
        
        # Navigation row - Moved outside the col1/col2 layout for better consistency
        st.write("")
        nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 3, 1, 1])
        
        # Always save the current edits before navigation
        st.session_state.bullet_points[current_frame] = edited_text
        
        with nav_col1:
            if current_frame > 0:
                if st.button("⬅️ Précédent", use_container_width=True, key=f"prev_{current_frame}"):
                    # Go to previous frame
                    st.session_state.current_frame -= 1
                    st.rerun()
        
        with nav_col2:
            if st.button("⬅️ Retour", use_container_width=True, key=f"back_{current_frame}"):
                st.session_state.current_step = 2
                st.rerun()
        
        with nav_col4:
            # Next button or finish button
            if current_frame < total_frames - 1:
                next_button_label = "Suivant ➡️"
            else:
                next_button_label = "Terminer ➡️"
                
            if st.button(next_button_label, use_container_width=True, key=f"next_{current_frame}"):                
                # If not the last frame, go to next
                if current_frame < total_frames - 1:
                    st.session_state.current_frame += 1
                    st.rerun()
                else:
                    # Move to the next step - either audio or video generation
                    if st.session_state.add_voiceover or st.session_state.add_music:
                        # If voiceover or music is enabled, go to audio step
                        st.session_state.current_step = 4
                    else:
                        # Otherwise skip to video generation
                        st.session_state.current_step = 5
                    st.rerun()
        
        with nav_col5:
            if current_frame < total_frames - 1:
                if st.button("➡️ Dernier", use_container_width=True, key=f"last_{current_frame}"):
                    # Go to last frame
                    st.session_state.current_frame = total_frames - 1
                    st.rerun()
    else:
        st.error("Aucun frame disponible. Veuillez revenir à l'étape précédente.")
        
        # Display more detailed error information
        if total_frames == 0:
            st.warning("Aucun point n'a été défini. Veuillez générer des points dans l'étape précédente.")
        elif len(st.session_state.frame_images) == 0:
            st.warning("Aucune image n'a été générée. Veuillez vérifier les logs pour plus de détails.")
        elif current_frame >= len(st.session_state.frame_images):
            st.warning(f"Le frame actuel ({current_frame + 1}) est en dehors de la plage des images disponibles ({len(st.session_state.frame_images)}).")
        elif current_frame >= len(st.session_state.frame_image_bytes):
            st.warning(f"Le frame actuel ({current_frame + 1}) est en dehors de la plage des données d'image en mémoire ({len(st.session_state.frame_image_bytes)}).")
        elif st.session_state.frame_image_bytes[current_frame] is None:
            st.warning("Les données d'image en mémoire sont manquantes pour ce frame.")
            
            # Try to recover the image bytes
            if current_frame < len(st.session_state.frame_images):
                image_path = st.session_state.frame_images[current_frame]
                if os.path.exists(image_path):
                    st.info(f"Tentative de récupération de l'image depuis le disque: {image_path}")
                    try:
                        with open(image_path, "rb") as f:
                            st.session_state.frame_image_bytes[current_frame] = f.read()
                        st.success("✅ Image récupérée avec succès! Cliquez sur le bouton ci-dessous pour actualiser.")
                        if st.button("Actualiser", use_container_width=True):
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la récupération de l'image: {e}")
                else:
                    st.warning(f"Le fichier image n'existe pas: {image_path}")
        
        # Add option to force regenerate all images
        if st.button("🔄 Régénérer toutes les images", use_container_width=True):
            try:
                # Process bullet points to regenerate all images
                process_bullet_points()
                st.success("✅ Images régénérées avec succès!")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la régénération des images: {e}")
        
        if st.button("Retour à l'édition des points", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_audio_interface():
    """Step 4: Audio Interface"""
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    st.subheader("Étape 4: Configuration audio et personnalisation")
    
    # Initialize tabs for different audio settings
    tabs = st.tabs(["Musique de fond", "Voix off", "Personnalisation"])
    
    # Tab 1: Background Music
    with tabs[0]:
        st.markdown("### 🎵 Musique de fond")
        if st.session_state.add_music:
            # Create directory if it doesn't exist
            os.makedirs("cache/music/", exist_ok=True)
            
            # Create a music selection section
            st.markdown("#### Sélection de musique")
            music_tab1, music_tab2 = st.tabs(["Browser", "Télécharger votre musique"])
            
            # Tab 1: Browser
            with music_tab1:
                st.markdown("#### Parcourir la bibliothèque musicale Jamendo")
                
                # Initialize session state for music
                if 'music_provider' not in st.session_state:
                    st.session_state.music_provider = "jamendo"  # Always use Jamendo
                
                if 'music_search_query' not in st.session_state:
                    st.session_state.music_search_query = ""
                
                if 'music_category_filter' not in st.session_state:
                    st.session_state.music_category_filter = "Tous"
                
                if 'music_duration_filter' not in st.session_state:
                    st.session_state.music_duration_filter = "Tous"
                
                # Function to perform search and update results
                def perform_music_search():
                    query = st.session_state.music_search_query
                    category = st.session_state.music_category_filter
                    duration_filter = st.session_state.music_duration_filter
                    
                    # Show a spinner during search
                    with st.spinner("Recherche en cours..."):
                        try:
                            # Use Jamendo for search with category filter directly in the API call
                            results = music_api.search_music(
                                q=query,
                                category=category if category != "Tous" else None,
                                provider="jamendo",
                                page=1,
                                per_page=30
                            )
                            
                            if results and "tracks" in results and len(results["tracks"]) > 0:
                                tracks = results["tracks"]
                                
                                # Apply duration filter if needed (need to do this client-side)
                                if duration_filter != "Tous":
                                    # Get the duration ranges
                                    duration_ranges = music_api.get_duration_ranges()
                                    # Find the matching range
                                    selected_range = next((r for r in duration_ranges if r["label"] == duration_filter), None)
                                    if selected_range:
                                        min_duration = selected_range["min_seconds"]
                                        max_duration = selected_range["max_seconds"]
                                        tracks = [t for t in tracks if min_duration <= t.get("duration", 0) < max_duration]
                                
                                st.session_state.music_results = tracks
                                st.session_state.search_count = len(tracks)
                            else:
                                st.session_state.music_results = []
                                st.session_state.search_count = 0
                                
                        except Exception as e:
                            st.error(f"Erreur lors de la recherche: {str(e)}")
                            st.session_state.music_results = []
                            st.session_state.search_count = 0
                
                # Update search query
                def update_search_query():
                    if 'search_input' in st.session_state:
                        st.session_state.music_search_query = st.session_state.search_input
                    perform_music_search()
                
                # Update category filter
                def update_category_filter():
                    st.session_state.music_category_filter = st.session_state.category_select
                    perform_music_search()
                
                # Update duration filter
                def update_duration_filter():
                    st.session_state.music_duration_filter = st.session_state.duration_select
                    perform_music_search()
                
                # Layout with filters and search bar
                st.markdown("Recherchez de la musique dans la bibliothèque Jamendo (plus de 600,000 titres disponibles)")
                
                # Add filters in two columns
                filter_col1, filter_col2 = st.columns(2)
                
                with filter_col1:
                    # Get categories from the API
                    api_categories = ["Tous"] + music_api.get_category_names()
                    st.selectbox(
                        "Catégorie:", 
                        api_categories,
                        key="category_select",
                        on_change=update_category_filter,
                        index=api_categories.index(st.session_state.music_category_filter) if st.session_state.music_category_filter in api_categories else 0
                    )
                
                with filter_col2:
                    # Get duration ranges from the API
                    duration_ranges = music_api.get_duration_ranges()
                    duration_labels = ["Tous"] + [d["label"] for d in duration_ranges]
                    st.selectbox(
                        "Durée:",
                        duration_labels,
                        key="duration_select",
                        on_change=update_duration_filter,
                        index=duration_labels.index(st.session_state.music_duration_filter) if st.session_state.music_duration_filter in duration_labels else 0
                    )
                
                search_query = st.text_input(
                    "Recherche par titre, artiste ou genre:", 
                    value=st.session_state.music_search_query,
                    key="search_input",
                    on_change=update_search_query,
                    placeholder="rock, piano, ambiance, etc."
                )
                
                # Perform initial search if we don't have results yet
                if 'music_results' not in st.session_state:
                    # Initial search with a popular genre to show some results
                    st.session_state.music_search_query = "ambient"  
                    perform_music_search()
                    # Reset the search query after initial load
                    st.session_state.music_search_query = ""
                
                # Display search status
                if 'search_count' in st.session_state:
                    if st.session_state.search_count > 0:
                        st.success(f"✅ {st.session_state.search_count} musiques trouvées!")
                    else:
                        st.warning("Aucune musique trouvée. Essayez d'autres termes.")
                
                # Display results if available
                if 'music_results' in st.session_state and len(st.session_state.music_results) > 0:
                    st.markdown("### Résultats")
                    
                    # Initialize preview state if needed
                    if 'previews_playing' not in st.session_state:
                        st.session_state.previews_playing = {}
                    
                    # Display results in a better layout
                    for i, track in enumerate(st.session_state.music_results):
                        with st.container():
                            cols = st.columns([3, 1, 1])
                            with cols[0]:
                                title = track['title']
                                artist = track['artist']
                                genre = track.get('category', 'Musique')
                                duration = track.get('duration_str', '3:00')
                                
                                st.markdown(f"**{title}**  \n{artist} · {duration} · {genre}")
                            
                            with cols[1]:
                                preview_btn_key = f"preview_{i}"
                                preview_url = track.get("url", "")
                                
                                # When button is clicked, toggle play state for this track
                                if preview_url and st.button("🔊 Écouter", key=preview_btn_key):
                                    # Toggle preview state for this track
                                    track_id = track.get('id', f"track_{i}")
                                    if track_id in st.session_state.previews_playing:
                                        # If already playing, stop it
                                        del st.session_state.previews_playing[track_id]
                                    else:
                                        # Start playing this track
                                        st.session_state.previews_playing[track_id] = preview_url
                                    st.rerun()
                            
                            with cols[2]:
                                if st.button("✅ Sélectionner", key=f"select_{i}"):
                                    try:
                                        with st.spinner(f"Téléchargement de '{track['title']}'..."):
                                            # Create music directory if it doesn't exist
                                            music_dir = "cache/music"
                                            if not os.path.exists(music_dir):
                                                os.makedirs(music_dir)
                                            
                                            # Download using our music_api
                                            success = music_api.download_music(
                                                track['id'], 
                                                os.path.join(music_dir, "background.mp3")
                                            )
                                            
                                            if success:
                                                st.session_state.selected_music_title = track['title']
                                                st.success(f"✅ '{track['title']}' téléchargée et sélectionnée!")
                                                st.rerun()
                                            else:
                                                st.error("Échec du téléchargement de la musique")
                                    except Exception as e:
                                            st.error(f"Erreur lors du téléchargement: {str(e)}")
                                
                                # Display audio player right under this track if it's being played
                                track_id = track.get('id', f"track_{i}")
                                if track_id in st.session_state.previews_playing:
                                    audio_url = st.session_state.previews_playing[track_id]
                                    st.audio(audio_url, format="audio/mp3")
                                    # Add a button to stop playing
                                    if st.button("⏹️ Arrêter", key=f"stop_{i}"):
                                        del st.session_state.previews_playing[track_id]
                                        st.rerun()
                                
                                st.markdown("---")
                    
                    # Display currently playing preview if any
                    # if st.session_state.preview_playing is not None and 'preview_url' in st.session_state:
                    #     track = st.session_state.music_results[st.session_state.preview_playing]
                    #     st.markdown(f"**En cours de lecture:** {track['title']}")
                    #     # Play the audio preview
                    #     st.audio(st.session_state.preview_url)
                
            # Tab 2: Upload your own music
            with music_tab2:
                st.markdown("#### Télécharger votre propre musique")
                st.markdown("Vous pouvez télécharger votre propre fichier audio MP3 pour l'utiliser comme musique de fond.")
                
                uploaded_file = st.file_uploader("Choisir un fichier MP3", type=["mp3"])
                
                if uploaded_file is not None:
                    # Save the uploaded file
                    with st.spinner("Traitement du fichier audio..."):
                        # Create music directory if it doesn't exist
                        music_dir = "cache/music"
                        if not os.path.exists(music_dir):
                            os.makedirs(music_dir)
                        
                        # Save the file
                        music_path = os.path.join(music_dir, "background.mp3")
                        with open(music_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        st.success(f"✅ Musique '{uploaded_file.name}' téléchargée avec succès!")
                        st.session_state.selected_music_title = uploaded_file.name
                        
                        # Show audio preview
                        st.audio(uploaded_file)
                
                # Display currently selected music if any
                if os.path.exists("cache/music/background.mp3") and 'selected_music_title' in st.session_state:
                    st.markdown("---")
                    st.markdown(f"**Musique actuelle:** {st.session_state.selected_music_title}")
                    
                    # Option to remove current music
                    if st.button("Supprimer la musique actuelle"):
                        if os.path.exists("cache/music/background.mp3"):
                            os.remove("cache/music/background.mp3")
                            if 'selected_music_title' in st.session_state:
                                del st.session_state.selected_music_title
                            st.success("✅ Musique supprimée avec succès!")
                            st.rerun()
        else:
            st.info("Option musique de fond désactivée. Pour l'activer, cochez l'option dans les paramètres.")
    
    # Tab 2: Voiceover
    with tabs[1]:
        st.markdown("### 🎙️ Voix off")
        if st.session_state.add_voiceover:
            if st.session_state.auto_duration:
                st.info("Mode durée automatique activé: La durée des slides sera adaptée au temps de lecture des textes.")
                
                if st.button("Générer automatiquement toutes les voix", use_container_width=True):
                    # Generate all audio at once
                    with st.spinner("Génération de toutes les voix..."):
                        os.makedirs("cache/aud/", exist_ok=True)
                        for i, point in enumerate(st.session_state.bullet_points):
                            audio_path = f"cache/aud/point_{i+1}.mp3"
                            text_to_speech(point, audio_path, st.session_state.language)
                        st.success("✅ Toutes les voix ont été générées")
            else:
                st.warning("Mode durée automatique désactivé. Les voix seront générées lors de la création de la vidéo.")
        else:
            st.info("Option voix off désactivée. Pour l'activer, cochez l'option dans les paramètres.")
    
    # Tab 3: Customization
    with tabs[2]:
        st.markdown("### 🎨 Personnalisation")
        
        # Create a directory for custom assets if it doesn't exist
        os.makedirs("cache/custom/", exist_ok=True)
        
        # Logo customization
        st.markdown("#### Logo dans la vidéo (Optionnel)")
        st.write("Vous pouvez ajouter un logo qui apparaîtra sur chaque slide de la vidéo générée. Cette étape est entièrement optionnelle.")
        
        # Check if we already have a custom logo
        custom_logo_path = "cache/custom/logo.png"
        
        if os.path.exists(custom_logo_path):
            col1, col2 = st.columns([1, 2])
            with col1:
                # Read the image from disk directly
                img = read_image(custom_logo_path)
                if img:
                    st.image(img, caption="Logo actuel", width=200)
                else:
                    st.warning("Impossible de charger le logo")
            with col2:
                st.success("✅ Logo personnalisé configuré")
                # Add a remove button
                if st.button("❌ Supprimer le logo", key="remove_logo_btn"):
                    if os.path.exists(custom_logo_path):
                        os.remove(custom_logo_path)
                    if os.path.exists("video_logo.png"):
                        os.remove("video_logo.png")
                    st.success("✅ Logo supprimé avec succès!")
                    st.session_state.refresh_counter += 1
                    st.rerun()
        else:
            st.info("Aucun logo ajouté. Les vidéos seront générées sans logo.")
        
        # Upload new logo
        uploaded_logo = st.file_uploader(
            "Télécharger un logo (optionnel)",
            type=["png", "jpg", "jpeg"],
            key=f"custom_logo_upload_{st.session_state.refresh_counter}"
        )
        
        if uploaded_logo is not None:
            try:
                # Ensure custom directory exists
                os.makedirs("cache/custom", exist_ok=True)
                
                # Save directly to both locations
                with open(custom_logo_path, "wb") as f:
                    f.write(uploaded_logo.getvalue())
                
                # Also save to root for immediate use
                with open("video_logo.png", "wb") as f:
                    f.write(uploaded_logo.getvalue())
                
                # Increment refresh counter to force reload
                st.session_state.refresh_counter += 1
                st.success("✅ Logo téléchargé avec succès!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erreur lors du traitement du logo: {str(e)}")
        
        # Outro customization
        st.markdown("---")
        st.markdown("#### Image de fin (Optionnel)")
        st.write("Vous pouvez ajouter une image qui sera affichée à la fin de la vidéo générée. Cette étape est entièrement optionnelle.")
        
        # Check if we already have a custom outro
        custom_outro_path = "cache/custom/outro.png" 
        
        if os.path.exists(custom_outro_path):
            col1, col2 = st.columns([1, 2])
            with col1:
                # Read the image from disk directly
                img = read_image(custom_outro_path)
                if img:
                    st.image(img, caption="Image de fin actuelle", width=200)
                else:
                    st.warning("Impossible de charger l'image de fin")
            with col2:
                st.success("✅ Image de fin personnalisée configurée")
                # Add a remove button
                if st.button("❌ Supprimer l'image de fin", key="remove_outro_btn"):
                    if os.path.exists(custom_outro_path):
                        os.remove(custom_outro_path)
                    if os.path.exists("outro.png"):
                        os.remove("outro.png")
                    st.success("✅ Image de fin supprimée avec succès!")
                    st.session_state.refresh_counter += 1
                    st.rerun()
        else:
            st.info("Aucune image de fin ajoutée. Les vidéos se termineront sans image personnalisée.")
        
        # Upload new outro
        uploaded_outro = st.file_uploader(
            "Télécharger une image de fin (optionnel)",
            type=["png", "jpg", "jpeg"],
            key=f"custom_outro_upload_{st.session_state.refresh_counter}"
        )
        
        if uploaded_outro is not None:
            try:
                # Ensure custom directory exists
                os.makedirs("cache/custom", exist_ok=True)
                
                # Process the image (resize to video dimensions)
                image = Image.open(BytesIO(uploaded_outro.getvalue()))
                
                # Resize to match video dimensions while maintaining aspect ratio
                target_width = 1080
                target_height = 1920
                
                # Calculate dimensions to maintain aspect ratio
                original_aspect = image.width / image.height
                target_aspect = target_width / target_height
                
                if original_aspect > target_aspect:
                    # Original image is wider than target
                    new_width = int(target_height * original_aspect)
                    new_height = target_height
                    image = image.resize((new_width, new_height))
                    left = (new_width - target_width) // 2
                    image = image.crop((left, 0, left + target_width, target_height))
                else:
                    # Original image is taller than target
                    new_height = int(target_width / original_aspect)
                    new_width = target_width
                    image = image.resize((new_width, new_height))
                    top = (new_height - target_height) // 2
                    image = image.crop((0, top, target_width, top + target_height))
                
                # Convert to RGB to ensure proper saving
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Save processed image to both locations
                image.save(custom_outro_path)
                image.save("outro.png")
                
                # Increment refresh counter to force reload
                st.session_state.refresh_counter += 1
                st.success("✅ Image de fin téléchargée avec succès!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erreur lors du traitement de l'image de fin: {str(e)}")
        
        # Video Frame/Outline customization 
        st.markdown("---")
        st.markdown("#### Cadre de vidéo (Optionnel)")
        st.write("Vous pouvez ajouter un cadre qui sera superposé sur chaque slide dans la vidéo. Cette étape est entièrement optionnelle.")
        
        # Check if we already have a custom frame
        custom_frame_path = "cache/custom/frame.png"
        
        if os.path.exists(custom_frame_path):
            col1, col2 = st.columns([1, 2])
            with col1:
                # Read the image from disk directly
                img = read_image(custom_frame_path)
                if img:
                    st.image(img, caption="Cadre actuel", width=200)
                else:
                    st.warning("Impossible de charger le cadre")
            with col2:
                st.success("✅ Cadre personnalisé configuré")
                # Add a remove button
                if st.button("❌ Supprimer le cadre", key="remove_frame_btn"):
                    if os.path.exists(custom_frame_path):
                        os.remove(custom_frame_path)
                    if os.path.exists("frame.png"):
                        os.remove("frame.png")
                    st.success("✅ Cadre supprimé avec succès!")
                    st.session_state.refresh_counter += 1
                    st.rerun()
        else:
            st.info("Aucun cadre ajouté. Les vidéos seront générées sans cadre.")
        
        # Upload new frame
        uploaded_frame = st.file_uploader(
            "Télécharger un cadre (PNG avec transparence recommandé, optionnel)",
            type=["png", "jpg", "jpeg"],
            key=f"custom_frame_upload_{st.session_state.refresh_counter}",
            help="Pour de meilleurs résultats, utilisez une image PNG avec fond transparent aux dimensions 1080x1920 pixels."
        )
        
        if uploaded_frame is not None:
            try:
                # Ensure directory exists
                os.makedirs("cache/custom", exist_ok=True)
                
                # Process the image (resize to video dimensions)
                image = Image.open(BytesIO(uploaded_frame.getvalue()))
                
                # Resize to match video dimensions
                target_width = 1080
                target_height = 1920
                
                # Resize while maintaining aspect ratio
                original_aspect = image.width / image.height
                target_aspect = target_width / target_height
                
                if original_aspect > target_aspect:
                    # Original image is wider than target
                    new_width = int(target_height * original_aspect)
                    new_height = target_height
                    image = image.resize((new_width, new_height))
                    left = (new_width - target_width) // 2
                    image = image.crop((left, 0, left + target_width, target_height))
                else:
                    # Original image is taller than target
                    new_height = int(target_width / original_aspect)
                    new_width = target_width
                    image = image.resize((new_width, new_height))
                    top = (new_height - target_height) // 2
                    image = image.crop((0, top, target_width, top + target_height))
                
                # Convert to RGBA to ensure transparency support
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                
                # Save processed image to both locations
                image.save(custom_frame_path)
                image.save("frame.png") 
                
                # Increment refresh counter to force reload
                st.session_state.refresh_counter += 1
                st.success("✅ Cadre téléchargé avec succès!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erreur lors du traitement du cadre: {str(e)}")
    
    # Navigation buttons
    st.write("")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Retour", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
    
    with col3:
        if st.button("Générer la vidéo ➡️", use_container_width=True):
            st.session_state.current_step = 5
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_video_generation():
    """Step 5: Video Generation"""
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    st.subheader("Étape 5: Génération de la vidéo")
    
    # Check if we need to generate the video
    if not os.path.exists("cache/vid/final.mp4"):
        # Show settings summary
        st.write("### Résumé des paramètres")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Langue:** {st.session_state.language}")
            st.write(f"**Points:** {len(st.session_state.bullet_points)}")
            st.write(f"**Musique:** {'Activée' if st.session_state.add_music else 'Désactivée'}")
        with col2:
            st.write(f"**Voix off:** {'Activée' if st.session_state.add_voiceover else 'Désactivée'}")
            st.write(f"**Durée automatique:** {'Activée' if st.session_state.auto_duration else 'Désactivée'}")
            total_duration = sum(st.session_state.frame_durations) + 3.0  # Add outro
            st.write(f"**Durée estimée:** {total_duration:.1f} secondes")
        
        # Generate video button
        if st.button("🎬 Générer la vidéo", use_container_width=True):
            generate_video()
    else:
        # Display the generated video in a centered container with controlled size
        st.success("✅ Vidéo générée avec succès!")
        
        # Create a centered container for the video
        _, center_col, _ = st.columns([7, 6, 7])
        with center_col:
            # Display the video with a controlled size
            st.video("cache/vid/final.mp4")
        
        # Add download button
        with open("cache/vid/final.mp4", "rb") as file:
            st.download_button(
                label="📥 Télécharger la vidéo",
                data=file,
                file_name="video_lematin.mp4",
                mime="video/mp4"
            )
        
        # Regenerate button
        if st.button("🔄 Régénérer la vidéo", use_container_width=True):
            # Delete the existing video
            if os.path.exists("cache/vid/final.mp4"):
                os.remove("cache/vid/final.mp4")
            st.rerun()
    
    # Navigation button
    st.write("")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("⬅️ Retour", use_container_width=True):
            st.session_state.current_step = 4 if (st.session_state.add_voiceover or st.session_state.add_music) else 3
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def generate_video():
    """Generate the video with a progress bar"""
    
    # Create a progress bar and status area
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Show steps
    status_text.text("Préparation des fichiers...")
    progress_bar.progress(10)
    
    try:
        # Explicitly import functions from main to ensure they're available
        import main
        
        # Get frame durations and images
        frame_durations = st.session_state.frame_durations
        frame_images = st.session_state.frame_images
        bullet_points = st.session_state.bullet_points
        language = st.session_state.language
        add_voiceover = st.session_state.add_voiceover
        add_music = st.session_state.add_music
        
        print(f"Debug: Voiceover enabled: {add_voiceover}")
        print(f"Debug: Music enabled: {add_music}")
        print(f"Debug: Language: {language}")
        print(f"Debug: Number of frames: {len(frame_images)}")
        print(f"Debug: Number of bullet points: {len(bullet_points)}")
        
        # Create all necessary directories with explicit existence check
        for dir_path in ["cache", "cache/img", "cache/clg", "cache/aud", "cache/vid", "cache/custom"]:
            if not os.path.exists(dir_path):
                print(f"Creating directory: {dir_path}")
                os.makedirs(dir_path, exist_ok=True)
        
        # Clear existing collage directory to avoid old images
        for file in os.listdir("cache/clg/"):
            if file.endswith(".jpg"):
                try:
                    os.remove(os.path.join("cache/clg/", file))
                    print(f"Removed old file: {file} from cache/clg/")
                except Exception as e:
                    print(f"Warning: Failed to remove old file {file}: {e}")
        
        # Now add text to images and prepare frames for the video
        status_text.text("Préparation des images avec texte...")
        progress_bar.progress(20)
        
        # Need to ensure the source images have text overlay
        images_prepared = True # Flag to track if all images were prepared
        image_preparation_errors = []
        
        if not frame_images or len(frame_images) == 0:
            error_msg = "Erreur: Aucune image trouvée. Veuillez générer des images avant de créer la vidéo."
            status_text.text(error_msg)
            st.error(error_msg)
            return
        
        # Process each image to add text overlay for the video
        for i, (image_path, text) in enumerate(zip(frame_images, bullet_points)):
            print(f"Processing frame {i+1}: source image path = {image_path}")
            target_path = f"cache/clg/frame_{i:03d}.jpg"
            
            try:
                # First check if the source image exists
                if not os.path.exists(image_path):
                    print(f"Warning: Source image {image_path} not found!")
                    
                    # Try to recreate the image from session state bytes if available
                    if i < len(st.session_state.frame_image_bytes) and st.session_state.frame_image_bytes[i]:
                        try:
                            print(f"Attempting to recover image {i+1} from session state bytes")
                            image_bytes = st.session_state.frame_image_bytes[i]
                            with open(image_path, "wb") as f:
                                f.write(image_bytes)
                            print(f"Successfully recovered image from session state bytes: {image_path}")
                        except Exception as bytes_error:
                            print(f"Error recovering image from bytes: {bytes_error}")
                    
                    # If we still don't have the source image, try to generate a new one
                    if not os.path.exists(image_path):
                        print(f"Attempting to regenerate image {i+1} for text: {text[:30]}...")
                        # Generate a new image
                        new_image_path = main.generate_image_for_text(text, force_regenerate=True)
                        # Update the path
                        image_path = new_image_path
                        # Update in session state
                        if i < len(st.session_state.frame_images):
                            st.session_state.frame_images[i] = new_image_path
                
                # Now check again if we have a valid source image
                if os.path.exists(image_path):
                    # Add text overlay to the image and save directly to collage folder
                    print(f"  Applying text and saving to {target_path}...")
                    
                    # Now add text to the image
                    main.add_text_to_image(
                        text=text,
                        image_path=image_path,
                        output_path=target_path
                    )
                    
                    # Verify the target file was created
                    if not os.path.exists(target_path):
                        error_msg = f"Target file {target_path} was NOT created after add_text_to_image call."
                        print(f"  ERROR: {error_msg}")
                        image_preparation_errors.append(error_msg)
                        images_prepared = False
                    else:
                        print(f"  Successfully created {target_path}")
                else:
                    error_msg = f"Source image {image_path} not found after recovery attempts!"
                    print(f"  ERROR: {error_msg}")
                    image_preparation_errors.append(error_msg)
                    images_prepared = False
                    
                    # Create a fallback image with text
                    print(f"  Creating fallback image for {target_path}...")
                    try:
                        # Generate a fallback image with the text
                        from PIL import Image, ImageDraw, ImageFont
                        import textwrap
                        
                        fallback_img = Image.new('RGB', (1080, 1920), color=(50, 50, 50))
                        draw = ImageDraw.Draw(fallback_img)
                        
                        try:
                            # Try to load a font
                            font = ImageFont.truetype("Montserrat-Bold.ttf", 40)
                        except:
                            # Use default font if custom font fails
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
                        fallback_img.save(target_path)
                        print(f"  Created fallback image: {target_path}")
                    except Exception as fallback_error:
                        print(f"  Failed to create fallback image: {fallback_error}")
                    
            except Exception as img_proc_error:
                error_msg = f"Error processing image {image_path}: {img_proc_error}"
                print(f"  ERROR: {error_msg}")
                image_preparation_errors.append(error_msg)
                images_prepared = False
                
                # Try to create a fallback image
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    import textwrap
                    
                    fallback_img = Image.new('RGB', (1080, 1920), color=(50, 50, 50))
                    draw = ImageDraw.Draw(fallback_img)
                    
                    try:
                        font = ImageFont.truetype("Montserrat-Bold.ttf", 40)
                    except:
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
                    fallback_img.save(target_path)
                    print(f"  Created fallback image for {target_path} due to processing error")
                except Exception as e:
                    print(f"  Failed to create fallback image: {e}")

        # Check image preparation before continuing
        if not images_prepared:
            # Continue anyway with a warning
            warning_msg = "Attention: Certaines images n'ont pas été préparées correctement. Des images de secours seront utilisées."
            print(warning_msg)
            print(f"Image preparation errors: {image_preparation_errors}")
            status_text.text(warning_msg)
            st.warning(warning_msg)
            # Continue with the video generation
        else:
            print("All source images processed successfully into cache/clg/")

        # Generate audio files if voiceover is enabled
        if add_voiceover:
            status_text.text("Génération des fichiers audio...")
            progress_bar.progress(40)
            
            # Clear existing audio files
            os.makedirs("cache/aud/", exist_ok=True)
            for file in os.listdir("cache/aud/"):
                if file.endswith(".mp3"):
                    try:
                        os.remove(os.path.join("cache/aud/", file))
                    except Exception as e:
                        print(f"Warning: Failed to remove audio file: {e}")
            
            # Generate audio for each bullet point
            for i, text in enumerate(bullet_points):
                # Make sure we use the correct naming convention expected by image_audio_to_video
                # Should be "point_1.mp3", "point_2.mp3", etc.
                audio_path = f"cache/aud/point_{i+1}.mp3"
                
                try:
                    print(f"Generating audio for point {i+1}: {text[:30]}...")
                    main.text_to_speech(text, audio_path, language.lower())
                    
                    # Verify the audio file was created
                    if os.path.exists(audio_path):
                        print(f"✓ Audio file created: {audio_path}")
                    else:
                        print(f"✗ Failed to create audio file: {audio_path}")
                except Exception as audio_error:
                    print(f"Error generating audio for point {i+1}: {audio_error}")
        
        # Generate the video
        status_text.text("Création de la vidéo finale...")
        progress_bar.progress(70)
        
        # Make sure we have the generated summary
        generated_summary = st.session_state.generated_summary
        if not generated_summary or 'summary' not in generated_summary:
            # Create a temporary summary structure if needed
            generated_summary = {'summary': bullet_points}
        
        # Call do_work with the necessary parameters, but don't regenerate images
        main.do_work(
            generated_summary, 
            language.lower(),  # Make sure language is lowercase to match expected format
            add_voiceover,     # Explicitly pass boolean value
            add_music,         # Explicitly pass boolean value
            frame_durations,
            st.session_state.auto_duration,
            skip_image_generation=True  # Add a parameter to skip regenerating images
        )
        
        # Check if the video was actually created
        if not os.path.exists("cache/vid/final.mp4"):
            raise FileNotFoundError("Le fichier vidéo final n'a pas été créé. Vérifiez les logs pour plus de détails.")
        
        # Final progress update
        progress_bar.progress(100)
        status_text.text("Vidéo générée avec succès!")
        
        # Rerun to display the video
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        error_msg = f"Erreur lors de la génération de la vidéo: {str(e)}"
        st.error(error_msg)
        print(f"Video generation error: {str(e)}")
        import traceback
        traceback.print_exc()

def reset_project():
    """Reset the project to start a new one"""
    # Clear cache - we preserve certain directories:
    # - music directory to keep user uploaded music
    # - custom directory to keep user uploaded logo, frame, and outro
    folders_to_clear = ["cache/aud", "cache/img", "cache/clg", "cache/vid", "cache/custom_img"]
    
    # Delete all files in the specified folders
    for folder in folders_to_clear:
        if os.path.exists(folder):
            print(f"Clearing cache in {folder}...")
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        print(f"Deleted: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        print(f"Deleted directory: {file_path}")
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
    
    # Make sure all cache directories exist
    os.makedirs("cache/aud/", exist_ok=True)
    os.makedirs("cache/img/", exist_ok=True)
    os.makedirs("cache/clg/", exist_ok=True)
    os.makedirs("cache/vid/", exist_ok=True)
    os.makedirs("cache/music/", exist_ok=True)
    os.makedirs("cache/custom_img/", exist_ok=True)
    os.makedirs("cache/custom/", exist_ok=True)
    
    # Reset session state variables
    st.session_state.current_step = 1
    st.session_state.bullet_points = []
    st.session_state.article_text = ""
    st.session_state.frame_images = []
    st.session_state.frame_durations = []
    st.session_state.current_frame = 0
    st.session_state.generated_summary = {}
    
    print("Project reset complete. All cache has been cleared.")

def check_leelawadee_font():
    """Check if Leelawadee Bold font exists and create it if needed"""
    font_dir = "fonts"
    font_path = os.path.join(font_dir, "Leelawadee Bold.ttf")
    
    if os.path.exists(font_path):
        print(f"La police {font_path} existe déjà.")
        return
    
    # Essayer de copier depuis le répertoire racine si elle existe là-bas
    root_font_path = "Leelawadee Bold.ttf"
    if os.path.exists(root_font_path):
        # Assurez-vous que le répertoire fonts existe
        os.makedirs(font_dir, exist_ok=True)
        try:
            shutil.copy2(root_font_path, font_path)
            print(f"Police {root_font_path} copiée vers {font_path}")
            return
        except Exception as e:
            print(f"Erreur lors de la copie de {root_font_path} vers {font_path}: {e}")
    
    # Si la police n'existe pas, essayez de la créer
    print(f"La police {font_path} n'existe pas. Tentative de création...")
    try:
        # Assurez-vous que le répertoire fonts existe
        os.makedirs(font_dir, exist_ok=True)
        
        # Méthode 1: Utiliser notre script create_font.py
        from create_font import create_leelawadee_bold
        if create_leelawadee_bold():
            # Déplacer le fichier vers le dossier fonts
            try:
                shutil.move("Leelawadee Bold.ttf", font_path)
                print(f"Police {font_path} créée et déplacée avec succès!")
                return
            except Exception as e:
                print(f"Erreur lors du déplacement de la police: {e}")
        
        # Méthodes alternatives si les précédentes échouent...
        print("Impossible de créer ou de trouver la police Leelawadee Bold. Utilisation d'une police par défaut.")
    except Exception as e:
        print(f"Erreur lors de la vérification/création de la police: {e}")

def process_bullet_points():
    """
    Process bullet points to generate images and frames
    This is a separate function to make it easier to manage state
    """
    with st.spinner("Génération des images pour les points..."):
        bullet_points = st.session_state.bullet_points
        article_text = st.session_state.article_text
        
        # Generate images for all bullet points at once using batch processing
        frame_images = generate_images_for_bullet_points(bullet_points, article_text)
        
        # Store the generated images in session state
        st.session_state.frame_images = frame_images
        
        # Initialize the frame_image_bytes array if needed
        if 'frame_image_bytes' not in st.session_state:
            st.session_state.frame_image_bytes = [None] * len(frame_images)
        elif len(st.session_state.frame_image_bytes) < len(frame_images):
            # Extend the array if needed
            st.session_state.frame_image_bytes.extend([None] * (len(frame_images) - len(st.session_state.frame_image_bytes)))
        
        # Load raw images into memory for preview (no text overlay)
        for i, image_path in enumerate(frame_images):
            try:
                # Store the path to the raw image without text
                if not os.path.exists(image_path):
                    print(f"Warning: Image file not found: {image_path}")
                    continue
                    
                # Load the raw image bytes into memory
                with open(image_path, "rb") as f:
                    st.session_state.frame_image_bytes[i] = f.read()
                print(f"Loaded raw image bytes for frame {i} from {image_path}")
                
                # Calculate automatic duration based on text length
                if st.session_state.auto_duration:
                    # Base duration calculation: number of words × average time per word + fixed offset
                    word_count = len(bullet_points[i].split())
                    duration = max(3.0, min(8.0, word_count * 0.5 + 1.5))  # Between 3-8 seconds
                    if i < len(st.session_state.frame_durations):
                        st.session_state.frame_durations[i] = duration
                    else:
                        st.session_state.frame_durations.append(duration)
                else:
                    # Default fixed duration
                    if i < len(st.session_state.frame_durations):
                        st.session_state.frame_durations[i] = 5.0
                    else:
                        st.session_state.frame_durations.append(5.0)
                
                # Generate audio for the text if enabled
                if st.session_state.add_voiceover:
                    audio_file = f"cache/aud/audio_{i:03d}.mp3"
                    
                    # Check if existing audio files exist for this frame and delete them
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                        
                    # Generate text-to-speech
                    language = st.session_state.language
                    text_to_speech(
                        text=bullet_points[i],
                        output_file=audio_file,
                        language=language
                    )
                    
                    # Store the audio file path
                    if i < len(st.session_state.frame_audio):
                        st.session_state.frame_audio[i] = audio_file
                    else:
                        st.session_state.frame_audio.append(audio_file)
                    
                    # If auto_duration is enabled, update duration based on audio length
                    if st.session_state.auto_duration and os.path.exists(audio_file):
                        try:
                            from tinytag import TinyTag
                            tag = TinyTag.get(audio_file)
                            audio_duration = tag.duration
                            
                            # Add a small buffer to the audio duration (e.g., 0.5 seconds)
                            st.session_state.frame_durations[i] = audio_duration + 0.5
                        except Exception as e:
                            print(f"Error getting audio duration: {e}")
                            # Keep the text-based duration if there's an error
                
            except Exception as e:
                st.error(f"Error processing frame {i}: {e}")
                # Use a fallback frame
                fallback_image = generate_image_for_text(
                    f"Error: {bullet_points[i][:30]}...", force_regenerate=True
                )
                st.session_state.frame_images[i] = fallback_image
                
                # Load fallback image into memory
                try:
                    with open(fallback_image, "rb") as f:
                        st.session_state.frame_image_bytes[i] = f.read()
                    print(f"Loaded fallback image bytes for frame {i}")
                except Exception as read_error:
                    print(f"Warning: Failed to read fallback image file: {read_error}")
                
                if i < len(st.session_state.frame_durations):
                    st.session_state.frame_durations[i] = 3.0
                else:
                    st.session_state.frame_durations.append(3.0)  # Default duration
        
        # Set current frame to the first frame
        st.session_state.current_frame = 0
        st.session_state.needs_refresh = True

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("cache/aud/", exist_ok=True)
    os.makedirs("cache/img/", exist_ok=True)
    os.makedirs("cache/clg/", exist_ok=True)
    os.makedirs("cache/vid/", exist_ok=True)
    os.makedirs("cache/music/", exist_ok=True)
    os.makedirs("cache/custom_img/", exist_ok=True)
    os.makedirs("cache/custom/", exist_ok=True)
    
    main() 