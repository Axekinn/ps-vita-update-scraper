#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

def extract_game_updates(input_file, output_file):
    """
    Extrait uniquement le nom du jeu, la version de l'update et le lien de téléchargement
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    extracted_data = []
    
    for entry in data:
        # Essayer d'abord TITLE, puis ID si TITLE est vide
        title = entry.get('TITLE', '').strip()
        if not title:
            title = entry.get('ID', '').strip()
        
        updates = entry.get('updates', [])
        
        for update in updates:
            if update.get('url'):  # S'assurer qu'il y a un lien de téléchargement
                extracted_entry = {
                    "nom_jeu": title,
                    "version_update": update.get('version', ''),
                    "lien_telechargement": update.get('url', '')
                }
                extracted_data.append(extracted_entry)
    
    # Sauvegarder les données extraites
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)
    
    return len(extracted_data)

if __name__ == "__main__":
    input_file = "ps_vita_updates.json"
    output_file = "ps_vita_updates_extracted.json"
    
    if os.path.exists(input_file):
        count = extract_game_updates(input_file, output_file)
        print(f"Extraction terminée ! {count} mises à jour extraites dans '{output_file}'")
    else:
        print(f"Fichier '{input_file}' non trouvé !")
