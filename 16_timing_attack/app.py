"""Ordner 07 — Fix gegen SQL-Injection.

Behebt die Lücken aus Ordner 05. Kernregel: **niemals Eingaben in SQL-Strings
verketten**. Zwei sichere Wege:

  1. ORM (`filter_by(...)`) — wie in Ordner 02 ff. bereits genutzt.
  2. Roh-SQL nur mit **gebundenen Parametern**: `text("... :name")` +
     `.bindparams(name=...)`  (SQLAlchemy-`text()` mit ":" — genau der Aufgaben-Hinweis).

Zusätzlich: `SECRET_KEY` NUR noch aus der Umgebung (kein Default im Code) — geprüft mit
`bandit -r .` und `detect-secrets` (siehe README).
"""
import hmac
import io
import os
import time
from datetime import datetime, timedelta, timezone
from functools import wraps

import pyotp
import qrcode
import qrcode.image.svg
from flask import (
    Flask, render_template, redirect, url_for, session, flash, request,
    send_file, abort, Response,
)
from werkzeug.utils import safe_join  # Flask 3: safe_join lebt in werkzeug.utils
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Post, Note
from forms import RegisterForm, LoginForm, TotpForm, PostForm, SearchForm, ProfileForm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ISSUER = "HackingLab"

# Fix-Parameter gegen Brute Force
MAX_FAILED = 5              # so viele Fehlversuche ...
LOCK_MINUTES = 15          # ... dann Konto für 15 Minuten sperren

# Rate-Limit pro IP (2. Verteidigungslinie, unabhängig vom Konto)
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app() -> Flask:
    app = Flask(__name__)
    # --- Session-ID-Forgery-Szenario -------------------------------------
    # Flask SIGNIERT den Session-Cookie mit SECRET_KEY (er ist NICHT verschlüsselt).
    # Ist der Key schwach/ratbar/geleakt, kann ein Angreifer mit flask-unsign einen
    # eigenen Cookie fälschen, z. B. {"user":"admin"}.
    if os.environ.get("VULN_WEAK_SECRET") == "1":
        # ⚠️ SZENARIO: schwaches Secret -> flask-unsign knackt es per Wortliste.
        app.config["SECRET_KEY"] = "cowboy"
    else:
        # ✅ FIX: starkes Secret aus der Umgebung (bzw. zufällig pro Start).
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "hackinglab.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Fix: Session-Cookie härten -> JS kommt nicht mehr an den Cookie (Cookie-Klau tot).
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    db.init_app(app)
    limiter.init_app(app)

    @app.after_request
    def set_csp(resp):
        # Fix: Content-Security-Policy blockt inline-Skripte -> selbst wenn irgendwo
        # doch mal ungeescapter Input landet, führt der Browser kein <script> aus.
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            # script-src OHNE 'unsafe-inline' -> genau das killt Inline-XSS.
            "script-src 'self'; "
            # Styles inline erlaubt (das Cowboy-Theme nutzt <style>); Styles sind
            # nicht der XSS-Vektor, um den es hier geht.
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; "
            "img-src 'self' data:; object-src 'none'; base-uri 'none'"
        )
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp
    from ponies import bp as ponies_bp, seed_ponies
    app.register_blueprint(ponies_bp)
    with app.app_context():
        db.create_all()
        seed_ponies()

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
    # Fix (Rate-Limit): max. 10 Login-Versuche pro Minute und IP.
    @limiter.limit("10 per minute", methods=["POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            uname = form.username.data.strip()
            user = User.query.filter_by(username=uname).first()
            now = datetime.now(timezone.utc)

            # Fix (Lockout): gesperrtes Konto abweisen, egal ob Passwort stimmt.
            if user and user.locked_until and _aware(user.locked_until) > now:
                rest = int((_aware(user.locked_until) - now).total_seconds() // 60) + 1
                flash(f"Konto gesperrt. Versuch's in ~{rest} Min. erneut.", "danger")
                return render_template("login.html", form=form)

            if user and check_password_hash(user.password_hash, form.password.data):
                user.failed_attempts = 0          # Reset bei Erfolg
                user.locked_until = None
                db.session.commit()
                if user.totp_enabled:
                    session["2fa_pending"] = user.username
                    return redirect(url_for("twofa_verify"))
                _finish_login(user)
                return redirect(url_for("board"))

            # Fehlversuch zählen und ggf. sperren.
            if user:
                user.failed_attempts = (user.failed_attempts or 0) + 1
                if user.failed_attempts >= MAX_FAILED:
                    user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
                    user.failed_attempts = 0
                    flash(f"Zu viele Fehlversuche — Konto für {LOCK_MINUTES} Min. gesperrt.",
                          "danger")
                else:
                    left = MAX_FAILED - user.failed_attempts
                    flash(f"Falsches Passwort. Noch {left} Versuch(e) bis zur Sperre.",
                          "danger")
                db.session.commit()
            else:
                # Kein Timing-Unterschied preisgeben (siehe auch Ordner 16).
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

    # ----------------------------------------------------------------------
    # ⚠️ CSRF-LÜCKE: State-Change per GET, ohne CSRF-Token. Ein fremder
    # <img src=".../set-bio?bio=hacked"> im Opfer-Browser ändert dessen Bio,
    # weil der Session-Cookie automatisch mitgeschickt wird.
    # ----------------------------------------------------------------------
    @app.route("/set-bio")
    @login_required
    def set_bio_vuln():
        new_bio = request.args.get("bio", "")
        user = current_user()
        user.bio = new_bio[:200]
        db.session.commit()
        flash("Bio geändert (über unsichere GET-Route!).", "warning")
        return redirect(url_for("profile"))

    # FIX: Änderungen nur per POST mit CSRF-Token (form.hidden_tag()).
    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        user = current_user()
        form = ProfileForm(bio=user.bio)
        if form.validate_on_submit():   # prüft automatisch das CSRF-Token
            user.bio = form.bio.data or ""
            db.session.commit()
            flash("Steckbrief gespeichert (sicher, mit CSRF-Token).", "success")
            return redirect(url_for("profile"))
        return render_template("profile.html", form=form, bio=user.bio)

    # ----------------------------------------------------------------------
    # ⚠️ LFI-LÜCKE: Datei-Name kommt ungeprüft aus request.args und wird direkt
    # zusammengesetzt. Mit ../ (Path Traversal) lässt sich JEDE Datei lesen —
    # z. B. ../app.py -> daraus der SECRET_KEY (siehe auch Ordner 13!).
    # ----------------------------------------------------------------------
    DOCS_DIR = os.path.join(BASE_DIR, "docs")

    @app.route("/disclaimer")
    def disclaimer():
        page = request.args.get("page", "disclaimer.txt")
        # DIE LÜCKE: os.path.join folgt "../" aus dem Verzeichnis heraus.
        path = os.path.join(DOCS_DIR, page)
        try:
            return send_file(path)
        except Exception:
            abort(404)

    # ✅ FIX: safe_join blockt "../" (gibt None -> 404); zusätzlich Whitelist.
    ALLOWED_DOCS = {"disclaimer.txt", "agb.txt"}

    @app.route("/disclaimer-safe")
    def disclaimer_safe():
        page = request.args.get("page", "disclaimer.txt")
        if page not in ALLOWED_DOCS:
            abort(404)
        safe = safe_join(DOCS_DIR, page)
        if safe is None:
            abort(404)
        return send_file(safe)

    # ----------------------------------------------------------------------
    # ⚠️ TIMING-ATTACK: der Vergleich bricht beim ersten falschen Zeichen ab
    # (early return) + künstliche Verzögerung pro korrektem Zeichen. Wer die
    # Antwortzeit misst, kann das Token Zeichen für Zeichen erraten.
    # ----------------------------------------------------------------------
    API_TOKEN = os.environ.get("API_TOKEN", "S3CR3T")

    def insecure_compare(a: str, b: str) -> bool:
        if len(a) != len(b):
            return False
        for x, y in zip(a, b):
            if x != y:
                return False          # bricht früh ab -> messbarer Zeitunterschied
            time.sleep(0.005)         # verstärkt den Effekt für die Demo
        return True

    @app.route("/api/verify")
    def api_verify_vuln():
        token = request.args.get("token", "")
        ok = insecure_compare(token, API_TOKEN)
        return ("OK" if ok else "DENIED"), (200 if ok else 403)

    # ✅ FIX: konstante Zeit, unabhängig davon, wie viele Zeichen stimmen.
    @app.route("/api/verify-safe")
    def api_verify_safe():
        token = request.args.get("token", "")
        ok = hmac.compare_digest(token, API_TOKEN)
        return ("OK" if ok else "DENIED"), (200 if ok else 403)

    # ----------------------------------------------------------------------
    # ⚠️ IDOR: die Notiz-ID kommt aus der URL, aber es wird NICHT geprüft, ob die
    # Notiz dem eingeloggten User gehört. /note/1, /note/2, ... liest fremde Notizen.
    # ----------------------------------------------------------------------
    @app.route("/note/<int:nid>")
    @login_required
    def note_vuln(nid):
        note = Note.query.get_or_404(nid)          # KEIN Owner-Check!
        return render_template("note.html", note=note, safe=False)

    # ✅ FIX: zusätzlich zur ID die Zugehörigkeit zum aktuellen User prüfen.
    @app.route("/note-safe/<int:nid>")
    @login_required
    def note_safe(nid):
        note = Note.query.filter_by(id=nid, user_id=current_user().id).first()
        if note is None:
            abort(404)   # 404 statt 403: verrät nicht mal die Existenz
        return render_template("note.html", note=note, safe=True)

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


def _aware(dt: datetime) -> datetime:
    """SQLite gibt naive datetimes zurück -> als UTC interpretieren."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _finish_login(user: User) -> None:
    session.clear()
    session["user"] = user.username


app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    print(f" * 🤠 Cowboy-Forum reitet auf http://{host}:{port}  (nur im Kurs-Netz!)")
    app.run(host=host, port=port, debug=True)
