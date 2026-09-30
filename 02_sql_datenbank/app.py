"""Ordner 02 — Externe Anbindung SQL-Datenbank.

Evolution gegenüber Ordner 01: die JSON-Datei ist weg. Benutzer liegen jetzt in einer
echten SQL-Datenbank, angesprochen über das ORM (SQLAlchemy).

Wichtig für spätere Ordner: hier wird der DB-Zugriff **sauber über das ORM**
gemacht (parametrisiert, keine String-Verkettung). Das SQL-Injection-Szenario in
Ordner 05 baut absichtlich eine unsichere Roh-Query ein, um den Unterschied zu zeigen.
"""
import os
from functools import wraps

from flask import Flask, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User
from forms import RegisterForm, LoginForm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    # Externe DB per Umgebungsvariable; Default = lokale SQLite-Datei.
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "hackinglab.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()

    register_routes(app)

    @app.context_processor
    def _nav_helpers():
        return {"has_endpoint": lambda ep: ep in app.view_functions}

    return app


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            flash("Bitte zuerst einloggen.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return render_template("index.html", user=session.get("user"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            uname = form.username.data.strip()
            # ORM-Query -> parametrisiert, injektionssicher.
            if User.query.filter_by(username=uname).first():
                flash("Benutzername ist bereits vergeben.", "danger")
            else:
                user = User(
                    username=uname,
                    password_hash=generate_password_hash(form.password.data),
                )
                db.session.add(user)
                db.session.commit()
                flash("Registrierung erfolgreich. Bitte einloggen.", "success")
                return redirect(url_for("login"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            uname = form.username.data.strip()
            user = User.query.filter_by(username=uname).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                session.clear()
                session["user"] = user.username
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


app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    print(f" * 🤠 Cowboy-Forum reitet auf http://{host}:{port}  (nur im Kurs-Netz!)")
    app.run(host=host, port=port, debug=True)
