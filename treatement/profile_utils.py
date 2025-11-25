import os
import sys
import json
import re
import socket
import uuid
import platform
import requests
import distro
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

PROFILE_FILE = "user_profile.json"

# --- Validation Functions ---
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
        print(Fore.RED + f" Le champ '{field_name}' est obligatoire." + Style.RESET_ALL)
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


def clean_empty_values(data):
    """Supprime les valeurs vides (chaînes vides, listes vides, dictionnaires vides) du profil."""
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

def detect_installed_browsers():
    """Détecte les navigateurs installés sur le système"""
    browsers = []
    os_type = platform.system()
    
    if os_type == "Linux":
        distro_id = distro.id().lower()
        
        if distro_id in ["ubuntu", "debian", "linuxmint", "pop"]:
            browser_paths = {
                "Chrome": [
                    os.path.expanduser("~/.config/google-chrome"),
                    os.path.expanduser("~/.config/chrome")
                ],
                "Firefox": [
                    os.path.expanduser("~/.mozilla/firefox"),
                    os.path.expanduser("~/snap/firefox")  
                ],
                "Chromium": [
                    os.path.expanduser("~/.config/chromium"),
                    os.path.expanduser("~/snap/chromium") 
                ],
                "Brave": [
                    os.path.expanduser("~/.config/BraveSoftware/Brave-Browser")
                ],
                "Edge": [
                    os.path.expanduser("~/.config/microsoft-edge")
                ]
            }
        elif distro_id in ["fedora", "rhel", "centos"]:
            browser_paths = {
                "Chrome": [
                    os.path.expanduser("~/.config/google-chrome"),
                    os.path.expanduser("~/.config/chrome")
                ],
                "Firefox": [
                    os.path.expanduser("~/.mozilla/firefox")
                ],
                "Chromium": [
                    os.path.expanduser("~/.config/chromium")
                ],
                "Brave": [
                    os.path.expanduser("~/.config/BraveSoftware/Brave-Browser")
                ],
                "Edge": [
                    os.path.expanduser("~/.config/microsoft-edge")
                ]
            }
        else:
            browser_paths = {
                "Chrome": [
                    os.path.expanduser("~/.config/google-chrome")
                ],
                "Firefox": [
                    os.path.expanduser("~/.mozilla/firefox")
                ],
                "Chromium": [
                    os.path.expanduser("~/.config/chromium")
                ]
            }
    else:
        print(f"Système d'exploitation non supporté: {os_type}")
        browser_paths = {}
    
    for browser, paths in browser_paths.items():
        for path in paths:
            if os.path.exists(path):
                browsers.append(browser)
                break
    
    return browsers


def select_browsers_interactive():
    """Permet à l'utilisateur de sélectionner les navigateurs à analyser"""
    available_browsers = {
        "1": "Chrome",
        "2": "Firefox",
        "3": "Chromium",
        "4": "Brave",
        "5": "Edge"
    }
    
    installed = detect_installed_browsers()
    
    print(Fore.YELLOW + "\n--- Sélection des navigateurs ---" + Style.RESET_ALL)
    print("Navigateurs disponibles :")
    for key, browser in available_browsers.items():
        status = Fore.GREEN + " (installé)" + Style.RESET_ALL if browser in installed else Fore.RED + " (non détecté)" + Style.RESET_ALL
        print(f"  {key}. {browser}{status}")
    
    while True:
        choice = input("\n>> Sélectionnez les navigateurs (ex: 1,2,3): ").strip()
        
        if not choice:
            print(Fore.RED + "Veuillez sélectionner au moins un navigateur." + Style.RESET_ALL)
            continue
        
        selected_numbers = [num.strip() for num in choice.split(",")]
        selected_browsers = []
        
        invalid = False
        for num in selected_numbers:
            if num in available_browsers:
                selected_browsers.append(available_browsers[num])
            else:
                print(Fore.RED + f"Choix invalide: {num}" + Style.RESET_ALL)
                invalid = True
                break
        
        if not invalid and selected_browsers:
            return selected_browsers

def update_runtime_file(file_path, count, date):
    with open(file_path, "w") as file:
        file.write(f"count={count}\ndate={date}\n")

def init_runtime_file(path):
    if not os.path.exists(path):
        with open(path, "w") as file:
            file.write("count=0\nlastrun=0\n")
    
    with open(path, "r") as file:
        lines = file.readlines()
        
        # Parser avec gestion des valeurs vides
        try:
            count_value = lines[0].strip().split("=")[1]
            count = int(count_value) if count_value else 0
        except (IndexError, ValueError):
            count = 0
        
        try:
            date_value = lines[1].strip().split("=")[1]
            date = int(date_value) if date_value else 0
        except (IndexError, ValueError):
            date = 0
    
    return count, date

def load_config(profile):
    with open(profile, "r") as file:
        profile = json.load(file)
    browsers = profile["browsers"]
    profile.pop("browsers")
    users = profile
    return users, browsers

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

def prompt_field_validated(field_name, default="", validator=None, required=False, error_msg=None):
    """Affiche ancienne valeur et permet modification avec validation"""
    while True:
        if default:
            val = input(f">> {field_name} [{default}]: ").strip()
            val = val if val else default
        else:
            val = input(f">> {field_name}: ").strip()
        
        if required and not validate_non_empty(val, field_name):
            continue
        
        if validator and not validator(val):
            msg = error_msg or f" Format invalide pour '{field_name}'. Veuillez réessayer."
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
        
        if validator:
            invalid_items = []
            for item in items:
                if not validator(item):
                    invalid_items.append(item)
            
            if invalid_items:
                msg = error_msg or f" Éléments invalides: {', '.join(invalid_items)}"
                print(Fore.RED + msg + Style.RESET_ALL)
                continue
        
        return items


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
        error_msg="Format de date invalide. Utilisez JJ/MM/AAAA (ex: 15/03/1990)"
    )

    user_data["gender"] = prompt_field_validated(
        "Genre (male/female/other)", 
        old_data.get("gender", ""),
        validator=validate_gender,
        error_msg="Genre invalide. Utilisez: male, female ou other"
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
        error_msg="Format de compte invalide. Utilisez lettres, chiffres et tirets"
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
        error_msg="Certains emails sont invalides. Format attendu: user@domain.com"
    )
    
    if not user_data["email"]:  
        print(Fore.RED + "Au moins un email est requis." + Style.RESET_ALL)
        user_data["email"] = multi_input_validated(
            "Emails *", 
            [],
            validator=validate_email,
            error_msg="Format email invalide"
        )

    user_data["phone_number"] = multi_input_validated(
        "Numéros de téléphone", 
        old_data.get("phone_number", []),
        validator=validate_phone,
        error_msg="Format de téléphone invalide. Ex: +33123456789, 0123456789"
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
        print(Fore.RED + "Au moins une ville est requise." + Style.RESET_ALL)
        user_data["city"] = multi_input_validated("Villes *", [])

    user_data["country"] = multi_input_validated(
        "Pays", 
        old_data.get("country", [])
    )

    user_data["code_country"] = multi_input_validated(
        "Code pays (2 lettres, ex: FR, US)", 
        old_data.get("code_country", []),
        validator=validate_country_code,
        error_msg="Code pays invalide. Utilisez 2 lettres (ex: FR, US, DE)"
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
    user_data["browsers"] = select_browsers_interactive()
    user_data["ip_info"] = get_system_info()

    # Nettoie les valeurs vides avant de sauvegarder
    cleaned_user_data = clean_empty_values(user_data)
    save_profile(cleaned_user_data)
    
    print(Fore.GREEN + "\n Profil sauvegardé avec succès!" + Style.RESET_ALL)
    return cleaned_user_data

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

def clean_results(input_path, output_path):
    """
    Nettoie les résultats en ne gardant que les valeurs non-nulles.
    """
    if not os.path.exists(input_path):
        return
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cleaned_data = {}
        
        for browser, domains in data.items():
            cleaned_domains = {}
            
            for domain, domain_data in domains.items():
                cleaned_domain = {}
                
                # Nettoyer personal_information - ne garder que les statistiques
                if 'personal_information' in domain_data:
                    cleaned_personal_info = {}
                    for key, info in domain_data['personal_information'].items():
                        if info.get('exact', 0) > 0 or info.get('variants', 0) > 0:
                            # Ne garder que les compteurs, pas les matches
                            cleaned_personal_info[key] = {
                                'exact': info.get('exact', 0),
                                'variants': info.get('variants', 0),
                                'unique_count': info.get('unique_count', 0)
                            }
                    
                    if cleaned_personal_info:
                        cleaned_domain['personal_information'] = cleaned_personal_info
                
                # Garder decoded_tokens si count > 0
                if 'decoded_tokens' in domain_data:
                    if domain_data['decoded_tokens'].get('count', 0) > 0:
                        cleaned_domain['decoded_tokens'] = domain_data['decoded_tokens']
                
                # Garder detected_emails si count > 0
                if 'detected_emails' in domain_data:
                    if domain_data['detected_emails'].get('count', 0) > 0:
                        cleaned_domain['detected_emails'] = domain_data['detected_emails']
                
                # Garder suspicious_tokens si count > 0
                if 'suspicious_tokens' in domain_data:
                    if domain_data['suspicious_tokens'].get('count', 0) > 0:
                        cleaned_domain['suspicious_tokens'] = domain_data['suspicious_tokens']
                
                # Ne garder le domaine que s'il a des données
                if cleaned_domain:
                    cleaned_domains[domain] = cleaned_domain
            
            if cleaned_domains:
                cleaned_data[browser] = cleaned_domains
        
        # Sauvegarder le fichier nettoyé
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.GREEN}✓ Fichier nettoyé sauvegardé: {output_path}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}Erreur lors du nettoyage de {input_path}: {e}{Style.RESET_ALL}")

def print_summary(cookies_path='result_cookies.json', dom_path='result_dom.json'):
    """
    Affiche un résumé des statistiques des informations trouvées.
    """
    print(Fore.CYAN + "\n" + "="*70)
    print(Fore.YELLOW + "   RÉSUMÉ DE L'ANALYSE - STATISTIQUES")
    print(Fore.CYAN + "="*70 + Style.RESET_ALL)
    
    total_stats = {
        'personal_info': {},
        'decoded_tokens': 0,
        'decoded_tokens_with_personal_info': 0,
        'personal_info_in_decoded': {},
        'detected_emails': set(),
        'suspicious_tokens': 0,
        'suspicious_tokens_by_type': {},
        'domains': 0
    }
    
    # Analyser les cookies
    if os.path.exists(cookies_path):
        try:
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
                
            for browser, domains in cookies_data.items():
                for domain, data in domains.items():
                    total_stats['domains'] += 1
                    
                    # Informations personnelles
                    if 'personal_information' in data:
                        for key, info in data['personal_information'].items():
                            if key not in total_stats['personal_info']:
                                total_stats['personal_info'][key] = {'exact': 0, 'variants': 0}
                            total_stats['personal_info'][key]['exact'] += info.get('exact', 0)
                            total_stats['personal_info'][key]['variants'] += info.get('variants', 0)
                    
                    # Tokens décodés et informations personnelles dedans
                    if 'decoded_tokens' in data:
                        total_stats['decoded_tokens'] += data['decoded_tokens'].get('count', 0)
                        
                        # Analyser les informations personnelles dans les tokens décodés
                        for token in data['decoded_tokens'].get('items', []):
                            personal_matches = token.get('personal_info_matches')
                            if personal_matches:
                                total_stats['decoded_tokens_with_personal_info'] += 1
                                for match in personal_matches:
                                    info_type = match.get('info_type')
                                    if info_type:
                                        if info_type not in total_stats['personal_info_in_decoded']:
                                            total_stats['personal_info_in_decoded'][info_type] = 0
                                        total_stats['personal_info_in_decoded'][info_type] += 1
                    
                    # Emails détectés
                    if 'detected_emails' in data:
                        for email in data['detected_emails'].get('unique_emails', []):
                            total_stats['detected_emails'].add(email)
                    
                    # Tokens suspects avec comptage par type
                    if 'suspicious_tokens' in data:
                        total_stats['suspicious_tokens'] += data['suspicious_tokens'].get('count', 0)
                        
                        # Compter par type de pattern
                        for item in data['suspicious_tokens'].get('items', []):
                            subtype = item.get('subtype', 'other')
                            if subtype not in total_stats['suspicious_tokens_by_type']:
                                total_stats['suspicious_tokens_by_type'][subtype] = 0
                            total_stats['suspicious_tokens_by_type'][subtype] += 1
        except Exception as e:
            print(Fore.RED + f"Erreur lors de la lecture de {cookies_path}: {e}" + Style.RESET_ALL)
    
    # Analyser le DOM
    if os.path.exists(dom_path):
        try:
            with open(dom_path, 'r', encoding='utf-8') as f:
                dom_data = json.load(f)
                
            for browser, domains in dom_data.items():
                for domain, data in domains.items():
                    # Informations personnelles
                    if 'personal_information' in data:
                        for key, info in data['personal_information'].items():
                            if key not in total_stats['personal_info']:
                                total_stats['personal_info'][key] = {'exact': 0, 'variants': 0}
                            total_stats['personal_info'][key]['exact'] += info.get('exact', 0)
                            total_stats['personal_info'][key]['variants'] += info.get('variants', 0)
                    
                    # Tokens décodés et informations personnelles dedans
                    if 'decoded_tokens' in data:
                        total_stats['decoded_tokens'] += data['decoded_tokens'].get('count', 0)
                        
                        # Analyser les informations personnelles dans les tokens décodés
                        for token in data['decoded_tokens'].get('items', []):
                            personal_matches = token.get('personal_info_matches')
                            if personal_matches:
                                total_stats['decoded_tokens_with_personal_info'] += 1
                                for match in personal_matches:
                                    info_type = match.get('info_type')
                                    if info_type:
                                        if info_type not in total_stats['personal_info_in_decoded']:
                                            total_stats['personal_info_in_decoded'][info_type] = 0
                                        total_stats['personal_info_in_decoded'][info_type] += 1
                    
                    # Emails détectés
                    if 'detected_emails' in data:
                        for email in data['detected_emails'].get('unique_emails', []):
                            total_stats['detected_emails'].add(email)
                    
                    # Tokens suspects avec comptage par type
                    if 'suspicious_tokens' in data:
                        total_stats['suspicious_tokens'] += data['suspicious_tokens'].get('count', 0)
                        
                        # Compter par type de pattern
                        for item in data['suspicious_tokens'].get('items', []):
                            subtype = item.get('subtype', 'other')
                            if subtype not in total_stats['suspicious_tokens_by_type']:
                                total_stats['suspicious_tokens_by_type'][subtype] = 0
                            total_stats['suspicious_tokens_by_type'][subtype] += 1
        except Exception as e:
            print(Fore.RED + f"Erreur lors de la lecture de {dom_path}: {e}" + Style.RESET_ALL)
    
    # Affichage des statistiques
    print(f"\n{Fore.GREEN}📊 Domaines analysés: {total_stats['domains']}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}🔍 INFORMATIONS PERSONNELLES TROUVÉES:{Style.RESET_ALL}")
    if total_stats['personal_info']:
        for key, counts in sorted(total_stats['personal_info'].items()):
            total = counts['exact'] + counts['variants']
            if total > 0:
                print(f"  • {key:20} : {Fore.GREEN}{counts['exact']:3} exact{Style.RESET_ALL}, "
                      f"{Fore.CYAN}{counts['variants']:3} variants{Style.RESET_ALL} "
                      f"(Total: {Fore.MAGENTA}{total}{Style.RESET_ALL})")
    else:
        print(f"  {Fore.RED}Aucune information personnelle trouvée{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}🔓 TOKENS DÉCODÉS:{Style.RESET_ALL}")
    print(f"  • Total: {Fore.MAGENTA}{total_stats['decoded_tokens']}{Style.RESET_ALL} tokens décodés (JWT/Base64)")
    if total_stats['decoded_tokens_with_personal_info'] > 0:
        print(f"  • {Fore.GREEN}{total_stats['decoded_tokens_with_personal_info']}{Style.RESET_ALL} tokens contiennent des informations personnelles")
        if total_stats['personal_info_in_decoded']:
            print(f"  • Informations trouvées dans les tokens:")
            for info_type, count in sorted(total_stats['personal_info_in_decoded'].items()):
                print(f"    - {info_type}: {Fore.CYAN}{count}{Style.RESET_ALL} occurrence(s)")
    
    print(f"\n{Fore.YELLOW}📧 EMAILS DÉTECTÉS:{Style.RESET_ALL}")
    if total_stats['detected_emails']:
        print(f"  • Total: {Fore.MAGENTA}{len(total_stats['detected_emails'])}{Style.RESET_ALL} emails uniques")
        print(f"  • Liste: {Fore.CYAN}{', '.join(sorted(total_stats['detected_emails']))}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}Aucun email détecté{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}⚠️  TOKENS SUSPECTS:{Style.RESET_ALL}")
    print(f"  • Total: {Fore.MAGENTA}{total_stats['suspicious_tokens']}{Style.RESET_ALL} tokens suspects")
    
    if total_stats['suspicious_tokens_by_type']:
        print(f"  • Détail par type de pattern:")
        # Grouper les patterns similaires
        important_types = ['user_agent', 'user_id', 'device_id', 'session_id', 'api_key', 'uuid']
        
        for pattern_type in important_types:
            if pattern_type in total_stats['suspicious_tokens_by_type']:
                count = total_stats['suspicious_tokens_by_type'][pattern_type]
                print(f"    - {pattern_type:20}: {Fore.CYAN}{count:5}{Style.RESET_ALL}")
        
        # Afficher les autres types
        other_count = sum(count for ptype, count in total_stats['suspicious_tokens_by_type'].items() 
                         if ptype not in important_types)
        if other_count > 0:
            print(f"    - {'autres':20}: {Fore.CYAN}{other_count:5}{Style.RESET_ALL}")
    
    print(Fore.CYAN + "\n" + "="*70 + "\n" + Style.RESET_ALL)
