# Article2Video Application

This application converts articles to videos by generating images with OpenAI's GPT-image-1 model, creating voiceovers, and combining them into a video.

## Setup

1. Ensure you have Python 3.8+ installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key in one of these ways:
   - Create a `.streamlit/secrets.toml` file with your API keys (recommended method):
     ```
     OPENAI_API_KEY = "your-openai-api-key"
     GEMINI_API_KEY = "your-gemini-api-key"
     ```
   - Set these environment variables manually
   - Use the utility script to apply your keys: `python apply_api_key.py`

## API Keys Configuration

This application requires API keys for two services:

1. **OpenAI API Key**: Used for image generation with the GPT-image-1 model
2. **Google Gemini API Key**: Used for article summarization and text processing

To set up your API keys:

1. Rename `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Add your actual API keys to this file
3. Run `python test_secrets.py` to verify your keys are set up correctly

The application will check for these keys in your secrets.toml file before starting.

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
- Run `python test_secrets.py` to verify your API keys are properly configured
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