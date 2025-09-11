from flask import Flask, render_template

app = Flask(__name__)

# Exemple de données
computers = [
    {"id": 1, "modele": "Dell Optiplex 7010", "etat": "SSD installé"},
    {"id": 2, "modele": "HP EliteBook 840", "etat": "Nettoyage en cours"},
]

@app.route("/")
def index():
    return render_template("index.html", computers=computers)

if __name__ == "__main__":
    app.run(debug=True)
