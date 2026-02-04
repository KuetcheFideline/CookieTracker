# Cookie & DOM Tracker

Outil d'analyse des donnees stockees par les navigateurs (cookies et DOM) pour detecter les informations personnelles et les tokens suspects.

---

## Table des matieres

- [Installation Rapide](#installation-rapide)
- [Description](#description)
- [Fichiers Generes](#fichiers-generes)
- [Fonctionnalites](#fonctionnalites)
- [Utilisation](#utilisation)
- [Partage des Resultats](#partage-des-resultats)

---

## Installation Rapide

### Linux

1. Telechargez le fichier `main` depuis le dossier `dist`
2. Donnez les droits d'execution:
   ```bash
       chmod +x main
   ```
3. Lancez le programme:
   ```bash
   ./main
   ```


**IMPORTANT**: Fermez tous les navigateurs avant de lancer le script.

---

## Description

Cet outil analyse les donnees stockees par les navigateurs web pour identifier:
- Les informations personnelles (nom, email, adresse,villes ,date de naissance  etc.)
- Les tokens decodes (JWT, Base64)
- Les tokens suspects (session IDs, API keys, UUIDs, etc.)
- Les emails detectes dans les cookies et le DOM

Le script:
1. Collecte le profil utilisateur via la ligne de commande
2. Analyse les navigateurs selectionnes (Firefox, Chrome, etc.)
3. Genere des fichiers JSON avec les resultats
4. Affiche un resume statistique detaille

---

## Fichiers Generes

Le script genere 4 fichiers JSON:

### Fichiers Complets (verification locale)
- `result_cookies.json` - Toutes les donnees des cookies
- `result_dom.json` - Toutes les donnees du DOM
- result_cleaned_cookies.json` - Statistiques anonymisees des cookies


### Fichiers Nettoyes (a partager)
- `- `result_global_stats.json` - Statistiques anonymisees du storage complet 

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
## Partage des Resultats

Deposez les fichiers suivants dans le depot Google Drive:
- `result_global_stats.json`

**Lien Drive**: [https://drive.google.com/drive/folders/1q0xpeikKirlZ5dfc8Q0O23MA2EgA2I-U?usp=sharing)

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
- - `result_cleaned_cookies.json` - Anonymized cookie statistics

### Cleaned Files (to share)

 - `result_global_stats.json` - Anonymized  Data storage statistics

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


### Files sended
Cleaned files include:
- Count by information type
- Breakdown of suspicious tokens by type
- Personal information found in decoded tokens
- No raw personal data

---





## Sharing Results

Upload the following files to the Google Drive repository:
- `result_global_stats.json`

**Do not share** the complete files (`result_cookies.json` and `result_dom.json`). They are for local verification only.
