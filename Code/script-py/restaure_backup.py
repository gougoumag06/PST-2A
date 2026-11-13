import os
import sys
from pymongo import MongoClient

# Configuration
DB_NAME = "PST-BUTTON_QUEST"
BASE_MEDIA_PATH = "/media/pst/"

# -----------------------------------------------------------
# Fonction qui recherche la dernière backup sur le clé usb
# -----------------------------------------------------------
def find_latest_backup():
    """Scanne la clé USB et retourne le chemin du fichier de backup le plus récent"""
    if not os.path.exists(BASE_MEDIA_PATH):
        print(f"❌ Erreur : Le chemin {BASE_MEDIA_PATH} n'existe pas.")
        return None

    # Détection de la clé USB
    devices = [d for d in os.listdir(BASE_MEDIA_PATH) if os.path.isdir(os.path.join(BASE_MEDIA_PATH, d))]
    if not devices:
        print("❌ Aucune clé USB détectée.")
        return None

    usb_path = os.path.join(BASE_MEDIA_PATH, devices[0])
    backup_dir = os.path.join(usb_path, "backups_pst")

    if not os.path.exists(backup_dir):
        print(f"❌ Dossier de sauvegarde introuvable sur la clé : {backup_dir}")
        return None

    # Liste tous les fichiers d'export joueurs
    files = [f for f in os.listdir(backup_dir) if f.startswith("export_joueurs_") and f.endswith(".txt")]
    if not files:
        print("⚠ Aucun fichier de sauvegarde valide trouvé.")
        return None

    # Tri alphabétique (le format YYYYMMDD_HHMMSS se trie naturellement dans l'ordre chronologique)
    files.sort()
    latest_file = files[-1]  # Le dernier est le plus récent
    
    return os.path.join(backup_dir, latest_file)

# -----------------------------------------------------------
# Fonction qui parse les données pour reconstruire dans la base de donnée
# PARAMETRE filepath : Chemin du fichier
# -----------------------------------------------------------
def parse_backup_file(filepath):
    """Lit le fichier texte personnalisé et le reconstruit en objets Python/Mongo"""
    joueurs_extraits = []
    
    print(f"📖 Lecture du fichier : {os.path.basename(filepath)}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            # On ignore les lignes d'en-tête, de pied de page ou vides
            if not line.strip() or line.startswith("---") or line.startswith("Total:"):
                continue
            
            # Exemple de ligne : Pseudo: Max | Méthode: Email | Contact: m@ok.com | Essais: 2 | Temps: 45 | Boîtes: 3
            if "Pseudo:" in line and "|" in line:
                try:
                    champs = line.strip().split(" | ")
                    data_joueur = {}
                    
                    for champ in champs:
                        if ":" in champ:
                            cle, valeur = champ.split(":", 1)
                            cle = cle.strip()
                            valeur = valeur.strip()
                            
                            # Correspondance avec les clés de ta base de données originelle
                            if cle == "Pseudo":
                                data_joueur["pseudo"] = valeur
                            elif cle == "Méthode":
                                data_joueur["contact_method"] = valeur
                            elif cle == "Contact":
                                data_joueur["contact_info"] = valeur
                            elif cle == "Essais":
                                data_joueur["try"] = int(valeur) if valeur.isdigit() else 0
                            elif cle == "Temps":
                                data_joueur["time"] = int(valeur) if valeur.isdigit() else 0
                            elif cle == "Boîtes":
                                data_joueur["nb_box"] = int(valeur) if valeur.isdigit() else 0
                    
                    if data_joueur:
                        joueurs_extraits.append(data_joueur)
                        
                except Exception as e:
                    print(f"⚠ Ligne corrompue ignorée : {line.strip()} ({e})")
                    
    return joueurs_extraits

# -----------------------------------------------------------
# Fonction principale qui lance la restauration du la base de donnée
# -----------------------------------------------------------
def run_restore():
    print("=======================================================")
    print("        DÉMARRAGE DE LA RESTAURATION MONGO            ")
    print("=======================================================")
    
    # 1. Trouver le fichier
    backup_file = find_latest_backup()
    if not backup_file:
        return

    # 2. Extraire les données du fichier
    joueurs = parse_backup_file(backup_file)
    if not joueurs:
        print("❌ Échec : Aucun joueur valide trouvé dans le fichier.")
        return

    print(f"🔍 {len(joueurs)} joueurs prêts à être restaurés.")

    # 3. Réinjection sécurisée dans MongoDB
    client = None
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        db = client[DB_NAME]
        players_coll = db["players"]

        # --- SÉCURITÉ DOUBLE VALIDATION ---
        print("\n⚠ ATTENTION : Cette action va écraser les joueurs actuels en base de données.")
        reponse = input("👉 Confirmer la restauration ? (oui/non) : ").strip().lower()
        if reponse != "oui":
            print("❌ Restauration annulée par l'utilisateur.")
            return

        # Nettoyage de la table actuelle
        print("🗑 Vidage de la collection actuelle...")
        players_coll.delete_many({})

        # Insertion des données restaurées
        print("📥 Insertion des données de secours...")
        result = players_coll.insert_many(joueurs)
        
        print("\n=======================================================")
        print(f"✅ RESTAURATION RÉUSSIE AVEC SUCCÈS !")
        print(f"👉 {len(result.inserted_ids)} joueurs importés dans '{DB_NAME}.players'.")
        print("=======================================================")

    except Exception as e:
        print(f"❌ Erreur critique lors de l'accès à MongoDB : {e}")
        
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    run_restore()