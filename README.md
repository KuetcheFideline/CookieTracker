# Cookie & DOM Tracker

Outil d'analyse des donnees stockees par les navigateurs (cookies et DOM) pour detecter les informations personnelles et les tokens suspects.

---

## Table des matieres

- [Installation Rapide](#installation-rapide)
- [Description](#description)
- [Fichiers Generes](#fichiers-generes)
- [Fonctionnalites](#fonctionnalites)
- [Installation Normale](#installation-normale)
- [Utilisation](#utilisation)
- [Partage des Resultats](#partage-des-resultats)

---

## Installation Rapide

### Linux

1. Telechargez le fichier `main` depuis le dossier `dist`
2. Donnez les droits d'execution:
   ```bash
   sudo chmod +x main
   ```
3. Lancez le programme:
   ```bash
   ./main
   ```

### Windows

1. Ouvrez le terminal en mode Administrateur
2. Naviguez vers l'emplacement du fichier
3. Lancez le programme:
   ```bash
   .\mainW.exe
   ```

**IMPORTANT**: Fermez tous les navigateurs avant de lancer le script.

---

## Description

Cet outil analyse les donnees stockees par les navigateurs web pour identifier:
- Les informations personnelles (nom, email, adresse, etc.)
- Les tokens decodes (JWT, Base64)
- Les tokens suspects (session IDs, API keys, UUIDs, etc.)
- Les emails detectes dans les cookies et le DOM

Le script:
1. Demande un profil utilisateur via un formulaire interactif
2. Analyse les navigateurs selectionnes (Firefox, Chrome, etc.)
3. Genere des fichiers JSON avec les resultats
4. Affiche un resume statistique detaille

---

## Fichiers Generes

Le script genere 4 fichiers JSON:

### Fichiers Complets (verification locale)
- `result_cookies.json` - Toutes les donnees des cookies
- `result_dom.json` - Toutes les donnees du DOM

### Fichiers Nettoyes (a partager)
- `result_cleaned_cookies.json` - Statistiques anonymisees des cookies
- `result_cleaned_dom.json` - Statistiques anonymisees du DOM

**Note**: Les fichiers nettoyes contiennent uniquement des compteurs et statistiques, sans les valeurs personnelles.

---

## Fonctionnalites

### Resume Statistique
A la fin de l'analyse, un resume detaille affiche:
- Nombre de domaines analyses
- Informations personnelles trouvees (exact + variantes)
- Tokens decodes avec informations personnelles
- Emails detectes
- Tokens suspects par type (session_id, api_key, uuid, etc.)

### Detection Avancee
- Detection de tous les emails (pas seulement ceux du profil)
- Detection des User-Agents
- Detection des tokens decodes (JWT/Base64) avec informations personnelles
- Exclusion automatique des patterns de navigation du total

### Fichiers Nettoyes
Les fichiers nettoyes incluent:
- Statistiques par domaine
- Comptage par type d'information
- Breakdown des tokens suspects par type
- Informations personnelles trouvees dans les tokens decodes
- Aucune donnee personnelle brute

---

## Installation Normale

### Linux

1. Creez un environnement virtuel:
   ```bash
   python3 -m venv env
   ```

2. Activez l'environnement:
   ```bash
   source env/bin/activate
   ```

3. Installez les dependances:
   ```bash
   pip install -r requirements.txt
   ```

4. Lancez le programme:
   ```bash
   python main.py
   ```

### Windows

1. Creez un environnement virtuel:
   ```bash
   python -m venv env
   ```

2. Activez l'environnement:
   ```bash
   .\env\Scripts\activate
   ```

3. Installez les dependances:
   ```bash
   pip install -r requirements.txt
   ```

4. Lancez le programme:
   ```bash
   python mainW.py
   ```

---

## Utilisation

1. Lancez le script
2. Remplissez le formulaire de profil utilisateur
3. Selectionnez les navigateurs a analyser
4. Attendez la fin de l'analyse
5. Consultez le resume statistique affiche
6. Recuperez les fichiers nettoyes pour partage

---

## Partage des Resultats

Deposez les fichiers suivants dans le depot Google Drive:
- `result_cleaned_cookies.json`
- `result_cleaned_dom.json`

**Lien Drive**: [https://drive.google.com/drive/folders/1q0xpeikKirlZ5dfc8Q0O23MA2EgA2I-U?usp=sharing](https://drive.google.com/drive/folders/1q0xpeikKirlZ5dfc8Q0O23MA2EgA2I-U?usp=sharing)

**Ne partagez pas** les fichiers complets (`result_cookies.json` et `result_dom.json`). Ils sont uniquement pour verification locale.

---

# English Version

## Cookie & DOM Tracker

Tool for analyzing data stored by web browsers (cookies and DOM) to detect personal information and suspicious tokens.

---

## Table of Contents

- [Quick Installation](#quick-installation-1)
- [Description](#description-1)
- [Generated Files](#generated-files)
- [Features](#features)
- [Normal Installation](#normal-installation-1)
- [Usage](#usage-1)
- [Sharing Results](#sharing-results)

---

## Quick Installation

### Linux

1. Download the `main` file from the `dist` folder
2. Grant execution rights:
   ```bash
   sudo chmod +x main
   ```
3. Run the program:
   ```bash
   ./main
   ```

### Windows

1. Open terminal as Administrator
2. Navigate to the file location
3. Run the program:
   ```bash
   .\mainW.exe
   ```

**IMPORTANT**: Close all browsers before running the script.

---

## Description

This tool analyzes data stored by web browsers to identify:
- Personal information (name, email, address, etc.)
- Decoded tokens (JWT, Base64)
- Suspicious tokens (session IDs, API keys, UUIDs, etc.)
- Detected emails in cookies and DOM

The script:
1. Requests a user profile via an interactive form
2. Analyzes selected browsers (Firefox, Chrome, etc.)
3. Generates JSON files with results
4. Displays a detailed statistical summary

---

## Generated Files

The script generates 4 JSON files:

### Complete Files (local verification)
- `result_cookies.json` - All cookie data
- `result_dom.json` - All DOM data

### Cleaned Files (to share)
- `result_cleaned_cookies.json` - Anonymized cookie statistics
- `result_cleaned_dom.json` - Anonymized DOM statistics

**Note**: Cleaned files contain only counters and statistics, without personal values.

---

## Features

### Statistical Summary
At the end of analysis, a detailed summary displays:
- Number of analyzed domains
- Personal information found (exact + variants)
- Decoded tokens with personal information
- Detected emails
- Suspicious tokens by type (session_id, api_key, uuid, etc.)

### Advanced Detection
- Detection of all emails (not just profile ones)
- User-Agent detection
- Decoded token detection (JWT/Base64) with personal information
- Automatic exclusion of navigation patterns from total

### Cleaned Files
Cleaned files include:
- Statistics per domain
- Count by information type
- Breakdown of suspicious tokens by type
- Personal information found in decoded tokens
- No raw personal data

---

## Normal Installation

### Linux

1. Create a virtual environment:
   ```bash
   python3 -m venv env
   ```

2. Activate the environment:
   ```bash
   source env/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the program:
   ```bash
   python main.py
   ```

### Windows

1. Create a virtual environment:
   ```bash
   python -m venv env
   ```

2. Activate the environment:
   ```bash
   .\env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the program:
   ```bash
   python mainW.py
   ```

---

## Usage

1. Run the script
2. Fill in the user profile form
3. Select browsers to analyze
4. Wait for analysis completion
5. Review the displayed statistical summary
6. Retrieve cleaned files for sharing

---

## Sharing Results

Upload the following files to the Google Drive repository:
- `result_cleaned_cookies.json`
- `result_cleaned_dom.json`

**Drive Link**: [https://drive.google.com/drive/folders/1q0xpeikKirlZ5dfc8Q0O23MA2EgA2I-U?usp=sharing](https://drive.google.com/drive/folders/1q0xpeikKirlZ5dfc8Q0O23MA2EgA2I-U?usp=sharing)

**Do not share** the complete files (`result_cookies.json` and `result_dom.json`). They are for local verification only.
