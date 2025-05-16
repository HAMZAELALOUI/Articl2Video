import os
import json
from json import loads
import re
import unicodedata
from json_utils import fix_json_quotes, additional_json_cleanup
from prompts import get_openai_summarization_prompt
from openai_client import summarize_with_openai

# Configure Gemini API using environment variable is no longer needed since we're using OpenAI
# But we'll keep it for compatibility with other functions
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("Warning: GEMINI_API_KEY environment variable not found. But it's not used for summarization anymore.")
    # No need to raise an error since we're not using Gemini for summarization

def call_llm_api(article_text, slidenumber, wordnumber, language):
    """
    Call the LLM API to generate bullet points summarizing an article.
    Now uses OpenAI instead of Gemini.
    
    Args:
        article_text (str): The text of the article to summarize
        slidenumber (int): The number of bullet points to generate
        wordnumber (int): The max number of words per bullet point
        language (str): The language to generate the summary in
        
    Returns:
        dict: The generated summary data
    """
    try:
        # Call OpenAI directly for summarization
        print(f"Using OpenAI for text summarization in {language}...")
        result = summarize_with_openai(article_text, slidenumber, wordnumber, language)
        return result
        
    except Exception as e:
        print(f"Error in OpenAI API call: {str(e)}")
        # Return a fallback response with error message
        return {
            "summary": [f"Error generating summary: {str(e)}"],
            "total": "0",
            "tone": "Neutral"
        }


def fix_unicode(text):
    """
    Replace Unicode escape sequences with their actual characters.
    
    Args:
        text (str): Text with potential Unicode escape sequences
        
    Returns:
        str: Text with Unicode characters properly displayed
    """
    # Preprocess text - replace common Unicode characters
    # French characters
    text = text.replace('\\u00e9', 'é').replace('\\u00e8', 'è').replace('\\u00ea', 'ê')
    text = text.replace('\\u00e0', 'à').replace('\\u00e2', 'â').replace('\\u00f9', 'ù')
    text = text.replace('\\u00fb', 'û').replace('\\u00ee', 'î').replace('\\u00ef', 'ï')
    text = text.replace('\\u00e7', 'ç').replace('\\u0153', 'œ').replace('\\u00e6', 'æ')
    text = text.replace('\\u20ac', '€').replace('\\u00ab', '«').replace('\\u00bb', '»')
    text = text.replace('\\u2013', '–').replace('\\u2014', '—').replace('\\u2018', ''')
    text = text.replace('\\u2019', ''').replace('\\u201a', '‚').replace('\\u201c', '"')
    text = text.replace('\\u201d', '"').replace('\\u201e', '„').replace('\\u2026', '…')
    text = text.replace('\\u2030', '‰').replace('\\u0152', 'Œ').replace('\\u00a0', ' ')
    text = text.replace('\\u00b0', '°').replace('\\u00a3', '£').replace('\\u00a7', '§')
    text = text.replace('\\u00b7', '·').replace('\\u00bf', '¿').replace('\\u00a9', '©')
    text = text.replace('\\u00ae', '®').replace('\\u2122', '™').replace('\\u00bc', '¼')
    text = text.replace('\\u00bd', '½').replace('\\u00be', '¾').replace('\\u00b1', '±')
    text = text.replace('\\u00d7', '×').replace('\\u00f7', '÷').replace('\\u00a2', '¢')
    text = text.replace('\\u00a5', '¥').replace('\\u00ac', '¬').replace('\\u00b6', '¶')
    text = text.replace('\\u2022', '•')

    # Spanish characters
    text = text.replace('\\u00f1', 'ñ').replace('\\u00ed', 'í').replace('\\u00f3', 'ó')
    text = text.replace('\\u00fa', 'ú').replace('\\u00fc', 'ü').replace('\\u00a1', '¡')
    text = text.replace('\\u00bf', '¿').replace('\\u00e1', 'á').replace('\\u00e9', 'é')
    text = text.replace('\\u00f3', 'ó').replace('\\u00fa', 'ú').replace('\\u00fc', 'ü')
    # German characters
    text = text.replace('\\u00df', 'ß').replace('\\u00e4', 'ä').replace('\\u00f6', 'ö')
    text = text.replace('\\u00fc', 'ü')

    # Italian characters
    text = text.replace('\\u00e0', 'à').replace('\\u00e8', 'è').replace('\\u00e9', 'é')
    text = text.replace('\\u00ec', 'ì').replace('\\u00f2', 'ò').replace('\\u00f9', 'ù')
    text = text.replace('\\u00f9', 'ù')

    # Russian characters
    text = text.replace('\\u0410', 'А').replace('\\u0411', 'Б').replace('\\u0412', 'В')
    text = text.replace('\\u0413', 'Г').replace('\\u0414', 'Д').replace('\\u0415', 'Е')
    text = text.replace('\\u0416', 'Ж').replace('\\u0417', 'З').replace('\\u0418', 'И')
    text = text.replace('\\u0419', 'Й').replace('\\u041a', 'К').replace('\\u041b', 'Л')
    text = text.replace('\\u041c', 'М').replace('\\u041d', 'Н').replace('\\u041e', 'О')
    text = text.replace('\\u041f', 'П').replace('\\u0420', 'Р').replace('\\u0421', 'С')
    text = text.replace('\\u0422', 'Т').replace('\\u0423', 'У').replace('\\u0424', 'Ф')
    text = text.replace('\\u0425', 'Х').replace('\\u0426', 'Ц').replace('\\u0427', 'Ч')
    text = text.replace('\\u0428', 'Ш').replace('\\u0429', 'Щ').replace('\\u042a', 'Ъ')
    text = text.replace('\\u042b', 'Ы').replace('\\u042c', 'Ь').replace('\\u042d', 'Э')
    text = text.replace('\\u042e', 'Ю').replace('\\u042f', 'Я').replace('\\u0430', 'а')
    text = text.replace('\\u0431', 'б').replace('\\u0432', 'в').replace('\\u0433', 'г')
    text = text.replace('\\u0434', 'д').replace('\\u0435', 'е').replace('\\u0436', 'ж')
    text = text.replace('\\u0437', 'з').replace('\\u0438', 'и').replace('\\u0439', 'й')
    text = text.replace('\\u043a', 'к').replace('\\u043b', 'л').replace('\\u043c', 'м')
    text = text.replace('\\u043d', 'н').replace('\\u043e', 'о').replace('\\u043f', 'п')
    text = text.replace('\\u0440', 'р').replace('\\u0441', 'с').replace('\\u0442', 'т')
    text = text.replace('\\u0443', 'у').replace('\\u0444', 'ф').replace('\\u0445', 'х')
    text = text.replace('\\u0446', 'ц').replace('\\u0447', 'ч').replace('\\u0448', 'ш')
    text = text.replace('\\u0449', 'щ').replace('\\u044a', 'ъ').replace('\\u044b', 'ы')
    text = text.replace('\\u044c', 'ь').replace('\\u044d', 'э').replace('\\u044e', 'ю')
    text = text.replace('\\u044f', 'я')
    
    # Arabic characters - generic replacement for common encoding issues
    text = text.replace('\\u0627', 'ا').replace('\\u064a', 'ي').replace('\\u0644', 'ل')
    text = text.replace('\\u062a', 'ت').replace('\\u0646', 'ن').replace('\\u0633', 'س')
    text = text.replace('\\u0645', 'م').replace('\\u0631', 'ر').replace('\\u0648', 'و')
    text = text.replace('\\u0639', 'ع').replace('\\u062f', 'د').replace('\\u0628', 'ب')
    text = text.replace('\\u0649', 'ى').replace('\\u0629', 'ة').replace('\\u062c', 'ج')
    text = text.replace('\\u0642', 'ق').replace('\\u0641', 'ف').replace('\\u062d', 'ح')
    text = text.replace('\\u0635', 'ص').replace('\\u0637', 'ط').replace('\\u0632', 'ز')
    text = text.replace('\\u0634', 'ش').replace('\\u063a', 'غ').replace('\\u062e', 'خ')
    text = text.replace('\\u0623', 'أ').replace('\\u0621', 'ء').replace('\\u0624', 'ؤ')
    text = text.replace('\\u0626', 'ئ').replace('\\u0625', 'إ').replace('\\u0651', 'ّ')
    text = text.replace('\\u0652', 'ْ').replace('\\u064b', 'ً').replace('\\u064c', 'ٌ')
    text = text.replace('\\u064d', 'ٍ').replace('\\u064f', 'ُ').replace('\\u0650', 'ِ')
    text = text.replace('\\u064e', 'َ').replace('\\u0653', 'ٓ').replace('\\u0654', 'ٔ')
    text = text.replace('\\u0670', 'ٰ').replace('\\u0671', 'ٱ').replace('\\u0672', 'ٲ')
    text = text.replace('\\u0673', 'ٳ').replace('\\u0675', 'ٵ').replace('\\u0676', 'ٶ')
    text = text.replace('\\u0677', 'ٷ').replace('\\u0678', 'ٸ').replace('\\u0679', 'ٹ')
    text = text.replace('\\u067a', 'ٺ').replace('\\u067b', 'ٻ').replace('\\u067c', 'ټ')
    text = text.replace('\\u067d', 'ٽ').replace('\\u067e', 'پ').replace('\\u067f', 'ٿ')
    text = text.replace('\\u0680', 'ڀ').replace('\\u0681', 'ځ').replace('\\u0682', 'ڂ')
    text = text.replace('\\u0683', 'ڃ').replace('\\u0684', 'ڄ').replace('\\u0685', 'څ')
    text = text.replace('\\u0686', 'چ').replace('\\u0687', 'ڇ').replace('\\u0688', 'ڈ')
    text = text.replace('\\u0689', 'ډ').replace('\\u068a', 'ڊ').replace('\\u068b', 'ڋ')
    text = text.replace('\\u068c', 'ڌ').replace('\\u068d', 'ڍ').replace('\\u068e', 'ڎ')
    text = text.replace('\\u068f', 'ڏ').replace('\\u0690', 'ڐ').replace('\\u0691', 'ڑ')
    text = text.replace('\\u0692', 'ڒ').replace('\\u0693', 'ړ').replace('\\u0694', 'ڔ')
    text = text.replace('\\u0695', 'ڕ').replace('\\u0696', 'ږ').replace('\\u0697', 'ڗ')
    text = text.replace('\\u0698', 'ژ').replace('\\u0699', 'ڙ').replace('\\u069a', 'ښ')
    text = text.replace('\\u069b', 'ڛ').replace('\\u069c', 'ڜ').replace('\\u069d', 'ڝ')
    text = text.replace('\\u069e', 'ڞ').replace('\\u069f', 'ڟ').replace('\\u06a0', 'ڠ')
    text = text.replace('\\u06a1', 'ڡ').replace('\\u06a2', 'ڢ').replace('\\u06a3', 'ڣ')
    text = text.replace('\\u06a4', 'ڤ').replace('\\u06a5', 'ڥ').replace('\\u06a6', 'ڦ')
    text = text.replace('\\u06a7', 'ڧ').replace('\\u06a8', 'ڨ').replace('\\u06a9', 'ک')
    text = text.replace('\\u06aa', 'ڪ').replace('\\u06ab', 'ګ').replace('\\u06ac', 'ڬ')
    text = text.replace('\\u06ad', 'ڭ').replace('\\u06ae', 'ڮ').replace('\\u06af', 'گ')
    text = text.replace('\\u06b0', 'ڰ').replace('\\u06b1', 'ڱ').replace('\\u06b2', 'ڲ')
    text = text.replace('\\u06b3', 'ڳ').replace('\\u06b4', 'ڴ').replace('\\u06b5', 'ڵ')
    text = text.replace('\\u06b6', 'ڶ').replace('\\u06b7', 'ڷ').replace('\\u06b8', 'ڸ')
    text = text.replace('\\u06b9', 'ڹ').replace('\\u06ba', 'ں').replace('\\u06bb', 'ڻ')

    return text


def print_summary_points(data):
    """
    Print the summary points in a formatted way.
    
    Args:
        data (dict): The summary data
    """
    if 'summary' in data:
        for point in data['summary']:
            point = fix_unicode(point)
            print(f"• {point}")

        print(f"\nTotal points: {data.get('Total', 'N/A')}")
        print(f"Recommended tone: {data.get('Tone', 'N/A')}")


def clean_encoding_issues(text):
    """
    Clean text with encoding issues like replacement characters
    
    Args:
        text (str): The text with potential encoding issues
        
    Returns:
        str: Cleaned text
    """
    # Replace replacement character with space
    text = text.replace('\ufffd', ' ')
    
    # Try to normalize unicode characters
    try:
        text = unicodedata.normalize('NFKD', text)
    except Exception as e:
        print(f"Warning: Unicode normalization failed: {e}")
    
    # Manually fix some common encoding issues in French text
    text = text.replace('fractur\ufffd', 'fracturée')
    text = text.replace('pr\ufffd', 'pré')
    text = text.replace('\ufffdchanges', 'échanges')
    text = text.replace('\ufffd', 'é')
    
    # Remove any remaining control characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    return text 