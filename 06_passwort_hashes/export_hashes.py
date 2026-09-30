"""Exportiert die Passwort-Hashes aus der DB in Dateien für Cracking-Tools.

Erzeugt:
  hashes.txt        -> "username:hash"  (für John the Ripper)
  hashes_only.txt   -> nur der Hash pro Zeile (für Hashcat)

Realistisch: genau diese Hashes zieht ein Angreifer per SQL-Injection (Ordner 05,
UNION SELECT username, password_hash) aus dem Cowboy-Forum. Hier werden sie danach
OFFLINE geknackt — nur gegen die eigenen Lab-Hashes.
"""
from app import app
from models import User

with app.app_context():
    users = User.query.all()
    with open("hashes.txt", "w", encoding="utf-8") as f_full, \
         open("hashes_only.txt", "w", encoding="utf-8") as f_only:
        for u in users:
            f_full.write(f"{u.username}:{u.password_hash}\n")
            f_only.write(f"{u.password_hash}\n")
    print(f"{len(users)} Hashes exportiert -> hashes.txt / hashes_only.txt")
    for u in users:
        print(f"  {u.username}: {u.password_hash[:40]}...")
