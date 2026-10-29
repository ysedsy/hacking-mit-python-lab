# challenge_jwt/ — Übungs-Ziel: JWT-Fälschung

Bewusst verwundbare Mini-Flask-App. Das Token (Cookie `token`) ist ein JWT mit
zwei klassischen Prüf-Fehlern: Der Server akzeptiert **`alg:none`** (ganz ohne
Signatur) **und** nutzt ein **schwaches HMAC-Secret** (`secret`). Beides erlaubt,
sich selbst ein Token mit `role=admin` auszustellen.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1`; für die
> Nachbar-Challenge `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5004`)
- `challenge.md` — die Aufgabenstellung

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# Login: team-test / test123  (role=user)
# Ziel:  /admin  (role=admin)  -> Token mit alg:none ODER Secret "secret" bauen
```

**Fix:** Algorithmus serverseitig erzwingen (`HS256`, `none` ablehnen), langes
Zufalls-Secret nur aus der Umgebung, dem `alg`-Feld des Tokens nie vertrauen.
