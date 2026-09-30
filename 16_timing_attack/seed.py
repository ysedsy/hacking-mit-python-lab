"""Testdaten fürs IDOR-Lab: User + je eine private Notiz."""
from werkzeug.security import generate_password_hash

from app import app
from models import db, User, Note

DEMO = {"alice": "password1", "bob": "hunter2", "admin": "letmein123"}
NOTES = {
    "alice": "Alices geheime Ranch-Koordinaten: 34.05N, 118.24W",
    "bob":   "Bobs Tresor-Code: 4-8-15-16-23-42",
    "admin": "ADMIN-Masterpasswort-Hinweis: das Pferd heisst Silver",
}

with app.app_context():
    for uname, pw in DEMO.items():
        if not User.query.filter_by(username=uname).first():
            db.session.add(User(
                username=uname,
                password_hash=generate_password_hash(pw),
                totp_enabled=False,
            ))
    db.session.commit()
    for uname, text in NOTES.items():
        u = User.query.filter_by(username=uname).first()
        if u and not Note.query.filter_by(user_id=u.id).first():
            db.session.add(Note(user_id=u.id, secret_text=text))
    db.session.commit()
    print("Seed ok. User:", [u.username for u in User.query.all()])
    for n in Note.query.all():
        print(f"  Note #{n.id} -> user_id {n.user_id}")
