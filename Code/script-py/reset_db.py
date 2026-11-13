import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import players_collection

# Direction d'ou doit lire python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Supprime tous les documents (joueurs) de la collection
resultat = players_collection.delete_many({})

print(f"Nettoyage terminé : {resultat.deleted_count} participants ont été effacés avec succès !")