from flask import Blueprint, render_template, jsonify, session, request
import threading
import time
import logging

# =============================================
#  FILTRE ANTI-SPAM CONSOLE (SILENCE RADIO)
# =============================================
log = logging.getLogger('werkzeug')
class NoPollingSpamFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if '/maboul/status' in msg or '/bouton/obtenirTempsActuel' in msg or '/bouton/getGameStatus' in msg or '/mastermind/obtenirEnigme' in msg or '/bouton/verifierQuiz' in msg:
            return False
        return True
log.addFilter(NoPollingSpamFilter())

maboul_bp = Blueprint('maboul', __name__, template_folder='templates')

# === LES CALLBACKS POUR COMMUNIQUER AVEC LE RESTE DU JEU ===
CALLBACK_VICTOIRE = None
CALLBACK_PENALITE = None

def enregistrer_callback_victoire(fonction):
    global CALLBACK_VICTOIRE
    CALLBACK_VICTOIRE = fonction

def enregistrer_callback_penalite(fonction):
    global CALLBACK_PENALITE
    CALLBACK_PENALITE = fonction

# =============================================
#  IMPORT GPIO
# =============================================
try:
    from GPIO import get_maboul_input, init_gpio
    _gpio_ok = True
    print("[MABOUL] Import GPIO OK")
except ImportError as e:
    print(f"[MABOUL] Impossible d'importer gestion_gpio : {e}")
    _gpio_ok = False

def _get_pins(ligne):
    if not _gpio_ok:
        return None, None, None
    try:
        ligne_int = int(ligne)
        return (
            get_maboul_input(ligne_int, 'start'),
            get_maboul_input(ligne_int, 'touch'),
            get_maboul_input(ligne_int, 'end'),
        )
    except Exception as e:
        print(f"[MABOUL] Erreur récupération pins : {e}")
        return None, None, None

# =============================================
#  STRUCTURE DE L'ÉTAT DU JEU
# =============================================
class MabulState:
    def __init__(self, ligne):
        self.ligne_active = str(ligne)
        self.reset()

    def reset(self):
        self.phase = 'inactive'
        self.result = None
        self.temps_bonus = 5.0 # Valeur de la pénalité
        self.start_time = None
        self.timer_thread = None
        self.watch_thread = None  
        self.stop_event = threading.Event()
        self.nb_touches = 0

ETAT_MABOUL = {
    '1': MabulState('1'),
    '2': MabulState('2')
}

def _build_payload(ligne):
    state = ETAT_MABOUL[ligne]
    return {
        'ligne': ligne,
        'phase': state.phase,
        'result': state.result,
        'nb_touches': state.nb_touches
    }

# =============================================
#  BOUCLE TIMER INFINI + SURVEILLANCE
# =============================================
def timer_loop(ligne, pin_touch, pin_end):
    state = ETAT_MABOUL[ligne]
    last_touch = False
    last_end   = False

    while not state.stop_event.is_set():
        time.sleep(0.05)
        if state.phase != 'playing':
            continue

        if pin_touch:
            cur = pin_touch.is_pressed
            if cur and not last_touch:
                state.nb_touches += 1
                print(f"[MABOUL LIGNE {ligne}] 💥 TOUCHE FIL → Pénalité +{state.temps_bonus}s envoyée au général !")
                
                if CALLBACK_PENALITE:
                    CALLBACK_PENALITE(ligne)
                    
            last_touch = cur

        if pin_end:
            cur = pin_end.is_pressed
            if cur and not last_end:
                print(f"[MABOUL] 🏁 CONTACT END DETECTÉ !")
                _game_over(ligne, 'success')
                
                if CALLBACK_VICTOIRE:
                    CALLBACK_VICTOIRE(ligne)
                break
            last_end = cur

def _game_over(ligne, result):
    state = ETAT_MABOUL[ligne]
    state.phase  = 'finished'
    state.result = result
    state.stop_event.set()

# =============================================
#  SURVEILLANCE DÉPART STRICTE SUR LE 'START'
# =============================================
def watch_start(ligne):
    state = ETAT_MABOUL[ligne]
    pin_start, pin_touch, pin_end = _get_pins(ligne)

    print(f"[MABOUL LIGNE {ligne}] 🕵️ Surveillance activée. Touchez uniquement le plot START pour lancer le jeu...")

    while not state.stop_event.is_set():
        time.sleep(0.05)
        if state.phase != 'idle':
            break

        # On ne regarde QUE le capteur START
        s_pressed = pin_start.is_pressed if pin_start else False

        # Dès que START passe en "Touché" (True)
        if s_pressed:
            print(f"[MABOUL LIGNE {ligne}] 🚀 DÉMARRAGE ! Le joueur a touché le START.")
            
            # Petite grâce d'une demi-seconde pour laisser le joueur lever la main
            # sans déclencher le fil de cuivre instantanément s'il tremble
            time.sleep(0.5) 
            
            _start_game(ligne, pin_touch, pin_end)
            break

def _start_game(ligne, pin_touch, pin_end):
    state = ETAT_MABOUL[ligne]
    state.phase = 'playing'
    state.start_time = time.time()
    state.stop_event.clear()

    state.timer_thread = threading.Thread(target=timer_loop, args=(ligne, pin_touch, pin_end), daemon=True)
    state.timer_thread.start()

# =============================================
#  FONCTIONS EXPORTÉES : LANCEMENT ET ARRÊT
# =============================================
def lancer_maboul_physique(ligne='1'):
    ligne = str(ligne)
    state = ETAT_MABOUL[ligne]
    state.stop_event.set()
    
    if state.timer_thread and state.timer_thread.is_alive(): state.timer_thread.join(timeout=0.5)
    if state.watch_thread and state.watch_thread.is_alive(): state.watch_thread.join(timeout=0.5)

    state.reset()
    state.phase = 'idle' 
    
    state.watch_thread = threading.Thread(target=watch_start, args=(ligne,), daemon=True)
    state.watch_thread.start()

def arreter_maboul_physique(ligne='1'):
    ligne = str(ligne)
    if ligne in ETAT_MABOUL:
        state = ETAT_MABOUL[ligne]
        state.stop_event.set()
        state.reset()

# =============================================
#  ROUTES API
# =============================================
@maboul_bp.route('/')
def index():
    return render_template('maboul.html')

@maboul_bp.route('/status')
def status():
    ligne = request.args.get('line') or str(session.get('line_id', '1'))
    return jsonify(_build_payload(ligne))

@maboul_bp.route('/desactiver', methods=['POST'])
def desactiver():
    ligne = request.args.get('line') or str(session.get('line_id', '1'))
    arreter_maboul_physique(ligne)
    return jsonify({'ok': True})
