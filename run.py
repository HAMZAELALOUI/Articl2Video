from moviepy import VideoFileClip
import os

def extract_audio(video_path, output_path=None):
    """
    Extract audio from a video file and save it as an mp3.
    
    Args:
        video_path (str): Path to the video file
        output_path (str, optional): Path to save the extracted audio. 
                                    If None, audio is saved in the same directory
                                    as the video with the same name but .mp3 extension.
    
    Returns:
        str: Path to the extracted audio file
    """
    try:
        # Get the video file name without extension
        if output_path is None:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(os.path.dirname(video_path), f"{video_name}.mp3")
        
        # Load the video
        video = VideoFileClip(video_path)
        
        # Extract the audio
        audio = video.audio
        
        # Save the audio
        audio.write_audiofile(output_path)
        
        # Close the video to release resources
        video.close()
        
        print(f"Audio extracted successfully to {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    video_file =  "example.mp4"
    output_file = "music.mp3"
    
    if not output_file:
        output_file = None
    
    extract_audio(video_file, output_file)