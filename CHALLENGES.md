# Challenges — Übungs-Ziele zum Angreifen

Eigenständige, **bewusst verwundbare** Mini-Apps für den Kurs „Hacking mit
Python". Jede liegt in einem eigenen `challenge_*`-Ordner mit:
`app.py` (das Ziel), `challenge.md` (Aufgabe + Lösungsweg), `README.md`,
`requirements.txt`.

> **Grenze:** Nur gegen die **eigene** oder eine **ausdrücklich dazu
> freigegebene** Instanz im Kurs-Netz. Keine fremden/öffentlichen Systeme.
> Payloads harmlos halten (`alert`, `whoami`), kein DoS, keine echten Daten
> abfließen lassen. Nur während der Übungstermine.

## Start (für jede Challenge gleich)
```powershell
cd challenge_<name>
pip install -r requirements.txt
python app.py                      # nur lokal: http://127.0.0.1:<port>
# Für die Nachbar-Challenge im Kurs-Netz:
$env:HOST = "0.0.0.0"; python app.py
```

## Übersicht

| Challenge | Lücke (OWASP) | Angriffsziel | Port | Niveau |
|-----------|----------------|--------------|------|--------|
| [`challenge_mass_assignment`](challenge_mass_assignment/) | Mass Assignment (A01 Broken Access Control) | Mit Extra-Feld `is_admin=1` bei der Registrierung Admin werden | 5005 | leicht |
| [`challenge_stored_xss`](challenge_stored_xss/) | Stored XSS (A03 Injection) | Script in die Ticket-Beschreibung schmuggeln, das bei Betrachtern feuert | 5002 | leicht–mittel |
| [`challenge_file_upload`](challenge_file_upload/) | Unrestricted File Upload (A04/A05) | `.html`/`.svg` hochladen, das im App-Origin JavaScript ausführt | 5006 | mittel |
| [`challenge_session_forgery`](challenge_session_forgery/) | Session-Fälschung (A02 Crypto Failures) | Flask-Session-Cookie mit schwachem `SECRET_KEY` selbst signieren → als `admin` einloggen | 5001 | mittel |
| [`challenge_jwt`](challenge_jwt/) | JWT-Fälschung (A02/A07) | Token via `alg:none` oder schwachem Secret auf `role=admin` fälschen | 5004 | mittel |
| [`challenge_ssti`](challenge_ssti/) | Server-Side Template Injection → RCE (A03) | Über das Namensfeld Server-Code ausführen (`{{7*7}}` → `whoami`) | 5003 | mittel–schwer |

## Zusätzlich im Repo
- [`attacking/`](attacking/) — generischer Web-Schwachstellen-Scanner
  (`attack_all.py`), der viele dieser Lücken automatisch findet, inkl.
  Session-Forgery-Check. Nur gegen eigene/autorisierte Instanzen.
- Nummerierte Lab-Ordner `01_…`–`16_…` + `99_secret_scanner` — die progressive
  Lernstrecke (Feature → Angriff → Fix); die Challenges oben greifen dieselben
  Themen als eigenständige „Kapere die Seite"-Aufgaben heraus.

## Thematischer Bezug zur Lernstrecke
- Stored XSS → `10_xss` / `11_fix_xss`
- Session-Fälschung → `13_session_forgery`
- SSTI, JWT, Mass Assignment, File Upload → ergänzen die Lab-Themen um
  verbreitete Praxis-Lücken, die in der nummerierten Strecke (noch) fehlen.
