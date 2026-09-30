"""Ponyverkauf (Blueprint) — saubere, injektionssichere Variante (ORM).

Öffentlicher Marktplatz: jeder kann stöbern. Wird in app.py per
register_blueprint(bp) eingehängt; seed_ponies() legt beim ersten Start Ponys an.
"""
from flask import Blueprint, render_template, request
from models import db, Pony

bp = Blueprint("ponies", __name__)

DEFAULT_PONIES = [
    ("Blitz", "Mustang", 1200, "Temperamentvoller Wallach, perfekt für lange Ausritte durch die Prärie.", "Ranch Goldgräber"),
    ("Sternschnuppe", "Appaloosa", 1500, "Sanftmütige Stute mit auffälliger Fellzeichnung. Ideal für Anfänger.", "Miller's Stables"),
    ("Donner", "Friese", 2400, "Kräftiger Hengst, ideal für die harte Arbeit am Hof.", "Ranch Goldgräber"),
    ("Kaktus", "Shetland-Pony", 600, "Kleines, freches Pony – der Liebling aller Kinder.", "Doña Rosa"),
    ("Silber", "Quarter Horse", 1800, "Schnell und wendig, ein echter Rodeo-Champion.", "Silver Creek"),
    ("Whiskey", "Palomino", 1600, "Goldene Mähne, ruhiges Gemüt, treuer Begleiter.", "Miller's Stables"),
]


def seed_ponies() -> None:
    if Pony.query.count() == 0:
        for name, breed, price, desc, seller in DEFAULT_PONIES:
            db.session.add(Pony(name=name, breed=breed, price=price,
                                description=desc, seller=seller))
        db.session.commit()


@bp.app_context_processor
def inject_featured():
    try:
        return {"featured_ponies": Pony.query.order_by(Pony.id).limit(3).all()}
    except Exception:
        return {"featured_ponies": []}


@bp.route("/ponys")
def list_ponys():
    q = request.args.get("q", "").strip()
    if q:
        # Sicher: ORM-Parameter, kein String-Bau.
        like = f"%{q}%"
        ponies = Pony.query.filter(
            Pony.name.ilike(like) | Pony.breed.ilike(like)
        ).order_by(Pony.id).all()
    else:
        ponies = Pony.query.order_by(Pony.id).all()
    return render_template("ponys.html", ponies=ponies, q=q)


@bp.route("/pony/<int:pid>")
def pony_detail(pid):
    pony = Pony.query.get_or_404(pid)
    return render_template("pony.html", pony=pony)
