# PST - Button Quest

Bienvenue sur le dépôt de **Button Quest**, notre Projet Scientifique et Technique (PST) de 2ème année à l'ESIEA. 

L'idée derrière ce projet était de construire une platforme d'arcade interactive capable d'animer nos stands sur des salons ou des événements étudiants. Concrètement, deux joueurs s'affrontent côte à côte (Ligne 1 contre Ligne 2) sur une série de mini-jeux qui mélangent électronique pure (boutons d'arcade, fil sous tension, crochetage) et épreuves sur écran dans une ambiance rétro-gaming.

---

## Comment se déroule une partie ?

Le but est d'aller au bout des 4 boîtes d'épreuves le plus vite possible. Tout est rythmé par des gros boutons lumineux : chaque fois qu'une étape est validée, le bouton suivant s'allume.

1. **Le top départ (`START`)** : Le joueur entre son pseudo sur l'écran, choisit sa ligne, puis tape sur le gros bouton **START** qui clignote pour lancer son chronomètre.
2. **Boîte 1 — Le Docteur Maboul** : On commence par de l'adresse physique. Il faut faire glisser un anneau métallique le long d'un fil de cuivre tordu sans le toucher. À chaque contact, c'est **+5 secondes de pénalité** directes sur le chrono (avec une alerte à l'écran et sur l'afficheur 7 segments). Une fois au bout du fil, le bouton **B1** s'allume.
3. **Boîte 2 — Mastermind Matrix** : En appuyant sur **B1**, un Mastermind s'affiche à l'écran. Il faut deviner la combinaison secrète de 4 couleurs parmi 6 (jouable à la souris ou directement au clavier avec les touches `K, R, B, P, Y, G`). Dès que le code tombe, ça débloque le bouton **B2**.
4. **Boîte 3 — Survival Mission (Le Quiz)** : L'appui sur **B2** lance un quiz de 5 questions piochées au hasard dans nos fichiers CSV (Info, Élec, Maths, Physique, Culture geek). Il faut faire au moins **4/5** pour allumer le bouton **B3**. En dessous, le jeu relance une nouvelle salve de questions !
5. **Boîte 4 — Le Crochetage (Lockpicking)** : Dernière ligne droite après avoir pressé **B3**. Le joueur doit crocheter un vrai cadenas pour accéder au bouton final **B4**, stopper son chrono et envoyer son temps dans le classement général (*High Scores*).

---

## Ce qu'il y a sous le capot

### Côté Matériel (Hardware)
* **Un Raspberry Pi** qui fait tourner à la fois le serveur web, la base de données et toute la gestion des broches.
* **2 modules d'extension MCP23017 en I2C** (aux adresses `0x20` et `0x21`) parce qu'on manquait vite de broches sur le Pi avec deux lignes complètes à gérer. On a codé une surcouche avec des verrous (`RLock`) dans `GPIO.py` pour éviter que le bus I2C ne plante en cas de faux contact ou de micro-coupure pendant qu'un joueur s'acharne sur un bouton.
* **2 afficheurs 7 segments (TM1637)** directement intégrés aux boîtes pour afficher le chrono et faire clignoter les `+5` de pénalité en temps réel.
* **Le câblage d'arcade** : Boutons poussoirs à LEDs, les circuits en cuivre pour le Maboul (plots Start, Fil et End) et les cadenas d'entraînement.

### Côté Logiciel (Software)
* **Backend** : Python 3 avec **Flask** découpé en *Blueprints* pour séparer les routes joueur, l'admin et la gestion des jeux, le tout soutenu par des threads en arrière-plan pour surveiller le matériel.
* **Base de données** : **MongoDB 4.4** qui tourne dans un conteneur **Docker** pour ne pas s'embêter avec l'installation locale.
* **Frontend** : HTML/CSS/JS fait maison dans un style borne d'arcade 8-bit.
* **Sécurité anti-crash** : Un petit script (`auto_usb_backup.py`) détecte automatiquement si une clé USB est branchée sur le Raspberry Pi et y exporte tous les joueurs et leurs scores en fichier `.txt` au démarrage et à chaque fin de partie.

---

## Le câblage (Pinout)

Si jamais un fil se débranche pendant le transport de la valise, voici où tout doit être rebranché :

| Composant | Ligne 1 | Ligne 2 | Branché sur... |
| :--- | :--- | :--- | :--- |
| **Écran Chrono TM1637 (CLK / DIO)** | GPIO 18 / GPIO 23 | GPIO 8 / GPIO 7 | Raspberry Pi (Natif) |
| **Bouton & LED START** | Btn: GPIO 15 / LED: GPIO 14 | Btn: GPIO 25 / LED: GPIO 24 | Raspberry Pi (Natif) |
| **Bouton & LED Boîte 1 (B1)** | Btn: Pin 2 / LED: Pin 0 | Btn: Pin 10 / LED: Pin 8 | Module I2C #2 (`0x21`) |
| **Bouton & LED Boîte 2 (B2)** | Btn: Pin 2 / LED: Pin 0 | Btn: Pin 10 / LED: Pin 8 | Module I2C #1 (`0x20`) |
| **Bouton & LED Boîte 3 (B3)** | Btn: GPIO 22 / LED: GPIO 27 | Btn: GPIO 5 / LED: GPIO 11 | Raspberry Pi (Natif) |
| **Bouton & LED Boîte 4 (B4)** | Btn: GPIO 17 / LED: GPIO 4 | Btn: GPIO 10 / LED: GPIO 9 | Raspberry Pi (Natif) |
| **Dr. Maboul (Start / Fil / Fin)** | Pins 4 / 7 / 6 | Pins 12 / 15 / 14 | Module I2C #2 (`0x21`) |

---

## Organisation des fichiers

* `app.py` : Le fichier principal qui lance le serveur Flask.
* `GPIO.py` : Toute la configuration des broches du Pi et des deux modules I2C.
* `maboul.py`, `mastermind.py`, `quiz.py` : La logique respective de nos trois mini-jeux.
* `routes/` : Les contrôleurs Flask (`bouton.py` gère l'enchaînement des étapes et le chrono, `admin.py` gère le classement et les réglages, `player.py` gère l'inscription).
* `csv/` : Nos banques de questions pour le quiz.
* `script-py/` : Nos petits scripts de dépannage à lancer dans le terminal pendant les salons.
* `pst.sh` : Le script qui lance tout d'un coup.

---

## Installation et lancement

### 1. Préparer l'environnement (la première fois)
Assurez-vous que l'**I2C est bien activé** sur le Raspberry Pi (`sudo raspi-config` > *Interface Options* > *I2C*) et que **Docker** est installé.

Clonez le projet et installez les librairies Python dans un environnement virtuel :

    git clone <url-du-repo>
    cd PST
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Vérifiez qu'il y a bien un fichier `.env` à la racine avec ces deux lignes :

    MONGO_URI="mongodb://localhost:27017/"
    DB_NAME="PST-BUTTON_QUEST"

### 2. Lancer la valise
Pas besoin de lancer Docker et Python séparément. On a fait un script `pst.sh` qui s'occupe de démarrer la base MongoDB, de faire une sauvegarde sur la clé USB et de lancer le serveur Flask avec les droits `sudo` (indispensables pour accéder aux GPIO) :

    sudo bash pst.sh

Une fois lancé, le jeu est accessible sur le navigateur à l'adresse `http://localhost:5000`.

### 3. Éteindre le Raspberry Pi proprement
Pour éviter de corrompre la carte SD ou la base de données en débranchant la prise sauvagement à la fin de la journée :

    sudo poweroff

---

## Les commandes utiles en plein événement

Si vous avez besoin d'intervenir sur la base de données ou sur les LEDs pendant que le stand tourne, ouvrez un autre terminal, activez le venv (`source .venv/bin/activate`) et utilisez les scripts du dossier `script-py/` :

* **Retrouver les infos ou le score d'un joueur :**
  `python3 script-py/chercherjoueur.py`

* **Supprimer un joueur (pseudo doublon ou erreur de saisie) :**
  `python3 script-py/supprimer_joueur.py`

* **Restaurer les joueurs depuis la clé USB (en cas de pépin sur la BDD) :**
  `python3 script-py/restaure_backup.py`

* **Vider complètement le classement avant un nouvel événement :**
  `python3 script-py/reset_db.py`

* **Éteindre toutes les LEDs de force et remettre les broches à zéro :**
  `python3 script-py/reset_gpio.py`

> **Astuce :** Depuis le menu principal du site, le bouton **SETTINGS** (`/admin/setting`) permet aussi de changer la durée maximale d'une partie (10 minutes par défaut) et d'activer ou cacher le bouton **Bypass Devs** sur le quiz pour passer l'épreuve rapidement pendant nos tests.

---

## L'Équipe

Projet imaginé, câblé et codé par :
* **Thomas Couanon**
* **Adam Fouchard**
* **Goulven Magliulo**
* **Helena Petry**
