import plyvel
import sys
import traceback
import os

leveldb_path = r"C:/Users/tp/AppData/Local/Google/Chrome/User Data/Default/Local Storage/leveldb"

print("[DEBUG] Début du test d'ouverture LevelDB...")
try:
    if not os.path.exists(leveldb_path):
        print(f"[ERREUR] Le dossier LevelDB n'existe pas : {leveldb_path}")
        sys.exit(2)
    if not os.listdir(leveldb_path):
        print(f"[ERREUR] Le dossier LevelDB est vide : {leveldb_path}")
        sys.exit(3)
    db = plyvel.DB(leveldb_path, create_if_missing=False)
    print("[OK] Ouverture de la base LevelDB réussie.")
    count = 0
    for key, value in db:
        count += 1
        if count <= 5:
            print(f"Clé: {key[:50]}... | Valeur: {value[:50]}...")
    print(f"Nombre total d'entrées: {count}")
    db.close()
except KeyboardInterrupt:
    print("[ERREUR] Interruption clavier (KeyboardInterrupt). Le processus a été stoppé par l'utilisateur.")
    sys.exit(4)
except SystemExit:
    print("[ERREUR] Le processus s'est terminé brutalement (SystemExit).")
    sys.exit(5)
except Exception as e:
    print(f"[ERREUR] Impossible d'ouvrir la base LevelDB: {e}")
    print("[DEBUG] Traceback complet :")
    traceback.print_exc()
    sys.exit(1)
except:
    print("[ERREUR] Le processus est mort de manière inexpliquée.")
    traceback.print_exc()
    sys.exit(6)
