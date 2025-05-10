import streamlit as st
import os
import shutil
import time
import random
import uuid

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
from main import scrape_text_from_url, call_llm_api, save_and_clean_json, fix_unicode, do_work, clear_cache, generate_image_for_text, text_to_speech, add_text_to_image
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
            min_value=8,
            max_value=12,
            value=10,
            key="slidenumber_slider"
        )
        st.session_state.slidenumber = slidenumber

        wordnumber = st.slider(
            "Mots par point",
            min_value=10,
            max_value=20,
            value=13,
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
    """Process the article text and generate a summary"""
    with st.spinner("Génération du résumé..."):
        try:
            llm_response = call_llm_api(
                st.session_state.article_text, 
                st.session_state.slidenumber, 
                st.session_state.wordnumber, 
                st.session_state.language
            )
            Json = save_and_clean_json(llm_response, "summary.json")
            st.session_state.generated_summary = Json
            
            if 'summary' in Json:
                st.session_state.bullet_points = [fix_unicode(point) for point in Json['summary']]
                st.success("Résumé généré avec succès!")
                
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
            
            # Generate images for all bullet points at once
            with st.spinner("Génération des images..."):
                try:
                    # Ensure cache directories exist
                    os.makedirs("cache/img/", exist_ok=True)
                    os.makedirs("cache/clg/", exist_ok=True)
                    
                    frame_images_paths = []
                    frame_image_bytes_list = []
                    
                    for i, point in enumerate(edited_points):
                        # Generate image
                        image_path = generate_image_for_text(point)
                        frame_images_paths.append(image_path)
                        
                        # Read the generated image file and store its bytes
                        try:
                            with open(image_path, "rb") as f:
                                image_bytes = f.read()
                                frame_image_bytes_list.append(image_bytes)
                                print(f"Successfully cached image {i+1} in session state")
                        except Exception as e:
                            st.error(f"Error reading generated image {image_path}: {e}")
                            frame_image_bytes_list.append(None)
                    
                    # Update session state
                    st.session_state.frame_images = frame_images_paths
                    st.session_state.frame_image_bytes = frame_image_bytes_list
                    st.session_state.current_frame = 0
                    
                    # Initialize frame durations with default values
                    st.session_state.frame_durations = [3.0] * len(edited_points)
                    
                    # Move to the next step
                    st.session_state.current_step = 3
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error during image generation: {str(e)}")
                    st.stop()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_frame_interface():
    """Step 3: Frame/Slide Interface"""
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    # Get current frame index and total frames
    current_frame = st.session_state.current_frame
    total_frames = len(st.session_state.bullet_points)
    
    st.subheader(f"Étape 3: Visualisation des slides ({current_frame + 1}/{total_frames})")
    
    # Information about font
    st.info("💡 La police Leelawadee Bold est utilisée pour le texte, avec les mots clés entre guillemets mis en évidence en vert (#79C910).")
    
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
                st.image(img, caption=f"Slide {current_frame + 1}", use_container_width=True, width=300)
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
                        
                        # Apply text overlay to the image
                        from main import add_text_to_image
                        target_path = f"cache/img/point_{current_frame+1}.jpg"
                        add_text_to_image(st.session_state.bullet_points[current_frame], custom_image_path, target_path)

                        # Update the frame image path in session state
                        st.session_state.frame_images[current_frame] = target_path

                        # --- Read the final image and update bytes in session state ---
                        try:
                            with open(target_path, "rb") as f:
                                st.session_state.frame_image_bytes[current_frame] = f.read()
                            print(f"Updated image bytes for frame {current_frame} from custom upload.")
                        except Exception as read_error:
                            st.error(f"Failed to read processed custom image for state update: {read_error}")
                        # --- End update bytes ---

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

                        # Force regenerate image and get path
                        new_image_path = generate_image_for_text(edited_text, force_regenerate=True)
                        st.session_state.frame_images[current_frame] = new_image_path # Update path

                        # --- Read the new image and update bytes in session state ---
                        try:
                            with open(new_image_path, "rb") as f:
                                st.session_state.frame_image_bytes[current_frame] = f.read()
                            print(f"Updated image bytes for frame {current_frame} from regeneration.")
                        except Exception as read_error:
                            st.error(f"Failed to read regenerated image for state update: {read_error}")
                        # --- End update bytes ---

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
        if st.button("Retour à l'édition des points"):
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
        
        # Copy existing images to collage directory in the correct order
        status_text.text("Préparation des images...")
        progress_bar.progress(20)
        
        # Need to ensure the source images have text overlay
        images_prepared = True # Flag to track if all images were prepared
        image_preparation_errors = []
        
        if not frame_images or len(frame_images) == 0:
            error_msg = "Erreur: Aucune image trouvée. Veuillez générer des images avant de créer la vidéo."
            status_text.text(error_msg)
            st.error(error_msg)
            return
        
        # Try to use bytes from session state if available
        use_bytes_from_state = (
            'frame_image_bytes' in st.session_state and 
            len(st.session_state.frame_image_bytes) == len(frame_images) and
            all(bytes is not None for bytes in st.session_state.frame_image_bytes)
        )
        
        print(f"Debug: Using image bytes from session state: {use_bytes_from_state}")
        
        for i, (image_path, text) in enumerate(zip(frame_images, bullet_points)):
            print(f"Processing frame {i+1}: source image path = {image_path}")
            target_path = f"cache/clg/point_{i+1}.jpg"
            
            try:
                # First check if the source image exists
                if not os.path.exists(image_path):
                    print(f"Warning: Source image {image_path} not found!")
                    
                    # Try to recreate the image from session state bytes if available
                    if use_bytes_from_state and i < len(st.session_state.frame_image_bytes):
                        try:
                            print(f"Attempting to recover image {i+1} from session state bytes")
                            image_bytes = st.session_state.frame_image_bytes[i]
                            if image_bytes:
                                with open(image_path, "wb") as f:
                                    f.write(image_bytes)
                                print(f"Successfully recovered image from session state bytes: {image_path}")
                            else:
                                print(f"Error: No valid bytes found in session state for image {i+1}")
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
                    
                    # Create a copy of the image first to avoid modifying the original
                    from PIL import Image
                    img = Image.open(image_path)
                    temp_path = f"cache/img/temp_{i+1}.jpg"
                    img.save(temp_path)
                    
                    # Now add text to the copy
                    main.add_text_to_image(text, temp_path, target_path)
                    
                    # Verify the target file was created
                    if not os.path.exists(target_path):
                        error_msg = f"Target file {target_path} was NOT created after add_text_to_image call."
                        print(f"  ERROR: {error_msg}")
                        image_preparation_errors.append(error_msg)
                        images_prepared = False
                    else:
                        print(f"  Successfully created {target_path}")
                        
                        # Optionally clean up the temp file
                        try:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        except:
                            pass
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