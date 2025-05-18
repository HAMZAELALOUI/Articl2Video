from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import re
import os
from text_processor import fix_unicode
from image_utils import smart_wrap_text, calculate_shadow
import textwrap

def add_text_to_image(text, image_path, output_path):
    """
    Add text to an image with proper text wrapping and highlighting for quoted words.
    
    Args:
        text (str): The text to add to the image
        image_path (str): The path to the input image
        output_path (str): The path to save the output image
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        
        # Try to load font from different locations
        font = None
        font_paths = [
            "fonts/Montserrat-Bold.ttf",  # Priority to Montserrat Bold
            "Montserrat-Bold.ttf",
            "fonts/Leelawadee Bold.ttf",
            "Leelawadee Bold.ttf"
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 50)
                    small_font = ImageFont.truetype(font_path, 40)
                    print(f"Loaded font from {font_path}")
                    break
            except Exception as e:
                print(f"Could not load font from {font_path}: {e}")
        
        # If no custom font found, use default
        if font is None:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            print("Using default font")
        
        # Add logo if it exists
        width, height = img.size
        
        # Check for custom logo
        logo_path = "cache/custom/logo.png"
        if os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path)
                # Resize logo to be 20% of image width, maintaining aspect ratio
                logo_width = int(width * 0.3)  # percentage of image width
                logo_height = int(logo.height * (logo_width / logo.width))
                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                
                # Calculate position to center logo at the top with some margin
                logo_x = (width - logo_width) // 2
                logo_y = int(height * 0.05)  # 5% from the top
                
                # Make sure logo has alpha channel for proper overlay
                if logo.mode != 'RGBA':
                    logo = logo.convert('RGBA')
                
                # If the image is not RGBA, convert it
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                    
                # Create a temporary image for the logo
                logo_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
                logo_layer.paste(logo, (logo_x, logo_y), logo)
                
                # Composite the logo onto the image
                img = Image.alpha_composite(img, logo_layer)
                print(f"Added logo from {logo_path} to image")
            except Exception as e:
                print(f"Error adding logo to image: {e}")
        
        # Text settings
        highlight_color = "#79C910"  # Green for highlighting quoted text
        highlight_color_rgb = ImageColor.getrgb(highlight_color)
        text_color = (255, 255, 255)  # White
        
        # Calculate position - we need to adjust for logo if it was added
        text_width = width - 100  # Padding on sides
        
        # Function to find quoted text
        def find_quoted_text(text):
            pattern = r'"([^"]*)"'
            return re.findall(pattern, text)
        
        # Process text
        quoted_texts = find_quoted_text(text)
        print(f"Found quoted keywords: {quoted_texts}")
        
        # Wrap text to fit width
        wrapper = textwrap.TextWrapper(width=30)
        wrapped_lines = wrapper.wrap(text)
        
        # Calculate text height to position correctly
        line_height = 60
        text_block_height = len(wrapped_lines) * line_height
        
        # Adjust start_y to account for logo if present
        start_y = (height - text_block_height) // 2
        if os.path.exists(logo_path):
            # Push text down a bit when logo is present
            logo_margin = int(height * 0.20)  # 20% from top
            start_y = max(start_y, logo_margin)
        
        # Draw semi-transparent black background for text
        padding = 20
        bg_top = start_y - padding
        bg_bottom = start_y + text_block_height + padding
        bg_left = 50 - padding
        bg_right = width - 50 + padding
        
        # Create a semi-transparent overlay
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle([(bg_left, bg_top), (bg_right, bg_bottom)], fill=(0, 0, 0, 180))
        
        # Composite the overlay onto the image
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        
        # Remove quotes from the text for display
        # This preserves the ability to highlight keywords while removing visual quotes
        display_text = text
        for quoted in quoted_texts:
            # Replace each quoted text with just the text (no quotes)
            display_text = display_text.replace(f'"{quoted}"', quoted)
        
        # Re-wrap the display text without quotes
        wrapped_display_lines = wrapper.wrap(display_text)
        
        # Draw text with highlighted quotes
        y = start_y
        for i, line in enumerate(wrapped_display_lines):
            line_positions = []
            current_text = line
            
            # Check for quoted text in this line (using original quoted texts list)
            for quoted in quoted_texts:
                if quoted in current_text:
                    parts = current_text.split(quoted, 1)
                    
                    # Calculate positions
                    if parts[0]:
                        w1 = draw.textlength(parts[0], font=font)
                        line_positions.append((parts[0], (50, y), text_color))
                    else:
                        w1 = 0
                    
                    # Add the keyword with highlight color, without quotes
                    line_positions.append((quoted, (50 + w1, y), highlight_color_rgb))
                    
                    # If there's text after the keyword
                    if len(parts) > 1 and parts[1]:
                        w2 = draw.textlength(quoted, font=font)
                        line_positions.append((parts[1], (50 + w1 + w2, y), text_color))
                    
                    current_text = ""  # Processed this text
                    break
            
            # If no quotes were found, add the whole line
            if current_text:
                line_positions.append((current_text, (50, y), text_color))
            
            # Draw all parts of the line
            for text_part, position, color in line_positions:
                draw.text(position, text_part, fill=color, font=font)
            
            y += line_height
        
        # Add frame overlay if it exists
        frame_path = "cache/custom/frame.png"
        if os.path.exists(frame_path):
            try:
                frame = Image.open(frame_path)
                # Resize frame if needed
                if frame.size != img.size:
                    frame = frame.resize(img.size, Image.Resampling.LANCZOS)
                
                # Ensure frame has alpha
                if frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')
                
                # Composite frame on top
                img = Image.alpha_composite(img, frame)
                print(f"Added frame overlay from {frame_path}")
            except Exception as e:
                print(f"Error adding frame: {e}")
        
        # Convert to RGB for JPEG
        img = img.convert('RGB')
        
        # Save the image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        print(f"✓ Saved image with text to {output_path}")
        return True
    
    except Exception as e:
        print(f"❌ Error adding text to image: {e}")
        return False

def add_text_to_image_old(text, image_path, output_path):
    """
    Add text overlay to an image with highlighting for keywords.
    
    Args:
        text (str): The text to add to the image
        image_path (str): Path to the input image
        output_path (str): Path to save the output image
        
    Returns:
        None
    """
    text = fix_unicode(text)
    
    # Open the image
    img = Image.open(image_path)
    
    # Create a copy of the image
    img_with_overlay = img.copy()
    
    # Create draw object
    draw = ImageDraw.Draw(img_with_overlay)
    
    # Calculate dimensions
    width, height = img.size
    
    # Check if frame exists to adjust content positioning
    frame_exists = False
    frame_path = "cache/custom/frame.png" if os.path.exists("cache/custom/frame.png") else "frame.png"
    frame_border_width = 0
    if os.path.exists(frame_path):
        frame_exists = True
        # Load frame to check its design
        frame = Image.open(frame_path)
        frame_rgba = frame.convert('RGBA')
        
        # More robust frame border detection
        # Check multiple points around the frame edges
        border_samples = []
        
        # Sample points from all four edges
        edge_points = [
            [(i, 5) for i in range(0, width, width//10)],             # Top edge
            [(i, height-5) for i in range(0, width, width//10)],       # Bottom edge
            [(5, i) for i in range(0, height, height//10)],            # Left edge
            [(width-5, i) for i in range(0, height, height//10)]       # Right edge
        ]
        
        # Find border width from each edge
        for edge in edge_points:
            for x, y in edge:
                try:
                    # Check if this point has alpha (part of frame)
                    if x < frame_rgba.width and y < frame_rgba.height:
                        _, _, _, a = frame_rgba.getpixel((x, y))
                        if a > 100:  # If edge pixel has alpha, frame likely has border
                            # Scan inward until we find a transparent/semi-transparent pixel
                            if x <= 5:  # Left edge sample
                                for i in range(20, 150, 5):
                                    if i >= frame_rgba.width:
                                        break
                                    if frame_rgba.getpixel((i, y))[3] < 100:
                                        border_samples.append(i)
                                        break
                            elif x >= width-5:  # Right edge sample
                                for i in range(width-20, width-150, -5):
                                    if i < 0:
                                        break
                                    if frame_rgba.getpixel((i, y))[3] < 100:
                                        border_samples.append(width - i)
                                        break
                            elif y <= 5:  # Top edge sample
                                for i in range(20, 150, 5):
                                    if i >= frame_rgba.height:
                                        break
                                    if frame_rgba.getpixel((x, i))[3] < 100:
                                        border_samples.append(i)
                                        break
                            elif y >= height-5:  # Bottom edge sample
                                for i in range(height-20, height-150, -5):
                                    if i < 0:
                                        break
                                    if frame_rgba.getpixel((x, i))[3] < 100:
                                        border_samples.append(height - i)
                                        break
                except Exception as e:
                    continue  # Skip problematic pixels
        
        # Use the median value for more stability (or minimum 60px if detection fails)
        if border_samples:
            border_samples.sort()
            frame_border_width = border_samples[len(border_samples)//2]  # Median
            # Add safety margin
            frame_border_width += 20
        else:
            frame_border_width = 60  # Conservative default
        
        print(f"Detected frame border width: {frame_border_width}px")
    
    # Add semi-transparent gray overlay over the entire image (with reduced opacity)
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(0, 0), (width, height)], 
                           fill=(50, 50, 50, 140))  # Semi-transparent gray with reduced opacity
    
    # Paste overlay onto the image
    img_with_overlay = Image.alpha_composite(img_with_overlay.convert('RGBA'), overlay)
    
    # Add logo overlay
    try:
        # Check if user wants a logo at all
        use_logo = False  # Default to no logo unless user has explicitly uploaded one
        
        # For video frames: Check for custom uploaded logo only
        video_logo_path = "cache/custom/logo.png"
        
        # Only use a logo if the user has explicitly uploaded one
        if os.path.exists(video_logo_path):
            use_logo = True
        
        if use_logo and os.path.exists(video_logo_path):
            logo = Image.open(video_logo_path)
            # Resize logo to be x of image width, maintaining aspect ratio
            logo_width = int(width * 0.4)  # percentage of image width
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # Calculate position to center logo at the top with some margin
            logo_x = (width - logo_width) // 2
            logo_y = int(height * 0.10)  # distance from the top
            
            # Make sure logo has alpha channel for proper overlay
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
                
            # Paste logo onto the image
            img_with_overlay.paste(logo, (logo_x, logo_y), logo)
            print(f"Added logo from {video_logo_path} to video frame")
        else:
            print("No logo will be added to video frame - user did not upload a logo")
    except Exception as e:
        print(f"Could not add logo to video frame: {e}")
    
    # --- Font Loading START ---
    # Try to load Leelawadee Bold from system fonts first (Windows has it by default)
    # or fall back to the bundled TTF file
    system_font_names = ["Leelawadee Bold", "Leelawadee UI Bold", "Arial Bold", "Segoe UI Bold"]
    bundled_font_path = "fonts/Leelawadee Bold.ttf"
    final_font_path = None

    # Determine safe margins based on frame existence
    left_margin = int(width * 0.15) if frame_exists else int(width * 0.08)
    right_margin = int(width * 0.20) if frame_exists else int(width * 0.10)  # Increase right margin
    bottom_margin = int(height * 0.15) if frame_exists else int(height * 0.08)
    top_margin = int(height * 0.35)  # Keep more space at top for logo and title

    # If we detected a substantial frame border, use it to inform margins
    if frame_border_width > 0:
        left_margin = max(left_margin, frame_border_width + 30)
        right_margin = max(right_margin, frame_border_width + 50)  # Extra padding on right
        bottom_margin = max(bottom_margin, frame_border_width + 30)

    # Calculate maximum width for text - use a more conservative width
    max_text_width = width - (left_margin + right_margin + 40)  # Extra 40px safety margin

    # Set an upper limit to text height based on remaining vertical space
    max_text_height = height - top_margin - bottom_margin

    # Calculate font size adaptively
    initial_font_size = max(int(width * 0.055), 46)
    font_size = initial_font_size
    font = None

    # Try to fit text with current font size, reduce if necessary
    text_too_large = True
    min_font_size = 30  # Don't go smaller than this
    attempt = 0
    final_font_path = None # Keep track of the font path that works

    while text_too_large and font_size > min_font_size and attempt < 5:
        attempt += 1
        try:
            # Try system fonts first in order of preference
            font_loaded = False
            for system_font in system_font_names:
                try:
                    font = ImageFont.truetype(system_font, font_size)
                    final_font_path = system_font
                    font_loaded = True
                    print(f"Using system font: {system_font} at size {font_size}px")
                    break
                except Exception:
                    continue  # Try next font in list
                    
            # If system fonts failed, try bundled font file
            if not font_loaded and os.path.exists(bundled_font_path):
                font = ImageFont.truetype(bundled_font_path, font_size)
                final_font_path = bundled_font_path
                font_loaded = True
                print(f"Using bundled font: {bundled_font_path} at size {font_size}px")
                
            # If still no success, use default font
            if not font_loaded:
                font = ImageFont.load_default().font_variant(size=font_size)
                final_font_path = "Default font"
                font_loaded = True
                print(f"Using default font at size {font_size}px")

            # Use smart text wrapping based on pixel measurements
            wrapped_lines = smart_wrap_text(text, font, max_text_width, draw)

            # Calculate total text height with this font
            estimated_text_height = len(wrapped_lines) * font_size * 1.1 + (font_size * 1.2)  # Add padding

            # Check if it fits in allowed vertical space
            if estimated_text_height <= max_text_height:
                text_too_large = False
                print(f"Using font size {font_size}px after {attempt} attempts - text fits")
            else:
                # Reduce font size by 10% and try again
                font_size = int(font_size * 0.9)
                print(f"Reducing font size to {font_size}px - text too large")

        except Exception as e:
            print(f"Error during font loading: {e}")
            # Reduce font size and try again
            font_size = int(font_size * 0.9)
            # If all attempts fail with current font size, try using default font
            try:
                font = ImageFont.load_default().font_variant(size=font_size)
                final_font_path = "Default font"
                print(f"Falling back to default font at size {font_size}px")
            except:
                print("ERROR: Unable to load any font.")
                font = ImageFont.load_default()
                final_font_path = "Default font (Minimal)"
                font_size = 20  # Use a small default size

    # Ensure font is not None before proceeding
    if font is None:
        print("ERROR: Font object is None. Using absolute default.")
        font = ImageFont.load_default()
        final_font_path = "Pillow Default (Final Fallback)"
        font_size = 20 # Use a small default size

    print(f"Final font used: {final_font_path} at {font_size}px")
    # --- Font Loading END ---

    # Get final text wrapping with the chosen font size
    lines = smart_wrap_text(text, font, max_text_width, draw)
    
    # Find keywords to highlight in green (words in quotes)
    # Update regex to handle multiple quote patterns:
    # 1. Regular quotes: "word"
    # 2. Escaped quotes from JSON: \"word\"
    # 3. Double-escaped quotes: \\"word\\"
    green_words_pattern = r'(?:"([^"]+)"|\\+"([^"]+)\\+"|\\\\+"([^"]+)\\\\+")'
    
    green_word_matches = re.findall(green_words_pattern, text)
    
    # Process matches - each match is a tuple with groups for different quote styles
    # We need to extract the actual word from whichever group matched
    green_words = []
    for match_groups in green_word_matches:
        # Find the non-empty group in the match
        for group in match_groups:
            if group:
                green_words.append(group)
                break
    
    # Process text with highlighted parts
    has_highlights = len(green_words) > 0
    
    # Remove quotation marks from the display text
    display_text = text
    if has_highlights:
        for word in green_words:
            # Replace quoted words with just the words (no quotes)
            # Handle different quotation patterns
            display_text = re.sub(f'"{word}"', word, display_text)
            display_text = re.sub(f'\\\\"?{word}\\\\"?', word, display_text)
    
    # Calculate text positioning for left alignment
    text_x = left_margin  # Left margin
    
    # Position in bottom portion with safe margin
    # Adjust position to ensure text doesn't go below safe area
    text_height_total = len(lines) * font_size * 1.1  # Calculate total text height
    
    # Center text vertically in the available space below the logo area
    available_height = height - top_margin - bottom_margin
    text_y = top_margin + (available_height - text_height_total) // 2
    
    # Ensure text stays within bounds
    text_y = max(text_y, top_margin)
    text_y = min(text_y, height - bottom_margin - text_height_total)
    
    print(f"Text positioning: x={text_x}, y={text_y}, width={max_text_width}, height={text_height_total}")
    print(f"Image borders: left={left_margin}, right={right_margin}, top={top_margin}, bottom={bottom_margin}")

    # Add a blurred dark background behind the text for better visibility
    text_height = len(lines) * font_size * 1.1  # Tight line spacing (1.1)
    
    # Calculate text background dimensions with safe margins
    bg_padding_x = int(font_size * 0.6)  # Horizontal padding
    bg_padding_y = int(font_size * 0.6)  # Vertical padding
    
    # Ensure background stays within frame margins
    bg_x0 = max(text_x - bg_padding_x, left_margin - 10)
    bg_y0 = max(text_y - bg_padding_y, top_margin - 10)
    bg_x1 = min(text_x + max_text_width + bg_padding_x, width - right_margin + 10)
    bg_y1 = min(text_y + text_height + bg_padding_y, height - bottom_margin + 10)
    
    # Create a new layer for the text background
    text_bg = Image.new('RGBA', img.size, (0, 0, 0, 0))
    text_bg_draw = ImageDraw.Draw(text_bg)
    
    # Draw a soft, darker semi-transparent background
    corner_radius = int(font_size * 0.3)  # Rounded corners
    
    # Draw the rounded rectangle
    text_bg_draw.rounded_rectangle(
        [bg_x0, bg_y0, bg_x1, bg_y1],
        radius=corner_radius,
        fill=(0, 0, 0, 160)  # Slightly darker for better readability
    )
    
    # Apply a gaussian blur for modern look
    try:
        text_bg = text_bg.filter(ImageFilter.GaussianBlur(radius=corner_radius/2))
    except:
        pass
    
    # Composite the blurred background
    img_with_overlay = Image.alpha_composite(img_with_overlay, text_bg)
    
    # Re-create draw object after compositing
    draw = ImageDraw.Draw(img_with_overlay)
    
    # Draw text line by line with tight spacing (1.1)
    line_y = text_y
    
    # Update the smart_wrap_text to use the display_text without quotes
    display_lines = smart_wrap_text(display_text, font, max_text_width, draw)
    
    for line in display_lines:
        # Force additional text wrap check to catch any lines that might be too long
        if font.getlength(line) > max_text_width:
            # If line is still too long, use our smart wrapping to break it again
            sub_lines = smart_wrap_text(line, font, max_text_width, draw)
            for sub_line in sub_lines:
                # Check if this line contains any words to highlight
                if has_highlights:
                    # Draw highlighted words in green, rest in white
                    current_x = text_x
                    
                    # Split the line into parts that need different colors
                    parts = []
                    last_end = 0
                    
                    # Process line to highlight keywords without showing quotation marks
                    for word in green_words:
                        # Find the word in the line
                        word_index = sub_line.find(word)
                        while word_index != -1:
                            # Add text before the keyword
                            if word_index > last_end:
                                parts.append((sub_line[last_end:word_index], "white"))
                            
                            # Add the keyword in green
                            parts.append((word, "green"))
                            
                            # Update last_end and search for next occurrence
                            last_end = word_index + len(word)
                            word_index = sub_line.find(word, last_end)
                    
                    # Add any remaining text
                    if last_end < len(sub_line):
                        parts.append((sub_line[last_end:], "white"))
                        
                    # Draw each part with its color - ensure it stays within bounds
                    for part_text, color in parts:
                        # Calculate width of this part
                        part_bbox = draw.textbbox((0, 0), part_text, font=font)
                        part_width = part_bbox[2] - part_bbox[0]
                        
                        # Skip if this would go beyond right margin
                        if current_x + part_width > width - right_margin:
                            break
                            
                        # Calculate dynamic shadow based on text size and content type
                        prominence = 1.2 if color == "green" else 1.0  # Highlighted text gets stronger shadow
                        shadow_offset, shadow_opacity = calculate_shadow(font_size, prominence)
                        
                        # Draw dynamic shadow for better readability
                        draw.text((current_x + shadow_offset, line_y + shadow_offset), 
                                 part_text, font=font, fill=(0, 0, 0, shadow_opacity))
                        
                        # Draw the text in the appropriate color
                        if color == "green":
                            draw.text((current_x, line_y), part_text, font=font, fill="#79C910")  # Updated color
                        else:
                            draw.text((current_x, line_y), part_text, font=font, fill="#FFFFFF")
                        
                        # Move x position for next part
                        current_x += part_width
                else:
                    # Skip if this line would be too long
                    if font.getlength(sub_line) > max_text_width:
                        sub_line = sub_line[:int(len(sub_line) * 0.9)] + "..."
                    
                    # Calculate dynamic shadow for regular text
                    shadow_offset, shadow_opacity = calculate_shadow(font_size, 1.0)
                    
                    # No highlights - draw entire line in white with shadow
                    # Dynamic shadow for better readability
                    draw.text((text_x + shadow_offset, line_y + shadow_offset), 
                             sub_line, font=font, fill=(0, 0, 0, shadow_opacity))
                    
                    # Draw the text in white
                    draw.text((text_x, line_y), sub_line, font=font, fill="#FFFFFF")
                
                # Move to next line with tight spacing (1.1)
                line_y += font_size * 1.1
                
                # Safety check - stop if we're getting too close to bottom
                if line_y > height - bottom_margin:
                    break
            
        else:
            # Original handling for lines that fit
            if has_highlights:
                # Process as before
                # Draw highlighted words in green, rest in white
                current_x = text_x
                
                # Split the line into parts that need different colors
                parts = []
                last_end = 0
                
                # Process line to highlight keywords without showing quotation marks
                for word in green_words:
                    # Find the word in the line
                    word_index = line.find(word)
                    while word_index != -1:
                        # Add text before the keyword
                        if word_index > last_end:
                            parts.append((line[last_end:word_index], "white"))
                        
                        # Add the keyword in green
                        parts.append((word, "green"))
                        
                        # Update last_end and search for next occurrence
                        last_end = word_index + len(word)
                        word_index = line.find(word, last_end)
                
                # Add any remaining text
                if last_end < len(line):
                    parts.append((line[last_end:], "white"))
                    
                # Draw each part with its color
                for part_text, color in parts:
                    # Calculate width of this part
                    part_bbox = draw.textbbox((0, 0), part_text, font=font)
                    part_width = part_bbox[2] - part_bbox[0]
                    
                    # Skip if this would go beyond right margin
                    if current_x + part_width > width - right_margin:
                        break
                    
                    # Calculate dynamic shadow based on text size and content type
                    prominence = 1.2 if color == "green" else 1.0  # Highlighted text gets stronger shadow
                    shadow_offset, shadow_opacity = calculate_shadow(font_size, prominence)
                    
                    # Draw dynamic shadow for better readability
                    draw.text((current_x + shadow_offset, line_y + shadow_offset), 
                             part_text, font=font, fill=(0, 0, 0, shadow_opacity))
                    
                    # Draw the text in the appropriate color
                    if color == "green":
                        draw.text((current_x, line_y), part_text, font=font, fill="#79C910")  # Updated color
                    else:
                        draw.text((current_x, line_y), part_text, font=font, fill="#FFFFFF")
                    
                    # Move x position for next part
                    current_x += part_width
            else:
                # Calculate dynamic shadow for regular text
                shadow_offset, shadow_opacity = calculate_shadow(font_size, 1.0)
                
                # No highlights - draw entire line in white with shadow
                # Dynamic shadow for better readability
                draw.text((text_x + shadow_offset, line_y + shadow_offset), 
                         line, font=font, fill=(0, 0, 0, shadow_opacity))
                
                # Draw the text in white
                draw.text((text_x, line_y), line, font=font, fill="#FFFFFF")
            
            # Move to next line with tight spacing (1.1)
            line_y += font_size * 1.1
            
            # Safety check - stop if we're getting too close to bottom
            if line_y > height - bottom_margin:
                break
    
    # Apply frame overlay if it exists (last step to ensure it's on top of everything)
    try:
        # Check if user wants a frame
        use_frame = False  # Default to no frame unless user has explicitly uploaded one
        
        # Check for custom frame only
        frame_path = "cache/custom/frame.png"
        
        # Only use a frame if the user has explicitly uploaded one
        if os.path.exists(frame_path):
            use_frame = True
        
        if use_frame and os.path.exists(frame_path):
            # Load frame image
            frame = Image.open(frame_path)
            
            # Ensure frame has correct dimensions
            if frame.width != width or frame.height != height:
                frame = frame.resize((width, height), Image.LANCZOS)
            
            # Make sure frame has alpha channel for proper overlay
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')
                
            # Create a new image with the frame overlaid
            img_with_frame = Image.alpha_composite(img_with_overlay, frame)
            img_with_overlay = img_with_frame
            print(f"Added frame overlay from {frame_path} to video frame")
        else:
            print("No frame overlay will be added - user did not upload a frame")
    except Exception as e:
        print(f"Could not add frame overlay to video frame: {e}")
    
    # Save the image
    img_with_overlay.convert('RGB').save(output_path)
    print(f"Collage saved to {output_path}") 