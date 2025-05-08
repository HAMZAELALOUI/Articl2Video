"""
Utility script to apply API keys from .streamlit/secrets.toml.
Run this script before running the main application to ensure the API keys are set.
"""

import os
import toml

# Path to the secrets file
secrets_path = '.streamlit/secrets.toml'

def apply_api_keys():
    """Apply the API keys from secrets.toml to the environment"""
    try:
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            success = True
            
            # Check for required keys
            required_keys = ["OPENAI_API_KEY", "GEMINI_API_KEY"]
            missing_keys = []
            
            for key in required_keys:
                if key in secrets:
                    api_key = secrets[key]
                    os.environ[key] = api_key
                    
                    # Show a portion of the key for verification (first 4 and last 4 chars)
                    if len(api_key) > 8:
                        masked_key = f"{api_key[:4]}...{api_key[-4:]}"
                    else:
                        masked_key = "***" # Too short to meaningfully mask
                    print(f"✅ Successfully applied {key}: {masked_key}")
                else:
                    missing_keys.append(key)
                    success = False
            
            if missing_keys:
                print(f"❌ Missing required keys: {', '.join(missing_keys)}")
                print("Please add these keys to your .streamlit/secrets.toml file.")
            
            return success
        else:
            print(f"❌ Secrets file not found: {secrets_path}")
            print("Please create this file with your API keys:")
            print("""
Example .streamlit/secrets.toml:
OPENAI_API_KEY = "your-openai-api-key"
GEMINI_API_KEY = "your-gemini-api-key"
            """)
    except Exception as e:
        print(f"❌ Error reading or applying API keys: {e}")
    
    return False

if __name__ == "__main__":
    # When run directly, apply the API keys
    if apply_api_keys():
        print("\n✅ API keys are now set in the environment.")
        print("You can now run your application.")
    else:
        print("\n❌ Failed to set all required API keys.")
        print(f"Please check your {secrets_path} file and ensure it contains all required keys.") 