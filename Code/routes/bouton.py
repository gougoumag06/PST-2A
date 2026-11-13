from flask import Blueprint, render_template, request, session, jsonify
from config import players_collection
from maboul import lancer_maboul_physique, enregistrer_callback_victoire, enregistrer_callback_penalite, arreter_maboul_physique
from routes.admin import CONFIG_EPREUVES
from auto_usb_backup import run_backup
import time
import GPIO  
import mastermind
import threading
import tm1637
import logging

# Configuration du logger pour filtrer les requêtes répétitives
log = logging.getLogger('werkzeug')
class NoPollingSpamFilter(logging.Filter):
    # -----------------------------------------------------------
    # Filtre les logs des requêtes de polling pour ne pas surcharger la console
    # PARAMETRE record : L'élément de log à vérifier
    # RETURN : Un booléen (True si on garde le log, False si on le masque)
    # -----------------------------------------------------------
    def filter(self, record):
        msg = record.getMessage()
        if '/maboul/status' in msg or '/bouton/obtenirTempsActuel' in msg or '/bouton/getGameStatus' in msg or '/mastermind/obtenirEnigme' in msg or '/bouton/verifierQuiz' in msg:
            return False
        return True
log.addFilter(NoPollingSpamFilter())

bouton_bp = Blueprint('bouton', __name__)

# État global des deux lignes de jeu (valises)
ETAT_LIGNES = {
    '1': {'temps_depart': None, 'dernier_temps': None, 'chrono_arrete': False, 'nb_boite_faite': 0, 'checkpoint': 5, 'tm': None, 'quiz_actif': False, 'maboul_actif': False, 'maboul_en_cours': False, 'penalite_timestamp': 0},
    '2': {'temps_depart': None, 'dernier_temps': None, 'chrono_arrete': False, 'nb_boite_faite': 0, 'checkpoint': 5, 'tm': None, 'quiz_actif': False, 'maboul_actif': False, 'maboul_en_cours': False, 'penalite_timestamp': 0}
}

# -----------------------------------------------------------
# Éteint toutes les LEDs et désactive les boutons d'une ligne
# PARAMETRE ligne_int : Le numéro de la ligne en entier
# -----------------------------------------------------------
def vider_tous_les_boutons(ligne_int):
    for b in ['start', 'b1', 'b2', 'b3', 'b4']:
        led = GPIO.get_led(ligne_int, b)
        bouton = GPIO.get_bouton(ligne_int, b)
        if led: led.off()
        if bouton: bouton.when_pressed = None

# -----------------------------------------------------------
# Initialise l'écran 7 segments de la ligne si ce n'est pas déjà fait
# PARAMETRE ligne : Le numéro de la ligne en texte ('1' ou '2')
# -----------------------------------------------------------
def init_ecran_tm1637(ligne):
    if ETAT_LIGNES[ligne].get('tm') is not None:
        return

    try:
        if ligne == '1':
            pin_clk = 18 
            pin_dio = 23 
        elif ligne == '2':
            pin_clk = 8
            pin_dio = 7
        else:
            return

        try:
            if f'display_clk_L{ligne}' in GPIO.Dict_GPIO:
                GPIO.Dict_GPIO[f'display_clk_L{ligne}'].close()
            if f'display_dio_L{ligne}' in GPIO.Dict_GPIO:
                GPIO.Dict_GPIO[f'display_dio_L{ligne}'].close()
        except Exception as e:
            pass

        tm = tm1637.TM1637(clk=pin_clk, dio=pin_dio)
        tm.brightness(2) 
        tm.numbers(0, 0)
        ETAT_LIGNES[ligne]['tm'] = tm
        print(f"[ECRAN] Connecté avec succès sur LIGNE {ligne}")
    except Exception as e:
        print(f"[ECRAN] Erreur d'initialisation LIGNE {ligne}: {e}")
        ETAT_LIGNES[ligne]['tm'] = None

# -----------------------------------------------------------
# Gère l'affichage du temps et des animations de pénalité en arrière-plan
# -----------------------------------------------------------
def background_display():
    while True:
        now_time = time.time()
        for ligne, etat in ETAT_LIGNES.items():
            tm = etat['tm']
            if tm:
                try:
                    if etat.get('penalite_timestamp', 0) and (now_time - etat['penalite_timestamp']) < 1.5:
                        if int((now_time - etat['penalite_timestamp']) * 5) % 2 == 0:
                            try:
                                tm.show(' + 5') 
                            except:
                                try:
                                    tm.write([0x73, 0x00, 0x00, 0x6D]) 
                                except:
                                    tm.numbers(0, 5) 
                        else:
                            try:
                                tm.write([0x00, 0x00, 0x00, 0x00])
                            except:
                                pass
                    else:
                        if etat['temps_depart'] is not None and not etat['chrono_arrete']:
                            now = now_time - etat['temps_depart']
                            minutes = int(now // 60)
                            secondes = int(now % 60)
                            tm.numbers(minutes, secondes)
                        elif etat['chrono_arrete'] and etat['dernier_temps'] is not None:
                            minutes = int(etat['dernier_temps'] // 60)
                            secondes = int(etat['dernier_temps'] % 60)
                            tm.numbers(minutes, secondes)
                        else:
                            tm.numbers(0, 0)
                except Exception as e:
                    pass
        time.sleep(0.1) 

# Lancement du thread pour l'affichage en arrière-plan
threading.Thread(target=background_display, daemon=True).start()

# -----------------------------------------------------------
# Enregistre ou met à jour le score du joueur dans la base de données
# PARAMETRE temps : Le temps final mis par le joueur
# PARAMETRE nb_boites : Le nombre de boîtes validées par le joueur
# -----------------------------------------------------------
def enregistrer_score(temps, nb_boites):
    pseudo = session.get('player_pseudo', 'Joueur')
    player = players_collection.find_one({"pseudo": pseudo})
    
    if not player:
        if nb_boites == 0:
            players_collection.insert_one({"pseudo": pseudo, "time": None, "nb_box": 0, "try": 1})
        else:
            players_collection.insert_one({"pseudo": pseudo, "time": temps, "nb_box": nb_boites, "try": 1})
        return
    
    if nb_boites == 0:
        update_query = {
            "$inc": {"try": 1}
        }
        print(f"[BDD] Abandon de {pseudo} avec 0 boîte. Essai comptabilisé, temps ignoré.")
    else:
        update_query = {
            "$inc": {"try": 1},
            "$set": {"time": temps, "nb_box": nb_boites}
        }
        print(f"[BDD] Partie validée pour {pseudo} ({nb_boites} boîtes). Score enregistré.")

    players_collection.update_one({"pseudo": pseudo}, update_query)

# -----------------------------------------------------------
# Incrémente le compteur de boîtes et enregistre le temps intermédiaire
# PARAMETRE ligne : Le numéro de la ligne active
# -----------------------------------------------------------
def enregistrer_checkpoint(ligne):
    ETAT_LIGNES[ligne]['nb_boite_faite'] += 1
    if ETAT_LIGNES[ligne]['temps_depart'] is not None:
        ETAT_LIGNES[ligne]['checkpoint'] = time.time() - ETAT_LIGNES[ligne]['temps_depart']

# -----------------------------------------------------------
# Clôture la partie, enregistre le score et réinitialise les boutons
# PARAMETRE ligne : Le numéro de la ligne active
# PARAMETRE temps_final : Le temps final obtenu
# -----------------------------------------------------------
def terminer_jeu(ligne, temps_final):
    etat = ETAT_LIGNES[ligne]
    print(f"[INFO] Ligne {ligne} - Fin du jeu: {temps_final:.2f}s")
    enregistrer_score(temps_final, etat['nb_boite_faite'])
    vider_tous_les_boutons(int(ligne))
    run_backup()

# -----------------------------------------------------------
# Gère l'appui sur START : démarre le chrono et le Docteur Maboul
# PARAMETRE ligne : Le numéro de la ligne active
# -----------------------------------------------------------
def on_bouton_start_pressed(ligne):
    print(f"[INFO] Ligne {ligne} - START pressé -> Démarrage Chrono & MABOUL")
    ligne_int = int(ligne)
    
    arreter_maboul_physique(ligne)
    
    led_start = GPIO.get_led(ligne_int, 'start')
    bouton_start = GPIO.get_bouton(ligne_int, 'start')
    if led_start: led_start.off()
    if bouton_start: bouton_start.when_pressed = None
    
    ETAT_LIGNES[ligne]['temps_depart'] = time.time()
    lancer_maboul_physique(ligne)

# -----------------------------------------------------------
# Gère la réussite de Maboul : allume le bouton B1 pour l'étape suivante
# PARAMETRE ligne : Le numéro de la ligne active
# -----------------------------------------------------------
def on_maboul_success(ligne):
    print(f"[INFO] Ligne {ligne} - MABOUL terminé -> Allumage B1")
    ligne_int = int(ligne)
    
    led_b1 = GPIO.get_led(ligne_int, 'b1')
    bouton_b1 = GPIO.get_bouton(ligne_int, 'b1')
    if led_b1 and bouton_b1:
        led_b1.on()
        bouton_b1.when_pressed = lambda: on_bouton_b1_pressed(ligne)    

# -----------------------------------------------------------
# Gère l'appui sur B1 : lance l'énigme du Mastermind
# PARAMETRE ligne : Le numéro de la ligne active
# -----------------------------------------------------------
def on_bouton_b1_pressed(ligne):
    if ETAT_LIGNES[ligne]['nb_boite_faite'] != 0:
        return

    print(f"[INFO] Ligne {ligne} - B1 pressé -> Lancement MASTERMIND")
    ligne_int = int(ligne)
    arreter_maboul_physique(ligne)
    
    led_b1 = GPIO.get_led(ligne_int, 'b1')
    bouton_b1 = GPIO.get_bouton(ligne_int, 'b1')
    if led_b1: led_b1.off()
    if bouton_b1: bouton_b1.when_pressed = None
    
    enregistrer_checkpoint(ligne)  
    mastermind.activer_enigme(ligne)

# -----------------------------------------------------------
# Gère l'appui sur B2 : active l'épreuve du Quiz
# PARAMETRE ligne : Le numéro de la ligne active
# -----------------------------------------------------------
def on_bouton_b2_pressed(ligne):
    if ETAT_LIGNES[ligne]['nb_boite_faite'] != 1:
        return

    print(f"[INFO] Ligne {ligne} - B2 pressé -> Lancement QUIZ")
    ligne_int = int(ligne)
    
    led_b2 = GPIO.get_led(ligne_int, 'b2')
    bouton_b2 = GPIO.get_bouton(ligne_int, 'b2')
    if led_b2: led_b2.off()
    if bouton_b2: bouton_b2.when_pressed = None
    
    enregistrer_checkpoint(ligne)  
    ETAT_LIGNES[ligne]['quiz_actif'] = True

# -----------------------------------------------------------
# Gère l'appui sur B3 : lance l'épreuve physique du code César
# PARAMETRE ligne : Le numéro de la ligne active
# -----------------------------------------------------------
def on_bouton_b3_pressed(ligne):
    if ETAT_LIGNES[ligne]['nb_boite_faite'] != 2:
        return

    print(f"[INFO] Ligne {ligne} - B3 pressé -> Épreuve CÉSAR en cours")
    ligne_int = int(ligne)
    
    led_b3 = GPIO.get_led(ligne_int, 'b3')
    bouton_b3 = GPIO.get_bouton(ligne_int, 'b3')
    if led_b3: led_b3.off()
    if bouton_b3: bouton_b3.when_pressed = None
    
    enregistrer_checkpoint(ligne)  

    led_b4 = GPIO.get_led(ligne_int, 'b4')
    bouton_b4 = GPIO.get_bouton(ligne_int, 'b4')
    if led_b4 and bouton_b4:
        led_b4.on()
        bouton_b4.when_pressed = lambda: on_bouton_b4_pressed(ligne)
        
# -----------------------------------------------------------
# Gère l'appui sur B4 : arrête le chrono et marque la fin définitive du jeu
# PARAMETRE ligne : Le numéro de la ligne active
# -----------------------------------------------------------
def on_bouton_b4_pressed(ligne):
    if ETAT_LIGNES[ligne]['nb_boite_faite'] != 3 or ETAT_LIGNES[ligne]['chrono_arrete']:
        return

    print(f"[INFO] Ligne {ligne} - B4 pressé -> FIN DU JEU")
    ligne_int = int(ligne)
    
    led_b4 = GPIO.get_led(ligne_int, 'b4')
    bouton_b4 = GPIO.get_bouton(ligne_int, 'b4')
    if led_b4: led_b4.off()
    if bouton_b4: bouton_b4.when_pressed = None
    
    ETAT_LIGNES[ligne]['chrono_arrete'] = True  
    enregistrer_checkpoint(ligne)  
    
    if ETAT_LIGNES[ligne]['temps_depart'] is not None:
        temps_ecoule = time.time() - ETAT_LIGNES[ligne]['temps_depart']
        ETAT_LIGNES[ligne]['dernier_temps'] = temps_ecoule

# -----------------------------------------------------------
# Applique une pénalité de temps (+5s) en cas d'erreur sur le Docteur Maboul
# PARAMETRE ligne : Le numéro de la ligne active
# -----------------------------------------------------------
def on_maboul_penalite(ligne):
    if ETAT_LIGNES[ligne]['temps_depart'] is not None:
        ETAT_LIGNES[ligne]['temps_depart'] -= 5.0
        ETAT_LIGNES[ligne]['penalite_timestamp'] = time.time()
        print(f"[INFO] Ligne {ligne} - ⚡ PÉNALITÉ +5s !")


# ============================================================
# ROUTES WEB FLASK
# ============================================================

# -----------------------------------------------------------
# Route qui charge l'interface HTML du jeu en cours
# RETURN : Le rendu du template HTML "InGame.html"
# -----------------------------------------------------------
@bouton_bp.route('/jeux')
def page_jeux():
    return render_template('InGame.html')

# -----------------------------------------------------------
# Route qui initialise et lance une nouvelle partie sur la ligne active
# RETURN : Un JSON de succès ou d'erreur
# -----------------------------------------------------------
@bouton_bp.route('/lancerJeux', methods=['POST'])
def lancer_jeu():
    ligne = str(session.get('line_id') or '1')
    ligne_int = int(ligne)
    print(f"[INFO] Démarrage d'une nouvelle partie sur la LIGNE {ligne}")
    
    arreter_maboul_physique(ligne)
    vider_tous_les_boutons(ligne_int)
    
    tm_existant = ETAT_LIGNES[ligne].get('tm')
    ETAT_LIGNES[ligne] = {'temps_depart': None, 'dernier_temps': None, 'chrono_arrete': False, 'nb_boite_faite': 0, 'checkpoint': 5, 'tm': tm_existant, 'quiz_actif': False, 'maboul_actif': False, 'maboul_en_cours': False, 'penalite_timestamp': 0}
    
    init_ecran_tm1637(ligne)
    mastermind.reset_enigme(ligne)
    
    if ETAT_LIGNES[ligne]['tm']:
        ETAT_LIGNES[ligne]['tm'].numbers(0, 0)
    
    led_start = GPIO.get_led(ligne_int, 'start')
    bouton_start = GPIO.get_bouton(ligne_int, 'start')
    
    if led_start and bouton_start:
        led_start.on()
        bouton_start.when_pressed = lambda: on_bouton_start_pressed(ligne)
        return jsonify({'status': 'success', 'message': f'Jeu démarré sur la ligne {ligne}'})
    else:
        return jsonify({'status': 'error', 'message': 'Erreur START'}), 500

# -----------------------------------------------------------
# Route appelée en continu pour obtenir le temps actuel du chronomètre
# RETURN : Un JSON contenant le statut de la partie et le temps écoulé
# -----------------------------------------------------------
@bouton_bp.route('/obtenirTempsActuel', methods=['GET'])
def obtenir_temps_actuel():
    ligne = str(session.get('line_id') or '1')
    etat = ETAT_LIGNES[ligne]
    
    if etat['chrono_arrete'] and etat['dernier_temps'] is not None:
        terminer_jeu(ligne, etat['dernier_temps'])
        return jsonify({'status': 'stopped', 'temps': etat['dernier_temps'], 'temps_formate': f"{etat['dernier_temps']:.2f}"})
    
    if etat['temps_depart'] is not None and not etat['chrono_arrete']:
        temps_ecoule = time.time() - etat['temps_depart']
        temps_max_config = CONFIG_EPREUVES.get('temps_max', 600)
        
        if temps_ecoule >= temps_max_config:
            etat['dernier_temps'] = temps_ecoule
            etat['chrono_arrete'] = True
            terminer_jeu(ligne, etat['checkpoint'])
            return jsonify({'status': 'stopped', 'temps': etat['dernier_temps'], 'temps_formate': f"{etat['dernier_temps']:.2f}", 'message': 'Temps dépassé'})
        else:
            return jsonify({'status': 'running', 'temps': temps_ecoule, 'temps_formate': f"{temps_ecoule:.2f}"})
    
    return jsonify({'status': 'waiting', 'message': 'En attente'})

# -----------------------------------------------------------
# Route qui reçoit et vérifie la proposition du joueur pour le Mastermind
# RETURN : Un JSON contenant le résultat de la vérification
# -----------------------------------------------------------
@bouton_bp.route('/verifierReponseMastermind', methods=['POST'])
def verifier_reponse_bouton():
    ligne = str(session.get('line_id') or '1')
    ligne_int = int(ligne)
    data = request.get_json()
    guess = data.get('guess', [])
    
    statut = mastermind.get_statut_enigme(ligne)
    if not statut['active']:
        return jsonify({'status': 'error', 'message': 'Aucune énigme active'}), 400
    
    resultat = mastermind.verifier_reponse(ligne, guess)
    
    if resultat['status'] == 'correct':
        led_b2 = GPIO.get_led(ligne_int, 'b2')
        bouton_b2 = GPIO.get_bouton(ligne_int, 'b2')
        if led_b2 and bouton_b2:
            led_b2.on()
            bouton_b2.when_pressed = lambda: on_bouton_b2_pressed(ligne)
            
        return jsonify({'status': 'correct', 'message': resultat['message']})
    else:
        return jsonify(resultat)

# -----------------------------------------------------------
# Route qui vérifie si le Quiz est actif pour l'afficher côté client
# RETURN : Un JSON avec le statut "active" ou "waiting"
# -----------------------------------------------------------
@bouton_bp.route('/verifierQuiz', methods=['GET'])
def verifier_quiz():
    ligne = str(session.get('line_id') or '1')
    if ETAT_LIGNES[ligne].get('quiz_actif', False):
        return jsonify({'status': 'active'})
    return jsonify({'status': 'waiting'})

# -----------------------------------------------------------
# Route appelée après avoir réussi le Quiz pour allumer le bouton B3
# RETURN : Un JSON confirmant le succès de la validation
# -----------------------------------------------------------
@bouton_bp.route('/validerQuiz', methods=['POST'])
def valider_quiz():
    ligne = str(session.get('line_id') or '1')
    ligne_int = int(ligne)
    ETAT_LIGNES[ligne]['quiz_actif'] = False 
    
    led_b3 = GPIO.get_led(ligne_int, 'b3')
    bouton_b3 = GPIO.get_bouton(ligne_int, 'b3')
    if led_b3 and bouton_b3:
        led_b3.on()
        bouton_b3.when_pressed = lambda: on_bouton_b3_pressed(ligne)
        
    return jsonify({'status': 'success'})

# -----------------------------------------------------------
# Route qui remet à zéro l'état complet de la ligne sans enregistrer de score
# RETURN : Un JSON confirmant la réinitialisation
# -----------------------------------------------------------
@bouton_bp.route('/resetJeu', methods=['POST'])
def reset_jeu():
    ligne = str(session.get('line_id') or '1')
    ligne_int = int(ligne)
    arreter_maboul_physique(ligne)
    
    vider_tous_les_boutons(ligne_int)
    
    ETAT_LIGNES[ligne] = {'temps_depart': None, 'dernier_temps': None, 'chrono_arrete': False, 'nb_boite_faite': 0, 'checkpoint': 5, 'tm': ETAT_LIGNES[ligne].get('tm'), 'quiz_actif': False, 'maboul_actif': False, 'maboul_en_cours': False, 'penalite_timestamp': 0}
    mastermind.reset_enigme(ligne)
    
    if ETAT_LIGNES[ligne]['tm']:
        ETAT_LIGNES[ligne]['tm'].numbers(0, 0)

    return jsonify({'status': 'success', 'message': f'Ligne {ligne} réinitialisée'})

# -----------------------------------------------------------
# Route qui gère l'abandon : calcule le temps, enregistre le score actuel et stoppe tout
# RETURN : Un JSON confirmant l'enregistrement et l'arrêt
# -----------------------------------------------------------
@bouton_bp.route('/abandonnerJeu', methods=['POST'])
def abandonner_jeu():
    ligne = str(session.get('line_id') or '1')
    etat = ETAT_LIGNES[ligne]
    
    if etat['temps_depart'] is not None and not etat['chrono_arrete']:
        temps_final = time.time() - etat['temps_depart']
    else:
        temps_final = etat.get('dernier_temps') or 0.0

    terminer_jeu(ligne, temps_final)
    
    arreter_maboul_physique(ligne)
    mastermind.reset_enigme(ligne)
    
    tm_existant = etat.get('tm')
    ETAT_LIGNES[ligne] = {
        'temps_depart': None, 
        'dernier_temps': None, 
        'chrono_arrete': False, 
        'nb_boite_faite': etat['nb_boite_faite'], 
        'checkpoint': 5, 
        'tm': tm_existant, 
        'quiz_actif': False, 
        'maboul_actif': False, 
        'maboul_en_cours': False, 
        'penalite_timestamp': 0
    }
    
    if ETAT_LIGNES[ligne]['tm']:
        ETAT_LIGNES[ligne]['tm'].numbers(0, 0)

    return jsonify({'status': 'success', 'message': 'Mission abandonnée, score enregistré.'})

# -----------------------------------------------------------
# Route qui renvoie l'état de la ligne nettoyé pour le suivi de l'interface
# RETURN : Un JSON contenant la configuration et l'état de jeu actuel
# -----------------------------------------------------------
@bouton_bp.route('/getGameStatus', methods=['GET'])
def get_game_status():
    ligne = str(session.get('line_id') or '1')
    etat_propre = ETAT_LIGNES[ligne].copy()
    if 'tm' in etat_propre:
        del etat_propre['tm']
        
    return jsonify({
        'ligne_active': ligne,
        'etat': etat_propre,
        'mode_dev': CONFIG_EPREUVES.get('mode_dev', True)
    })

# Liaison des fonctions de callback pour le module Maboul physique
enregistrer_callback_victoire(on_maboul_success)
enregistrer_callback_penalite(on_maboul_penalite)