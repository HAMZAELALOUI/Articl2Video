from json_utils import fix_json_quotes, additional_json_cleanup, save_and_clean_json
import json
import sys
from io import StringIO

# Redirect stdout to capture output
old_stdout = sys.stdout
redirected_output = StringIO()
sys.stdout = redirected_output

# Test cases with common JSON errors
test_cases = [
    # Case 1: Unescaped quotes within string values
    '{"summary": ["Text with "inner quotes" that break JSON"]}',
    
    # Case 2: Missing commas between items
    '{"summary": ["First item" "Second item"]}',
    
    # Case 3: Unclosed bracket
    '{"summary": ["Text with unclosed bracket", "Another item"',
    
    # Case 4: Double-escaped quotes (common from LLMs)
    '{"summary": ["Text with \\"double escaped\\" quotes"]}',
    
    # Case 5: Trailing comma before closing bracket
    '{"summary": ["Item 1", "Item 2", ]}',
    
    # Case 6: Nested quotes with different escaping
    '{"summary": ["Tensions diplomatiques s\'intensifient après que la \\"Chine\\" accuse", "La délégation américaine rencontre les \"autorités taiwanaises\""]}',
]

print("Testing JSON fixing functions...")
print("-------------------------------")

for i, test_json in enumerate(test_cases, 1):
    print(f"\nTest Case {i}:")
    print(f"Original: {test_json}")
    
    # Test fix_json_quotes
    fixed = fix_json_quotes(test_json)
    print(f"After fix_json_quotes: {fixed}")
    
    # Try to parse it
    try:
        parsed = json.loads(fixed)
        print("✅ Successfully parsed!")
        print(f"Parsed result: {parsed}")
    except json.JSONDecodeError as e:
        print(f"❌ Still has JSON errors: {e}")
        
        # Try additional_json_cleanup
        print("Applying additional_json_cleanup...")
        cleaned = additional_json_cleanup(fixed)
        print(f"After cleanup: {cleaned}")
        
        try:
            parsed = json.loads(cleaned)
            print("✅ Successfully parsed after additional cleanup!")
            print(f"Parsed result: {parsed}")
        except json.JSONDecodeError as e:
            print(f"❌ Still failed to parse: {e}")
    
    print("-------------------------------")

print("\nTesting save_and_clean_json with a complex case...")
complex_case = '''
{
  "summary": [
    "Premier point: La "Chine" a des tensions avec les "États-Unis" sur "Taiwan".",
    "Deuxième point: Les négociations continuent malgré les "défis diplomatiques" actuels."
  ],
  "total": "2",
  "tone": "Informative"
}
'''

result = save_and_clean_json(complex_case, "test_output.json")
print(f"save_and_clean_json result: {result}")

# Try to read the saved file
try:
    with open("test_output.json", "r", encoding="utf-8") as f:
        saved_content = f.read()
        print(f"Saved file content: {saved_content}")
except Exception as e:
    print(f"Error reading saved file: {e}")

print("\nTests completed!")

# Restore stdout
sys.stdout = old_stdout

# Write results to a file
output = redirected_output.getvalue()
with open("json_test_results.txt", "w", encoding="utf-8") as f:
    f.write(output)

print("Test completed! Results written to json_test_results.txt") 