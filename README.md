
# **Script d'Analyse des Données Navigateurs (Cookies & DOM)**

## Langue : Français / Language: English

---

### **But / Purpose**

Le script analyse les données stockées par les navigateurs (DOM et cookies) à partir d'un profil utilisateur fourni via un formulaire en ligne de commande, puis génère des résultats statistiques en JSON.
This script analyzes data stored by browsers (DOM & cookies) from a user profile provided via a command-line form, and then generates statistical results in JSON.

---

## **Installation rapide / Quick Installation**

### **Sur Linux / On Linux**

1. **Téléchargement** : Dirigez-vous vers le dossier `dist` et téléchargez le fichier `main`.
2. **Donner les droits d'exécution** :

   ```bash
   sudo chmod +x main
   ```
3. **Lancer le Programme** :

   ```bash
   ./main
   ```

### **Sur Windows / On Windows**

1. **Ouvrir le terminal en mode super-utilisateur** (Administrateur)
2. **Se diriger vers l'emplacement du fichier**
3. **Lancer le Programme** :

   ```bash
   .\mainW.exe
   ```
##  <p style="color:red; font-weight: bold;">Avant de lancer le script, il est impératif de bien fermer tous les navigateurs.</p>

---

## **1. Description rapide / Quick Description**

Le script :
The script:

* Demande un **profil utilisateur** via un formulaire en ligne de commande (nom, email, adresse, navigateurs à analyser, etc.).
  Asks for a **user profile** through a command-line form (name, email, address, browsers to analyze, etc.).
* Traite les navigateurs supportés (ex. Firefox, Chrome) et collecte les données DOM et cookies.
  Processes supported browsers (e.g., Firefox, Chrome) and collects DOM and cookie data.
* Génère **4 fichiers JSON** : deux bruts (avec la colonne `matches`) et deux nettoyés (sans `matches`) pour l'analyse.
  Generates **4 JSON files**: two raw (with the `matches` column) and two "clean" (without `matches`) for analysis.
* En cas d'erreur sur un navigateur, le script **continue** avec les autres navigateurs.
  In case of an error with a browser, the script **continues** with the other browsers.

---

## **2. À savoir / Notes**

* **Fichiers générés / Files Generated**:

  * `result_cookies.json` → Cookies bruts (avec matches) / Raw cookies (with matches)
  * `result_dom.json` → DOM brut (avec matches) / Raw DOM (with matches)
  * `result_cookies_clean.json` → Cookies nettoyés (à envoyer) / Cleaned cookies (to send)
  * `result_dom_clean.json` → DOM nettoyé (à envoyer) / Cleaned DOM (to send)

Les fichiers nettoyés (`*_clean.json`) doivent être envoyés pour analyse, tandis que les fichiers bruts (`result_*.json`) sont pour la vérification locale et le debug.


## **3. Action requise / Action Required**

Déposez les deux fichiers suivants dans le dépôt Google Drive pour analyse :
Please upload the following two files to the Google Drive repository for analysis:

* `result_cookies_clean.json`
* `result_dom_clean.json`

**Dépôt Drive / Drive Folder** :
[https://drive.google.com/drive/folders/1q0xpeikKirlZ5dfc8Q0O23MA2EgA2I-U?usp=sharing](https://drive.google.com/drive/folders/1q0xpeikKirlZ5dfc8Q0O23MA2EgA2I-U?usp=sharing)

Les fichiers bruts (comme `result_cookies.json` et `result_dom.json`) sont uniquement pour la vérification locale. Ne les envoyez pas.
The raw files (such as `result_cookies.json` and `result_dom.json`) are only for local verification. Do not send them.
---

## **4. Fichier `runtime.txt`**

* Contient le **compteur d’exécution** et la **date** de la dernière exécution.
  Contains the **execution counter** and the **date** of the last execution.
* À chaque lancement, le compteur est incrémenté automatiquement.
  Each time the script is run, the counter is automatically incremented.
* **Pour réinitialiser** le compteur : supprimer le fichier `runtime.txt` avant de relancer le script.
  **To reset** the counter: delete the `runtime.txt` file before running the script again.

Voici la section mise à jour pour l'installation normale avec un environnement virtuel et l'installation des dépendances :

---

## **5. Installation Normale / Normal Installation**

### **Sur Linux / On Linux**

1. **Créer un environnement virtuel / Create a virtual environment** :

   ```bash
   python3 -m venv env
   ```

2. **Activer l'environnement virtuel / Activate the virtual environment** :

   ```bash
   source env/bin/activate
   ```

3. **Installer les dépendances / Install the dependencies** :

   ```bash
   pip install -r requirements.txt
   ```

4. **Lancer le programme / Run the program** :

   ```bash
   python main.py
   ```

### **Sur Windows / On Windows**

1. **Créer un environnement virtuel / Create a virtual environment** :

   ```bash
   python -m venv env
   ```

2. **Activer l'environnement virtuel / Activate the virtual environment** :

   ```bash
   .\env\Scripts\activate
   ```

3. **Installer les dépendances / Install the dependencies** :

   ```bash
   pip install -r requirements.txt
   ```

4. **Lancer le programme / Run the program** :

   ```bash
   python mainW.py
   ```
