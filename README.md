# 🕹️ PST - Button Quest

> **Projet Scientifique et Technique (PST 2A) — ESIEA**  
> Système de table/valise d'arcade interactive à deux lignes de jeu simultanées, alliant défis électroniques matériels (Raspberry Pi, I2C, GPIO) et épreuves logicielles via une interface web rétro-gaming.

---

## 📋 Présentation du Projet

**Button Quest** est un système de jeu interactif développé pour animer des stands et conventions. Deux joueurs ou équipes s'affrontent en parallèle sur deux lignes de production physiques (**Ligne 1** et **Ligne 2**). 

L'objectif : franchir **4 boîtes d'épreuves** mêlant adresse, logique, culture technique et crochetage en un minimum de temps. La progression est rythmée par des boutons d'arcade lumineux, des afficheurs 7 segments matériels et un tableau de bord web en temps réel.

### 🎮 Déroulement d'une partie (Les 4 Épreuves)

1. **Démarrage (`START`)** : Le joueur s'inscrit sur l'interface, choisit sa ligne et appuie sur le bouton physique **START** allumé pour lancer le chronomètre.
2. **Boîte 1 — Opération Dr. Maboul (Épreuve physique)** : Parcours d'adresse avec un anneau métallique le long d'un fil de cuivre sous tension logique. Chaque contact avec le fil inflige une **pénalité immédiate de +5 secondes** (affichée sur l'écran web et clignotant sur l'afficheur 7 segments). Valider la fin du parcours débloque le bouton **B1**.
3. **Boîte 2 — Mastermind Matrix (Épreuve logicielle)** : L'appui sur **B1** lance un Mastermind sur l'écran (combinaison secrète de 4 couleurs parmi 6, jouable à la souris ou au clavier via les raccourcis `K, R, B, P, Y, G`). Trouver le code allume le bouton **B2**.
4. **Boîte 3 — Survival Mission (Quiz technique)** : L'appui sur **B2** déclenche une série de 5 questions tirées aléatoirement depuis une banque de données CSV (Informatique, Électronique, Mathématiques, Physique, Culture Tech). Un score minimum de **4/5** est requis pour allumer le bouton **B3** (en cas d'échec, un nouveau quiz est généré).
5. **Boîte 4 — Crochetage / Lockpicking (Épreuve physique)** : L'appui sur **B3** active le dernier défi matériel. Le joueur doit crocheter le cadenas physique pour accéder au bouton final **B4**, stopper le chronomètre et enregistrer son score dans le classement général (*High Scores*).

---

## 🛠️ Architecture Matérielle & Logicielle

### Matériel (Hardware)
* **Unité centrale** : Raspberry Pi (contrôle du serveur web, de la base de données et du bus matériel).
* **Extensions d'entrées/sorties** : 2 modules **MCP23017** pilotés en **I2C** (adresses `0x20` et `0x21`) avec verrouillage thread-safe (`RLock`) et bouclier logiciel anti-rebond / anti-microcoupures I2C.
* **Affichage physique** : 2 afficheurs 4 digits 7 segments **TM1637** (un par ligne) affichant le chronomètre en temps réel et les animations de pénalité (`+5`).
* **Composants d'interaction** : Boutons d'arcade lumineux (LEDs + Switchs), circuit fil de cuivre Dr. Maboul (Start, Touch, End) et cadenas d'entraînement.

### Stack Technique (Software)
* **Backend** : Python 3, Flask (architecture modulaire par *Blueprints*), Multithreading.
* **Hardware Libraries** : `gpiozero`, `Adafruit-Blinka`, `adafruit-circuitpython-mcp230xx`, `raspberrypi-tm1637`.
* **Base de données** : MongoDB 4.4 conteneurisée via **Docker Compose** (`pymongo`).
* **Frontend** : HTML5, CSS3 (Design Rétro Arcade 8-bit avec polices *Press Start 2P* & *VT323*), JavaScript Vanilla (Polling temps réel).
* **Sécurité & Persistance** : Système de sauvegarde automatique sur clé USB (`auto_usb_backup.py`) à chaque démarrage et fin de partie.

---

## 🔌 Brochage Matériel (Pinout)

| Composant | Ligne 1 | Ligne 2 | Interface |
| :--- | :--- | :--- | :--- |
| **Afficheur TM1637 (CLK / DIO)** | GPIO 18 / GPIO 23 | GPIO 8 / GPIO 7 | GPIO Natif Pi |
| **Bouton & LED START** | Btn: GPIO 15 / LED: GPIO 14 | Btn: GPIO 25 / LED: GPIO 24 | GPIO Natif Pi |
| **Bouton & LED Boîte 1 (B1)** | Btn: Pin 2 / LED: Pin 0 | Btn: Pin 10 / LED: Pin 8 | I2C `MCP23017 #2` (`0x21`) |
| **Bouton & LED Boîte 2 (B2)** | Btn: Pin 2 / LED: Pin 0 | Btn: Pin 10 / LED: Pin 8 | I2C `MCP23017 #1` (`0x20`) |
| **Bouton & LED Boîte 3 (B3)** | Btn: GPIO 22 / LED: GPIO 27 | Btn: GPIO 5 / LED: GPIO 11 | GPIO Natif Pi |
| **Bouton & LED Boîte 4 (B4)** | Btn: GPIO 17 / LED: GPIO 4 | Btn: GPIO 10 / LED: GPIO 9 | GPIO Natif Pi |
| **Dr. Maboul (Start / Touch / End)** | Pins 4 / 7 / 6 | Pins 12 / 15 / 14 | I2C `MCP23017 #2` (`0x21`) |

---

## 📁 Structure du Projet

* **`app.py`** : Point d'entrée de l'application Flask
* **`config.py`** : Connexion à MongoDB et gestion des variables d'environnement
* **`GPIO.py`** : Couche d'abstraction matérielle (GPIO natifs + I2C MCP23017)
* **`maboul.py`** : Logique et threads de surveillance du jeu Dr. Maboul
* **`mastermind.py`** : Moteur du mini-jeu Mastermind
* **`quiz.py`** : Générateur de questions aléatoires depuis les fichiers CSV
* **`auto_usb_backup.py`** : Export automatique de la BDD vers un support USB externe
* **`docker-compose.yml`** : Conteneurisation de MongoDB 4.4
* **`pst.sh`** : Script de démarrage global (Docker + Backup USB + Serveur)
* **`requirements.txt`** : Dépendances Python
* **`csv/`** : Banques de questions thématiques (`.csv`)
* **`routes/`** : Blueprints Flask (`main`, `player`, `admin`, `bouton`)
* **`script-py/`** : Scripts CLI d'administration (reset BDD/GPIO, recherche, backup)
* **`static/`** : Assets graphiques, feuilles de style CSS et scripts JS
* **`templates/`** : Vues HTML Jinja2 (Accueil, Login, InGame, Leaderboard, Settings)

---

## 🚀 Installation et Démarrage

### 1. Prérequis
* Raspberry Pi sous Linux (Debian / Raspberry Pi OS) avec l'interface **I2C activée** (`sudo raspi-config` > *Interface Options* > *I2C*).
* **Docker** et **Docker Compose** installés.
* **Python 3** et `venv`.

### 2. Configuration de l'environnement
Clonez le dépôt et configurez l'environnement virtuel Python :

    git clone <url-du-repo>
    cd PST
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Créez un fichier `.env` à la racine du projet :

    MONGO_URI="mongodb://localhost:27017/"
    DB_NAME="PST-BUTTON_QUEST"

### 3. Lancement automatique (Production)
Le script `pst.sh` démarre automatiquement le conteneur MongoDB, exécute une sauvegarde sur clé USB (si branchée dans `/media/pst/`) et lance le serveur Flask avec les privilèges matériels requis :

    sudo bash pst.sh

L'interface est ensuite accessible sur `http://localhost:5000` (ou via l'IP locale du Raspberry Pi sur le port `5000`).

### 4. Extinction du Raspberry Pi
Pour éteindre proprement le système après utilisation :

    sudo poweroff
    # ou
    sudo shutdown -h now

---

## 🛠️ Scripts de Maintenance & Administration

Le dossier `script-py/` contient plusieurs utilitaires en ligne de commande pour gérer l'événement en direct (après avoir activé le venv avec `source .venv/bin/activate`) :

* **Rechercher un joueur et voir son score :**

      python3 script-py/chercherjoueur.py

* **Supprimer un joueur spécifique :**

      python3 script-py/supprimer_joueur.py

* **Restaurer la base de données depuis la dernière sauvegarde USB :**

      python3 script-py/restaure_backup.py

* **Réinitialiser entièrement la base de données :**

      python3 script-py/reset_db.py

* **Forcer l'extinction de toutes les LEDs et remettre les GPIO/MCP23017 à zéro :**

      python3 script-py/reset_gpio.py

### ⚙️ Panneau de Configuration Web (`/admin/setting`)
Accessible depuis le bouton **SETTINGS** du menu principal, il permet d'ajuster à la volée :
* **Le temps maximum d'une partie** (par défaut : 600 secondes).
* **Le Mode Développeur** : active ou masque le bouton *Bypass Devs* pendant le quiz.

---

## 👥 Équipe & Crédits

Projet réalisé dans le cadre du cursus ingénieur à l'**ESIEA** (Promotion 2029) par :
* **Thomas Couanon**
* **Adam Fouchard**
* **Goulven Magliulo**
* **Helena Petry**
