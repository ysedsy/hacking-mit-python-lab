"""Testdaten für das SQLi-Lab. Legt ein paar User mit Passwort-Hashes an."""
from werkzeug.security import generate_password_hash

from app import app
from models import db, User

DEMO = {"alice": "password1", "bob": "hunter2", "admin": "letmein123"}

with app.app_context():
    for uname, pw in DEMO.items():
        if not User.query.filter_by(username=uname).first():
            db.session.add(User(
                username=uname,
                password_hash=generate_password_hash(pw),
                totp_enabled=False,
            ))
    db.session.commit()
    print("Seed ok. User:", [u.username for u in User.query.all()])
