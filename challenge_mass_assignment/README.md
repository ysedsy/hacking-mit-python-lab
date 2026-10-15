# challenge_mass_assignment/ — Übungs-Ziel: Mass Assignment

Bewusst verwundbare Mini-Flask-App. Die Registrierung übernimmt **alle**
gesendeten Formularfelder ungefiltert ins Konto (`user.update(request.form)`).
Das Formular zeigt nur Benutzername/Passwort — schmuggelt man ein Feld
`is_admin=1` mit, wird man sofort Administrator.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1`; für die
> Nachbar-Challenge `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5005`)
- `challenge.md` — die Aufgabenstellung

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# Angriff:
#   curl -i -c cj.txt -d "username=evil&password=x&is_admin=1" http://127.0.0.1:5005/
#   curl -b cj.txt http://127.0.0.1:5005/admin      -> Admin-Bereich
```

**Fix:** Allowlist — nur erwartete Felder übernehmen; Rollen/Rechte serverseitig
vergeben, nie aus Nutzereingaben.
