# PST-2A
PST-2A avec ADAM Fouchard, HELENA Petry, THOMAS Couanon et GOULVEN Magliulo


INSTALLATION MODULE : 
pip install -r requirements.txt

----------------------------------

Activation du VENV :  
source .venv/bin/activate

LANCEMENT DU CODE : 
sudo bash pst.sh

ETEINDRE RASPBERRY
sudo poweroff
sudo shutdown -h now

---------------------------------

RESET BASE DE DONNEE : 
python3 script-py/reset_db.py

CHERCHER JOUEUR : 
python3 script-py/chercherjoueur.py

RESTAURATION BACKUP:
python3 script-py/restaure_backup.py

SUPPRIMER JOUEUR:
python3 script-py/supprimer_joueur.py

---------------------------------

RESET GPIO:
python3 script-py/reset_gpio.py
