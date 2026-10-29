# Challenge: JWT-Fälschung (Token selbst ausstellen)

Ziel dieser Übung: Zeigt, dass ein „sicher aussehendes" Token (JWT) wertlos ist,
wenn die Prüfung schwach ist. Ihr stellt euch selbst ein Token mit **role=admin**
aus und betretet den Admin-Bereich.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner; der/die
**Nachbar:in** greift diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5004
> ```

---

## Spielregeln

- Nur die eingeladene Instanz. Nur fiktive Konten. Kein DoS, keine Fremddaten.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Nach dem Login (`team-test` / `test123`) bekommst du ein Token im Cookie `token`
mit `role=user`. Der **Admin-Bereich** (`/admin`) verlangt `role=admin`. Ein
Admin-Passwort kennst du nicht.

Ein JWT besteht aus drei Base64-Teilen: `header.payload.signature`. **Header** und
**Payload** sind nur base64-codiert (lesbar/änderbar), die **Signatur** soll
Manipulation verhindern.

## Aufgabe

Verschaffe dir Zugang zu `/admin`, indem du ein **eigenes Token mit `role=admin`**
vorlegst — ohne Admin-Zugangsdaten.

## Hinweis

Es gibt **zwei** Wege (einer reicht):

1. **`alg: none`** — Setze im Header `"alg":"none"` und lass die Signatur weg
   (dritter Teil leer). Akzeptiert der Server das, braucht es gar keine Signatur.
2. **Schwaches Secret** — Das HMAC-Secret ist ein naheliegendes Standardwort.
   Errätst du es, kannst du ein gültig signiertes Token mit `role=admin` bauen
   (z. B. mit `jwt.io` oder der Bibliothek `PyJWT`).

Dekodiere zuerst dein aktuelles Token (Payload base64-decoden), ändere `role` auf
`admin`, und baue es nach einem der beiden Wege neu zusammen. Dann Cookie `token`
auf den neuen Wert setzen und `/admin` öffnen.

## Erfolgskriterium

- `/admin` zeigt den Admin-Bereich („Angriff geglückt … role=admin").
- Du hast kein Admin-Passwort verwendet, sondern das Token selbst erzeugt.

## Zählt **nicht** als Lösung

- Den vorhandenen `role=user`-Token unverändert benutzen.
- Nur den Payload ändern, aber die Signatur so lassen (wird bei korrektem Server
  abgelehnt — hier klappt es nur über `alg:none` **oder** das richtige Secret).

---

## Verteidigung / Fix

- **Ursache 1:** Server akzeptiert `alg:none` → **Algorithmus serverseitig
  erzwingen** (nur `HS256`), `none` ablehnen.
- **Ursache 2:** schwaches Secret → **langes Zufalls-Secret** nur aus der Umgebung.
- Nie dem `alg`-Feld aus dem Token vertrauen; Bibliothek mit `algorithms=["HS256"]`
  und erzwungener Verifikation nutzen.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```python
import base64, hmac, hashlib, json
b64=lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
p=b64(json.dumps({"user":"x","role":"admin"}).encode())

# Weg 1: alg:none
h=b64(json.dumps({"alg":"none","typ":"JWT"}).encode()); print(f"{h}.{p}.")

# Weg 2: schwaches Secret "secret"
h=b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
sig=b64(hmac.new(b"secret", f"{h}.{p}".encode(), hashlib.sha256).digest())
print(f"{h}.{p}.{sig}")
```
Token als Cookie `token=<wert>` setzen → `/admin`.
</details>
