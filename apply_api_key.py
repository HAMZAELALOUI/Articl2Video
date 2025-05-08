"""
Utility script to apply the OpenAI API key from .streamlit/secrets.toml.
Run this script before running the main application to ensure the API key is set.
"""

import os
import toml

# Path to the secrets file
secrets_path = '.streamlit/secrets.toml'

def apply_api_key():
    """Apply the OpenAI API key from secrets.toml to the environment"""
    try:
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            if 'OPENAI_API_KEY' in secrets:
                api_key = secrets['OPENAI_API_KEY']
                os.environ["OPENAI_API_KEY"] = api_key
                print(f"✓ Successfully applied OpenAI API key from {secrets_path}")
                # Show a portion of the key for verification (first 4 and last 4 chars)
                masked_key = f"{api_key[:4]}...{api_key[-4:]}"
                print(f"  Key: {masked_key}")
                return True
            else:
                print(f"✗ No OPENAI_API_KEY found in {secrets_path}")
        else:
            print(f"✗ Secrets file not found: {secrets_path}")
    except Exception as e:
        print(f"✗ Error reading or applying API key: {e}")
    
    return False

if __name__ == "__main__":
    # When run directly, apply the API key
    if apply_api_key():
        print("API key is now set in the environment.")
        print("You can now run your application.")
    else:
        print("\nFailed to set API key.")
        print(f"Please ensure your API key is in {secrets_path} under OPENAI_API_KEY.") 