# challenge_race_condition/ — Übungs-Ziel: Race Condition (TOCTOU)

Bewusst verwundbare Mini-Flask-App. Die Auszahlung prüft das Guthaben, wartet
kurz („Buchung") und zieht erst dann ab — ohne Lock. Parallele Requests
bestehen alle den Check, man hebt von 100 Gold z. B. 1000 ab.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1`; für die
> Nachbar-Challenge `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5008`)
- `challenge.md` — die Aufgabenstellung (+ Lösungsskript im Aufklapper)

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# Angriff: 10 parallele POST /abheben betrag=100 mit demselben Cookie
#   (Skript siehe challenge.md)
```

**Fix:** Check + Abbuchung atomar machen (Lock bzw.
`UPDATE … WHERE gold >= ?` in einer Transaktion).
