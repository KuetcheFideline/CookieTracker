import sqlite3
import shutil
import os
import json
from pathlib import Path
import configparser

class Firefox:
    """
    Class for Firefox

    """

    def __init__(self, os_name):

        self.os_name = os_name

        # self.data_path = data_path
        self.data = None
        self.cookies_path = None
        self.dom_path=None

        # destination_dir = "data/"
        # destination_file = "data/data.json"
        #
        # os.makedirs(destination_dir, exist_ok=True)
        #
        # shutil.copy(self.data_path, destination_file)

    def get_cookies_file_path(self):
            import configparser
            from pathlib import Path
            import os

            profile_dir = None

            # 1️⃣ Déterminer le dossier Firefox selon l'OS
            if self.os_name != "Windows":
                profile_dir = Path("~/.mozilla/firefox/").expanduser()
                if not profile_dir.exists():
                    profile_dir = Path("~/snap/firefox/common/.mozilla/firefox/").expanduser()
            else:
                profile_dir = Path("~/AppData/Roaming/Mozilla/Firefox/").expanduser()

            if profile_dir is None:
                raise Exception("Cannot determine Firefox profile directory")

            # 2️⃣ Lire profiles.ini
            profiles_ini_path = profile_dir / "profiles.ini"
            if not profiles_ini_path.exists():
                # Si Linux/Snap, tenter Snap
                if self.os_name != "Windows":
                    profile_dir = Path("~/snap/firefox/common/.mozilla/firefox/").expanduser()
                    profiles_ini_path = profile_dir / "profiles.ini"
                    if not profiles_ini_path.exists():
                        raise FileNotFoundError("Firefox profiles.ini file not found.")
                else:
                    raise FileNotFoundError("Firefox profiles.ini file not found.")

            profiles_ini = configparser.ConfigParser()
            profiles_ini.read(profiles_ini_path)

            profile_path = None

            # 3️⃣ Firefox >= 67
            installs = [s for s in profiles_ini.sections() if s.startswith("Install")]
            if installs:
                profile_path = profiles_ini[installs[0]]["Default"]
            else:
                # Firefox < 67
                profiles = [s for s in profiles_ini.sections() if s.startswith("Profile")]
                for p in profiles:
                    if profiles_ini[p].get("Default") == "1":
                        profile_path = profiles_ini[p]["Path"]
                        break
                else:
                    if profiles:
                        profile_path = profiles_ini[profiles[0]]["Path"]
                    else:
                        raise Exception(f"No profiles found at {profile_dir}")

            # 4️⃣ Construire le chemin final vers cookies.sqlite
            if self.os_name == "Windows":
                profile_dir = profile_dir / "Profiles" / profile_path
            else:
                profile_dir = profile_dir / profile_path

            self.cookies_path = profile_dir / "cookies.sqlite"

            if not self.cookies_path.exists():
                raise FileNotFoundError(f"Cookies database not found at {self.cookies_path}")


    def get_domstorage_file_path(self):
            profile_dir = None

            if self.os_name != "Windows":
                profile_dir = Path("~/.mozilla/firefox/").expanduser()
                if not profile_dir.exists():
                    profile_dir = Path("~/snap/firefox/common/.mozilla/firefox/").expanduser()
            else:
                profile_dir = Path("~/AppData/Roaming/Mozilla/Firefox/").expanduser()

          
            # Find the default profile directory
            profile_ini = profile_dir / "profiles.ini"
      

            if not profile_ini.exists():
                profile_dir = Path("~/snap/firefox/common/.mozilla/firefox/").expanduser()
                profile_ini= profile_dir / "profiles.ini"
                if not profile_ini.exists():
                    raise FileNotFoundError("Firefox profiles.ini file not found.")

            profiles_ini = configparser.ConfigParser()
            profiles_ini.read(profile_ini)

            installs = [s for s in profiles_ini.sections() if s.startswith("Install")]
            if installs:  # Firefox >= 67
                profile = profiles_ini[installs[0]]["Default"]
            else:  # Firefox < 67
                profiles = [s for s in profiles_ini.sections() if s.startswith("Profile")]
                for p in profiles:
                    if profiles_ini[p].get("Default") == "1":
                        profile = profiles_ini[p]["Path"]
                        break
                else:
                    if profiles:
                        profile = profiles_ini[profiles[0]]["Path"]
                    else:
                        raise Exception("No profiles found at {}".format(profile_dir))

            # Ajustement pour Windows
           
            profile_path = profile_dir /profile

              
            # 📌 Dossier du DOM Storage moderne
            domstorage_dir = profile_path / "storage" / "default"

            if not domstorage_dir.exists():
                raise FileNotFoundError(f"DOM Storage directory not found at {domstorage_dir}")

            self.dom_path = domstorage_dir

    

    def move_cookies_file_to_temp_dir(self):
                temp_dir = "tmp/"
                temp_file = "tmp/cookies.sqlite"

                os.makedirs(temp_dir, exist_ok=True)
                if shutil.copy(self.cookies_path, temp_dir):

                    print("--------Copy done: ready to hack the code ha ha ha ---------")

                pass
    def move_dom_file_to_temp_dir(self):
                temp_dir = "tmp2/"
                temp_file = "tmp2/webappsstore.sqlite"

                os.makedirs(temp_dir, exist_ok=True)
                if shutil.copy(self.dom_path, temp_dir):

                    print("--------Copy done: ready to hack the code ha ha ha ---------")

                pass
    def print_os(self):
                self.get_cookies_file_path()
                self.get_domstorage_file_path()
                # self.move_cookies_file_to_temp_dir()
