from flask import Blueprint, jsonify, request, session
import random

mastermind_bp = Blueprint('mastermind', __name__)

COLORS = ['black', 'red', 'blue', 'purple', 'yellow', 'green']
FRENCH_COLORS = {'black': 'Noir', 'red': 'Rouge', 'blue': 'Bleu', 'purple': 'Violet', 'yellow': 'Jaune', 'green': 'Vert'}

# Dictionnaire d'état par ligne (remplace les variables globales)
ETAT_MASTERMIND = {
    '1': {'active': False, 'resolue': False, 'secret_code': [], 'history': []},
    '2': {'active': False, 'resolue': False, 'secret_code': [], 'history': []}
}

def activer_enigme(ligne):
    ETAT_MASTERMIND[ligne]['active'] = True
    ETAT_MASTERMIND[ligne]['resolue'] = False
    
    # Remplacement de random.choice par random.sample pour éviter les doublons
    ETAT_MASTERMIND[ligne]['secret_code'] = random.sample(COLORS, 4)
    
    ETAT_MASTERMIND[ligne]['history'] = []
    print(f"[DEBUG MASTERMIND] Ligne {ligne} - Code secret généré : {ETAT_MASTERMIND[ligne]['secret_code']}")

def reset_enigme(ligne):
    ETAT_MASTERMIND[ligne]['active'] = False
    ETAT_MASTERMIND[ligne]['resolue'] = False
    ETAT_MASTERMIND[ligne]['secret_code'] = []
    ETAT_MASTERMIND[ligne]['history'] = []

def get_statut_enigme(ligne):
    return {
        'active': ETAT_MASTERMIND[ligne]['active'],
        'resolue': ETAT_MASTERMIND[ligne]['resolue'],
        'history': ETAT_MASTERMIND[ligne]['history']
    }

def verifier_reponse(ligne, guess):
    etat = ETAT_MASTERMIND[ligne]
    
    if len(guess) != 4:
        return {'status': 'error', 'message': 'Il faut 4 couleurs !'}

    secret_code = etat['secret_code']
    exact = sum(1 for s, g in zip(secret_code, guess) if s == g)
    
    secret_temp = secret_code[:]
    guess_temp = guess[:]
    
    for i in range(3, -1, -1):
        if secret_temp[i] == guess_temp[i]:
            del secret_temp[i]
            del guess_temp[i]

    partial = 0
    for g in guess_temp:
        if g in secret_temp:
            partial += 1
            secret_temp.remove(g)

    etat['history'].append({'guess': guess, 'exact': exact, 'partial': partial})

    if exact == 4:
        etat['resolue'] = True
        etat['active'] = False
        return {'status': 'correct', 'message': 'Code trouvé ! Le bouton suivant est actif.'}
    
    return {'status': 'incorrect', 'history': etat['history']}

@mastermind_bp.route('/obtenirEnigme', methods=['GET'])
def obtenir_enigme():
    ligne = str(session.get('line_id', '1'))
    etat = ETAT_MASTERMIND[ligne]
    
    if etat['active'] and not etat['resolue']:
        return jsonify({
            'status': 'active', 
            'history': etat['history'], 
            'colors': COLORS, 
            'french_colors': FRENCH_COLORS
        })
    elif etat['resolue']:
        return jsonify({'status': 'resolved', 'message': 'Énigme Mastermind résolue'})
    return jsonify({'status': 'inactive'})
