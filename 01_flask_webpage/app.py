"""Ordner 01 — Webpage mit Flask.

Feature-Stand:
  * Login / Register
  * Sessions (server-signiertes Cookie via SECRET_KEY)
  * WTForms mit Feld-Validierung (siehe forms.py)
  * WARNUNG: Passwoerter werden hier ABSICHTLICH im Klartext gespeichert (unsicher,
    wie im Aufgaben-Status). Hashing kommt spaeter als Fix (Ordner 06_passwort_hashes).

Speicherung: hier noch eine einfache JSON-Datei. In Ordner 02 wird das durch eine
echte SQL-Datenbank (SQLAlchemy) ersetzt.
"""
import json
import os
from functools import wraps

from flask import (
    Flask, render_template, redirect, url_for, session, flash, abort
)

from forms import RegisterForm, LoginForm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

app = Flask(__name__)
# In der Übung ok; produktiv NIE hart im Code -> os.environ (siehe Ordner 14 LFI!).
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# Ponyverkauf (statische Variante, da Ordner 01 noch keine SQL-DB hat).
from ponies import bp as ponies_bp  # noqa: E402
app.register_blueprint(ponies_bp)


# --- Mini-"Datenbank": JSON-Datei -------------------------------------------
def load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_users(users: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as fh:
        json.dump(users, fh, indent=2, ensure_ascii=False)


# --- Auth-Helfer ------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            flash("Bitte zuerst einloggen.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# --- Routen -----------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", user=session.get("user"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        users = load_users()
        uname = form.username.data.strip()
        if uname in users:
            flash("Benutzername ist bereits vergeben.", "danger")
        else:
            users[uname] = {
                # WARNUNG: Klartext (unsicher) - Fix (Hashing) in Ordner 06.
                "password": form.password.data,
            }
            save_users(users)
            flash("Registrierung erfolgreich. Bitte einloggen.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        users = load_users()
        user = users.get(form.username.data.strip())
        # WARNUNG: Klartext-Vergleich (unsicher) - Fix in Ordner 06.
        if user and user.get("password") == form.password.data:
            session.clear()
            session["user"] = form.username.data.strip()
            flash("Willkommen zurück!", "success")
            return redirect(url_for("dashboard"))
        flash("Falscher Benutzername oder Passwort.", "danger")
    return render_template("login.html", form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=session["user"])


@app.route("/logout")
def logout():
    session.clear()
    flash("Ausgeloggt.", "info")
    return redirect(url_for("index"))


@app.context_processor
def _nav_helpers():
    # Erlaubt der Cowboy-Nav, Links nur zu zeigen, wenn es die Route gibt.
    return {"has_endpoint": lambda ep: ep in app.view_functions}


if __name__ == "__main__":
    # Gruppen-Lab: standardmäßig im Netz erreichbar (0.0.0.0), damit die anderen
    # aus dem Kurs die Lücken ausprobieren können. NUR im vertrauenswürdigen Netz!
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    print(f" * 🤠 Cowboy-Forum reitet auf http://{host}:{port}  (nur im Kurs-Netz!)")
    app.run(host=host, port=port, debug=True)
