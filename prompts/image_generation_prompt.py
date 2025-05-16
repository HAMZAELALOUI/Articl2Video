def get_image_generation_prompt(headline):
    """
    Generate the prompt for image generation
    
    Args:
        headline (str): The text to visualize in the image
        
    Returns:
        str: The formatted prompt text
    """
    return (
        f"Ultra-realistic 4K editorial photograph press shot illustrating the following topic: {headline}. "
        "Symbolic, in-animate elements that visually convey the story; dramatic cinematic lighting, high contrast, deep shadows, news-photography style, vertical 9:16 composition. "
        "Scene is completely deserted — absolutely no humans, silhouettes or body parts; no written text, no logos, no flags or religious symbols.no public figures. "
    ) 