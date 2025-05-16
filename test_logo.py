import os
import shutil
from PIL import Image
from text_overlay import add_text_to_image

def create_sample_logo():
    """Create a sample logo for testing"""
    os.makedirs("cache/custom", exist_ok=True)
    
    # Create a red logo with transparent background
    logo_width, logo_height = 300, 100
    logo = Image.new('RGBA', (logo_width, logo_height), (0, 0, 0, 0))
    
    # Draw something on the logo
    from PIL import ImageDraw
    draw = ImageDraw.Draw(logo)
    draw.rectangle([(10, 10), (logo_width-10, logo_height-10)], 
                  outline=(255, 0, 0, 255), fill=(255, 0, 0, 128), width=3)
    
    # Add text to the logo
    from PIL import ImageFont
    try:
        font = ImageFont.truetype("fonts/Montserrat-Bold.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    draw.text((logo_width//2, logo_height//2), "LOGO", 
              font=font, fill=(255, 255, 255, 255), anchor="mm")
    
    # Save the logo
    logo_path = "cache/custom/logo.png"
    logo.save(logo_path)
    print(f"Created sample logo at {logo_path}")
    return logo_path

def create_sample_frame():
    """Create a sample frame for testing"""
    os.makedirs("cache/custom", exist_ok=True)
    
    # Create a frame with transparent center and blue border
    frame_width, frame_height = 1080, 1920
    frame = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
    
    # Draw border
    from PIL import ImageDraw
    draw = ImageDraw.Draw(frame)
    border_width = 30
    
    # Draw colored border
    draw.rectangle([(0, 0), (frame_width, frame_height)], 
                  outline=(0, 0, 255, 255), fill=(0, 0, 0, 0), width=border_width)
    
    # Add corner decorations
    corner_size = 100
    # Top-left corner
    draw.rectangle([(0, 0), (corner_size, corner_size)], 
                  fill=(0, 0, 255, 128))
    # Top-right corner
    draw.rectangle([(frame_width-corner_size, 0), (frame_width, corner_size)], 
                  fill=(0, 0, 255, 128))
    # Bottom-left corner
    draw.rectangle([(0, frame_height-corner_size), (corner_size, frame_height)], 
                  fill=(0, 0, 255, 128))
    # Bottom-right corner
    draw.rectangle([(frame_width-corner_size, frame_height-corner_size), 
                   (frame_width, frame_height)], fill=(0, 0, 255, 128))
    
    # Save the frame
    frame_path = "cache/custom/frame.png"
    frame.save(frame_path)
    print(f"Created sample frame at {frame_path}")
    return frame_path

def test_logo_and_frame():
    """Test that logos and frames are properly added to images"""
    # Create test directories
    os.makedirs("cache/test", exist_ok=True)
    
    # Create test image
    test_image = Image.new('RGB', (1080, 1920), color=(100, 100, 100))
    test_image_path = "cache/test/logo_test_input.jpg"
    test_image.save(test_image_path)
    
    # Create logo and frame
    logo_path = create_sample_logo()
    frame_path = create_sample_frame()
    
    # Output path
    output_path = "cache/test/logo_test_output.jpg"
    
    # Sample text with quoted keywords
    test_text = 'Example text with "highlighted" keywords for "testing" the logo and frame.'
    
    # Generate the image with logo and frame
    try:
        result = add_text_to_image(
            text=test_text,
            image_path=test_image_path,
            output_path=output_path
        )
        
        # Check result
        if result and os.path.exists(output_path):
            print(f"SUCCESS: Image created with logo and frame at {output_path}")
            print("Please check the image to verify:")
            print("1. The logo appears at the top center")
            print("2. The frame appears around the image")
            print("3. The quoted words are highlighted in green")
            print("4. The text appears below the logo")
            return True
        else:
            print(f"ERROR: Output file not created at {output_path}")
            return False
    except Exception as e:
        print(f"ERROR: Exception occurred: {e}")
        return False

if __name__ == "__main__":
    test_logo_and_frame() 