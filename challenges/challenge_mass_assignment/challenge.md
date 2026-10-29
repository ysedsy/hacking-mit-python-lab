# Challenge: Mass Assignment (heimlich Admin werden)

Ziel dieser Übung: Zeigt, dass ein Formular mehr Felder entgegennehmen kann, als
es anzeigt. Beim Registrieren schmuggelt ihr ein zusätzliches Feld mit und werdet
dadurch **Administrator** — obwohl das Formular gar keinen „Admin"-Haken hat.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner; der/die
**Nachbar:in** greift diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5005
> ```

---

## Spielregeln

- Nur die eingeladene Instanz. Nur fiktive Konten. Kein DoS, keine Fremddaten.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Die Registrierung zeigt nur **Benutzername** und **Passwort**. Intern hat ein
Konto aber auch ein Feld `is_admin` (Standard: `false`). Der Admin-Bereich
(`/admin`) ist nur für Konten mit `is_admin = true`.

## Aufgabe

Lege ein Konto an, das **sofort Admin** ist, und öffne `/admin` — ohne dass das
Formular eine Admin-Option anbietet.

## Hinweis

- Der Server übernimmt **alle** gesendeten Formularfelder ins Konto, nicht nur die
  angezeigten. Was, wenn du ein **zusätzliches** Feld `is_admin` mitschickst?
- Du musst dafür das Formular „erweitern". Zwei einfache Wege:
  - **Browser-DevTools:** Im Registrier-Formular ein Feld hinzufügen:
    ```html
    <input name="is_admin" value="1">
    ```
    (F12 → Elements → ins `<form>` einfügen), dann absenden.
  - **Request direkt bauen:**
    ```bash
    curl -i -c cj.txt -d "username=evil&password=x&is_admin=1" http://ZIEL:5005/
    curl -b cj.txt http://ZIEL:5005/admin
    ```

## Erfolgskriterium

- Dein frisch registriertes Konto erreicht `/admin` („… ist Administrator").
- Du hast dafür nur ein extra Formularfeld mitgeschickt, kein Admin-Konto gekapert.

## Zählt **nicht** als Lösung

- Ein bereits vorhandenes Admin-Konto übernehmen.
- `/admin` ohne gültiges, als Admin markiertes Konto aufrufen.

---

## Verteidigung / Fix

- **Ursache:** Das Konto wird aus **allen** Eingabefeldern gebaut
  (`user.update(request.form)`) — sensible Felder wie `is_admin` inklusive.
- **Fix:** **Allowlist** — nur erwartete Felder übernehmen
  (`username`, `password`). Rechte/Rollen **nie** aus Nutzereingaben setzen,
  sondern serverseitig vergeben.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```bash
curl -i -c cj.txt -d "username=evil&password=x&is_admin=1" http://127.0.0.1:5005/
curl -b cj.txt http://127.0.0.1:5005/admin      # -> Admin-Bereich
```
Varianten, die der `_truthy`-Check ebenfalls akzeptiert: `is_admin=true`,
`is_admin=on`, `is_admin=admin`.
</details>
