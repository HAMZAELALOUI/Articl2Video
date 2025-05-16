from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import re
import hashlib
from io import BytesIO
from text_processor import fix_unicode

def calculate_shadow(font_size, text_prominence=1.0):
    """
    Calculate shadow offset and opacity based on font size and text prominence.
    
    Args:
        font_size (int): Font size in pixels
        text_prominence (float): Prominence factor for the text (1.0 = normal)
        
    Returns:
        tuple: (shadow_offset, shadow_opacity)
    """
    # Base shadow size scales with font size but not linearly
    base_offset = font_size * 0.04  # Base scaling factor
    
    # Scale offset by prominence factor (bigger for headlines, smaller for body text)
    shadow_offset = max(1, int(base_offset * text_prominence))
    
    # Shadow opacity is inversely related to offset - smaller shadows are more opaque
    # but should never be too light or too dark
    base_opacity = 140  # Base opacity level (out of 255)
    opacity_scale = min(1.0, max(0.6, 1.1 - (shadow_offset / 10)))  # Inverse scaling
    shadow_opacity = int(base_opacity * opacity_scale)
    
    return shadow_offset, shadow_opacity


def smart_wrap_text(text, font, max_width, draw):
    """
    Wrap text using actual pixel measurements to maximize space usage.
    
    Args:
        text (str): Text to wrap
        font (ImageFont): Font to use for measurement
        max_width (int): Maximum width in pixels
        draw (ImageDraw): ImageDraw object for text measurement
        
    Returns:
        list: List of wrapped lines
    """
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        # Calculate width including this word and a space
        word_with_space = word + " " if current_line else word
        word_bbox = draw.textbbox((0, 0), word_with_space, font=font)
        word_width = word_bbox[2] - word_bbox[0]
        
        if current_line and current_width + word_width > max_width:
            # This word doesn't fit, start a new line
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = draw.textbbox((0, 0), word, font=font)[2]
        else:
            # Word fits, add it
            current_line.append(word)
            current_width += word_width
    
    # Add the last line if it contains words
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines 