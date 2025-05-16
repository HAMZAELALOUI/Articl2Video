import os
import sys
import re
import time
import json
from web_scraper import scrape_text_from_url
from text_processor import print_summary_points, fix_unicode, clean_encoding_issues
from json_utils import save_and_clean_json
from image_generator import generate_image, generate_image_for_text, generate_images_for_bullet_points
from text_overlay import add_text_to_image
from audio_processor import text_to_speech, prepare_background_music
from video_creator import image_audio_to_video, clear_cache
from moviepy.editor import AudioFileClip
from openai_client import summarize_with_openai

def do_work(data, language, add_voiceover, add_music, frame_durations=None, auto_duration=False, skip_image_generation=False):
    """
    Main function to orchestrate the video creation process.
    
    Args:
        data (dict): The generated summary data in JSON format.
        language (str): The language for the text-to-speech.
        add_voiceover (bool): Whether to add voiceover to the video.
        add_music (bool): Whether to add background music to the video.
        frame_durations (list): Optional list of durations for each frame.
        auto_duration (bool): Whether to calculate durations automatically.
        skip_image_generation (bool): Whether to skip image generation (use existing images).
    """
    print("Starting video creation process...")
    
    # Before doing anything else, make sure all required directories exist
    # Not checking if the directories exist first can cause issues
    os.makedirs("cache/img/", exist_ok=True)
    os.makedirs("cache/aud/", exist_ok=True)
    os.makedirs("cache/clg/", exist_ok=True)
    os.makedirs("cache/vid/", exist_ok=True)
    
    # Ensure we have a "summary" key in the data
    if not data or 'summary' not in data:
        print("Error: Invalid data format. 'summary' key missing.")
        print(f"Data received: {data}")
        return
    
    # Log the total number of points
    print(f"Processing {len(data['summary'])} summary points...")
    
    # Use provided frame durations or set defaults
    if not frame_durations:
        frame_durations = []
        # Set default durations - we'll use 5 seconds per frame unless auto_duration is True
        for point in data['summary']:
            if auto_duration:
                # Calculate duration based on text length
                word_count = len(point.split())
                # Roughly calculate reading time: 0.5 second per word plus a base time
                duration = max(3.0, min(8.0, word_count * 0.5 + 1.5))
                frame_durations.append(duration)
            else:
                # Default fixed duration
                frame_durations.append(5.0)
    
    # Generate audio files if voiceover is enabled
    if add_voiceover:
        print("Generating voiceover audio...")
        for i, point in enumerate(data['summary'], 1):
            print(f"Generating audio for point {i}: {point[:50]}...")
            # Generate the audio file with the specified language
            text_to_speech(
                text=point,
                output_file=f"cache/aud/point_{i}.mp3",
                language=language
            )
            
            # If auto_duration is True, adjust the frame duration based on the audio length
            if auto_duration and os.path.exists(f"cache/aud/point_{i}.mp3"):
                try:
                    from tinytag import TinyTag
                    tag = TinyTag.get(f"cache/aud/point_{i}.mp3")
                    audio_duration = tag.duration
                    
                    # Add a small buffer to the audio duration (e.g., 0.5 seconds)
                    if i-1 < len(frame_durations):
                        frame_durations[i-1] = audio_duration + 0.5
                        print(f"Adjusted duration for point {i} to {frame_durations[i-1]} seconds")
                except Exception as e:
                    print(f"Error getting audio duration: {e}")
                    # Keep the text-based duration if there's an error
    
    # Generate images and add text only if not skipping image generation
    if not skip_image_generation:
        print("Generating images for bullet points...")
        try:
            # Get the full text from the data if available
            article_text = data.get("full_text", "")
            if not article_text:
                # Combine the summary points as a fallback
                article_text = " ".join(data["summary"])
            
            # Use the batch image generation approach for all bullet points
            image_paths = generate_images_for_bullet_points(data["summary"], article_text)
            
            # Add text overlay to each image
            for i, (point, image_path) in enumerate(zip(data["summary"], image_paths), 1):
                # Configure text properties
                text_color = (255, 255, 255)  # White
                background_color = (0, 0, 0, 153)  # Semi-transparent black background
                highlight_color = "#79C910"  # Highlight color for quoted words
                text_position = "center"
                text_padding = 20
                
                # Create the final frame
                frame_path = f"cache/clg/point_{i}.jpg"
                
                # Add text to the image
                add_text_to_image(
                    image_path=image_path,
                    output_path=frame_path,
                    text=point,
                    font_path="fonts/Leelawadee Bold.ttf",
                    font_size=65,
                    text_color=text_color,
                    background_color=background_color,
                    position=text_position,
                    padding=text_padding,
                    highlight_color=highlight_color
                )
        except Exception as e:
            print(f"Error in batch image generation: {e}")
            # Fall back to individual image generation
            print("Falling back to individual image generation...")
            for i, point in enumerate(data["summary"], 1):
                try:
                    generate_image(point, f"cache/img/point_{i}.jpg")
                    add_text_to_image(point, f"cache/img/point_{i}.jpg", f"cache/clg/point_{i}.jpg")
                except Exception as img_error:
                    print(f"Error generating image for point {i}: {img_error}")
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
    
    # Scrape and clean the article text
    raw_article_text = scrape_text_from_url(url)
    article_text = clean_encoding_issues(raw_article_text)
    print(f"Article scraped and cleaned, length: {len(article_text)} chars")
    
    # Use OpenAI for summarization instead of Gemini
    print("Summarizing article with OpenAI...")
    Json = summarize_with_openai(article_text, slidenumber, wordnumber, language)
    save_and_clean_json(Json, "summary.json")
    
    print("\nSummary points:")
    print_summary_points(Json)
    
    print("\nGenerating video...")
    do_work(Json, language, add_voiceover, add_music)
    
    print("\nVideo generation complete!")
    print(f"Output video: cache/vid/final.mp4") 