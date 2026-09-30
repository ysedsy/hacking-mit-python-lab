# Ordner 01 — Webpage mit Flask

Erste Stufe des Labs. Eine minimale, **saubere** Flask-App als Fundament.

## Enthalten
- **Login / Register** (`/login`, `/register`)
- **Sessions** über signiertes Cookie (`SECRET_KEY`)
- **WTForms** mit Feld-Validierung (`forms.py`) — Länge, erlaubte Zeichen, Passwort-Bestätigung
- **Passwort-Hashing** mit Werkzeug (PBKDF2) — Klartext wird nie gespeichert
- `form.hidden_tag()` liefert nebenbei schon den CSRF-Token (Details: Ordner 12)

Speicherung: einfache `users.json`. Ab **Ordner 02** ersetzt eine echte SQL-Datenbank
(SQLAlchemy) diese Datei.

## Starten
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
→ http://127.0.0.1:5000

## Lernpunkte
| Konzept | Wo |
|---|---|
| Field Validation / WTForms | `forms.py` |
| Sessions | `session[...]` in `app.py` |
| Passwort-Hashing | `generate_password_hash` / `check_password_hash` |
| Login-Schutz per Decorator | `login_required` in `app.py` |

> Hinweis: `SECRET_KEY` hier als Default im Code — das ist bewusst der Anknüpfungspunkt
> für das **LFI-Szenario in Ordner 14** (Secret Key auslesen).
