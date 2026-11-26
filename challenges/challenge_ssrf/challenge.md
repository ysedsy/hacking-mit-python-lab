# Challenge: SSRF (Server-Side Request Forgery)

Ziel dieser Übung: Zeigt, wie man den **Server** dazu bringt, URLs abzurufen,
die nur **er** erreicht. Ein „Steckbrief-Importer" lädt Bilder per URL — und
lädt genauso bereitwillig die interne Marshal-Seite.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner; der/die
**Nachbar:in** greift diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5011
> ```

---

## Spielregeln

- Nur die eingeladene Instanz. **Keine echten/fremden URLs** abrufen lassen.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Der Importer holt ein Foto von einer angegebenen `url`. Das **interne**
Marshal-Board `/intern` beantwortet Anfragen nur, wenn sie von `localhost`
kommen — von außen gibt es `403`. Auf dem Server läuft alles unter `127.0.0.1`.

## Aufgabe

Lies den Inhalt von `/intern`, obwohl er dir direkt `403` liefert.

## Hinweise

- Ruf `/intern` erst direkt auf — du bekommst `403`.
- Der Importer macht die Anfrage **für dich**, vom Server aus. Welche Absender-
  Adresse sieht `/intern` dann?
- Welche `url` müsstest du dem Importer geben, damit er sich quasi selbst
  aufruft? Der Server lauscht lokal auf seinem eigenen Port.

## Erfolgskriterium

- Die Importer-Antwort zeigt den geheimen Board-Text und „Angriff geglückt".

## Zählt **nicht** als Lösung

- `/intern` direkt von localhost aufrufen (wenn du selbst auf dem Server sitzt).
  Der Angriff muss über den Importer laufen.

---

## Verteidigung / Fix

- **Ursache:** Der Server ruft eine **beliebige**, nutzergesteuerte URL ab und
  vertraut internen Anfragen allein wegen der Absenderadresse.
- **Fix:** Ziel-URLs **allowlisten** (erlaubte Hosts/Domains), interne/lokale
  Adressen (127.0.0.0/8, 169.254.169.254, private Netze) blocken, Redirects
  prüfen, keine Autorisierung nur auf „kommt von localhost" stützen.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```bash
# Direkt -> 403:
curl -i http://127.0.0.1:5011/intern
# Ueber den Importer -> Server ruft sich selbst auf, /intern sieht localhost:
curl "http://127.0.0.1:5011/import?url=http://127.0.0.1:5011/intern"
```
</details>
