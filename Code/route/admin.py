from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from config import players_collection


admin_bp = Blueprint('admin', __name__)

from flask import Blueprint, render_template, request
from config import players_collection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/Leaderboard')
def leaderboard():
    # recuperation du filtre 
    filter_val = request.args.get('nb_box', 'all')
    
    query = {}
    sort_criteria = []
    if filter_val != 'all':
        try:
            #filtre pour un nombre de boitre spécifique
            query['nb_box'] = int(filter_val)
            # On trie par le temps 
            sort_criteria = [("time", 1)]
        except ValueError:
            pass
    
    # si sur all ou pas valide 
    if not sort_criteria:
        # trie des boite en decroissant 
        # trie des temps croissant 
        sort_criteria = [("nb_box", -1), ("time", 1)]
            
    players = list(players_collection.find(query).sort(sort_criteria))
    
    return render_template('leaderboard.html', players=players, current_filter=filter_val)

@admin_bp.route('/choicesline')
def choicesline():
    """Affiche la page de choix de ligne"""
    return render_template('choicesline.html')

@admin_bp.route('/select_line/<int:line_id>')
def select_line(line_id):
    """
    1. Enregistre la ligne dans la session
    2. Redirige vers le login joueur
    """
    session['line_id'] = line_id
    print(f"[INFO] Ligne sélectionnée : {line_id}")
    
    # On redirige vers la page de login du joueur
    return redirect(url_for('player.login'))


    
@admin_bp.route('/setting')
def setting_admin():
    return render_template('setting.html')