import os
import shutil
import plyvel
import json
from multiprocessing import Process ,Queue




def openDb(db_path, queue):
    try:
        db = plyvel.DB(db_path, create_if_missing=False, error_if_exists=False, write_buffer_size=0)
        grouped_data = {}

        for key_raw, value_raw in db:
            try:
                key = key_raw.decode("utf-8", errors="ignore")
                value = value_raw.decode("utf-8", errors="ignore")
            except Exception:
                continue  # Skip non-decodable entries

            if "http" in key or "https" in key:
                origin = key.split("_")[0]
                if origin not in grouped_data:
                    grouped_data[origin] = []
                grouped_data[origin].append({
                    "key": key,
                    "value": value
                })

        db.close()
        queue.put({"status": "success", "data": grouped_data})
    except Exception as e:
        print(str(e))
        queue.put({"status": "error", "error": str(e)})

def safe_open(path):
    q = Queue()
    p = Process(target=openDb, args=(path, q))
    p.start()
    p.join()
    result = q.get() if not q.empty() else None
    if result is None:
        print("[ERROR] Aucun résultat retourné par le process.")
        return None
    if result.get("status") == "error":
        print(f"[ERROR] Impossible d’ouvrir leveldb : {result.get('error')}")
        return None
    print("[DEBUG] grouped_data extrait avec succès.")
    return result.get("data")

def get_dom_storage_data(session_id, browser_name, path_dom_storage):
    import traceback
    print(f"[DEBUG] Test d'ouverture directe du dossier LevelDB : {path_dom_storage}")
    if not os.path.exists(path_dom_storage):
        print(f"[ERREUR] Le dossier LevelDB n'existe pas : {path_dom_storage}")
        return None
    if not os.listdir(path_dom_storage):
        print(f"[ERREUR] Le dossier LevelDB est vide : {path_dom_storage}")
        return None
    try:
        db = plyvel.DB(path_dom_storage, create_if_missing=False)
        print("[OK] Ouverture de la base LevelDB réussie.")
        grouped_data = {}
        count = 0
        for key_raw, value_raw in db:
            count += 1
            try:
                key = key_raw.decode("utf-8", errors="ignore")
                value = value_raw.decode("utf-8", errors="ignore")
            except Exception:
                continue
            origin = key.split("_")[0]
            if origin not in grouped_data:
                grouped_data[origin] = []
                grouped_data[origin].append({
                    "key": key,
                    "value": value
                })
           
        db.close()
    except Exception as e:
        print(f"[ERREUR] Impossible d'ouvrir la base LevelDB: {e}")
        print("[DEBUG] Traceback complet :")
        traceback.print_exc()
        return None
    # Écrire le résultat dans un fichier JSON
    directory = f"chromium_windows/output/json"
    os.makedirs(directory, exist_ok=True)
    json_file_path = os.path.join(directory, f"{browser_name}_domstorage_{session_id}.json")
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(grouped_data, f, indent=4, ensure_ascii=False)
    print(f"[INFO] Fichier DOM Storage sauvegardé : {json_file_path}")
    return json_file_path
