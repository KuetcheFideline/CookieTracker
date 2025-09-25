import os
import sys
import json
import re
import socket
import uuid
import platform
import requests
from datetime import datetime
from colorama import Fore, Style, init

PROFILE_FILE = "user_profile.json"

def validate_date(date_str):
    """Valide le format de date JJ/MM/AAAA"""
    if not date_str:
        return True 
    pattern = r'^\d{2}/\d{2}/\d{4}$'
    if not re.match(pattern, date_str):
        return False
    try:
        day, month, year = map(int, date_str.split('/'))
        datetime(year, month, day)
        current_year = datetime.now().year
        if year < 1900 or year > current_year:
            return False
        return True
    except ValueError:
        return False

def validate_email(email):
    if not email:
        return True
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    if not phone:
        return True
    pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$'
    return re.match(pattern, phone.replace(' ', '')) is not None

def validate_gender(gender):
    if not gender:
        return True
    valid_genders = ['male', 'female', 'other', 'others', 'm', 'f', 'o']
    return gender.lower() in valid_genders

def validate_country_code(code):
    if not code:
        return True
    pattern = r'^[A-Z]{2}$'
    return re.match(pattern, code.upper()) is not None

def validate_account_number(account_num):
    if not account_num:
        return True
    pattern = r'^[A-Z0-9\s\-]{10,34}$'
    return re.match(pattern, account_num.replace(' ', '')) is not None

def validate_non_empty(value, field_name):
    if not value or not value.strip():
        print(Fore.RED + f"❌ Le champ '{field_name}' est obligatoire." + Style.RESET_ALL)
        return False
    return True

def validate_length(value, min_len=None, max_len=None):
    if not value:
        return True
    length = len(value.strip())
    if min_len and length < min_len:
        return False
    if max_len and length > max_len:
        return False
    return True

def remove_empty_values(data):
    """Supprime les valeurs vides (chaînes vides, listes vides, None) du dictionnaire."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            cleaned_v = remove_empty_values(v)
            if cleaned_v is not None and cleaned_v != "" and cleaned_v != [] and cleaned_v != {}:
                cleaned[k] = cleaned_v
        return cleaned
    elif isinstance(data, list):
        cleaned_list = []
        for item in data:
            cleaned_item = remove_empty_values(item)
            if cleaned_item is not None and cleaned_item != "" and cleaned_item != [] and cleaned_item != {}:
                cleaned_list.append(cleaned_item)
        return cleaned_list
    else:
        return data

def remove_matches_field(data):
    if isinstance(data, dict):
        return {k: remove_matches_field(v) for k, v in data.items() if k != "matches"}
    elif isinstance(data, list):
        return [remove_matches_field(item) for item in data]
    else:
        return data

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def load_existing_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profile(user_data):
    with open(PROFILE_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

def get_system_info():
    try:
        ip_public = requests.get("https://api.ipify.org", timeout=5).text
    except:
        ip_public = "Non disponible"
    try:
        ip_local = socket.gethostbyname(socket.gethostname())
    except:
        ip_local = "Non disponible"
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                        for i in range(0, 8*6, 8)][::-1])
    except:
        mac = "Non disponible"
    return {
        "ip_public": ip_public,
        "ip_local": ip_local,
        "mac_address": mac,
        "os": platform.system(),
        "os_version": platform.release(),
        "processor": platform.processor()
    }





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




def prompt_field_validated(field_name, default="", validator=None, required=False, error_msg=None):
    """Affiche ancienne valeur et permet modification avec validation"""
    while True:
        if default:
            val = input(f">> {field_name} [{default}]: ").strip()
            val = val if val else default
        else:
            val = input(f">> {field_name}: ").strip()
        
        # Vérifier si le champ est requis
        if required and not validate_non_empty(val, field_name):
            continue
        
        # Appliquer le validateur si fourni
        if validator and not validator(val):
            msg = error_msg or f"❌ Format invalide pour '{field_name}'. Veuillez réessayer."
            print(Fore.RED + msg + Style.RESET_ALL)
            continue
        
        return val

def multi_input_validated(field_name, default=None, validator=None, error_msg=None):
    """Champ multiple séparé par des virgules avec validation"""
    while True:
        if default:
            print(f">> {field_name} actuel: {', '.join(map(str, default))}")
        val = input(f">> {field_name} (séparez par des virgules, Entrée pour garder): ").strip()
        
        if not val and default is not None:
            return default
        
        if not val:
            return []
        
        items = [v.strip() for v in val.split(",") if v.strip()]
        
        # Valider chaque élément si un validateur est fourni
        if validator:
            invalid_items = []
            for item in items:
                if not validator(item):
                    invalid_items.append(item)
            
            if invalid_items:
                msg = error_msg or f"❌ Éléments invalides: {', '.join(invalid_items)}"
                print(Fore.RED + msg + Style.RESET_ALL)
                continue
        
        return items

# Fonction principale avec validation
def load_profile_from_terminal_validated():
    old_data = load_existing_profile()

    print(Fore.CYAN + "="*50)
    print(Fore.YELLOW + "   FORMULAIRE PROFIL UTILISATEUR (AVEC VALIDATION)")
    print(Fore.CYAN + "="*50 + Style.RESET_ALL)
    print(Fore.GREEN + "Les champs marqués d'un * sont obligatoires" + Style.RESET_ALL)
    print()

    user_data = {}

    # Champs avec validation spécifique
    user_data["name"] = prompt_field_validated(
        "Nom complet *", 
        old_data.get("name", ""), 
        required=True
    )

    user_data["birthday"] = prompt_field_validated(
        "Date de naissance (JJ/MM/AAAA)", 
        old_data.get("birthday", ""),
        validator=validate_date,
        error_msg="❌ Format de date invalide. Utilisez JJ/MM/AAAA (ex: 15/03/1990)"
    )

    user_data["gender"] = prompt_field_validated(
        "Genre (male/female/other)", 
        old_data.get("gender", ""),
        validator=validate_gender,
        error_msg="❌ Genre invalide. Utilisez: male, female ou other"
    )

    user_data["adresse"] = prompt_field_validated(
        "Adresse *", 
        old_data.get("adresse", ""),
        required=True
    )

    user_data["pobox"] = prompt_field_validated(
        "PO Box (optionnel)", 
        old_data.get("pobox", "")
    )

    user_data["nationality"] = prompt_field_validated(
        "Nationalité *", 
        old_data.get("nationality", ""),
        required=True
    )

    user_data["marital_status"] = prompt_field_validated(
        "Statut marital", 
        old_data.get("marital_status", "")
    )

    user_data["profession"] = prompt_field_validated(
        "Profession", 
        old_data.get("profession", "")
    )

    # Données bancaires
    print(Fore.YELLOW + "\n--- Informations bancaires ---" + Style.RESET_ALL)
    user_data["bank"] = {
    "account_number": prompt_field_validated(
        "N° compte bancaire",
        old_data.get("bank", {}).get("account_number", "") or "0000000000",
        validator=validate_account_number,
        error_msg="❌ Format de compte invalide. Utilisez lettres, chiffres et tirets"
    ),
    "bank_name": prompt_field_validated(
        "Nom banque", 
        old_data.get("bank", {}).get("bank_name", "") or "Inconnu"
    )
}


    # Champs multiples avec validation
    print(Fore.YELLOW + "\n--- Contacts et communications ---" + Style.RESET_ALL)
    user_data["email"] = multi_input_validated(
        "Emails *", 
        old_data.get("email", []),
        validator=validate_email,
        error_msg="❌ Certains emails sont invalides. Format attendu: user@domain.com"
    )
    
    if not user_data["email"]:  # Au moins un email requis
        print(Fore.RED + "❌ Au moins un email est requis." + Style.RESET_ALL)
        user_data["email"] = multi_input_validated(
            "Emails *", 
            [],
            validator=validate_email,
            error_msg="❌ Format email invalide"
        )

    user_data["phone_number"] = multi_input_validated(
        "Numéros de téléphone", 
        old_data.get("phone_number", []),
        validator=validate_phone,
        error_msg="❌ Format de téléphone invalide. Ex: +33123456789, 0123456789"
    )

    user_data["isp"] = multi_input_validated(
        "Fournisseurs internet (ISP)", 
        old_data.get("isp", [])
    )
    
    user_data["username"] = multi_input_validated(
        "Usernames", 
        old_data.get("username", [])
    )

    # Localisation
    print(Fore.YELLOW + "\n--- Localisation ---" + Style.RESET_ALL)
    user_data["city"] = multi_input_validated(
        "Villes *", 
        old_data.get("city", [])
    )
    print(Fore.YELLOW + "\n--- Recherches ---" + Style.RESET_ALL)
    user_data["Recherches"] = multi_input_validated(
        "Vos dernieres Recherche sur les sites Mot separer par des virgules  ", 
        old_data.get("Recherches", [])
    )
    
    if not user_data["city"]:  # Au moins une ville requise
        print(Fore.RED + "❌ Au moins une ville est requise." + Style.RESET_ALL)
        user_data["city"] = multi_input_validated("Villes *", [])

    user_data["country"] = multi_input_validated(
        "Pays", 
        old_data.get("country", [])
    )

    user_data["code_country"] = multi_input_validated(
        "Code pays (2 lettres, ex: FR, US)", 
        old_data.get("code_country", []),
        validator=validate_country_code,
        error_msg="❌ Code pays invalide. Utilisez 2 lettres (ex: FR, US, DE)"
    )

    user_data["language"] = multi_input_validated(
        "Langues", 
        old_data.get("language", [])
    )

    # Autres informations
   
    
    user_data["brand"] = multi_input_validated(
        "Marques d'appareils", 
        old_data.get("brand", [])
    )
    
    user_data["siblings"] = multi_input_validated(
        "Nom de vos contacts les plus récents", 
        old_data.get("siblings", [])
    )

    # Informations système automatiques
    user_data["browsers"] = old_data.get("browsers", ["Chrome", "Firefox"])
    user_data["ip_info"] = get_system_info()

    # Nettoie les valeurs vides avant de sauvegarder
    cleaned_user_data = clean_empty_values(user_data)
    save_profile(cleaned_user_data)
    
    print(Fore.GREEN + "\n✅ Profil sauvegardé avec succès!" + Style.RESET_ALL)
    return cleaned_user_data

# Fonction d'affichage du profil pour vérification
def display_profile_summary(profile):
    """Affiche un résumé du profil pour vérification"""
    print(Fore.CYAN + "\n" + "="*50)
    print(Fore.YELLOW + "   RÉSUMÉ DU PROFIL")
    print(Fore.CYAN + "="*50 + Style.RESET_ALL)
    
    print(f"Nom: {profile.get('name', 'Non renseigné')}")
    print(f"Date de naissance: {profile.get('birthday', 'Non renseigné')}")
    print(f"Genre: {profile.get('gender', 'Non renseigné')}")
    print(f"Emails: {', '.join(profile.get('email', []))}")
    print(f"Téléphones: {', '.join(profile.get('phone_number', []))}")
    print(f"Villes: {', '.join(profile.get('city', []))}")
    
    # Demander confirmation
    confirm = input(f"\n{Fore.YELLOW}Les informations sont-elles correctes ? (o/n): {Style.RESET_ALL}").strip().lower()
    return confirm in ['o', 'oui', 'y', 'yes']

# Autres fonctions nécessaires (à garder de votre code original)
def load_existing_profile():
    PROFILE_FILE = "user_profile.json"
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profile(user_data):
    PROFILE_FILE = "user_profile.json"
    with open(PROFILE_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

def clean_empty_values(data):
    """Supprime les valeurs vides du profil."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            cleaned_value = clean_empty_values(v)
            if cleaned_value or cleaned_value == 0 or cleaned_value is False:
                if not (isinstance(cleaned_value, (str, list, dict)) and len(cleaned_value) == 0):
                    cleaned[k] = cleaned_value
        return cleaned
    elif isinstance(data, list):
        return [clean_empty_values(item) for item in data if item and str(item).strip()]
    else:
        return data

def get_system_info():
    """Retourne infos système automatiques"""
    try:
        ip_public = requests.get("https://api.ipify.org", timeout=5).text
    except:
        ip_public = "Non disponible"
    
    try:
        ip_local = socket.gethostbyname(socket.gethostname())
    except:
        ip_local = "Non disponible"
    
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                        for i in range(0, 8*6, 8)][::-1])
    except:
        mac = "Non disponible"
    
    return {
        "ip_public": ip_public,
        "ip_local": ip_local,
        "mac_address": mac,
        "os": platform.system(),
        "os_version": platform.release(),
        "processor": platform.processor()
    }



def remove_matches_field(data):
    """Supprime la clé 'matches' à tous les niveaux du dictionnaire imbriqué."""
    if isinstance(data, dict):
        return {k: remove_matches_field(v) for k, v in data.items() if k != "matches"}
    elif isinstance(data, list):
        return [remove_matches_field(item) for item in data]
    else:
        return data


def clean_empty_values(data):
    """Supprime les valeurs vides (chaînes vides, listes vides, dictionnaires vides) du profil."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            cleaned_value = clean_empty_values(v)
            # Garde seulement les valeurs non vides
            if cleaned_value or cleaned_value == 0 or cleaned_value is False:  # Garde 0 et False
                if not (isinstance(cleaned_value, (str, list, dict)) and len(cleaned_value) == 0):
                    cleaned[k] = cleaned_value
        return cleaned
    elif isinstance(data, list):
        # Filtre les éléments vides et nettoie récursivement
        return [clean_empty_values(item) for item in data if item and str(item).strip()]
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



