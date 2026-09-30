"""Ordner 05 — SQL-Injection-Szenario (ABSICHTLICH VERWUNDBAR).

⚠️ Dieser Ordner enthält BEWUSST unsichere Queries. Nur lokal, nur zum Lernen!
Der Fix folgt in Ordner 07.

Evolution gegenüber Ordner 04: zwei neue, verwundbare Stellen mit ROH-SQL
(String-Verkettung statt Parameter):

  * /search        -> UNION-/Boolean-Injection, um Daten (auch Hashes) zu ziehen
  * /login-legacy  -> Auth-Bypass mit  ' OR '1'='1' --  (umgeht sogar 2FA!)

Alle anderen Routen (ORM-basiert) bleiben sicher — das zeigt den Kontrast.
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
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
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
    # ⚠️ VERWUNDBAR — ROH-SQL mit String-Verkettung. Fix in Ordner 07.
    # ----------------------------------------------------------------------
    @app.route("/search", methods=["GET", "POST"])
    @login_required
    def search():
        form = SearchForm()
        results, executed_sql, error = None, None, None
        q = None
        if form.validate_on_submit():
            q = form.q.data
        elif request.args.get("q"):
            q = request.args.get("q")

        if q is not None:
            # DIE LÜCKE: Eingabe wird direkt in den SQL-String verkettet.
            sql = f"SELECT id, username FROM users WHERE username LIKE '%{q}%'"
            executed_sql = sql
            try:
                rows = db.session.execute(text(sql)).fetchall()
                results = [tuple(r) for r in rows]
            except Exception as exc:  # zeigt DB-Fehler -> hilft dem Angreifer
                error = str(exc)
        return render_template("search.html", form=form,
                               results=results, sql=executed_sql, error=error)

    @app.route("/login-legacy", methods=["GET", "POST"])
    def login_legacy():
        """⚠️ Verwundbarer Alt-Login mit Roh-SQL. Payload:  ' OR '1'='1' --"""
        error, executed_sql = None, None
        if request.method == "POST":
            uname = request.form.get("username", "")
            pw = request.form.get("password", "")
            # DIE LÜCKE: keine Parameter, kein Hash-Vergleich.
            sql = (
                "SELECT id, username FROM users "
                f"WHERE username = '{uname}' AND password_hash = '{pw}'"
            )
            executed_sql = sql
            try:
                row = db.session.execute(text(sql)).fetchone()
            except Exception as exc:
                row = None
                error = str(exc)
            if row:
                session.clear()
                session["user"] = row[1]  # Bypass: 2FA wird komplett übersprungen
                flash("Legacy-Login erfolgreich (unsicher!).", "success")
                return redirect(url_for("board"))
            if not error:
                error = "Login fehlgeschlagen."
        return render_template("login_legacy.html", error=error, sql=executed_sql)

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
