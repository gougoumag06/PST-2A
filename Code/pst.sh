#!/bin/bash

# Script pour démarrer la BDD Docker et l'application web.
# Ce script doit être lancé avec sudo (ex: sudo ./start_app.sh)
# car RPi.GPIO et Docker l'exigent.

# 0. Nettoyer le terminal et afficher le logo
clear
echo -e "\e[1;34m" # Couleur Bleu Vif
echo '  ____  ____ _____ '
echo ' |  _ \/ ___|_   _|'
echo ' | |_) \___ \ | |  '
echo ' |  __/ ___) || |  '
echo ' |_|   |____/ |_|  '
echo '                   '
echo -e "\e[0m" # Reset couleur
echo 'Initialisation du système PST...'
echo ''

# 1. Vérification et démarrage du conteneur Docker
echo "Vérification de la base de données MongoDB..."

# IMPORTANT : Place-toi dans le dossier où se trouve ton docker-compose.yml
cd /home/pst/PST/

# docker compose up -d gère tout intelligemment (création, démarrage, ou rien si déjà UP)
docker compose up -d

echo "Attente de 5 secondes pour l'initialisation de la BDD..."
sleep 5
echo "Base de données prête !"

echo "-----------------------------------------------------"
echo "Lancement de la sauvegarde automatique sur clé USB..."
echo "-----------------------------------------------------"

# On utilise le python de ton environnement virtuel pour lancer le script
# (Note : si auto_usb_backup.py tourne en boucle infinie, ajoute un & à la fin de cette ligne)
/home/pst/PST/.venv/bin/python /home/pst/PST/auto_usb_backup.py

echo "-----------------------------------------------------"
echo "Lancement de l'application Flask (avec droits sudo pour GPIO)..."
echo "-----------------------------------------------------"

# Lancement de l'application app.py
/home/pst/PST/.venv/bin/python /home/pst/PST/app.py
