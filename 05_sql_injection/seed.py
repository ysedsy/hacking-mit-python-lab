"""Testdaten fuer das SQLi-Lab. Passwoerter hier absichtlich im KLARTEXT
(unsicher, wie im Aufgaben-Status). Hashing kommt als Fix ab Ordner 06."""
from app import app
from models import db, User

DEMO = {"alice": "password1", "bob": "hunter2", "admin": "letmein123"}

with app.app_context():
    for uname, pw in DEMO.items():
        if not User.query.filter_by(username=uname).first():
            db.session.add(User(
                username=uname,
                password=pw,   # WARNUNG: Klartext (unsicher)
                totp_enabled=False,
            ))
    db.session.commit()
    print("Seed ok. User:", [u.username for u in User.query.all()])
