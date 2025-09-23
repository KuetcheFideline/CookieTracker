import sqlite3
import os 
class PersonalCookies:
    def __init__(self, db, last_run):
        self.last_run = last_run
        self.db = sqlite3.connect(db)

    def filter_data_by_date(self, user):
        """Filtrer les cookies en fonction de la date et retourner les statistiques des informations personnelles."""
        cursor = self.db.cursor()
        personal = user
        if self.last_run == 0:
            # Récupérer toutes les données de cookies
            data = cursor.execute('SELECT * FROM moz_cookies').fetchall()
        else:
            # Récupérer les données de cookies créées après la dernière exécution
            data = cursor.execute(f'SELECT * FROM moz_cookies WHERE creationTime>{self.last_run}').fetchall()
        cookies_by_host = {}
        for row in data:
            host = row[4]
            cookie_dict = {
                "name": row[2],
                "value": row[3],
                "path": row[5],
                "expires_utc": row[7]
            }
            if host not in cookies_by_host:
                cookies_by_host[host] = []
            cookies_by_host[host].append(cookie_dict)

        return cookies_by_host











class PersonalDOM:
    def __init__(self, db, last_run):
        self.last_run = last_run
        self.db = db

   
    @staticmethod
    def bytes_to_str(obj):
        if isinstance(obj, dict):
            return {k: PersonalDOM.bytes_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [PersonalDOM.bytes_to_str(i) for i in obj]
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        else:
            return obj
    def filter_data_by_date(self, user):
        """Filtrer les cookies en fonction de la date et retourner toutes les paires clé/valeur du DOM Storage."""
        data = {}

        for elt in os.listdir(self.db):
            ls_db = os.path.join(self.db, elt)
            for item in os.listdir(ls_db):
                if item == 'ls':
                    db_path = os.path.join(ls_db, item, 'data.sqlite')
                    if not os.path.exists(db_path):
                        continue
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    sql = "SELECT key, value FROM data"
                    dat = cursor.execute(sql).fetchall()
                    conn.close()
                    donnes = {}
                    for row in dat:
                        key = row[0]
                        value = row[1]
                        donnes[key] = value  
                    data[elt] = donnes
        return self.bytes_to_str(data)
        

            
            
                    

        