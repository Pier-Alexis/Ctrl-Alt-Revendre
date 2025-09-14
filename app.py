from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_secret_key_to_something_random_and_long"  # CHANGE THIS in production

# --- Compte unique (en mémoire) ---
USER_NAME = "Langevin"
# On génère un hash à partir du mot de passe fourni (ce hash est en mémoire au démarrage).
# Si tu veux, tu peux remplacer cette ligne par un hash fixe généré une fois.
USER_PASSWORD_HASH = generate_password_hash("L@ngev1n208")

# Page d'accueil
@app.route("/")
def home():
    return render_template("index.html")

# Page de login (GET affiche le formulaire, POST traite la connexion)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Vérification du compte unique
        if username == USER_NAME and check_password_hash(USER_PASSWORD_HASH, password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            # utiliser flash pour afficher le message d'erreur dans le template
            flash("Identifiants incorrects", "error")
            return render_template("login.html"), 401

    # GET
    return render_template("login.html")

# Dashboard protégé : là où tu pourras ajouter/modifier PC plus tard
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        # Pour l'instant une page simple ; on l'étoffera ensuite
        return render_template("dashboard.html", user=session["user"])
    return redirect(url_for("login"))

# Déconnexion
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
