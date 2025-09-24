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
import psutil
from chromium_windows.main import main_chromium

from Firefox.__main__ import main_firefox
from Firefox.utils.utils import get_os_info

import os
import winreg

def get_browser_path_from_registry(browser_exe):
    """
    Recherche le chemin d'un exécutable de navigateur dans le registre Windows.
    """
    possible_keys = [
        fr"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{browser_exe}",
        fr"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\{browser_exe}",
    ]
    for key_path in possible_keys:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                path, _ = winreg.QueryValueEx(key, None)
                if os.path.exists(path):
                    return path
        except FileNotFoundError:
            continue
    return None

def check_browser_installed(browser_name):
    """Vérifie si un navigateur est installé sur Windows"""
    browser_paths = {
        'firefox': [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe")
        ],
        'chrome': [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ],
    }

    exe_names = {
        'firefox': 'firefox.exe',
        'chrome': 'chrome.exe',
    }

    browser_key = browser_name.lower()

    print

    if browser_key not in browser_paths:
        print(f"✗ Navigateur {browser_name} non reconnu.")
        return False

    # Vérifie chemins classiques
    for path in browser_paths[browser_key]:
        if os.path.exists(path):
            print(f"✓ {browser_name} trouvé: {path}")
            return True

    # Vérifie dans le registre (HKCU + HKLM)
    reg_path = get_browser_path_from_registry(exe_names[browser_key])
    if reg_path:
        print(f"✓ {browser_name} trouvé via registre: {reg_path}")
        return True

    print(f"✗ {browser_name} non installé.")
    return False



def remove_matches_field(data):
    """Supprime la clé 'matches' à tous les niveaux du dictionnaire imbriqué."""
    if isinstance(data, dict):
        return {k: remove_matches_field(v) for k, v in data.items() if k != "matches"}
    elif isinstance(data, list):
        return [remove_matches_field(item) for item in data]
    else:
        return data


def resource_path(relative_path):
    """ Trouve le bon chemin même avec PyInstaller """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def load_config(profile):
    with open(profile, "r") as file:
        profile = json.load(file)
    browsers = profile["browsers"]
    profile.pop("browsers")
    users = profile
    return users, browsers


def init_runtime_file(path):
    if not os.path.exists(path):
        with open(path, "w") as file:
            file.write("count=0\nlastrun=0\n")
    with open(path, "r") as file:
        lines = file.readlines()
        count = int(lines[0].strip().split("=")[1])
        date = int(lines[1].strip().split("=")[1])
    return count, date


def update_runtime_file(file_path, count, date):
    with open(file_path, "w") as file:
        file.write(f"count={count}\ndate={date}\n")


def json_Result(results):
    """
    Ajoute les keys de element comme super key dans final_stat.
    """
    cookies_stat = {}
    dom_stat = {}
    for element in results:
        for keys in element.keys():  
            for elt in element[keys]:
                if elt == 'cookies':
                    cookies_stat[keys] = element[keys][elt]
                if elt == 'dom':
                    dom_stat[keys] = element[keys][elt]
    
    print("Results structured. For you to see in result_cookies.json and result_dom.json")
    with open(f"result_cookies.json", "w") as file:
        json.dump(cookies_stat, file, indent=4)
    print("Results saved to result_cookies.json")
    
    with open(f"result_dom.json", "w") as file:
        json.dump(dom_stat, file, indent=4)
    print("Results saved to result_dom.json")

    cleaned_cookies_stat = remove_matches_field(cookies_stat)
    cleaned_dom_stat = remove_matches_field(dom_stat)

    with open(f"result_cleaned_cookies.json", "w") as file:
        json.dump(cleaned_cookies_stat, file, indent=4)
    with open(f"result_cleaned_dom.json", "w") as file:
        json.dump(cleaned_dom_stat, file, indent=4)
    print("Results structured. For us to send ")


init(autoreset=True)


def get_system_info():
    """Retourne infos système automatiques"""
    try:
        ip_public = requests.get("https://api.ipify.org").text
    except:
        ip_public = "Non disponible"
    ip_local = socket.gethostbyname(socket.gethostname())
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                    for i in range(0, 8*6, 8)][::-1])
    return {
        "ip_public": ip_public,
        "ip_local": ip_local,
        "mac_address": mac,
        "os": platform.system(),
        "os_version": platform.release(),
        "processor": platform.processor()
    }


PROFILE_FILE = "user_profile.json"



def is_browser_running(browser_name: str) -> bool:
    for proc in psutil.process_iter(attrs=['name', 'exe', 'cmdline']):
        try:
            name = proc.info['name'] or ''
            exe = proc.info['exe'] or ''
            cmdline = ' '.join(proc.info['cmdline'] or [])

            if browser_name.lower() == "chrome":
                if "google-chrome" in name.lower() or "google-chrome" in exe.lower():
                    return True

            elif browser_name.lower() in name.lower() or browser_name.lower() in exe.lower():
                return True

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False



def is_browser_running(browser_name: str) -> bool:
    """Vérifie si un navigateur est en cours d'exécution sur Windows"""
    browser_name = browser_name.lower()

    for proc in psutil.process_iter(attrs=['name', 'exe', 'cmdline']):
        try:
            name = proc.info['name'] or ''
            exe = proc.info['exe'] or ''
            cmdline = ' '.join(proc.info['cmdline'] or [])

            # Pour Chrome et Chromium, les exécutables sont 'chrome.exe' ou 'chromium.exe'
            if browser_name == "chrome":
                if "chrome.exe" in exe.lower() or "chrome" in cmdline.lower():
                    return True
            elif browser_name == "edge":
                if "msedge.exe" in exe.lower() or "msedge" in cmdline.lower():
                    return True
            elif browser_name == "firefox":
                if "firefox.exe" in exe.lower() or "firefox" in cmdline.lower():
                    return True
            elif browser_name == "opera":
                if "opera.exe" in exe.lower() or "opera" in cmdline.lower():
                    return True
            elif browser_name == "brave":
                if "brave.exe" in exe.lower() or "brave" in cmdline.lower():
                    return True
            else:
                # Vérifie pour d'autres navigateurs (par exemple, si le nom est partiel dans le processus)
                if browser_name in name.lower() or browser_name in exe.lower():
                    return True

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return False


def load_existing_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_profile(user_data):
    with open(PROFILE_FILE, "w") as f:
        json.dump(user_data, f, indent=4)


def prompt_field(field_name, default=""):
    """Affiche ancienne valeur et permet modification"""
    if default:
        val = input(f">> {field_name} [{default}]: ").strip()
        return val if val else default
    else:
        return input(f">> {field_name}: ").strip()


def multi_input(field_name, default=None):
    """Champ multiple séparé par des virgules"""
    if default:
        print(f">> {field_name} actuel: {', '.join(default)}")
    val = input(f">> {field_name} (séparez par des virgules, Entrée pour garder): ").strip()
    if not val and default is not None:
        return default
    return [v.strip() for v in val.split(",") if v.strip()]


def load_profile_from_terminal():
    old_data = load_existing_profile()

    print(Fore.CYAN + "="*40)
    print(Fore.YELLOW + "   FORMULAIRE PROFIL UTILISATEUR")
    print(Fore.CYAN + "="*40 + Style.RESET_ALL)

    user_data = {
        "name": prompt_field("Nom complet", old_data.get("name", "")),
        "birthday": prompt_field("Date de naissance (JJ/MM/AAAA)", old_data.get("birthday", "")),
        "gender": prompt_field("Genre (male/female/others)", old_data.get("gender", "")),
        "geolocation": prompt_field("Geolocation (optionnel)", old_data.get("geolocation", "")),
        "pobox": prompt_field("PO Box (optionnel)", old_data.get("pobox", "")),
        "browsers": old_data.get("browsers", [" google Chrome", "Firefox"]),
        "ip_info": get_system_info(),
        "nationality": prompt_field("Nationalité", old_data.get("nationality", "")),
        "marital_status": prompt_field("Statut marital", old_data.get("marital_status", "")),
        "profession": prompt_field("Profession", old_data.get("profession", "")),
        "bank": {
            "account_number": prompt_field("N° compte bancaire (optionnel)", old_data.get("bank", {}).get("account_number", "")),
            "bank_name": prompt_field("Nom banque", old_data.get("bank", {}).get("bank_name", ""))
        },
    }

    user_data["email"] = multi_input("Emails", old_data.get("email", []))
    user_data["isp"] = multi_input("Fournisseurs internet (ISP)", old_data.get("isp", [])) 
    user_data["username"] = multi_input("Usernames", old_data.get("username", []))
    user_data["phone_number"] = multi_input("Numéros de téléphone", old_data.get("phone_number", []))
    user_data["city"] = multi_input("Villes", old_data.get("city", []))
    user_data["country"] = multi_input("Pays", old_data.get("country", []))
    user_data["code_country"] = multi_input("Code pays", old_data.get("code_country", []))  
    user_data["language"] = multi_input("Langues", old_data.get("language", []))
    user_data["education"] = multi_input("Éducation", old_data.get("education", []))
    
    user_data.setdefault("device", {})
    user_data["device"]["os"] = multi_input("Systèmes d'exploitation", old_data.get("device", {}).get("os", []))
    user_data["device"]["brand"] = multi_input("Marques d'appareils", old_data.get("device", {}).get("brand", []))
    
    user_data.setdefault("relatives", {})
    user_data["relatives"]["siblings"] = multi_input("Nom de vos contact les plus recents ", old_data.get("relatives", {}).get("siblings", []))

    save_profile(user_data)
    return user_data


def search_profile():

    """
    Analyse des données stockées par les navigateurs dans le DOM et les cookies.

    Cette fonction :
    - Récupère le profil utilisateur via un formulaire en ligne de commande.
    - Vérifie quels navigateurs sont installés sur la machine et ignore ceux qui ne le sont pas.
    - Exécute le traitement des navigateurs supportés (Firefox, Chrome, etc.).
    - Sauvegarde les résultats en JSON (cookies et DOM).
    - Met à jour le fichier `runtime.txt` pour suivre les exécutions.

     Utilisation :
    1. Lancer le script et remplir le formulaire affiché.
    2. Fermer tous vos navigateurs AVANT le traitement.
    3. Lors d’une nouvelle exécution, supprimer le fichier `runtime.txt` pour réinitialiser le compteur.
    4. Quatre fichiers JSON sont générés :
       - `result_cookies.json` et `result_dom.json` (bruts, avec la colonne `matches`
         qui montre où les données ont été trouvées).
       - `result_cookies_clean.json` et `result_dom_clean.json` (nettoyés, sans la colonne `matches`,
         ceux-ci sont à transmettre pour analyse).

     Remarques :
    - Si aucun navigateur installé n’est détecté, le script s’arrête.
    - En cas d’erreur sur un navigateur, l’exécution continue avec les autres.
    - Les statistiques brutes permettent de vérifier l’exactitude avant nettoyage.
    """



    profile = load_profile_from_terminal()
    os_type = get_os_info().lower()
    count, date = init_runtime_file("runtime.txt")
    results = []
    browsers = [b.lower() for b in profile.get("browsers", [])]

    print(Fore.YELLOW + "\n=== VÉRIFICATION DES NAVIGATEURS INSTALLÉS ===" + Style.RESET_ALL)
    installed_browsers = []
    
    for browser in browsers:
        if check_browser_installed(browser):
            installed_browsers.append(browser)
        else:
            print(f"⚠️  {browser} n'est pas installé, ignoré")

    if not installed_browsers:
        print(Fore.RED + "⚠️  Aucun navigateur installé trouvé, arrêt du processus" + Style.RESET_ALL)
        return
    


    for browser in installed_browsers:
        if is_browser_running(browser):
            print(Fore.RED + f"⚠️  Le navigateur {browser} est encore ouvert. "
                             f"Veuillez le fermer avant de continuer." + Style.RESET_ALL)
            return 

    print(f"📋 Navigateurs à traiter: {', '.join(installed_browsers)}")

    if  os_type == "windows":
        from chromium_windows.main import main_chromium
        
        for browser in installed_browsers:
            print(Fore.GREEN + f"Processing browser: {browser}" + Style.RESET_ALL)
            if browser in ["mozilla", "firefox"]:
                try:
                    result_dict = main_firefox(date, user=profile)
                    results.append(result_dict)
                except Exception as e:
                    print(f"❌ Erreur lors du traitement de {browser}: {e}")
            else :
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