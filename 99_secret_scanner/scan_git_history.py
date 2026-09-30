"""Defensiver Secret-Scanner: durchsucht den EIGENEN Git-Verlauf nach versehentlich
committeten Geheimnissen (Secret Keys, Tokens, Passwörter, private Keys).

Hintergrund: Statt fremde GitHub-Repos nach echten Zugangsdaten zu durchsuchen
(das zielt auf fremde Systeme -> nicht Teil dieses Labs), lernt man hier die
DEFENSIVE Seite: findet man seine eigenen Leaks, bevor es jemand anderes tut.
Gleiche Lehre wie `trufflehog` / `detect-secrets`, nur zum Selbermachen.

Nutzung:
    python scan_git_history.py [PFAD_ZUM_REPO]        # Default: aktuelles Verzeichnis

Es wird der GESAMTE Verlauf gescannt (git log -p), nicht nur der aktuelle Stand —
denn ein später gelöschter Key bleibt in der History stehen und ist weiter abrufbar.
"""
import re
import subprocess
import sys

# Muster für typische Geheimnisse. Bewusst breit; Treffer bitte manuell prüfen.
PATTERNS = {
    "Flask SECRET_KEY":     re.compile(r"""SECRET_KEY\s*=\s*['"][^'"]{6,}['"]"""),
    "AWS Access Key ID":    re.compile(r"AKIA[0-9A-Z]{16}"),
    "Google API Key":       re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    "GitHub Token":         re.compile(r"gh[pousr]_[0-9A-Za-z]{36,}"),
    "Slack Token":          re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    "Generic API/secret":   re.compile(r"""(?i)(api[_-]?key|secret|token|passwd|password)\s*[:=]\s*['"][^'"]{6,}['"]"""),
    "Private Key Block":    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
}


def git_history(repo: str) -> str:
    """Kompletter Diff-Verlauf des Repos als Text."""
    try:
        out = subprocess.run(
            ["git", "-C", repo, "log", "-p", "--all", "--no-color"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
        )
    except FileNotFoundError:
        sys.exit("Fehler: git ist nicht installiert / nicht im PATH.")
    if out.returncode != 0:
        sys.exit(f"Fehler: kein Git-Repo unter {repo!r}?\n{out.stderr.strip()}")
    return out.stdout


def scan(text: str) -> list[tuple[str, str, str]]:
    """Liefert (Commit, Muster-Name, Trefferzeile)."""
    findings = []
    commit = "?"
    for line in text.splitlines():
        if line.startswith("commit "):
            commit = line.split()[1][:10]
            continue
        # nur hinzugefügte Zeilen (+) sind interessant, nicht der Diff-Header +++
        if line.startswith("+") and not line.startswith("+++"):
            for name, pat in PATTERNS.items():
                if pat.search(line):
                    findings.append((commit, name, line[1:].strip()[:120]))
    return findings


def main() -> int:
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    findings = scan(git_history(repo))
    if not findings:
        print("[OK] Keine offensichtlichen Geheimnisse im Git-Verlauf gefunden.")
        return 0
    print(f"[!] {len(findings)} verdaechtige Fund(e) im Git-Verlauf:\n")
    for commit, name, snippet in findings:
        print(f"  [{commit}] {name}")
        print(f"      {snippet}")
    print("\nNächste Schritte, falls es echte Secrets sind:")
    print("  1. Secret SOFORT rotieren (der alte Wert gilt als kompromittiert).")
    print("  2. Aus der History entfernen: git filter-repo (oder BFG Repo-Cleaner).")
    print("  3. Vorbeugen: .gitignore, detect-secrets als pre-commit-Hook.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
