# Ordner 02 — Externe Anbindung SQL-Datenbank

Zweite Stufe. Die `users.json` aus Ordner 01 wird durch eine **echte SQL-Datenbank**
ersetzt, angebunden über das ORM **SQLAlchemy** (`Flask-SQLAlchemy`).

## Neu gegenüber Ordner 01
- `models.py`: `User`-Modell (Tabelle `users`)
- DB-Zugriff über das ORM statt JSON
- App-Factory `create_app()` + `db.create_all()` beim Start

## Datenbank wählen
Default ist eine lokale **SQLite**-Datei (`hackinglab.db`, wird automatisch angelegt).
Für einen echten externen Server einfach `DATABASE_URL` setzen:

```powershell
# PostgreSQL (Treiber: pip install psycopg[binary])
$env:DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/hackinglab"

# MySQL/MariaDB (Treiber: pip install pymysql)
$env:DATABASE_URL = "mysql+pymysql://user:pass@localhost:3306/hackinglab"
```

## Starten
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
→ http://127.0.0.1:5000

## Wichtig fürs Lab
Hier wird **bewusst sauber** über das ORM abgefragt (`filter_by(...)`) — das ist
automatisch parametrisiert und damit **injektionssicher**. Ordner 05 baut dann
absichtlich eine unsichere Roh-SQL-Query ein, damit ihr den Unterschied im Angriff
(Ordner 05) und im Fix (Ordner 07) direkt seht.
