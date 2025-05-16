import json
import re

def fix_json_quotes(json_text):
    """
    Fix issues with quotes in JSON text that might cause parsing errors.
    
    Args:
        json_text (str): JSON text with potential quote issues
        
    Returns:
        str: Fixed JSON text
    """
    # Replace unescaped quotes within quotes with escaped quotes
    # This is a complex problem, but we'll try a simple approach
    
    # First convert any pairs of escaped quotes to a temporary marker
    temp_marker = "%%ESCAPED_QUOTE%%"
    json_text = json_text.replace('\\"', temp_marker)
    
    # Find all string values in JSON and fix any unescaped quotes within them
    fixed_parts = []
    i = 0
    in_string = False
    start_quote_pos = -1
    
    while i < len(json_text):
        if json_text[i] == '"' and (i == 0 or json_text[i-1] != '\\'):
            # This is an unescaped quote
            if not in_string:
                # Start of a string
                in_string = True
                start_quote_pos = i
                fixed_parts.append(json_text[i])
            else:
                # End of a string
                in_string = False
                fixed_parts.append(json_text[i])
        elif json_text[i] == '"' and in_string and json_text[i-1] != '\\':
            # This is an unescaped quote within a string - escape it
            fixed_parts.append('\\"')
        else:
            fixed_parts.append(json_text[i])
        i += 1
    
    # Convert back the temporary markers to properly escaped quotes
    json_text = ''.join(fixed_parts).replace(temp_marker, '\\"')
    
    # As a fallback, try a simpler regex approach
    # This should catch most of the common cases
    try:
        # Find parts that look like: "text "inner quote" more text"
        # and replace with: "text \"inner quote\" more text"
        json_text = re.sub(r'(?<="[^"]*)"([^"]*)"(?=[^"]*")', r'\\\"\1\\\"', json_text)
    except Exception as e:
        print(f"Regex cleanup failed: {e}")
    
    return json_text


def additional_json_cleanup(json_text):
    """
    Apply additional cleanup to try to fix broken JSON.
    
    Args:
        json_text (str): JSON text with potential errors
        
    Returns:
        str: Cleaned JSON text
    """
    # Fix common issues with nested quotes
    
    try:
        # Sometimes the model adds unnecessary escaping to already escaped quotes
        json_text = json_text.replace('\\\\"', '\\"')
        
        # Fix any brackets or braces that don't have matching pairs
        # Count the brackets and braces
        open_curly = json_text.count('{')
        close_curly = json_text.count('}')
        open_square = json_text.count('[')
        close_square = json_text.count(']')
        
        # If there are more opening than closing brackets, add the missing ones at the end
        if open_curly > close_curly:
            json_text += '}' * (open_curly - close_curly)
        if open_square > close_square:
            json_text += ']' * (open_square - close_square)
            
        # Remove trailing commas before closing brackets or braces (common JSON error)
        json_text = re.sub(r',\s*}', '}', json_text)
        json_text = re.sub(r',\s*]', ']', json_text)
        
        # Try to fix unescaped quotes in strings using regex patterns
        # This pattern looks for quoted strings and attempts to fix inner quotes
        json_text = re.sub(r'(?<="[^"\\]*)"(?=[^"\\]*")', r'\\"', json_text)
        
        # For debugging purposes
        print(f"Cleaned JSON: {json_text[:100]}...")
    except Exception as e:
        print(f"Error in additional JSON cleanup: {e}")
    
    return json_text


def save_and_clean_json(response, file_path):
    """
    Save and clean JSON data, handling various error cases.
    
    Args:
        response: Response from LLM API (can be dict or string)
        file_path: Path to save the JSON file
        
    Returns:
        dict: Cleaned JSON data
    """
    try:
        # First, handle the case where response is a string
        if isinstance(response, str):
            # Try to fix potential JSON issues before parsing
            try:
                response = fix_json_quotes(response)
                response = json.loads(response.replace('\n', '').replace('\\', ''))
            except json.JSONDecodeError:
                # If that fails, try more aggressive cleanup
                cleaned_response = additional_json_cleanup(response.replace('\n', ''))
                response = json.loads(cleaned_response)
        
        # If response is a dict and contains 'response' key
        if isinstance(response, dict) and 'response' in response:
            response = response['response']
            # If response is still a string, parse it
            if isinstance(response, str):
                try:
                    response = fix_json_quotes(response)
                    response = json.loads(response.replace('\n', '').replace('\\', ''))
                except json.JSONDecodeError:
                    # If that fails, try more aggressive cleanup
                    cleaned_response = additional_json_cleanup(response.replace('\n', ''))
                    response = json.loads(cleaned_response)

        # Write the cleaned JSON to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=4)
        
        return response
    except Exception as e:
        print(f"Error saving and cleaning JSON: {str(e)}")
        # Return a fallback response with error message
        return {
            "summary": [f"Error processing response: {str(e)}"],
            "Total": "0",
            "Tone": "Neutral"
        } 