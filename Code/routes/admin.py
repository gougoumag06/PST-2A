from flask import Blueprint, render_template, request, redirect, url_for, session
from config import players_collection

admin_bp = Blueprint('admin', __name__)

# ==========================================
# === PARAMÈTRES GLOBAUX DE LA VALISE ======
# ==========================================
CONFIG_EPREUVES = {
    'temps_max': 600, # 10 minutes par défaut
    'mode_dev': True  # Bouton Bypass activé par défaut
}

# -----------------------------------------------------------
# Fonction qui retourne la page du leaderbord
# -----------------------------------------------------------
@admin_bp.route('/Leaderboard')
def leaderboard():
    filter_val = request.args.get('nb_box', 'all')
    query = {}
    sort_criteria = []
    if filter_val != 'all':
        try:
            query['nb_box'] = int(filter_val)
            sort_criteria = [("time", 1)]
        except ValueError:
            pass
    
    if not sort_criteria:
        sort_criteria = [("nb_box", -1), ("time", 1)]
            
    players = list(players_collection.find(query).sort(sort_criteria))
    return render_template('leaderboard.html', players=players, current_filter=filter_val)

# -----------------------------------------------------------
# Fonction qui retourne le choix de la ligne
# -----------------------------------------------------------
@admin_bp.route('/choicesline')
def choicesline():
    return render_template('choicesline.html')

# -----------------------------------------------------------
# Fonction qui retourne le choix de la ligne et envoie le joueur sur la page d'inscription
# -----------------------------------------------------------
@admin_bp.route('/select_line/<int:line_id>')
def select_line(line_id):
    session['line_id'] = line_id
    print(f"[INFO] Ligne sélectionnée : {line_id}")
    return redirect(url_for('player.login'))

# -----------------------------------------------------------
# Fonction qui retourne la page de settings
# -----------------------------------------------------------
@admin_bp.route('/setting', methods=['GET', 'POST'])
def setting_admin():
    if request.method == 'POST':
        # Sauvegarde du Temps Maximum
        try:
            CONFIG_EPREUVES['temps_max'] = int(request.form.get('temps_max', 600))
        except ValueError:
            pass
            
        # Sauvegarde du Mode Dev
        CONFIG_EPREUVES['mode_dev'] = (request.form.get('mode_dev') == 'oui')
        
        print(f"[ADMIN] Paramètres sauvegardés : {CONFIG_EPREUVES}")
        
    return render_template('setting.html', config=CONFIG_EPREUVES)

@admin_bp.route('/api/config_epreuves', methods=['GET'])
def get_config():
    return CONFIG_EPREUVES