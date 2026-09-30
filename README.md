# Hacking mit Python — Sicherheits-Lab

Ein **Lehr-Lab** für den Kurs *Hacking mit Python*. Die Idee: eine Flask-Web-App,
die sich über nummerierte Ordner **schrittweise weiterentwickelt**. Jeder Ordner ist
eine eigenständig lauffähige Version, die auf der vorherigen aufbaut und ein neues
Thema (Feature, Schwachstelle **oder** Fix) hinzufügt.

> ⚠️ **Nur für Lehrzwecke & lokal.** Alle "Angriffe" richten sich ausschließlich gegen
> die selbst gebaute App auf `127.0.0.1`. Angriffe gegen fremde Systeme oder das
> Sammeln echter Zugangsdaten sind kein Teil dieses Labs.

## Aufbau — jede Zeile der Aufgabe = ein Ordner

| # | Ordner | Thema |
|---|--------|-------|
| 01 | `01_flask_webpage` | Webpage mit Flask: Login/Register, Sessions, WTForms-Validierung |
| 02 | `02_sql_datenbank` | Externe Anbindung SQL-Datenbank (SQLAlchemy) |
| 03 | `03_user_content_board` | Seite mit Content von allen Usern (Basis fürs XSS-Szenario) |
| 04 | `04_zwei_faktor_auth` | Zwei-Faktor-Authentifizierung (TOTP) bei Registrierung |
| 05 | `05_sql_injection` | SQL-Injection-Szenario **+ Handhabung mit Burp** |
| 06 | `06_passwort_hashes` | Passwortangriff mit Hashcat / OphCrack (offline, eigene Hashes) |
| 07 | `07_fix_sql_injection` | Fix gegen SQLi (parametrisiert), geprüft mit `bandit` + `detect-secrets` |
| 08 | `08_brute_force` | Brute Force: Burp / Hydra / Playwright (gegen eigene App) |
| 09 | `09_fix_brute_force` | Fix gegen Brute Force (Rate-Limit, Lockout) |
| 10 | `10_xss` | XSS-Szenario: Cookie-Klau & Keylogger (im eigenen Board) |
| 11 | `11_fix_xss` | Fix gegen XSS (Escaping, CSP) |
| 12 | `12_csrf` | CSRF-Szenario + Fix (`form.hidden_tag()`) |
| 13 | `13_session_forgery` | Session-ID-Forgery mit `flask-unsign` + Fix |
| 14 | `14_lfi` | Local File Inclusion + Fix (safe `send_file`) |
| 15 | `15_idor` | IDOR (ID in URL manipulieren) + Fix |
| 16 | `16_timing_attack` | Timing-/Zeitkanal-Angriff + Fix (`hmac.compare_digest`) |
| 99 | `99_secret_scanner` | **Defensiv statt offensiv:** eigenen Git-Verlauf nach committeten Secrets durchsuchen |

## Ausführen

Jeder Ordner hat eine eigene `requirements.txt` und `README.md`. Empfohlen:

```bash
cd 01_flask_webpage
python -m venv .venv
.venv\Scripts\activate      # Windows PowerShell
pip install -r requirements.txt
python app.py
# -> http://127.0.0.1:5000
```

## Didaktisches Prinzip

Für **jede** Schwachstelle gilt: erst das **Szenario** (wie greift man an), dann der
**Fix** (wie verhindert man es). Der Erkenntnisgewinn liegt im Kontrast.
