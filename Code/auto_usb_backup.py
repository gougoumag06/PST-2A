import os
import subprocess
from datetime import datetime
from pymongo import MongoClient

# Conf
DB_NAME = "PST-BUTTON_QUEST"
BASE_MEDIA_PATH = "/media/pst/"

def run_backup():
    # on detect la clé usb
    try:
        devices = os.listdir(BASE_MEDIA_PATH)
        if not devices:
            print("Aucune clé USB détectée.")
            return
        usb_path = os.path.join(BASE_MEDIA_PATH, devices[0])
    except:
        return

    backup_dir = os.path.join(usb_path, "backups_pst")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"export_joueurs_{timestamp}.txt"
    filepath = os.path.join(backup_dir, filename)

    try:
        #Connexion à MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client[DB_NAME]
        players_coll = db["players"]
        
        joueurs = list(players_coll.find())

        #ecriture dans le fichier texte
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"--- SAUVEGARDE DES JOUEURS PST ({datetime.now().strftime('%d/%m/%Y %H:%M')}) ---\n\n")
            for j in joueurs:
                #on recupere les infos de la base de données 
                ligne = (f"Pseudo: {j.get('pseudo', 'N/A')} | "
                         f"Méthode: {j.get('contact_method', 'N/A')} | "
                         f"Contact: {j.get('contact_info', 'N/A')} | "
                         f"Essais: {j.get('try', 0)} | "
                         f"Temps: {j.get('time', 0)} | "
                         f"Boîtes: {j.get('nb_box', 0)}\n")
                f.write(ligne)
            f.write(f"\nTotal: {len(joueurs)} joueurs exportés.")

        print(f"✅ Sauvegarde réussie : {filepath}")

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")

if __name__ == "__main__":
    run_backup()
