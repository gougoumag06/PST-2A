import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# Initialisation par défaut
players_collection = None

try:
    # Ajout d'un timeout court (ex: 3000ms = 3 secondes) pour éviter d'attendre 30 secondes dans le vide
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    
    # On force le test de la connexion avec une commande 'ping'
    client.admin.command('ping')
    
    # Si le ping passe, on connecte la base et la collection
    db = client[DB_NAME]
    players_collection = db["players"]
    
    print(f"✅ Connexion à MongoDB (db: {DB_NAME}) réussie!")

except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print("❌ Erreur : Impossible de se connecter à MongoDB. Le serveur est-il bien lancé ?")
    print(f"Détails techniques : {e}")
except Exception as e:
    print(f"❌ Une erreur inattendue est survenue : {e}")
