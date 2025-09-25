import sys
import os
import time
import json
import socket
import uuid
import platform
import requests
from colorama import Fore, Style, init
from datetime import datetime
import re

from Firefox.__main__ import main_firefox
from Firefox.utils.utils import get_os_info
from treatement.profile_utils import (update_runtime_file, json_Result,json_Result,init_runtime_file,load_profile_from_terminal_validated)

init(autoreset=True)

def search_profile():
    """
    Analyse des données stockées par les navigateurs dans le DOM et les cookies.

    Cette fonction :
    - Récupère le profil utilisateur via un formulaire en ligne de commande.
    - Exécute le traitement des navigateurs supportés (Firefox, Chrome, etc.).
    - Sauvegarde les résultats en JSON (cookies et DOM).
    - Met à jour le fichier `runtime.txt` pour suivre les exécutions.

     Utilisation :
    1. Lancer le script et remplir le formulaire affiché.
    2. Lors d'une nouvelle exécution, supprimer le fichier `runtime.txt` pour réinitialiser le compteur.
    3. Quatre fichiers JSON sont générés :
       - `result_cookies.json` et `result_dom.json` (bruts, avec la colonne `matches`
         qui montre où les données ont été trouvées).
       - `result_cookies_clean.json` et `result_dom_clean.json` (nettoyés, sans la colonne `matches`,
         ceux-ci sont à transmettre pour analyse).

     Remarques :
    - En cas d'erreur sur un navigateur, l'exécution continue avec les autres.
    - Les statistiques brutes permettent de vérifier l'exactitude avant nettoyage.
    """

    profile = load_profile_from_terminal_validated()
    os_type = get_os_info().lower()
    count, date = init_runtime_file("runtime.txt")
    results = []
    browsers = [b.lower() for b in profile.get("browsers", [])]

    print(f"📋 Navigateurs à traiter: {', '.join(browsers)}")

    print("profile to search : ",json.dumps(profile, indent=4))

    if os_type == "windows":
        from chromium_windows.main import main_chromium
        for browser in browsers:
            print(Fore.GREEN + f"Processing browser: {browser}" + Style.RESET_ALL)
            if browser in ["mozilla", "firefox"]:
                try:
                    result_dict = main_firefox(date, user=profile)
                    results.append(result_dict)
                except Exception as e:
                    print(f"❌ Erreur lors du traitement de {browser}: {e}")
            else:
                try:
                    result_dict = main_chromium(profile, date, browser)
                    results.append(result_dict)
                except Exception as e:
                    print(f"❌ Erreur lors du traitement de {browser}: {e}")
    count += 1
    current = int(time.time() * 1e6)
    update_runtime_file("runtime.txt", count, current)
    json_Result(results)

if __name__ == "__main__":
    search_profile()