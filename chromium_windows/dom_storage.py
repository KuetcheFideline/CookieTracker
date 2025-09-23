import os
import shutil
import uuid
import json
import plyvel 


def get_dom_storage_data(session_id, browser_name, path_dom_storage):
    # Copier le dossier leveldb dans un répertoire temporaire pour analyse
    temp_leveldb_dir = f"chromium_windows/output/db/{browser_name}_domstorage_{session_id}"
    os.makedirs(temp_leveldb_dir, exist_ok=True)

    # Copie tous les fichiers leveldb
    for file_name in os.listdir(path_dom_storage):
        full_file_path = os.path.join(path_dom_storage, file_name)
        if os.path.isfile(full_file_path):
            shutil.copy2(full_file_path, os.path.join(temp_leveldb_dir, file_name))

    # Charger la base de données leveldb
    # print(f"[INFO] Lecture de la base DOM Storage depuis : {temp_leveldb_dir}")
    try:
        db = plyvel.DB(temp_leveldb_dir, create_if_missing=False)
    except Exception as e:
        print(f"[ERROR] Impossible d’ouvrir leveldb : {e}")
        return None

    grouped_data = {}

    for key_raw, value_raw in db:
        try:
            key = key_raw.decode("utf-8", errors="ignore")
            value = value_raw.decode("utf-8", errors="ignore")
        except Exception as e:
            continue  # Skip non-decodable entries

        # Filtrage simple : ne prendre que les clés contenant un host ou des infos utiles
        if "http" in key or "https" in key:
            origin = key.split("_")[0]  # clé souvent formatée comme "https_www.example.com_0"
            if origin not in grouped_data:
                grouped_data[origin] = []

            grouped_data[origin].append({
                "key": key,
                "value": value
            })

    db.close()

    # Écrire le résultat dans un fichier JSON
    directory = f"chromium_windows/output/json"
    os.makedirs(directory, exist_ok=True)

    json_file_path = os.path.join(directory, f"{browser_name}_domstorage_{session_id}.json")

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(grouped_data, f, indent=4, ensure_ascii=False)

    print(f"[INFO] Fichier DOM Storage sauvegardé : {json_file_path}")
    return json_file_path
