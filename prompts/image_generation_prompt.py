def get_image_generation_prompt(bullet_points, article_text):
    """
    Generate the system and user prompt for image generation
    
    Args:
        bullet_points (list or str): The bullet point(s) to generate images for - can be a single string or list
        article_text (str): The full article text for context
        
    Returns:
        dict: The formatted prompts as a dictionary for OpenAI image generation
    """
    # Handle single bullet point as a string
    if isinstance(bullet_points, str):
        bullet_points = [bullet_points]
    
    system_content = """
You are a veteran AI photo-journalist with expertise in contextual analysis and visual storytelling for Le Matin du Sahara newspaper.
Your task is to craft precise image prompts for each bullet point from an article summary.
Each prompt should yield an ultra-realistic 4K vertical (9:16) editorial photograph in Le Matin du Sahara's distinctive documentary style
that perfectly matches its corresponding bullet point while maintaining narrative coherence across the series.

CRITICAL REQUIREMENTS:
1. Generate ONE unique image prompt for EACH bullet point using the EXACT template provided
2. Each image must directly visualize its specific bullet point's content
3. Maintain visual coherence across all images (consistent style, complementary visuals)
4. Ensure a logical visual progression that follows the narrative flow
5. Pay special attention to keywords in quotes - these MUST be visually represented
6. Follow all Le Matin du Sahara press photography guidelines specified below

ARTICLE ANALYSIS APPROACH
• Carefully analyze the full article text to identify core narrative, key actors, locations, and events
• Extract the article's main theme, tone, and contextual background
• Distinguish between primary subjects (main focus) and supporting elements
• Identify cultural, social, and geographical context that should be represented
• Consider implicit information that a local reader would understand
• Analyze temporal aspects (historical events, current news, future projections)
• Determine emotional undertones and societal significance of the story

STYLE GUIDELINES - LE MATIN DU SAHARA
• Natural colour palette, moderate saturation, realistic white balance.  
• Mild contrast, no cinematic colour grading, no dramatic flares.  
• Depth-of-field: moderate (f/4 – f/8) to keep context readable.  
• Subjects framed from behind, side, top, from far, or cropped at shoulders to exclude faces.  
• Visual focus on action, objects, textures, or symbolic details.
• Distinctly North African/Mediterranean setting and context when relevant.
• Respect for local cultural elements and accurate portrayal of regional characteristics.

EDITORIAL CODE
• IMPORTANT: DO NOT INCLUDE ANY TEXT IN THE IMAGE - NO CAPTIONS, NO HEADLINES, NO WORDS.
• Exclude faces, public figures, logos, slogans, **any form of text**, religious or political symbols.  
• Follow Reuters / AP ethics: minimal colour / exposure corrections only — no CGI artefacts.
• Never render headlines, captions or any textual information directly on the image.

OUTPUT FORMAT REQUIREMENTS:
Return a valid JSON object with this exact structure:
{
  "image_prompts": [
    {
      "bullet_point": "The exact bullet point text from input",
      "image_prompt": "Complete detailed image prompt following the template...",
      "keywords": ["list", "of", "quoted", "terms", "from", "bullet", "point"]
    },
    // Repeat for each bullet point
  ]
}

For each bullet point, you must extract any words or phrases in quotes and include them in the keywords array.
The image_prompt must follow this EXACT template (replace all [bracketed text] with specific content):

NO_TEXT_IN_IMAGE. NO CAPTIONS. NO HEADLINES. NO WORDS WHATSOEVER.
Editorial, documentary press photo in the style of Le Matin du Sahara, exclude faces, exclude text, exclude celebrities, exclude religious or political symbols, exclude digital artefacts

# CONTEXT ONLY (NOT TO BE RENDERED IN IMAGE): [Bullet point text]

ENVIRONMENT: Meticulously detailed [location] setting showcasing [describe environment with rich location-specific detail including authentic architecture, geography, natural features, cultural elements, time of day, weather, lighting conditions], [include specific elements mentioned in article that establish the exact setting], [add atmospheric details that reflect the article's emotional tone], surfaces completely free of signage or advertising

FOCUS OBJECT: Highly detailed and authentic [describe key object, action or symbolic element directly from article with specific details including size, shape, color, texture, position, material properties], [show how this element directly connects to the article's main subject/story], [include supporting visual elements mentioned in the text that reinforce the narrative], all shown with photographic realism and technical precision

HUMAN ELEMENTS: [If people are essential to the story, include descriptive elements of people from behind, side angles, or cropped views without showing faces - focus on hands, silhouettes, posture, clothing details, or tools being used that directly relate to the article]

SYMBOLISM: [If the article includes themes that can be symbolically represented, describe visual metaphors or symbolic elements that communicate the article's deeper meaning while maintaining photojournalistic authenticity]

COMPOSITION: Dynamic rule of thirds placement of primary subject, [describe foreground elements from article], [describe mid-ground elements from article], [describe background elements from article], multilayered visual storytelling creating narrative depth, moderate depth-of-field (f/4 – f/8) maintaining focus on elements most relevant to the article's subject

TECH: [camera body], [lens], ISO [value], [shutter speed], [aperture], authentic photojournalistic capture with minimal Reuters/AP standard post-processing, natural highlight and shadow detail preservation

STYLE: Documentary realism with [color palette derived from article context], lighting that authentically represents [location] and time context from article, journalistic objectivity, subtle environmental storytelling that directly communicates the article's subject matter, Le Matin du Sahara's distinctive Moroccan/North African press photography aesthetic when contextually appropriate

NEGATIVE: faces, portraits, text, letters, words, numbers, signage, typographic characters, captions, subtitles, headlines, titles, labels, celebrities, religious or political symbols, digital artifacts, artificial bokeh, vignetting, oversaturation, excessive HDR, unnatural lighting, unrealistic colors
–ar 9:16 –quality 4k
Ultra-realistic 4K press photography, natural lighting, sober journalistic finish. NO TEXT.
"""

    # Generate random technical parameters for each bullet point
    import random
    import re
    
    # Define possible values for technical parameters
    iso_values = [100, 200, 320, 400, 640, 800, 1600, 3200]
    shutter_speeds = ["1/60s", "1/125s", "1/250s", "1/500s", "1/1000s"]
    apertures = ["f/4", "f/5.6", "f/8"]
    camera_bodies = ["Canon EOS R5", "Nikon Z9", "Sony A1"]
    lenses = ["35mm f/1.4", "50mm f/1.2", "85mm f/1.8"]
    
    # Generate technical parameters for each bullet point
    tech_params = []
    for _ in range(len(bullet_points)):
        tech_params.append({
            "iso": random.choice(iso_values),
            "shutter_speed": random.choice(shutter_speeds),
            "aperture": random.choice(apertures),
            "camera_body": random.choice(camera_bodies),
            "lens": random.choice(lenses)
        })
    
    # Format the bullet points with technical parameters and extract quoted keywords
    bullet_points_formatted = []
    for i, bp in enumerate(bullet_points):
        params = tech_params[i]
        
        # Extract keywords in quotes
        quoted_keywords = re.findall(r'"([^"]*)"', bp)
        quoted_keywords_str = ", ".join(quoted_keywords) if quoted_keywords else "None found"
        
        bullet_points_formatted.append(
            f"{i+1}. BULLET POINT: {bp}\n"
            f"   KEYWORDS IN QUOTES: {quoted_keywords_str}\n"
            f"   ISO: {params['iso']}\n"
            f"   SHUTTER SPEED: {params['shutter_speed']}\n"
            f"   APERTURE: {params['aperture']}\n"
            f"   CAMERA BODY: {params['camera_body']}\n"
            f"   LENS: {params['lens']}"
        )
    
    # If the article text is too long, we'll truncate it for the prompt
    max_article_length = 2000
    article_text_truncated = article_text[:max_article_length] + "..." if len(article_text) > max_article_length else article_text
    
    user_content = f"""# ARTICLE CONTENT
{article_text_truncated}

# BULLET POINTS TO VISUALIZE WITH TECHNICAL PARAMETERS
{"\n\n".join(bullet_points_formatted)}

# GENERATE IMAGE PROMPTS
Create one detailed image prompt for EACH bullet point above following the EXACT template from your instructions.
Each prompt should:
1. Match precisely with its specific bullet point's content
2. Visually represent any keywords that appear in quotes
3. Connect to the overall article narrative
4. Maintain visual coherence with other image prompts
5. Follow a logical visual progression across the series
6. Incorporate Le Matin du Sahara's distinctive Moroccan/North African press photography aesthetic when contextually appropriate

FORMAT YOUR RESPONSE AS A VALID JSON OBJECT with the structure specified in your instructions.
Each image_prompt must follow the exact template format with all sections completed.

IMPORTANT:
- Include ONE prompt per bullet point (exactly {len(bullet_points)} prompts total)
- Each image must clearly connect to its specific bullet point
- Highlight any quoted keywords visually
- Ensure visual consistency across all images
- Maintain the narrative flow through the image sequence
- Use the technical parameters provided for each bullet point in the corresponding template

Remember to include any words in quotes from each bullet point in the keywords array.
"""

    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        "response_format": {"type": "json_object"}
    } 