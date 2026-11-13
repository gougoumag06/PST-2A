from flask import Blueprint, render_template, request, redirect, url_for, session 
from config import players_collection

player_bp = Blueprint('player', __name__)

# -----------------------------------------------------------
# Fonction qui retourne la page de login
# -----------------------------------------------------------
@player_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    # Si le formulaire est envoyé (POST)
    if request.method == 'POST':
        pseudo = request.form.get('pseudo', '').strip()
        contact_method = request.form.get('contact_method')
        contact_info = request.form.get('contact_info', '').strip()
        
        # --- RÉCUPÉRATION DE LA VARIABLE LIGNE ---
        line_choisie = request.form.get('line') 
        print(f"[INFO] Connexion de {pseudo} sur la LIGNE : {line_choisie}")
        
        session['line_id'] = line_choisie
        
        player = players_collection.find_one({"pseudo": pseudo})
        
        if player:
            if player.get('contact_info') == contact_info:
                session['player_pseudo'] = pseudo 
                return redirect(url_for('player.welcome_player', line=line_choisie))
            else:
                error = "Ce pseudo est déjà utilisé avec des coordonnées différentes."
        else:
            # === INITIALISATION PAR DÉFAUT À -1 ===
            new_player = {
                    "pseudo": pseudo,
                    "contact_method": contact_method,
                    "contact_info": contact_info,
                    "try": 0, 
                    "time": -1, 
                    "nb_box": -1
            }
            players_collection.insert_one(new_player)
            session['player_pseudo'] = pseudo
            return redirect(url_for('player.welcome_player', line=line_choisie))
            
    return render_template('player_login.html', error=error)

# -----------------------------------------------------------
# Fonction qui retourne la page de commencement
# -----------------------------------------------------------
@player_bp.route('/welcome_player')
def welcome_player():
    pseudo = session.get('player_pseudo', 'Joueur')
    line = request.args.get('line', 'Non définie')
    return render_template('index-players.html', pseudo=pseudo, line=line)

# -----------------------------------------------------------
# Fonction qui retourne la page de jeux
# -----------------------------------------------------------
@player_bp.route('/InGame')
def InGame():
    pseudo = session.get('player_pseudo', 'Joueur')
    line = request.args.get('line') 
    return render_template('InGame.html', pseudo=pseudo, line=line)