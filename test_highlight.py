import os
from PIL import Image
from text_overlay import add_text_to_image

def test_highlight_keywords():
    """
    Test the highlighting of quoted keywords in text overlay
    """
    # Create test directories if they don't exist
    os.makedirs("cache/test", exist_ok=True)
    
    # Create a simple blank test image
    test_image = Image.new('RGB', (1080, 1920), color=(50, 50, 50))
    test_image_path = "cache/test/highlight_test_input.jpg"
    test_image.save(test_image_path)
    
    # Create output path
    output_path = "cache/test/highlight_test_output.jpg"
    
    # Sample text with multiple quoted keywords
    test_text = 'La production "industrielle" a baissé de 10% selon les "données" ministérielles. Cela pourrait affecter "l\'économie nationale" et les "investissements" dans la région.'
    
    try:
        # Call add_text_to_image with the test text
        result = add_text_to_image(
            text=test_text,
            image_path=test_image_path,
            output_path=output_path
        )
        
        # Check if output file was created
        if os.path.exists(output_path):
            print(f"SUCCESS: Image with highlighted text created at {output_path}")
            print("Please check the image to verify that quoted words are highlighted in green (#79C910)")
            return True
        else:
            print(f"ERROR: Output file not created at {output_path}")
            return False
    except Exception as e:
        print(f"ERROR: Exception occurred: {e}")
        return False

if __name__ == "__main__":
    test_highlight_keywords() 