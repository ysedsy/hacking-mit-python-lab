# Ordner 08 — Brute Force gegen den Login (⚠️ ungeschützt)

Der Login hat hier **keine Bremse**: beliebig viele Versuche, kein Lockout, kein
Rate-Limit. Damit lässt er sich per Passwortliste durchprobieren. Fix in **Ordner 09**.

> Nur gegen die eigene Lab-Instanz `http://127.0.0.1:5000` bzw. die Kurs-Instanz im
> Lab-Netz. Die geseedeten User (`python seed.py`) haben schwache Passwörter und kein 2FA.

## Variante A — Playwright (Browser-Automatisierung)
```powershell
pip install playwright; playwright install chromium
python attack_playwright.py --user admin --wordlist rockyou_small.txt
```
(Analog mit **Selenium** oder **scrapy** möglich — siehe `selen.py` aus VL7.)

## Variante B — Hydra (HTTP POST form)
Hydra kennt das Formular anhand des Fehlertexts:
```bash
hydra -l admin -P rockyou.txt 127.0.0.1 -s 5000 \
  http-post-form "/login:username=^USER^&password=^PASS^:Falscher Benutzername oder Passwort"
```

## Variante C — Burp Intruder
1. Login-Request in Burp abfangen → **Send to Intruder**.
2. Payload-Position auf `password` setzen.
3. Payload-Liste (rockyou) laden → Attack.
4. Auf **abweichende Response-Length/Status** filtern (Treffer = Redirect/302 oder
   kürzere Fehlerseite).

## CSRF-Hinweis
Das Login-Formular nutzt Flask-WTF-CSRF. Für Hydra/Intruder muss pro Versuch ein
gültiges `csrf_token` mitgeschickt werden (erst GET `/login`, Token parsen, dann POST) —
Playwright/Selenium umgehen das automatisch, weil sie das echte Formular absenden.

## Lernpunkt
Ohne Gegenmaßnahmen ist ein schwaches Passwort nur eine Frage der Zeit.
**Ordner 09** bremst den Angriff: Rate-Limit + Account-Lockout (+ Verweis auf 2FA).
