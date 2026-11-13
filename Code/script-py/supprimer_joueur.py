import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import players_collection



# -----------------------------------------------------------
# Fonction qui supprime un joueur de la base de donnée
# -----------------------------------------------------------
def supprimer_joueur():
    print("--- SUPPRESSION D'UN JOUEUR ---")
    pseudo_a_supprimer = input("Entrez le pseudo du joueur à supprimer : ").strip()
    
    resultat = players_collection.delete_one({"pseudo": pseudo_a_supprimer})
    
    if resultat.deleted_count > 0:
        print(f"\n[SUCCÈS] Le joueur '{pseudo_a_supprimer}' a été effacé avec succès !")
    else:
        print(f"\n[ERREUR] Aucun joueur trouvé avec le pseudo '{pseudo_a_supprimer}'.")

if __name__ == "__main__":
    supprimer_joueur()