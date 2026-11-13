import sys
import os

# Direction d'ou doit lire python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import players_collection



# -----------------------------------------------------------
# Fonction qui retourne les informations du joueur sur le terminal
# -----------------------------------------------------------
def chercher_joueur():
    print("--- RECHERCHE DE JOUEUR DANS LA BASE ---")
    pseudo_recherche = input("Entrez le pseudo du joueur à chercher : ").strip()
    
    # Recherche dans la base de données MongoDB
    joueur = players_collection.find_one({"pseudo": pseudo_recherche})
    
    if joueur:
        print("\n=== INFORMATIONS TROUVÉES ===")
        print(f"Pseudo      : {joueur.get('pseudo', 'N/A')}")
        print(f"Contact     : {joueur.get('contact_method', 'N/A')}")
        print(f"Coordonnées : {joueur.get('contact_info', 'N/A')}")
        print(f"Boîtes      : {joueur.get('nb_box', 'N/A')}")
        print(f"Essais      : {joueur.get('try', 'N/A')}")
        print(f"Temps       : {joueur.get('time', 'N/A')}s")
        print("=============================\n")
    else:
        print(f"\n[ERREUR] Aucun joueur trouvé avec le pseudo '{pseudo_recherche}'.\n")

if __name__ == "__main__":
    chercher_joueur()