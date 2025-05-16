from gtts import gTTS
from moviepy.audio.AudioClip import AudioClip
from text_processor import fix_unicode

def text_to_speech(text, output_file, language):
    """
    Convert text to speech using Google's TTS service.
    
    Args:
        text (str): The text to convert to speech
        output_file (str): The path to save the audio file
        language (str): The language of the text
        
    Returns:
        None
    """
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


def prepare_background_music(music_file, total_duration):
    """
    Prepare background music by trimming or looping to match the estimated video duration.
    This creates a processed version that will be ready to use when generating the final video.
    
    Args:
        music_file: Path to the background music file
        total_duration: Total estimated duration of the video in seconds
        
    Returns:
        str: Path to the processed music file, or None if processing failed
    """
    try:
        from moviepy.editor import AudioFileClip
        import os
        
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