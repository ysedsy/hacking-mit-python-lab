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

> **Alle Aufgaben auf einer Seite (ohne Lösungen):**
> [`challenges/index.html`](challenges/index.html) — im Browser öffnen. Die Seite
> wird aus den `challenge.md`-Dateien erzeugt (`cd challenges && python build_index.py`).

| Challenge | Lücke (OWASP) | Angriffsziel | Port | Niveau |
|-----------|----------------|--------------|------|--------|
| [`challenge_mass_assignment`](challenges/challenge_mass_assignment/) | Mass Assignment (A01 Broken Access Control) | Mit Extra-Feld `is_admin=1` bei der Registrierung Admin werden | 5005 | leicht |
| [`challenge_stored_xss`](challenges/challenge_stored_xss/) | Stored XSS (A03 Injection) | Script in die Ticket-Beschreibung schmuggeln, das bei Betrachtern feuert | 5002 | leicht–mittel |
| [`challenge_business_logic`](challenges/challenge_business_logic/) | Business-Logic-Fehler (A04 Insecure Design) | Über eine negative Menge im Shop den 500-Gold-Sheriffstern für 50 Gold kaufen | 5009 | leicht–mittel |
| [`challenge_race_condition`](challenges/challenge_race_condition/) | Race Condition / TOCTOU (A04 Insecure Design) | Durch parallele Auszahlungen mehr Gold abheben, als auf dem Konto liegt | 5008 | mittel |
| [`challenge_session_forgery`](challenge_session_forgery/) | Session-Fälschung (A02 Crypto Failures) | Flask-Session-Cookie mit schwachem `SECRET_KEY` selbst signieren → als `admin` einloggen | 5001 | mittel |
| [`challenge_session_puppetry`](challenges/challenge_session_puppetry/) | Session-Abuse → Privilege Escalation (A01 Broken Access Control) | Über ein ungeplantes Feld `rang=marshal` die Session manipulieren (ohne `SECRET_KEY`) und ins Marshal-Büro kommen | 5007 | mittel |
| [`challenge_password_reset`](challenges/challenge_password_reset/) | Schwaches Reset-Token (A07 Auth Failures) | Vorhersagbares Reset-Token (Zeitstempel) raten und das Konto `marshal` übernehmen | 5010 | mittel |
| [`challenge_file_upload`](challenges/challenge_file_upload/) | Unrestricted File Upload (A04/A05) | `.html`/`.svg` hochladen, das im App-Origin JavaScript ausführt | 5006 | mittel |
| [`challenge_jwt`](challenges/challenge_jwt/) | JWT-Fälschung (A02/A07) | Token via `alg:none` oder schwachem Secret auf `role=admin` fälschen | 5004 | mittel |
| [`challenge_ssrf`](challenges/challenge_ssrf/) | Server-Side Request Forgery (A10) | Den Importer eine interne URL (`/intern`) abrufen lassen, die von außen `403` liefert | 5011 | mittel |
| [`challenge_ssti`](challenges/challenge_ssti/) | Server-Side Template Injection → RCE (A03) | Über das Namensfeld Server-Code ausführen (`{{7*7}}` → `whoami`) | 5003 | mittel–schwer |
| [`challenge_pickle`](challenges/challenge_pickle/) | Insecure Deserialization (A08 Integrity Failures) | Präpariertes `pickle`-Cookie (`__reduce__`) → Server führt Code aus (harmloser Marker) | 5012 | mittel–schwer |

## Alles auf einem Port: der Hub
- [`challenges/hub/`](challenges/hub/) — ein **Launcher** auf **einem Port**
  (Standard `5000`). Der Hub lädt die unveränderten `challenge_*/app.py` und
  mountet jede unter einem eigenen Prefix (`/mass_assignment`, `/ssti`, …); die
  Startseite verlinkt alle Challenges und zeigt die Aufgaben (ohne Lösungen).
  ```powershell
  cd challenges/hub
  pip install -r requirements.txt
  python hub.py                 # http://127.0.0.1:5000
  ```
  Eine schmale WSGI-Middleware biegt feste Links, Redirects und Cookie-Pfade auf
  den jeweiligen Prefix um — die einzelnen Apps bleiben unverändert und laufen
  weiterhin auch einzeln (`cd challenge_<name> && python app.py`).

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
