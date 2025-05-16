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
    # First try a simpler approach: direct JSON loading
    try:
        json.loads(json_text)
        return json_text  # If it loads fine, no need to fix
    except json.JSONDecodeError:
        # Continue with fixes if there are issues
        pass
    
    # Handle escaped quotes with a more reliable approach
    try:
        # Replace any triple backslashes (artifact of multiple escapes) with a temp marker
        temp_triple = "%%TRIPLE_ESCAPE%%"
        json_text = json_text.replace('\\\\\\', temp_triple)
        
        # Replace double backslashes with a temp marker
        temp_double = "%%DOUBLE_ESCAPE%%"
        json_text = json_text.replace('\\\\', temp_double)
        
        # Replace escaped quotes with a temp marker
        temp_quote = "%%ESCAPED_QUOTE%%"
        json_text = json_text.replace('\\"', temp_quote)
        
        # First pass: fix unescaped quotes inside JSON string values
        in_string = False
        result = []
        i = 0
        
        while i < len(json_text):
            char = json_text[i]
            
            # Handle opening/closing quotes
            if char == '"':
                # Check if this is an escape sequence
                if i > 0 and json_text[i-1] == '\\':
                    # This is an escaped quote, add it as is
                    result.append(char)
                else:
                    # This is a string boundary
                    in_string = not in_string
                    result.append(char)
            # Handle quotes inside strings
            elif char == '"' and in_string:
                # Add an escaped quote
                result.append('\\"')
            else:
                result.append(char)
            
            i += 1
        
        processed_text = ''.join(result)
        
        # Restore temp markers
        processed_text = processed_text.replace(temp_triple, '\\\\\\')
        processed_text = processed_text.replace(temp_double, '\\\\')
        processed_text = processed_text.replace(temp_quote, '\\"')
        
        # Second approach: use regex to find and fix common quote issues
        try:
            # Fix common issues with unescaped quotes in a complete JSON structure
            # Find all string literals and fix quotes inside them
            string_pattern = r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\''
            
            def fix_string(match):
                # Get the matched string without the outer quotes
                string_content = match.group(1) or match.group(2)
                # Replace any unescaped quotes with escaped quotes
                fixed_content = string_content.replace('"', '\\"')
                # Return with proper quotes
                return f'"{fixed_content}"'
            
            processed_text = re.sub(string_pattern, fix_string, processed_text)
            
            # Fix issues with missing commas between properties
            processed_text = re.sub(r'(\w+)"(\s*)"(\w+)', r'\1",\2"\3', processed_text)
            
            # Fix issue with trailing comma
            processed_text = re.sub(r',(\s*)}', r'\1}', processed_text)
            processed_text = re.sub(r',(\s*)]', r'\1]', processed_text)
        except Exception as e:
            print(f"Regex string fixing failed: {e}")
                
        return processed_text
    except Exception as e:
        print(f"Quote fixing failed: {e}")
        return json_text


def additional_json_cleanup(json_text):
    """
    Apply additional cleanup to try to fix broken JSON.
    
    Args:
        json_text (str): JSON text with potential errors
        
    Returns:
        str: Cleaned JSON text
    """
    # First try with simplified whitespace
    try:
        # Remove all newlines and excessive whitespace
        simplified = ' '.join(json_text.replace('\n', ' ').split())
        json.loads(simplified)
        return simplified
    except json.JSONDecodeError:
        # Continue with more aggressive fixes
        pass
    
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
        
        # Try to fix specific JSON structure issues
        # This handles cases where quotes are improperly terminated or commas are missing
        json_text = re.sub(r'([^\\])""', r'\1","', json_text)
        
        # Fix missing colons after property names
        json_text = re.sub(r'"([^"]+)"\s+(?=["{\[])', r'"\1": ', json_text)
        
        # Sometimes LLMs add extra text outside the JSON structure - try to extract just the JSON
        json_match = re.search(r'({[\s\S]*})', json_text)
        if json_match:
            potential_json = json_match.group(1)
            try:
                # See if this extracted part is valid JSON
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                # Continue with the original text if extraction didn't work
                pass
        
        # For debugging purposes
        print(f"Cleaned JSON (first 100 chars): {json_text[:100]}...")
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
        # If response is already a dict, just save it
        if isinstance(response, dict):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=4)
            return response
            
        # Handle string responses with multiple cleanup steps
        if isinstance(response, str):
            # First try direct parsing
            try:
                parsed_response = json.loads(response)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_response, f, ensure_ascii=False, indent=4)
                return parsed_response
            except json.JSONDecodeError as e:
                print(f"Initial JSON parsing failed: {e}")
                
                # Try with quote fixing
                try:
                    fixed_response = fix_json_quotes(response)
                    parsed_response = json.loads(fixed_response)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed_response, f, ensure_ascii=False, indent=4)
                    return parsed_response
                except json.JSONDecodeError as e:
                    print(f"Quote fixing failed to parse: {e}")
                    
                    # Try aggressive cleanup
                    try:
                        cleaned_response = additional_json_cleanup(response)
                        parsed_response = json.loads(cleaned_response)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(parsed_response, f, ensure_ascii=False, indent=4)
                        return parsed_response
                    except json.JSONDecodeError as e:
                        print(f"Additional cleanup failed: {e}")
                        
                        # Last resort: try to manually extract the JSON structure
                        try:
                            # Look for the basic JSON structure pattern
                            json_pattern = re.compile(r'({[\s\S]*})')
                            match = json_pattern.search(response)
                            if match:
                                extracted_json = match.group(1)
                                parsed_response = json.loads(extracted_json)
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    json.dump(parsed_response, f, ensure_ascii=False, indent=4)
                                return parsed_response
                        except Exception as e:
                            print(f"Manual extraction failed: {e}")
                            
        # Fallback response if all parsing attempts fail
        fallback_response = {
            "summary": [f"Error processing response. JSON parsing failed."],
            "total": "0",
            "tone": "Neutral"
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(fallback_response, f, ensure_ascii=False, indent=4)
            
        return fallback_response
                
    except Exception as e:
        print(f"Error saving and cleaning JSON: {str(e)}")
        # Return a fallback response with error message
        fallback_response = {
            "summary": [f"Error processing response: {str(e)}"],
            "total": "0",
            "tone": "Neutral"
        }
        
        # Try to save the fallback response
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(fallback_response, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
            
        return fallback_response 