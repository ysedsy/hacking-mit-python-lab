"""Ponyverkauf (Blueprint) — Variante ohne Datenbank (für Ordner 01).

Ordner 01 hat noch keine SQL-DB, daher eine statische Ponyliste im Code.
"""
from flask import Blueprint, render_template, request, abort

bp = Blueprint("ponies", __name__)

PONIES = [
    {"id": 1, "name": "Blitz", "breed": "Mustang", "price": 1200,
     "description": "Temperamentvoller Wallach, perfekt für lange Ausritte durch die Prärie.",
     "seller": "Ranch Goldgräber"},
    {"id": 2, "name": "Sternschnuppe", "breed": "Appaloosa", "price": 1500,
     "description": "Sanftmütige Stute mit auffälliger Fellzeichnung. Ideal für Anfänger.",
     "seller": "Miller's Stables"},
    {"id": 3, "name": "Donner", "breed": "Friese", "price": 2400,
     "description": "Kräftiger Hengst, ideal für die harte Arbeit am Hof.",
     "seller": "Ranch Goldgräber"},
    {"id": 4, "name": "Kaktus", "breed": "Shetland-Pony", "price": 600,
     "description": "Kleines, freches Pony – der Liebling aller Kinder.",
     "seller": "Doña Rosa"},
    {"id": 5, "name": "Silber", "breed": "Quarter Horse", "price": 1800,
     "description": "Schnell und wendig, ein echter Rodeo-Champion.",
     "seller": "Silver Creek"},
    {"id": 6, "name": "Whiskey", "breed": "Palomino", "price": 1600,
     "description": "Goldene Mähne, ruhiges Gemüt, treuer Begleiter.",
     "seller": "Miller's Stables"},
]


def seed_ponies() -> None:   # kein DB-Seed nötig; für einheitliche API vorhanden
    pass


@bp.app_context_processor
def inject_featured():
    return {"featured_ponies": PONIES[:3]}


@bp.route("/ponys")
def list_ponys():
    q = request.args.get("q", "").strip().lower()
    if q:
        ponies = [p for p in PONIES
                  if q in p["name"].lower() or q in p["breed"].lower()]
    else:
        ponies = PONIES
    return render_template("ponys.html", ponies=ponies, q=q)


@bp.route("/pony/<int:pid>")
def pony_detail(pid):
    pony = next((p for p in PONIES if p["id"] == pid), None)
    if pony is None:
        abort(404)
    return render_template("pony.html", pony=pony)
