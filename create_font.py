import os
import shutil
import sys
from pathlib import Path

def create_leelawadee_bold():
    """
    Crée un fichier de police Leelawadee Bold.ttf en copiant
    une police Arial Bold ou une autre police disponible
    """
    # Liste des polices candidates à copier (dans l'ordre de préférence)
    candidate_fonts = [
        r"C:\Windows\Fonts\arialbd.ttf",  # Arial Bold
        r"C:\Windows\Fonts\segoeui.ttf",   # Segoe UI
        r"C:\Windows\Fonts\calibrib.ttf",  # Calibri Bold
        r"C:\Windows\Fonts\tahomabd.ttf",  # Tahoma Bold
    ]
    
    # Vérifier si nous devons utiliser le dossier fonts/
    font_dir = "fonts"
    if os.path.exists(font_dir) and os.path.isdir(font_dir):
        # Le dossier fonts existe, utilisons-le
        target_font = os.path.join(font_dir, "Leelawadee Bold.ttf")
    else:
        # Sinon, utilisons le répertoire racine
        target_font = "Leelawadee Bold.ttf"
    
    # Vérifier si le fichier existe déjà
    if os.path.exists(target_font):
        print(f"Le fichier {target_font} existe déjà.")
        return True
    
    # Créer le répertoire fonts s'il n'existe pas et que nous l'utilisons
    if os.path.dirname(target_font) and not os.path.exists(os.path.dirname(target_font)):
        os.makedirs(os.path.dirname(target_font), exist_ok=True)
    
    # Essayer chaque police candidate
    for source_font in candidate_fonts:
        if os.path.exists(source_font):
            try:
                shutil.copy2(source_font, target_font)
                print(f"Police créée avec succès à partir de {source_font}!")
                return True
            except Exception as e:
                print(f"Erreur lors de la copie de {source_font}: {e}")
    
    print(f"Impossible de créer {target_font} - aucune police source trouvée.")
    return False

if __name__ == "__main__":
    create_leelawadee_bold() 