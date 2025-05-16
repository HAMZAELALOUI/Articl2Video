import os
from PIL import Image
from text_overlay import add_text_to_image

def test_add_text_to_image():
    """
    Test the add_text_to_image function with a simple example
    """
    # Create test directories if they don't exist
    os.makedirs("cache/test", exist_ok=True)
    
    # Create a simple blank test image
    test_image = Image.new('RGB', (1080, 1920), color=(50, 50, 50))
    test_image_path = "cache/test/test_input.jpg"
    test_image.save(test_image_path)
    
    # Create output path
    output_path = "cache/test/test_output.jpg"
    
    # Sample text with quoted keywords
    test_text = 'This is a test with "highlighted" keywords for testing'
    
    try:
        # Call add_text_to_image with the correct parameters
        add_text_to_image(
            text=test_text,
            image_path=test_image_path,
            output_path=output_path
        )
        
        # Check if output file was created
        if os.path.exists(output_path):
            print(f"SUCCESS: Image with text created at {output_path}")
            return True
        else:
            print(f"ERROR: Output file not created at {output_path}")
            return False
    except Exception as e:
        print(f"ERROR: Exception occurred: {e}")
        return False

if __name__ == "__main__":
    test_add_text_to_image() 