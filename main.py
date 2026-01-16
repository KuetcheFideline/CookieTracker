import sys
import os.path
import time
import uuid
import json
import socket
import uuid
import platform
import requests
import shutil
import subprocess
from colorama import Fore, Style, init

from Firefox.__main__ import main_firefox
from Firefox.utils.utils import get_os_info
from treatement.profile_utils import (json_Result, load_profile_from_terminal_validated, print_summary, clean_results, save_global_stats)
from chrome.chrome_linux import main_linux


# Fonctions de saisie avec validation
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
       - `result_cleaned_cookies.json` et `result_cleaned_dom.json` (nettoyés, sans la colonne `matches`,
         ceux-ci sont à transmettre pour analyse).

     Remarques :
    - En cas d'erreur sur un navigateur, l'exécution continue avec les autres.
    - Les statistiques brutes permettent de vérifier l'exactitude avant nettoyage.
    """

    profile = load_profile_from_terminal_validated()
    os_type = get_os_info()
    results = []
    browsers = [b.lower() for b in profile.get("browsers", [])]

    print(f" Navigateurs à traiter: {', '.join(browsers)}")

    print("profile to search : ",json.dumps(profile, indent=4))

        
    for browser in browsers:
            print(Fore.GREEN + f"Processing browser: {browser}" + Style.RESET_ALL)
            if browser in ["mozilla", "firefox"]:
                try:
                    # last_run=0 désactive le filtrage par date (analyse tous les cookies)
                    result_dict = main_firefox(last_run=0, user=profile)
                    results.append(result_dict)
                except Exception as e:
                    print(f" Erreur lors du traitement de {browser}: {e}")
            else :

                try:
                        linux_result = main_linux(user=profile, browser=browsers, date=0)
                        print(Fore.MAGENTA + "Linux results:" + Style.RESET_ALL)
                        results.extend(linux_result)
                except Exception as e:
                        print(f"Erreur lors du traitement des sites de chrome  : {e}")

    print(Fore.CYAN + "Saving raw results..." + Style.RESET_ALL)
    json_Result(results)
    
    # Nettoyer les résultats (ne garder que les valeurs non-nulles)
    # clean_results('result_cookies.json', 'result_cleaned_cookies.json')
    
    # Affichage du résumé des statistiques et sauvegarde des stats globales
    print(Fore.CYAN + "Generating summary and global statistics..." + Style.RESET_ALL)
    stats = print_summary()
    save_global_stats(stats)
    print(Fore.GREEN + "Processing complete!" + Style.RESET_ALL)


if __name__ == "__main__":
    search_profile()


