"""SQLAlchemy-Modelle — externe Anbindung einer SQL-Datenbank.

Standard: SQLite-Datei (keine Installation nötig). Für einen echten externen
Server (z. B. PostgreSQL/MySQL) einfach die DATABASE_URL setzen, z. B.:

    postgresql+psycopg://user:pass@localhost:5432/hackinglab
    mysql+pymysql://user:pass@localhost:3306/hackinglab

Das ORM abstrahiert den DB-Typ — der App-Code bleibt gleich.
"""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"


class Pony(db.Model):
    """Pony im Ponyverkauf (öffentlicher Marktplatz)."""
    __tablename__ = "ponies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    breed = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.String(1000), nullable=False, default="")
    seller = db.Column(db.String(80), nullable=False, default="Ranch")
