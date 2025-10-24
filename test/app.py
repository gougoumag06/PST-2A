from flask import Flask

from routes.bouton import bouton_bp


app = Flask(__name__)



app.register_blueprint(bouton_bp)




if __name__ == '__main__':
    app.run(debug=True)
