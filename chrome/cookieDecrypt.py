import sqlite3
import os
import json
import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
import secretstorage



class Cookie:
    # --- Cipher v10 (clé statique "peanuts") ---
    _cipher_v10 = AES.new(
        key=PBKDF2(
            password=b"peanuts",
            salt=b"saltysalt",
            dkLen=16,
            count=1
        ),
        mode=AES.MODE_CBC,
        iv=(b' ' * 16)
    )

    # --- Master keys Chrome/Chromium (v11) ---
    _master_keys = None

    def __init__(self, row):
        """
        row : sqlite3.Row ou dict contenant les colonnes de la table cookies
        """
        for key in row.keys():
            setattr(self, key, row[key])

    @staticmethod
    def get_master_keys():
        """Récupère toutes les master keys disponibles via libsecret (Linux)."""
        if Cookie._master_keys:
            return Cookie._master_keys

        bus = secretstorage.dbus_init()
        collection = secretstorage.get_default_collection(bus)
        keys = []
        for item in collection.get_all_items():
            label = item.get_label()
            if label in ("Chrome Safe Storage", "Chromium Safe Storage"):
                secret = item.get_secret()  # bytes
                key = PBKDF2(secret, b"saltysalt", 16, 1)
                keys.append(key)
        if not keys:
            raise RuntimeError("Impossible de récupérer la master key depuis libsecret")
        Cookie._master_keys = keys
        return keys

    @property
    def decrypted_value(self):
        if not self.encrypted_value:
            return None

        # --- v10 ---
        if self.encrypted_value.startswith(b"v10"):
            prefix = b"v10"
            ciphertext = self.encrypted_value[len(prefix):]
            plaintext = self._cipher_v10.decrypt(ciphertext)
            n_padding = plaintext[-1]
            if not all(p == n_padding for p in plaintext[-n_padding:]):
                return None
            value_slice = slice(32, -n_padding)
            return plaintext[value_slice].decode("utf8")

        # --- v11 ---
        elif self.encrypted_value.startswith(b"v11"):
            master_keys = self.get_master_keys()
            data = self.encrypted_value[3:]  # enlever "v11"
            iv = data[:12]
            payload = data[12:-16]
            tag = data[-16:]

            for master_key in master_keys:
                try:
                    cipher = AES.new(master_key, AES.MODE_GCM, iv)
                    decrypted = cipher.decrypt_and_verify(payload, tag)
                    return decrypted.decode("utf-8")
                except Exception as e:
                    continue  # essaie la clé suivante

            # aucune clé n'a fonctionné
            print("MAC check failed pour toutes les master keys")
            return None

        return None  # inconnu

    def __str__(self):
        return (
            f"Nom: {getattr(self, 'name', None)}, "
            f"Domaine: {getattr(self, 'host_key', None)}, "
            f"Valeur brute: {getattr(self, 'value', None)}, "
            f"Valeur déchiffrée: {self.decrypted_value}"
        )

    def to_dict(self):
        """Représentation exploitable du cookie."""
        return {
            "name": getattr(self, "name", None),
            "host": getattr(self, "host_key", None),
            "value": getattr(self, "value", None),
            "decrypted_value": self.decrypted_value,
            "path": getattr(self, "path", None),
            "expires_utc": getattr(self, "expires_utc", None),
        }
