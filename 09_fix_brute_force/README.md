# Ordner 09 — Fix gegen Brute Force

Behebt Ordner 08. Zwei unabhängige Verteidigungslinien plus Verweis auf 2FA.

## 1. Account-Lockout (kontobezogen)
In `models.py`: `failed_attempts` + `locked_until` am User.
In der Login-Route:
- Jeder Fehlversuch erhöht `failed_attempts`.
- Nach **5** Fehlversuchen wird das Konto **15 Minuten** gesperrt (`locked_until`).
- Erfolgreicher Login setzt den Zähler zurück.
- Ein gesperrtes Konto wird abgewiesen, **auch bei richtigem Passwort**.

## 2. Rate-Limit (IP-bezogen)
`Flask-Limiter` bremst zusätzlich pro IP:
```python
@limiter.limit("10 per minute", methods=["POST"])
def login(): ...
```
Das trifft auch Angreifer, die viele verschiedene Konten durchprobieren
(Credential Stuffing).

## 3. Zweiter Faktor
Selbst wenn ein Passwort fällt: mit aktivem **2FA (Ordner 04)** fehlt dem Angreifer
der TOTP-Code. Lockout + Rate-Limit + 2FA zusammen machen Online-Brute-Force
praktisch aussichtslos.

## Testen
```powershell
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
```
Der Angriff aus Ordner 08 (`attack_playwright.py` / Hydra) läuft jetzt nach wenigen
Versuchen in die Sperre bzw. ins Rate-Limit (HTTP 429).

## Hinweis Produktion
- Lockout kann für **User-Enumeration/DoS** missbraucht werden (Angreifer sperrt fremde
  Konten). Gegenmittel: gleiche Meldung für „gesperrt/falsch", CAPTCHA nach n Fehlern,
  IP-Reputation statt reiner Konto-Sperre.
- Rate-Limit-Storage produktiv auf Redis (`RATELIMIT_STORAGE_URI`) statt In-Memory.
