"""SQLAlchemy-Modelle. Neu gegenüber Ordner 03: 2FA-Felder am User."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    # 2FA: TOTP-Secret (Base32). enabled erst, wenn der User den ersten Code bestätigt.
    totp_secret = db.Column(db.String(64), nullable=True)
    totp_enabled = db.Column(db.Boolean, default=False, nullable=False)
    # Fix gegen Brute Force: Fehlversuche zählen und Konto temporär sperren.
    failed_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    bio = db.Column(db.String(200), default="", nullable=False)  # fürs CSRF-Szenario
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    posts = db.relationship("Post", backref="author", lazy=True)

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Pony(db.Model):
    """Pony im Ponyverkauf (öffentlicher Marktplatz)."""
    __tablename__ = "ponies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    breed = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.String(1000), nullable=False, default="")
    seller = db.Column(db.String(80), nullable=False, default="Ranch")
