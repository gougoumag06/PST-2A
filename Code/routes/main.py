from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

# -----------------------------------------------------------
# Fonction qui retourne la page d'acceuil
# -----------------------------------------------------------
@main_bp.route('/')
def index():
    return render_template('index.html')