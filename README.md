# Article2Video Application

This application converts articles to videos by generating images with OpenAI's GPT-image-1 model, creating voiceovers, and combining them into a video.

## Setup

1. Ensure you have Python 3.8+ installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key in one of these ways:
   - Create a `.streamlit/secrets.toml` file with your API key:
     ```
     OPENAI_API_KEY = "your-openai-api-key"
     ```
   - Set the `OPENAI_API_KEY` environment variable
   - Use the utility script to apply your key: `python apply_api_key.py`

## Running the Application

### Streamlit App (Recommended)
Run the Streamlit app for the full interface:
```
streamlit run streamlit_app.py
```

### Command Line
You can also run the application from the command line:
```
python main.py
```

## Testing Image Generation

To test if the image generation with GPT-image-1 is working:
```
python test_image.py
```

This will generate a test image in the `test_output` directory.

## Troubleshooting

### API Key Issues
- Run `python apply_api_key.py` to verify your API key is properly configured
- Check that your OpenAI account has access to the GPT-image-1 model
- Ensure you have sufficient credits in your OpenAI account

### Image Generation Failures
- The application will create fallback images if the API call fails
- Check the error messages for specific issues

## Features

- Generate images based on text descriptions using OpenAI's GPT-image-1 model
- Convert text to speech for voiceovers
- Combine images and audio into a video
- Add custom background music
- Customize video duration

## Credits

This application uses:
- OpenAI GPT-image-1 for image generation
- Google's gTTS for text-to-speech
- MoviePy for video creation 