# Article2Video

Application qui convertit automatiquement des articles en vidéos narratives.

## Architecture modulaire

Le code a été réorganisé en modules pour améliorer la maintenabilité et la lisibilité :

### Modules principaux

- **main.py** - Point d'entrée principal de l'application
- **web_scraper.py** - Extraction du contenu des articles web
- **text_processor.py** - Traitement de texte et appels à l'API Gemini
- **json_utils.py** - Utilitaires pour le traitement des données JSON
- **image_generator.py** - Génération d'images via l'API OpenAI
- **image_utils.py** - Fonctions utilitaires pour la manipulation d'images
- **text_overlay.py** - Ajout de texte avec formatage sur les images
- **audio_processor.py** - Génération et manipulation audio
- **video_creator.py** - Création de vidéos à partir d'images et d'audio
- **app_controller.py** - Coordination du workflow complet

### Interface utilisateur

- **streamlit_app.py** - Interface web Streamlit pour l'application

## Fonctionnalités

- Extraction du contenu d'articles depuis des URLs
- Résumé automatique avec des points clés en utilisant l'IA Gemini
- Génération d'images illustratives pour chaque point du résumé
- Mise en évidence des mots clés en vert (#79C910)
- Génération de narration audio avec text-to-speech
- Assemblage en vidéo avec fond musical optionnel
- Interface utilisateur pour personnaliser la génération

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Pour utiliser toutes les fonctionnalités, vous devez configurer les clés API suivantes :

1. Clé API OpenAI pour la génération d'images
2. Clé API Google Gemini pour le résumé d'articles

Créez un fichier `.streamlit/secrets.toml` avec le contenu suivant :

```toml
OPENAI_API_KEY = "votre-clé-openai"
GEMINI_API_KEY = "votre-clé-gemini"
```

## Utilisation

### Via l'interface Streamlit

```bash
streamlit run streamlit_app.py
```

### Via la ligne de commande

```bash
python main.py
```

## Notes sur les polices

L'application utilise la police Leelawadee Bold pour le texte. Elle doit être présente dans le dossier `fonts/`.

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