"""Ordner 07 — Fix gegen SQL-Injection.

Behebt die Lücken aus Ordner 05. Kernregel: **niemals Eingaben in SQL-Strings
verketten**. Zwei sichere Wege:

  1. ORM (`filter_by(...)`) — wie in Ordner 02 ff. bereits genutzt.
  2. Roh-SQL nur mit **gebundenen Parametern**: `text("... :name")` +
     `.bindparams(name=...)`  (SQLAlchemy-`text()` mit ":" — genau der Aufgaben-Hinweis).

Zusätzlich: `SECRET_KEY` NUR noch aus der Umgebung (kein Default im Code) — geprüft mit
`bandit -r .` und `detect-secrets` (siehe README).
"""
import io
import os
from functools import wraps

import pyotp
import qrcode
import qrcode.image.svg
from flask import Flask, render_template, redirect, url_for, session, flash, request
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Post
from forms import RegisterForm, LoginForm, TotpForm, PostForm, SearchForm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ISSUER = "HackingLab"


def create_app() -> Flask:
    app = Flask(__name__)
    # Fix: KEIN hartkodierter Default mehr. Secret kommt ausschließlich aus der Umgebung.
    # (bandit B105/hardcoded_password_string & detect-secrets würden einen Default melden.)
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        # Für die Lernumgebung: pro Start zufällig, statt fest im Code.
        secret = os.urandom(32).hex()
    app.config["SECRET_KEY"] = secret
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "hackinglab.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            flash("Bitte zuerst einloggen.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    if "user" in session:
        return User.query.filter_by(username=session["user"]).first()
    return None


def qr_svg_data_uri(uri: str) -> str:
    """QR-Code als inline-SVG-Data-URI (kein Pillow nötig)."""
    img = qrcode.make(uri, image_factory=qrcode.image.svg.SvgImage)
    buf = io.BytesIO()
    img.save(buf)
    import base64
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return render_template("index.html", user=session.get("user"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            uname = form.username.data.strip()
            if User.query.filter_by(username=uname).first():
                flash("Benutzername ist bereits vergeben.", "danger")
            else:
                user = User(
                    username=uname,
                    password_hash=generate_password_hash(form.password.data),
                    totp_secret=pyotp.random_base32(),  # Secret erzeugen
                    totp_enabled=False,                 # erst nach Bestätigung aktiv
                )
                db.session.add(user)
                db.session.commit()
                session["2fa_setup"] = user.username
                flash("Fast fertig — jetzt 2FA einrichten.", "info")
                return redirect(url_for("twofa_setup"))
        return render_template("register.html", form=form)

    @app.route("/2fa/setup", methods=["GET", "POST"])
    def twofa_setup():
        uname = session.get("2fa_setup")
        if not uname:
            return redirect(url_for("register"))
        user = User.query.filter_by(username=uname).first()
        if not user:
            session.pop("2fa_setup", None)
            return redirect(url_for("register"))

        totp = pyotp.TOTP(user.totp_secret)
        uri = totp.provisioning_uri(name=user.username, issuer_name=ISSUER)

        form = TotpForm()
        if form.validate_on_submit():
            if totp.verify(form.code.data, valid_window=1):
                user.totp_enabled = True
                db.session.commit()
                session.pop("2fa_setup", None)
                flash("2FA aktiviert. Bitte einloggen.", "success")
                return redirect(url_for("login"))
            flash("Code stimmt nicht. Nochmal versuchen.", "danger")

        return render_template(
            "twofa_setup.html", form=form,
            qr=qr_svg_data_uri(uri), secret=user.totp_secret,
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            uname = form.username.data.strip()
            user = User.query.filter_by(username=uname).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                if user.totp_enabled:
                    # Faktor 1 ok -> Faktor 2 anfordern.
                    session["2fa_pending"] = user.username
                    return redirect(url_for("twofa_verify"))
                _finish_login(user)
                return redirect(url_for("board"))
            flash("Falscher Benutzername oder Passwort.", "danger")
        return render_template("login.html", form=form)

    @app.route("/2fa/verify", methods=["GET", "POST"])
    def twofa_verify():
        uname = session.get("2fa_pending")
        if not uname:
            return redirect(url_for("login"))
        user = User.query.filter_by(username=uname).first()
        form = TotpForm()
        if form.validate_on_submit():
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(form.code.data, valid_window=1):
                session.pop("2fa_pending", None)
                _finish_login(user)
                flash("Willkommen zurück!", "success")
                return redirect(url_for("board"))
            flash("Code stimmt nicht.", "danger")
        return render_template("twofa_verify.html", form=form)

    # ----------------------------------------------------------------------
    # FIX der /search aus Ordner 05: gebundene Parameter statt Verkettung.
    # ----------------------------------------------------------------------
    @app.route("/search", methods=["GET", "POST"])
    @login_required
    def search():
        form = SearchForm()
        results = None
        q = None
        if form.validate_on_submit():
            q = form.q.data
        elif request.args.get("q"):
            q = request.args.get("q")[:32]

        if q is not None:
            # Variante A (empfohlen): reines ORM.
            #   results = User.query.filter(User.username.like(f"%{q}%")).all()
            # Variante B: Roh-SQL, aber SICHER — text() mit :param (Aufgaben-Hinweis).
            stmt = text(
                "SELECT id, username FROM users WHERE username LIKE :pattern"
            ).bindparams(pattern=f"%{q}%")
            rows = db.session.execute(stmt).fetchall()
            results = [tuple(r) for r in rows]
        return render_template("search.html", form=form, results=results)

    @app.route("/board", methods=["GET", "POST"])
    @login_required
    def board():
        form = PostForm()
        if form.validate_on_submit():
            db.session.add(Post(user_id=current_user().id,
                                content=form.content.data.strip()))
            db.session.commit()
            flash("Beitrag veröffentlicht.", "success")
            return redirect(url_for("board"))
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return render_template("board.html", form=form, posts=posts)

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html", user=session["user"])

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Ausgeloggt.", "info")
        return redirect(url_for("index"))


def _finish_login(user: User) -> None:
    session.clear()
    session["user"] = user.username


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
