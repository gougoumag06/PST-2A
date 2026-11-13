from flask import Blueprint, jsonify
import csv
import random
import os

quiz_bp = Blueprint('quiz', __name__)

# Direction du fichier quiz.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Direction du dossier csv.
CHEMIN_CSV = os.path.join(BASE_DIR, 'csv')

# -----------------------------------------------------------
# Fonction permetant de charger les questions 
# PARAMETRE : Le nom du fichier
# RETURN : Un tableaux avec la question et les réponses
# -----------------------------------------------------------
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


# -----------------------------------------------------------
# Fonction qui envoie les questions au JSON
# RETURN : Envoie les question au fichier JS pour afficher sur le web
# -----------------------------------------------------------
@quiz_bp.route('/api/questions')
def api_questions():
    fichiers_themes = ["culture2.csv", "elec.csv", "info.csv", "math.csv", "physique.csv"]
    questions_selectionnees = []
    
    #On va récupérer une question dans chaque fichier
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