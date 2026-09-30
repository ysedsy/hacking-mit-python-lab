"""Ponyverkauf (Blueprint) — ⚠️ VERWUNDBARE Variante (Roh-SQL in der Pony-Suche).

Die Suche baut die SQL-Abfrage per String-Verkettung -> SQL-Injection. Passt
natürlich zum Marktplatz: ein Kunde 'sucht' und schleust dabei SQL ein.
Nur lokal / im Kurs-Netz. Der Fix ist die parametrisierte Variante (ab Ordner 07).
"""
from flask import Blueprint, render_template, request
from sqlalchemy import text
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
    q = request.args.get("q", "")
    sql_shown = None
    if q:
        # ⚠️ DIE LÜCKE: Eingabe direkt in den SQL-String verkettet.
        sql = ("SELECT id, name, breed, price, description, seller "
               f"FROM ponies WHERE name LIKE '%{q}%' OR breed LIKE '%{q}%'")
        sql_shown = sql
        ponies = db.session.execute(text(sql)).fetchall()
    else:
        ponies = db.session.execute(text(
            "SELECT id, name, breed, price, description, seller FROM ponies"
        )).fetchall()
    return render_template("ponys.html", ponies=ponies, q=q, sql=sql_shown)


@bp.route("/pony/<int:pid>")
def pony_detail(pid):
    pony = Pony.query.get_or_404(pid)   # Detailseite bleibt ORM (sicher)
    return render_template("pony.html", pony=pony)
