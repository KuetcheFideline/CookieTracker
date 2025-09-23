import os
import plyvel  
import json
from chrome.helpers import count_matches

def storage_config(browser, storage_type="Local"):
    """Récupère tous les dossiers de LocalStorage ou SessionStorage de tous les profils."""
    storage_dirs = []


    title = browser

    if title == "chrome":
        base_path = os.path.expanduser("~/.config/google-chrome")
        snap_path = os.path.expanduser("~/snap/chromium/common/chromium")
    elif title == "chromium":
        base_path = os.path.expanduser("~/.config/chromium")
        snap_path = os.path.expanduser("~/snap/chromium/common/chromium")
    elif title == "Brave":
        base_path = os.path.expanduser("~/.config/BraveSoftware/Brave-Browser")
        snap_path = None
    elif title == "Edge":
        base_path = os.path.expanduser("~/.config/microsoft-edge")
        snap_path = None
    else:
        return []

    folders = []

    if base_path and os.path.exists(base_path):
        profiles = ["Default"] + [d for d in os.listdir(base_path) if d.startswith("Profile")]
        for p in profiles:
            path = os.path.join(base_path, p, f"Local Storage/leveldb")
            if os.path.exists(path):
                
                folders.append(path)

    if not folders and snap_path and os.path.exists(snap_path):
        profiles = ["Default"] + [d for d in os.listdir(snap_path) if d.startswith("Profile")]
        for p in profiles:
            path = os.path.join(snap_path, p, f"Local Storage/leveldb")
            if os.path.exists(path):
                folders.append(path)

    return folders




def read_storage(browser, storage_type="local"):
    """Lit et fusionne LocalStorage ou SessionStorage pour tous les profils."""
    folders = storage_config(browser, storage_type)
    all_data = {}

    for folder in folders:
        try:
            db = plyvel.DB(folder, compression=None)
        except Exception as e:
            print(f"Une erreur s'est produite lors de l'ouverture de la base de données : {e}")
            continue  
    

        data = {}
        main_separator = '\x00\x01'   
        embedded_separator = '\x00'  

        for key, value in db:
            raw_key = key.decode('utf-8', errors='ignore')
            value_str = value.decode('utf-8', errors='ignore')

            if "chrome-extension://" in raw_key:
                continue

            origin1 = ''
            origin2 = ''
            final_key = ''

            if main_separator in raw_key:
                origin1, final_key = raw_key.split(main_separator, 1)
                if embedded_separator in origin1:
                    origin2, origin1 = origin1.split(embedded_separator, 1)
                else:
                    origin2 = ''
            else:
                origin1 = raw_key
                origin2 = ''
                final_key = ''
            keys = origin1 + origin2
            # Initialisation sécurisée
            if origin1 not in data:
                data[keys] = {}
            data[origin1]= {final_key: value_str}

        db.close()

        # Fusionner dans all_data
        for k1, v1 in data.items():
            if k1 not in all_data:
                all_data[k1] = v1
            else:
                for k2, v2 in v1.items():
                    if k2 not in all_data[k1]:
                        all_data[k1][k2] = v2
                    else:
                        all_data[k1][k2].update(v2)
    return all_data


def process_val2(val2, item):
    """
    Parcourt récursivement val2 (dict, list ou str) et compte les correspondances avec item.
    """
    count = 0

    if isinstance(val2, dict):
        for v in val2.values():
            count += process_val2(v, item)
    elif isinstance(val2, list):
        for v in val2:
            count += process_val2(v, item)
    else:
        # val2 est un élément final (str, bool, int...)
        val_str = str(val2)
        count += count_matches(val_str, item)

    return count


def third(third_lists, data):
    statistiques_formatees = {}  

    for third_list in third_lists:
        for key, item in data.items():
            for url in third_list:
                for final, val in url.items():
                    if final.startswith("VERSION"):
                        continue
                    count = 0
                    if isinstance(val, dict):
                      for val2 in val.values():
                            count += process_val2(val2, item)

                    if final not in statistiques_formatees:
                        statistiques_formatees[final] = {}
                    statistiques_formatees[final][key] = count

    return statistiques_formatees


def transform(all_data):
    third_party = []
    first_party = []
    system = []

    for key, value in all_data.items():
        if key.startswith("META"):
            system.append({key: value})
        elif isinstance(value, dict):
            for subkey, subvalue in value.items():
                if subkey == "":  
                    first_party.append({key: subvalue})
                else: 
                    third_party.append({key: value})

    return [third_party, first_party, system]



