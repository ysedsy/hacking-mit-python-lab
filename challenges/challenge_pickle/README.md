# challenge_pickle/ — Übungs-Ziel: Insecure Deserialization

Bewusst verwundbare Mini-Flask-App. Die Merkliste wird als `pickle`-Objekt im
Cookie `merkliste` gespeichert und beim Laden mit `pickle.loads()` entpackt. Ein
präpariertes Cookie (`__reduce__`) führt beim Entpacken Server-Code aus; im Lab
legt der harmlose Payload nur `pwned.txt` an.

> Nur gegen die eigene/autorisierte Instanz. Payload harmlos halten. Standard-
> Bind `127.0.0.1`; für die Nachbar-Challenge `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5012`)
- `challenge.md` — die Aufgabenstellung (+ Lösungsskript im Aufklapper)

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# Angriff: Cookie 'merkliste' mit einem pickle-Objekt setzen, dessen
#   __reduce__ os.system(...) ausloest  (Skript siehe challenge.md)
```

**Fix:** Kein `pickle` auf Client-Daten — `json` + serverseitiger State,
signierte/verschlüsselte Cookies.
