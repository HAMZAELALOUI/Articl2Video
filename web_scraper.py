import requests
from bs4 import BeautifulSoup
import re

def scrape_text_from_url(url):
    """
    Extrait le texte d'une page web à partir de son URL.
    
    Args:
        url (str): L'URL de la page web à scraper
        
    Returns:
        str: Le texte extrait de la page web
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the URL: {url}")
    soup = BeautifulSoup(response.content, 'html.parser')
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()

    return text 