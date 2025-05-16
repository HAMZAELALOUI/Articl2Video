import os
import requests

def download_montserrat_bold():
    """Download Montserrat Bold font and save it to the fonts directory"""
    os.makedirs('fonts', exist_ok=True)
    
    url = 'https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf'
    output_path = 'fonts/Montserrat-Bold.ttf'
    
    try:
        print(f"Downloading Montserrat Bold from {url}...")
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Successfully downloaded Montserrat Bold to {output_path}")
        return True
    except Exception as e:
        print(f"Error downloading font: {e}")
        return False

if __name__ == "__main__":
    download_montserrat_bold() 