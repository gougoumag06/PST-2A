from flask import Blueprint, render_template, request, session, jsonify
from config import players_collection

from maboul import lancer_maboul_physique, enregistrer_callback_victoire, enregistrer_callback_penalite, arreter_maboul_physique

import time
import GPIO  
import mastermind
import threading
import tm1637
import logging

log = logging.getLogger('werkzeug')
class NoPollingSpamFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if '/maboul/status' in msg or '/bouton/obtenirTempsActuel' in msg or '/bouton/getGameStatus' in msg or '/mastermind/obtenirEnigme' in msg or '/bouton/verifierQuiz' in msg:
            return False
        return True
log.addFilter(NoPollingSpamFilter())

bouton_bp = Blueprint('bouton', __name__)

TEMPS_MAXIMUM = 1000

ETAT_LIGNES = {
    '1': {'temps_depart': None, 'dernier_temps': None, 'chrono_arrete': False, 'nb_boite_faite': 0, 'checkpoint': 5, 'tm': None, 'quiz_actif': False, 'maboul_actif': False, 'maboul_en_cours': False, 'penalite_timestamp': 0},
    '2': {'temps_depart': None, 'dernier_temps': None, 'chrono_arrete': False, 'nb_boite_faite': 0, 'checkpoint': 5, 'tm': None, 'quiz_actif': False, 'maboul_actif': False, 'maboul_en_cours': False, 'penalite_timestamp': 0}
}

def init_ecran_tm1637(ligne):
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
        print(f"[ECRAN] Connecté avec succès sur LIGNE {ligne} (CLK={pin_clk}, DIO={pin_dio})")
    except Exception as e:
        print(f"[ECRAN] Erreur d'initialisation LIGNE {ligne}: {e}")
        ETAT_LIGNES[ligne]['tm'] = None

def background_display():
    print("[THREAD] Démarrage de l'affichage en arrière-plan multi-lignes")
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

threading.Thread(target=background_display, daemon=True).start()

def enregistrer_score(temps, nb_boites):
    pseudo = session.get('player_pseudo', 'Joueur')
    player = players_collection.find_one({"pseudo": pseudo})
    
    if not player:
        players_collection.insert_one({"pseudo": pseudo, "time": temps, "nb_box": nb_boites})
        return
    
    ancien_temps = player.get("time", float('inf'))
    ancien_nb_box = player.get("nb_box", 0)
    
    if nb_boites > ancien_nb_box or (nb_boites == ancien_nb_box and temps < ancien_temps):
        players_collection.update_one({"pseudo": pseudo}, {"$set": {"time": temps, "nb_box": nb_boites}})

def enregistrer_checkpoint(ligne):
    ETAT_LIGNES[ligne]['nb_boite_faite'] += 1
    print(f"[INFO] Ligne {ligne} - Boîte complétée: {ETAT_LIGNES[ligne]['nb_boite_faite']}")
    if ETAT_LIGNES[ligne]['temps_depart'] is not None:
        ETAT_LIGNES[ligne]['checkpoint'] = time.time() - ETAT_LIGNES[ligne]['temps_depart']

def terminer_jeu(ligne, temps_final):
    etat = ETAT_LIGNES[ligne]
    print(f"[INFO] Ligne {ligne} - Fin du jeu: {temps_final:.2f}s")
    enregistrer_score(temps_final, etat['nb_boite_faite'])
    
    ligne_int = int(ligne)
    for b in ['start', 'b1', 'b2', 'b3', 'b4']:
        led = GPIO.get_led(ligne_int, b)
        if led: led.off()

def on_bouton_start_pressed(ligne):
    print(f"[INFO] Ligne {ligne} - Bouton START pressé - Lancement du CHRONO et MASTERMIND")
    ligne_int = int(ligne)
    
    arreter_maboul_physique(ligne)
    
    led_start = GPIO.get_led(ligne_int, 'start')
    bouton_start = GPIO.get_bouton(ligne_int, 'start')
    
    if led_start: led_start.off()
    ETAT_LIGNES[ligne]['temps_depart'] = time.time()
    if bouton_start: bouton_start.when_pressed = None
    
    mastermind.activer_enigme(ligne)

def on_bouton_b1_pressed(ligne):
    print(f"[INFO] Ligne {ligne} - Bouton B1 pressé - Lancement QUIZ")
    ligne_int = int(ligne)
    led_b1 = GPIO.get_led(ligne_int, 'b1')
    bouton_b1 = GPIO.get_bouton(ligne_int, 'b1')
    
    if led_b1: led_b1.off()
    if bouton_b1: bouton_b1.when_pressed = None
    
    enregistrer_checkpoint(ligne)
    ETAT_LIGNES[ligne]['quiz_actif'] = True

def on_bouton_b2_pressed(ligne):
    print(f"[INFO] Ligne {ligne} - Bouton B2 pressé - Lancement CESAR")
    ligne_int = int(ligne)
    
    led_b2 = GPIO.get_led(ligne_int, 'b2')
    bouton_b2 = GPIO.get_bouton(ligne_int, 'b2')
    
    if led_b2: led_b2.off()
    if bouton_b2: bouton_b2.when_pressed = None
    
    enregistrer_checkpoint(ligne)
    
    led_b3 = GPIO.get_led(ligne_int, 'b3')
    bouton_b3 = GPIO.get_bouton(ligne_int, 'b3')

    if led_b3 and bouton_b3:
        led_b3.on()
        bouton_b3.when_pressed = lambda: on_bouton_b3_pressed(ligne)

def on_bouton_b3_pressed(ligne):
    print(f"[INFO] Ligne {ligne} - Bouton B3 pressé - Lancement DR MABOUL")
    ligne_int = int(ligne)
    
    led_b3 = GPIO.get_led(ligne_int, 'b3')
    bouton_b3 = GPIO.get_bouton(ligne_int, 'b3')
    
    if led_b3: led_b3.off()
    if bouton_b3: bouton_b3.when_pressed = None
    
    enregistrer_checkpoint(ligne)
    lancer_maboul_physique(ligne) 
    
def on_maboul_penalite(ligne):
    if ETAT_LIGNES[ligne]['temps_depart'] is not None:
        ETAT_LIGNES[ligne]['temps_depart'] -= 5.0
        ETAT_LIGNES[ligne]['penalite_timestamp'] = time.time()
        print(f"[INFO] Ligne {ligne} - ⚡ PÉNALITÉ APPLIQUÉE : Affichage de +5s !")

def on_maboul_success(ligne):
    print(f"[INFO] Ligne {ligne} - VICTOIRE MABOUL (Fil END détecté) -> Passage au Bouton B4")
    ligne_int = int(ligne)
    
    enregistrer_checkpoint(ligne)
    
    led_b4 = GPIO.get_led(ligne_int, 'b4')
    bouton_b4 = GPIO.get_bouton(ligne_int, 'b4')

    if led_b4 and bouton_b4:
        led_b4.on()
        bouton_b4.when_pressed = lambda: on_bouton_b4_pressed(ligne)    
    else:
        print(f"⚠️ [ERREUR MATÉRIELLE] Impossible d'allumer B4 sur la Ligne {ligne_int} ! Vérifiez votre fichier GPIO.py.")

def on_bouton_b4_pressed(ligne):
    print(f"[INFO] Ligne {ligne} - Bouton B4 pressé - FIN DU JEU")
    ligne_int = int(ligne)
    
    led_b4 = GPIO.get_led(ligne_int, 'b4')
    bouton_b4 = GPIO.get_bouton(ligne_int, 'b4')
    
    if led_b4: led_b4.off()
    if bouton_b4: bouton_b4.when_pressed = None
    
    enregistrer_checkpoint(ligne)
    
    if ETAT_LIGNES[ligne]['temps_depart'] is not None:
        temps_ecoule = time.time() - ETAT_LIGNES[ligne]['temps_depart']
        ETAT_LIGNES[ligne]['dernier_temps'] = temps_ecoule
        ETAT_LIGNES[ligne]['chrono_arrete'] = True

@bouton_bp.route('/jeux')
def page_jeux():
    return render_template('InGame.html')

@bouton_bp.route('/lancerJeux', methods=['POST'])
def lancer_jeu():
    # LA PROTECTION EST ICI : si vide, on prend '1'
    ligne = str(session.get('line_id') or '1')
    ligne_int = int(ligne)
    
    print(f"[INFO] Démarrage d'une nouvelle partie sur la LIGNE {ligne}")
    
    arreter_maboul_physique(ligne)
    
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

@bouton_bp.route('/obtenirTempsActuel', methods=['GET'])
def obtenir_temps_actuel():
    ligne = str(session.get('line_id') or '1')
    etat = ETAT_LIGNES[ligne]
    
    if etat['chrono_arrete'] and etat['dernier_temps'] is not None:
        terminer_jeu(ligne, etat['dernier_temps'])
        return jsonify({'status': 'stopped', 'temps': etat['dernier_temps'], 'temps_formate': f"{etat['dernier_temps']:.2f}"})
    
    if etat['temps_depart'] is not None and not etat['chrono_arrete']:
        temps_ecoule = time.time() - etat['temps_depart']
        
        if temps_ecoule >= TEMPS_MAXIMUM:
            etat['dernier_temps'] = temps_ecoule
            etat['chrono_arrete'] = True
            terminer_jeu(ligne, etat['checkpoint'])
            return jsonify({'status': 'stopped', 'temps': etat['dernier_temps'], 'temps_formate': f"{etat['dernier_temps']:.2f}", 'message': 'Temps dépassé'})
        else:
            return jsonify({'status': 'running', 'temps': temps_ecoule, 'temps_formate': f"{temps_ecoule:.2f}"})
    
    return jsonify({'status': 'waiting', 'message': 'En attente'})

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
        led_b1 = GPIO.get_led(ligne_int, 'b1')
        bouton_b1 = GPIO.get_bouton(ligne_int, 'b1')
        
        if led_b1 and bouton_b1:
            led_b1.on()
            bouton_b1.when_pressed = lambda: on_bouton_b1_pressed(ligne)
            
        return jsonify({'status': 'correct', 'message': resultat['message']})
    else:
        return jsonify(resultat)

@bouton_bp.route('/verifierQuiz', methods=['GET'])
def verifier_quiz():
    ligne = str(session.get('line_id') or '1')
    if ETAT_LIGNES[ligne].get('quiz_actif', False):
        return jsonify({'status': 'active'})
    return jsonify({'status': 'waiting'})

@bouton_bp.route('/validerQuiz', methods=['POST'])
def valider_quiz():
    ligne = str(session.get('line_id') or '1')
    ligne_int = int(ligne)
    ETAT_LIGNES[ligne]['quiz_actif'] = False 
    
    led_b2 = GPIO.get_led(ligne_int, 'b2')
    bouton_b2 = GPIO.get_bouton(ligne_int, 'b2')
    
    if led_b2 and bouton_b2:
        led_b2.on()
        bouton_b2.when_pressed = lambda: on_bouton_b2_pressed(ligne)
        
    return jsonify({'status': 'success'})

@bouton_bp.route('/resetJeu', methods=['POST'])
def reset_jeu():
    ligne = str(session.get('line_id') or '1')
    ligne_int = int(ligne)
    
    arreter_maboul_physique(ligne)
    
    ETAT_LIGNES[ligne] = {'temps_depart': None, 'dernier_temps': None, 'chrono_arrete': False, 'nb_boite_faite': 0, 'checkpoint': 5, 'tm': ETAT_LIGNES[ligne].get('tm'), 'quiz_actif': False, 'maboul_actif': False, 'maboul_en_cours': False, 'penalite_timestamp': 0}
    mastermind.reset_enigme(ligne)
    
    for b in ['start', 'b1', 'b2', 'b3', 'b4']:
        led = GPIO.get_led(ligne_int, b)
        if led: led.off()
    
    if ETAT_LIGNES[ligne]['tm']:
        ETAT_LIGNES[ligne]['tm'].numbers(0, 0)

    return jsonify({'status': 'success', 'message': f'Ligne {ligne} réinitialisée'})

@bouton_bp.route('/getGameStatus', methods=['GET'])
def get_game_status():
    ligne = str(session.get('line_id') or '1')
    
    etat_propre = ETAT_LIGNES[ligne].copy()
    if 'tm' in etat_propre:
        del etat_propre['tm']
        
    return jsonify({
        'ligne_active': ligne,
        'etat': etat_propre
    })

enregistrer_callback_victoire(on_maboul_success)
enregistrer_callback_penalite(on_maboul_penalite)