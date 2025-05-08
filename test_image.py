import os
from main import generate_image, setup_openai_api_key

# Set up the API key (needed for testing)
if not setup_openai_api_key():
    # If setup fails, try using the key directly from secrets.toml
    try:
        import toml
        secrets_path = '.streamlit/secrets.toml'
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            if 'OPENAI_API_KEY' in secrets:
                os.environ["OPENAI_API_KEY"] = secrets['OPENAI_API_KEY']
                print(f"Successfully loaded API key from {secrets_path}")
            else:
                print(f"No OPENAI_API_KEY found in {secrets_path}")
        else:
            print(f"Secrets file not found: {secrets_path}")
    except Exception as e:
        print(f"Error loading secrets.toml: {e}")

# Create output directory if it doesn't exist
os.makedirs("test_output", exist_ok=True)

# Test the image generation
def test_image_generation():
    prompt = "A beautiful mountain landscape with a lake at sunset"
    output_file = "test_output/test_image.jpg"
    
    print(f"Testing image generation with prompt: '{prompt}'")
    generate_image(prompt, output_file)
    
    if os.path.exists(output_file):
        print(f"SUCCESS: Image was generated and saved to {output_file}")
        # Get file size
        file_size = os.path.getsize(output_file) / 1024  # Convert to KB
        print(f"Image size: {file_size:.2f} KB")
        return True
    else:
        print(f"FAILURE: Image was not generated.")
        return False

if __name__ == "__main__":
    test_image_generation() 