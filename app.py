from flask import Flask
from dotenv import load_dotenv
from config import *
from extensions import socketio  
import subprocess
import logging
import GPIO

#############################Blueprints import########################
from routes.main import main_bp
from routes.player import player_bp
from routes.admin import admin_bp
from routes.bouton import bouton_bp
from mastermind import mastermind_bp
from quiz import quiz_bp
from maboul import maboul_bp

############################Blueprints import########################

load_dotenv()
app = Flask(__name__)
app.secret_key = 'une_cle_tres_secrete'
socketio.init_app(app)  

GPIO.init_gpio()


# === FILTRE ANTI-SPAM CONSOLE ===
# class NoPollingFilter(logging.Filter):
#     def filter(self, record):
#         # On ignore le log s'il contient l'une de ces routes très fréquentes
#         message = record.getMessage()
#         return (
#             "/bouton/obtenirTempsActuel" not in message 
#             and "/bouton/verifierQuiz" not in message 
#             and "/mastermind/obtenirEnigme" not in message
#             and "/bouton/verifierReponseMastermind" not in message
#             and "/maboul/status" not in message
#         )
class NoPollingFilter(logging.Filter):
    def filter(self, record):
        # On ignore le log s'il contient l'une de ces routes très fréquentes
        message = record.getMessage()
        return (
            "/bouton/obtenirTempsActuel" not in message 
            and "/bouton/verifierQuiz" not in message 
            and "/mastermind/obtenirEnigme" not in message
            and "/bouton/verifierReponseMastermind" not in message
            and "/maboul/status" not in message
            and "/admin/Leaderboard" not in message
        )
# On applique le filtre au logger serveur (Werkzeug)
log = logging.getLogger('werkzeug')
log.addFilter(NoPollingFilter())
# ================================

#########################les blueprints########################
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix='/admin') 
app.register_blueprint(player_bp, url_prefix='/player') 
app.register_blueprint(bouton_bp, url_prefix='/bouton')
app.register_blueprint(mastermind_bp, url_prefix='/mastermind')
app.register_blueprint(quiz_bp, url_prefix='/quiz')
app.register_blueprint(maboul_bp, url_prefix='/maboul')

#########################les blueprints########################

if __name__ == '__main__':
    # On lance la sauvegarde avant de démarrer le serveur
    print("Tentative de sauvegarde automatique...")
    try:
        subprocess.Popen(['python3', '/home/pst/PST/auto_usb_backup.py'])
    except Exception as e:
        print(f"Erreur lors du lancement du backup : {e}")

    # On lance l'app avec SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)