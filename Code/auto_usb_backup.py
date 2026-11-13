import os
from datetime import datetime
from pymongo import MongoClient

# Configuration
DB_NAME = "PST-BUTTON_QUEST"
BASE_MEDIA_PATH = "/media/pst/"

def run_backup():
    print("🔍 Recherche d'un support USB...")
    
    # 1. Détection sécurisée de la clé USB
    try:
        if not os.path.exists(BASE_MEDIA_PATH):
            print(f"❌ Erreur : Le chemin racine {BASE_MEDIA_PATH} n'existe pas.")
            return

        # On filtre pour ne garder que les vrais répertoires (on évite les fichiers parasites)
        devices = [d for d in os.listdir(BASE_MEDIA_PATH) if os.path.isdir(os.path.join(BASE_MEDIA_PATH, d))]
        
        if not devices:
            print("⚠ Aucune clé USB détectée.")
            return
            
        # On prend le premier périphérique valide
        usb_path = os.path.join(BASE_MEDIA_PATH, devices[0])
        print(f"📁 Clé USB trouvée : {usb_path}")
        
    except Exception as e:
        print(f"❌ Impossible de scanner les périphériques : {e}")
        return

    # 2. Préparation des chemins
    backup_dir = os.path.join(usb_path, "backups_pst")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"export_joueurs_{timestamp}.txt"
    filepath = os.path.join(backup_dir, filename)

    # 3. Connexion et extraction (Tout est sécurisé dans le try)
    client = None
    try:
        # Création du dossier (gère le risque de clé USB en lecture seule)
        os.makedirs(backup_dir, exist_ok=True)

        # Connexion à MongoDB
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        db = client[DB_NAME]
        players_coll = db["players"]
        
        # Récupération des données
        joueurs = list(players_coll.find())

        # Écriture dans le fichier texte
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"--- SAUVEGARDE DES JOUEURS PST ({datetime.now().strftime('%d/%m/%Y %H:%M')}) ---\n\n")
            for j in joueurs:
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
        
    finally:
        # On s'assure de toujours fermer la connexion à la BDD
        if client:
            client.close()

if __name__ == "__main__":
    run_backup()