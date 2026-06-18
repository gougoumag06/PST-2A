from flask import Blueprint, jsonify
import csv
import random
import os

quiz_bp = Blueprint('quiz', __name__)

# --- CORRECTION DU CHEMIN ---
# On récupère le dossier actuel (la racine, là où se trouve quiz.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# On pointe vers le sous-dossier 'csv' que tu as créé
CHEMIN_CSV = os.path.join(BASE_DIR, 'csv')

def charger_questions(nom_fichier):
    questions = []
    chemin = os.path.join(CHEMIN_CSV, nom_fichier)
    
    if os.path.exists(chemin):
        with open(chemin, mode='r', encoding='utf-8') as f:
            lecteur = csv.reader(f, delimiter=',')
            next(lecteur) # Ignorer l'en-tête
            for ligne in lecteur:
                if len(ligne) == 7:
                    questions.append(ligne)
    else:
        print(f"[Attention] Fichier CSV introuvable : {chemin}")
    return questions

@quiz_bp.route('/api/questions')
def api_questions():
    fichiers_themes = ["culture2.csv", "elec.csv", "info.csv", "math.csv", "physique.csv"]
    questions_selectionnees = []
    
    for fichier in fichiers_themes:
        lignes = charger_questions(fichier)
        if lignes:
            q = random.choice(lignes)

            question_texte = q[0]
            bonne_reponse = q[1]
            choix = q[1:7]
            random.shuffle(choix)
            questions_selectionnees.append({
                "question": question_texte, 
                "choix": choix, 
                "bonne_reponse": bonne_reponse
            })
            
    return jsonify(questions_selectionnees)
