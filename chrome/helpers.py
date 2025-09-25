import json
import sqlite3
import os
import keyring
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import re 
import urllib.parse


def profile(path):
    count = 0
    path = os.path.expanduser(path)
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)) and item.startswith("Profile"):
            count += 1
    return count
    
    







    
def cookie_config(browser):
    """Configure le chemin des fichiers de cookies et récupère la clé de chiffrement."""

    if browser.title() == "Chrome":
        count = profile(os.path.expanduser("~/.config/google-chrome"))
        
        if count == 0:
            cookie_file = "~/.config/google-chrome/Default/Cookies"
        else:

            cookie_file = ["~/.config/google-chrome/Default/Cookies"]
            for i in range(1, count+1):

                profile_path = os.path.join("~/.config/google-chrome/", f"Profile {i}", "Cookies")
                if os.path.exists(profile_path):
                    cookie_file.append(f"~/.config/google-chrome/Profile {i}/Cookies")
    else:
           return 0        

    config = {
        "key_material": "peanuts",
        "iterations": 1,
        "cookie_file": cookie_file,
    }

    key_material = None
    try:
        import gi 
        gi.require_version("Secret", "1")
        from gi.repository import Secret
    except ImportError:
        pass
    else:
        flags = Secret.ServiceFlags.LOAD_COLLECTIONS
        service = Secret.Service.get_sync(flags)
        gnome_keyring = service.get_collections()
        unlocked_keyrings = service.unlock_sync(gnome_keyring).unlocked
        keyring_name = f"{browser.title()} Safe Storage"

        for unlocked_keyring in unlocked_keyrings:
            for item in unlocked_keyring.get_items():
                if item.get_label() == keyring_name:
                    item_app = item.get_attributes().get("application", browser)
                    if item_app.lower() != browser.lower():
                        continue
                    item.load_secret_sync()
                    key_material = item.get_secret().get_text()
                    break
            else:
                continue
            break

    if key_material is None:
        try:
            key_material = keyring.get_password(
                f"{browser} Keys",
                f"{browser} Safe Storage",
            )
        except RuntimeError:
            print("Erreur lors de la récupération du mot de passe du keyring.")

    if key_material is not None:
        config["key_material"] = key_material
    return config

def clean(decrypted):
    last = decrypted[-1]
    try:
        return decrypted[:-last].decode("utf-8")
    except UnicodeDecodeError:
        # décodage tolérant → remplace les octets invalides par �
        return decrypted[:-last].decode("utf-8", errors="replace")


def cookie_decrypt(encrypted_value, key, ini_vector,cookie_database_version):
    """Décrypte un cookie."""

   
    encrypted_value = encrypted_value[3:]  
    cipher = Cipher(
        algorithm=AES(key),
        mode=CBC(ini_vector),
    )
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_value) + decryptor.finalize()

    if cookie_database_version >= 24:
          decrypted = decrypted[32:]


    return clean(decrypted)





def get_encryption_key(config, password=None):
    """Génère la clé de chiffrement à partir du mot de passe ou de la configuration."""
    if isinstance(password, bytes):
        key_material = password
    elif isinstance(password, str):
        key_material = password.encode("utf8")
    elif isinstance(config["key_material"], str):
        key_material = config["key_material"].encode("utf8")
    else:
        raise ValueError("Mot de passe non valide.")

    kdf = PBKDF2HMAC(
        algorithm=SHA1(),
        iterations=config["iterations"],
        length=config["length"],
        salt=config["salt"],
    )
    return kdf.derive(key_material)

def get_cookies(browser, date):
    """Récupère et décrypte les cookies du navigateur spécifié."""
    config = cookie_config(browser)

    
    if config == 0:
        return 0

    config.update(
        {"init_vector": b" " * 16, "length": 16, "salt": b"saltysalt"}
    )


    password = None
    enc_key = get_encryption_key(config, password)

    if date == 0:
        sql = "SELECT host_key, path, expires_utc, name, value, encrypted_value FROM cookies"
    else:
        sql = f"SELECT host_key, path, expires_utc, name, value, encrypted_value FROM cookies WHERE creation_utc>{date}"

    cookies = {}

    if isinstance(config["cookie_file"], list):
        file_paths = config["cookie_file"]
    else:
        file_paths = [config["cookie_file"]]

    for cookie_file in file_paths:
        cookie_file = os.path.expanduser(cookie_file)
        try:
            conn = sqlite3.connect(f"file:{cookie_file}?mode=ro", uri=True)
        except sqlite3.OperationalError as e:
            print(f"Erreur de connexion à la base de données des cookies pour {cookie_file} :", e)
            continue

        # --- Récupération de la version de la DB ---
        sql_version = "select value from meta where key = 'version';"
        cookie_database_version = 0
        try:
            row = conn.execute(sql_version).fetchone()
            if row:
                cookie_database_version = int(row[0])
        except sqlite3.OperationalError:
            pass

        # --- Lecture des cookies ---
        for db_row in conn.execute(sql):
            host_key, path, expires_utc, name, value, encrypted_value = db_row

            if encrypted_value[:3] in (b'v10', b'v11'):
                decrypted_value = cookie_decrypt(
                    encrypted_value,
                    enc_key,
                    config["init_vector"],
                    cookie_database_version
                )

                # Chrome ≥ v24 : retirer les 32 premiers octets
                if cookie_database_version >= 24 and decrypted_value:
                    decrypted_value = decrypted_value[32:]
                
                cookie_dict = {
                    "name": name,
                    "value": decrypted_value,
                    "path": path,
                    "expires_utc": expires_utc,}
                

                if host_key not in cookies:
                    cookies[host_key] = []
                cookies[host_key].append(cookie_dict)

        conn.close()

    return cookies






def filters_cookies(cookies, data):
    """
    Filtre les cookies en fonction des valeurs spécifiées et retourne les statistiques.
    Utilise la fonction 'count_matches' pour détecter des correspondances.
    """

    statistiques = {}

    for cookie in cookies:
        host = cookie['host']
        valeur = urllib.parse.unquote(cookie['value'])  
        if host not in statistiques:
            statistiques[host] = {"host": host, "data": {key: 0 for key in data}}

        for key, item in data.items():
            count = count_matches(valeur, item)
            statistiques[host]["data"][key] += count

    statistiques_formatees = {
        host: {key: count for key, count in host_data["data"].items()}
        for host, host_data in statistiques.items()
    }

    return statistiques_formatees


    






def count_matches(text, item):
    """
    Compte combien de fois les éléments de 'item' apparaissent dans 'text'.
    'item' peut être une str, une list ou un dict.
    La recherche est insensible à la casse.
    """
    
    # time.sleep(1)

    text_lower = text.lower()
    count = 0

    if isinstance(item, list):
        for e in item:
            if e.lower() in text_lower:
                count += 1
    elif isinstance(item, dict):
        for val in item.values():
            if str(val).lower() in text_lower:
                count += 1
    else:  # str
        mots = item.lower().split()
        for m in mots:
            if m in text_lower:
                count += 1
    return count