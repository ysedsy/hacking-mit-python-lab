"""SQLAlchemy-Modelle. Neu gegenüber Ordner 02: das Post-Modell fürs Board."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    posts = db.relationship("Post", backref="author", lazy=True)

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"


class Post(db.Model):
    """Ein Beitrag, den ALLE User auf dem Board sehen.

    Genau dieser 'Content von allen Usern' ist die Bühne fürs XSS-Szenario
    (Ordner 10): dort wird der Beitrag absichtlich UNescaped gerendert.
    Hier in Ordner 03 wird noch sicher (autoescaped) ausgegeben.
    """
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Post {self.id} by user {self.user_id}>"
