# Ordner 04 — Zwei-Faktor-Authentifizierung bei der Registrierung

Vierte Stufe. Nach dem Registrieren richtet der User **2FA per TOTP** ein
(RFC 6238, `pyotp`). Der Login wird dadurch zweistufig.

## Ablauf
1. **Registrieren** → es wird ein TOTP-Secret erzeugt (`totp_enabled = False`).
2. **`/2fa/setup`** → QR-Code scannen (Google Authenticator, Aegis, 2FAS …) und
   ersten Code bestätigen → `totp_enabled = True`.
3. **Login** = Benutzername + Passwort **und** danach `/2fa/verify` (6-stelliger Code).

## Neu gegenüber Ordner 03
- `models.py`: `totp_secret`, `totp_enabled` am User
- `forms.py`: `TotpForm` (genau 6 Ziffern)
- Routen `/2fa/setup`, `/2fa/verify`; zweistufiger Login
- QR-Code als inline-SVG (kein Pillow nötig)

## Starten
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
→ http://127.0.0.1:5000

## Sicherheits-Notiz
Das TOTP-Secret liegt hier im Klartext in der DB — für ein Lab ok. Produktiv sollte
es verschlüsselt gespeichert werden. Wichtig ist die Zwei-Faktor-Logik: selbst wenn
ein Passwort geknackt wird (siehe Ordner 06/08), fehlt dem Angreifer der zweite Faktor.

> `valid_window=1` erlaubt ±1 Zeitfenster (±30 s) Toleranz gegen Uhr-Drift.
