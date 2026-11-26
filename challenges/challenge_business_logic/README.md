# challenge_business_logic/ — Übungs-Ziel: Business-Logic-Fehler

Bewusst verwundbare Mini-Flask-App. Der Laden prüft nur „Summe ≤ Gold", nicht
ob Mengen positiv sind (`min="0"` steht nur im HTML). Mit −100 Whiskey wird die
Bestellung billig genug für den 500-Gold-Sheriffstern.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1`; für die
> Nachbar-Challenge `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5009`)
- `challenge.md` — die Aufgabenstellung

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# Angriff:
#   curl -c cj.txt http://127.0.0.1:5009/
#   curl -b cj.txt -d "menge_stern=1&menge_whiskey=-100" http://127.0.0.1:5009/kaufen
```

**Fix:** Geschäftsregeln serverseitig erzwingen (Mengen > 0, Obergrenzen).
