# Challenge: Business-Logic-Fehler (Sheriffstern für 50 Gold)

Ziel dieser Übung: Zeigt, dass nicht nur Injection gefährlich ist — auch eine
fehlende **Plausibilitätsprüfung** in der Geschäftslogik. Ihr kauft mit
50 Gold einen Sheriffstern, der 500 kostet.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner; der/die
**Nachbar:in** greift diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5009
> ```

---

## Spielregeln

- Nur die eingeladene Instanz. Kein DoS, keine Fremddaten.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Im Kramladen gibt es Whiskey (5), Bohnen (2), Hufeisen (12) und den begehrten
**Sheriffstern (500)**. Du startest mit **50 Gold**. Der Laden prüft vor dem
Kauf, ob du dir die Bestellung leisten kannst.

## Aufgabe

Besitze einen Sheriffstern.

## Hinweise

- Das Mengenfeld hat `min="0"` — aber das ist nur **HTML**. Wer prüft das auf
  dem Server?
- Rechne nach: Was ergibt `500 * 1 + 5 * (-100)`?
- DevTools (Attribut `min` löschen) oder direkt per `curl` / `requests`.

## Erfolgskriterium

- Der Laden zeigt „Angriff geglückt" und den Stern im Inventar.

## Zählt **nicht** als Lösung

- Cookie eines anderen Kunden übernehmen, Server-Variablen direkt ändern.

---

## Verteidigung / Fix

- **Ursache:** Die Regel „Mengen sind positiv" existiert nur im Browser.
  Der Server vertraut der Eingabe.
- **Fix:** Jede Geschäftsregel **serverseitig** prüfen:
  `if menge < 0 or menge > 99: abort(400)`. Auch an Obergrenzen, Rundung,
  Währungsumrechnung, Gutschein-Mehrfachnutzung denken.
- Client-Validierung ist Komfort, keine Sicherheit.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```bash
curl -c cj.txt http://127.0.0.1:5009/ > /dev/null
curl -b cj.txt -d "menge_stern=1&menge_whiskey=-100" http://127.0.0.1:5009/kaufen
curl -b cj.txt http://127.0.0.1:5009/      # -> Angriff geglueckt
```
Summe = 500 − 500 = 0 ≤ 50. Inventar: Stern 1, Whiskey −100.
</details>
