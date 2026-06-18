from flask import Blueprint, render_template, request, redirect, url_for, session 
from config import players_collection

player_bp = Blueprint('player', __name__)


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
        
        # ==========================================
        # AJOUTE CETTE LIGNE EXACTEMENT ICI :
        session['line_id'] = line_choisie
        # ==========================================
        
        player = players_collection.find_one({"pseudo": pseudo})
        
        if player:
            if player.get('contact_info') == contact_info:
                session['player_pseudo'] = pseudo 
                # On redirige en gardant la ligne dans l'URL pour la suite
                return redirect(url_for('player.welcome_player', line=line_choisie))
            else:
                error = "Ce pseudo est déjà utilisé avec des coordonnées différentes."
        else:
            new_player = {
                    "pseudo": pseudo,
                    "contact_method": contact_method,
                    "contact_info": contact_info,
                    "try": 0, "time": 5, "nb_box": 0
            }
            players_collection.insert_one(new_player)
            session['player_pseudo'] = pseudo
            return redirect(url_for('player.welcome_player', line=line_choisie))
            
    return render_template('player_login.html', error=error)
# def login():
#     error = None
    
#     # Si le formulaire est envoyé (POST)
#     if request.method == 'POST':
#         pseudo = request.form.get('pseudo', '').strip()
#         contact_method = request.form.get('contact_method')
#         contact_info = request.form.get('contact_info', '').strip()
        
#         # --- RÉCUPÉRATION DE LA VARIABLE LIGNE ---
#         line_choisie = request.form.get('line') 
#         print(f"[INFO] Connexion de {pseudo} sur la LIGNE : {line_choisie}")
        
#         # Tu peux maintenant utiliser 'line_choisie' comme une simple variable
#         # Par exemple, la passer à la page suivante via l'URL si tu ne veux toujours pas de session
        
#         player = players_collection.find_one({"pseudo": pseudo})
        
#         if player:
#             if player.get('contact_info') == contact_info:
#                 session['player_pseudo'] = pseudo 
#                 # On redirige en gardant la ligne dans l'URL pour la suite
#                 return redirect(url_for('player.welcome_player', line=line_choisie))
#             else:
#                 error = "Ce pseudo est déjà utilisé avec des coordonnées différentes."
#         else:
#             new_player = {
#                     "pseudo": pseudo,
#                     "contact_method": contact_method,
#                     "contact_info": contact_info,
#                     "try": 0, "time": 5, "nb_box": 0
#             }
#             players_collection.insert_one(new_player)
#             session['player_pseudo'] = pseudo
#             return redirect(url_for('player.welcome_player', line=line_choisie))
            
#     return render_template('player_login.html', error=error)

@player_bp.route('/welcome_player')
def welcome_player():
    pseudo = session.get('player_pseudo', 'Joueur')
    # On récupère la ligne depuis l'URL pour l'afficher ou l'utiliser
    line = request.args.get('line', 'Non définie')
    return render_template('index-players.html', pseudo=pseudo, line=line)

# N'oublie pas d'ajouter InGame aussi si tu veux que la ligne suive jusqu'au jeu
@player_bp.route('/InGame')
def InGame():
    pseudo = session.get('player_pseudo', 'Joueur')
    line = request.args.get('line') # On récupère la ligne
    return render_template('InGame.html', pseudo=pseudo, line=line)