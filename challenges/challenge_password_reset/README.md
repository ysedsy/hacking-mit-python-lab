# challenge_password_reset/ — Übungs-Ziel: schwaches Reset-Token

Bewusst verwundbare Mini-Flask-App. Das „Passwort vergessen"-Token ist der
Sekunden-Zeitstempel `int(time.time())` — vorhersagbar. In einem kleinen
Zeitfenster geraten, lässt sich das Passwort des Kontos `marshal` neu setzen.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1`; für die
> Nachbar-Challenge `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5010`)
- `challenge.md` — die Aufgabenstellung (+ Lösungsskript im Aufklapper)

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# Angriff: Reset für 'marshal' anfordern, Token = aktueller Unix-Zeitstempel
#   (±wenige Sekunden durchprobieren), dann /reset mit neuem Passwort.
```

**Fix:** Zufälliges Token (`secrets.token_urlsafe`), kurze Gültigkeit,
einmalig, Rate-Limit.
