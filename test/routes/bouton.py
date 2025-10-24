from flask import Blueprint, render_template, request, redirect, url_for, session

bouton_bp = Blueprint('bouton', __name__)

@bouton_bp.route('/')
def home():
    return render_template('index.html') 

@bouton_bp.route('/API/API_bouton', methods=['GET', 'POST'])
def bouton_press():
    if request.method == 'POST':
        button_state = request.json.get('button_state')
        print(f'Button state received: {button_state}')
        return {'status': 'success', 'button_state': button_state}, 200
    return {'status': 'error', 'message': 'Invalid request method'}, 400



