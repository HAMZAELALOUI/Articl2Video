import os
from web_scraper import scrape_text_from_url
from text_processor import call_llm_api, print_summary_points, fix_unicode
from json_utils import save_and_clean_json
from image_generator import generate_image, generate_image_for_text
from text_overlay import add_text_to_image
from audio_processor import text_to_speech, prepare_background_music
from video_creator import image_audio_to_video, clear_cache
from moviepy.editor import AudioFileClip

def do_work(data, language, add_voiceover, add_music, frame_durations=None, auto_duration=False, skip_image_generation=False):
    """
    Main workflow function that processes data and generates a video.
    
    Args:
        data (dict): Data containing summary points
        language (str): Language for text-to-speech
        add_voiceover (bool): Whether to add voiceover
        add_music (bool): Whether to add background music
        frame_durations (list): Optional list of durations for each frame
        auto_duration (bool): Whether to calculate durations automatically
        skip_image_generation (bool): Whether to skip image generation
        
    Returns:
        None
    """
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
            import glob
            audio_files = sorted(glob.glob(os.path.join("cache/aud", "*.mp3")))
            print(f"Found {len(audio_files)} audio files: {audio_files}")
            
        image_audio_to_video("cache/clg", "cache/aud", f"cache/vid/final.mp4", add_voiceover, add_music, frame_durations)


def test_cli():
    """CLI test function to verify the workflow"""
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