import os
import sys
import logging
import music_api

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_music')

def test_music_api():
    """Run a comprehensive test of the music API to diagnose issues"""
    
    print("\n--- MUSIC API DIAGNOSTIC TEST ---\n")
    
    # Test 1: Check if we can get categories
    print("Test 1: Getting music categories...")
    try:
        categories = music_api.get_category_names()
        print(f"SUCCESS: Found {len(categories)} categories: {categories}")
    except Exception as e:
        print(f"ERROR: Failed to get categories: {str(e)}")
        return
    
    # Test 2: Try searching for music
    print("\nTest 2: Searching for music...")
    for category in categories:
        try:
            print(f"  Searching in category: {category}")
            results = music_api.search_music(category=category)
            print(f"  SUCCESS: Found {len(results['tracks'])} tracks in {category}")
            
            # If we found tracks, let's check the first one
            if results['tracks']:
                track = results['tracks'][0]
                print(f"  First track: {track['title']} by {track['artist']}")
                print(f"  URL: {track['url']}")
        except Exception as e:
            print(f"  ERROR: Failed to search in {category}: {str(e)}")
    
    # Test 3: Try to download a track
    print("\nTest 3: Downloading a track...")
    try:
        # Get the first track from any category
        results = music_api.search_music()
        if not results['tracks']:
            print("ERROR: No tracks found to test download")
            return
            
        track = results['tracks'][0]
        print(f"Attempting to download: {track['title']} (ID: {track['id']})")
        
        # Create a test directory
        test_dir = "test_cache"
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "test_music.mp3")
        
        # Try downloading
        success = music_api.download_music(track['id'], test_file)
        
        if success and os.path.exists(test_file):
            file_size = os.path.getsize(test_file)
            print(f"SUCCESS: Downloaded {file_size} bytes to {test_file}")
        else:
            print(f"ERROR: Download failed or file not created")
    except Exception as e:
        print(f"ERROR: Download test failed: {str(e)}")
    
    # Test 4: Network connectivity test
    print("\nTest 4: Testing network connectivity...")
    import requests
    try:
        sample_url = "https://cdn.freesound.org/previews/388/388290_7293382-lq.mp3"
        print(f"Testing connection to: {sample_url}")
        response = requests.get(sample_url, stream=True)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Network connection working")
        else:
            print(f"ERROR: Network request failed with status {response.status_code}")
    except Exception as e:
        print(f"ERROR: Network test failed: {str(e)}")
    
    print("\n--- TEST COMPLETE ---\n")

if __name__ == "__main__":
    test_music_api() 