import os
import glob
from PIL import Image
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips


from moviepy.audio.AudioClip import CompositeAudioClip

def image_audio_to_video(image_dir, audio_dir, output_path, add_voiceover, add_music, frame_durations=None):
    """
    Create a video from images and audio files.
    
    Args:
        image_dir (str): Directory containing image files
        audio_dir (str): Directory containing audio files
        output_path (str): Path to save the output video
        add_voiceover (bool): Whether to add voiceover to the video
        add_music (bool): Whether to add background music to the video
        frame_durations (list): List of durations for each frame
        
    Returns:
        None
    """
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
    """
    Clear cached files.
    """
    import shutil
    
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
