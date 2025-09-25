# Script d'analyse des données navigateurs (cookies & DOM)

**Langue :** Français  
**But :** Ce script récupère et analyse des données stockées par les navigateurs (DOM & cookies) à partir d'un profil utilisateur fourni via un formulaire en ligne de commande, puis génère des résultats JSON.

---

## 1. Description rapide
Le script :
- Demande au lancement un **profil utilisateur** via un formulaire terminal (nom, emails, adresses, navigateurs à analyser, etc.).  
- Traite les navigateurs supportés (ex. Firefox, Chrome) et collecte les données DOM et cookies.  
- Génère **4 fichiers JSON** : deux bruts (avec la colonne `matches`) et deux « clean » (sans `matches`) à transmettre pour analyse.  
- En cas d'erreur sur un navigateur, le script **continue** avec les autres navigateurs.

---

## 2.A savoir 


## 3.Utilisation ### Sur Linux
1. Donner les droits d'exécution :  
   ```bash
   sudo chmod +x main
2. Lancer le Programme :
   ```bash 
     ./main


## 4.Utilisation ### Sur Windows
1. Ouvrir le terminal en mode Super utilisateur 
2. Se diriger vers l'emplacement du fichier 
3. lancer le Programme  
      ```bash 
    .\mainW.exe
 

## 6. Fichiers générés

result_cookies.json → cookies bruts (avec matches)

result_dom.json → DOM brut (avec matches)

result_cookies_clean.json → cookies nettoyés (à envoyer)

result_dom_clean.json → DOM nettoyé (à envoyer)

Les fichiers *_clean.json sont destinés à être transmis.

Action requise : Déposez les deux fichiers suivants dans le dépôt Google Drive pour partage/analyse :

result_cookies_clean.json

result_dom_clean.json

Dépôt Drive : https://drive.google.com/drive/folders/1q0xpeikKirlZ5dfc8Q0O23MA2EgA2I-U?usp=sharing

Les fichiers bruts (result_*.json) servent à la vérification locale.Ne pas envoyer 

##  5.aller plus loin 

Le script produit les fichiers suivants :

- `result_cookies.json` → cookies bruts (contient la clé `matches`)  
- `result_dom.json` → DOM brut (contient la clé `matches`)  
- `result_cookies_clean.json` → cookies nettoyés (**à envoyer**)  
- `result_dom_clean.json` → DOM nettoyé (**à envoyer**)

Les fichiers `*_clean.json` sont destinés à être transmis pour analyse.  
Les fichiers bruts (`result_*.json`) servent à la **vérification locale** et au debug.

---

## 7. Fichier `runtime.txt`

- Contient le **compteur d’exécution** et la **date** de la dernière exécution.  
- À chaque lancement, le compteur est incrémenté automatiquement.  
- **Pour réinitialiser** le compteur : supprimer le fichier `runtime.txt` avant de relancer le script.



