"""Erzeugt challenges/index.html -- eine Uebersichtsseite mit ALLEN Challenge-
Formulierungen, OHNE Loesungen.

Je Challenge wird aus der challenge.md nur der Aufgaben-Teil uebernommen: vom
Titel bis AUSSCHLIESSLICH vor "## Verteidigung / Fix". Damit landen weder der
Fix noch der Loesungsweg-Aufklapper auf der Seite.

Aufruf (keine Abhaengigkeiten ausser Standardbibliothek):

    cd challenges
    python build_index.py          # schreibt index.html
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# Reihenfolge + Metadaten. 'path' ist relativ zu challenges/.
CHALLENGES = [
    ("challenge_mass_assignment", "Mass Assignment", "A01 Broken Access Control", 5005, "leicht"),
    ("challenge_stored_xss", "Stored XSS", "A03 Injection", 5002, "leicht–mittel"),
    ("challenge_business_logic", "Business-Logic-Fehler", "A04 Insecure Design", 5009, "leicht–mittel"),
    ("challenge_race_condition", "Race Condition (TOCTOU)", "A04 Insecure Design", 5008, "mittel"),
    ("../challenge_session_forgery", "Session-Fälschung", "A02 Cryptographic Failures", 5001, "mittel"),
    ("challenge_session_puppetry", "Session-Abuse", "A01 Broken Access Control", 5007, "mittel"),
    ("challenge_password_reset", "Schwaches Reset-Token", "A07 Auth Failures", 5010, "mittel"),
    ("challenge_file_upload", "Unrestricted File Upload", "A04/A05", 5006, "mittel"),
    ("challenge_jwt", "JWT-Fälschung", "A02/A07", 5004, "mittel"),
    ("challenge_ssrf", "Server-Side Request Forgery", "A10 SSRF", 5011, "mittel"),
    ("challenge_ssti", "SSTI → RCE", "A03 Injection", 5003, "mittel–schwer"),
    ("challenge_pickle", "Insecure Deserialization", "A08 Integrity Failures", 5012, "mittel–schwer"),
]


def inline(text):
    """Inline-Markdown -> HTML (nach Escaping): `code`, **bold**, *em*."""
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def render_blocks(lines):
    """Mini-Markdown-Renderer fuer die Aufgaben-Bloecke (rekursiv fuer Zitate).

    Listen werden ueber einen Einrueckungs-Stack korrekt verschachtelt; Code und
    Zitate reissen eine offene Liste nicht auf, sondern landen im aktuellen <li>.
    """
    out = []
    i, n = 0, len(lines)
    para = []
    stack = []          # Einrueckungstiefen der offenen <ul> (je 1 offenes <li>)

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para).strip()) + "</p>")
            para.clear()

    def close_lists():
        while stack:
            out.append("</li></ul>")
            stack.pop()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Code-Zaun ``` ... ```  (bleibt ggf. im offenen <li>)
        if stripped.startswith("```"):
            flush_para()
            lang = stripped[3:].strip()
            code = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i]); i += 1
            i += 1  # schliessendes ```
            cls = f' class="lang-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>" + html.escape("\n".join(code)) + "</code></pre>")
            continue

        # Blockzitat (nur ausserhalb von Listen zu erwarten)
        if stripped.startswith(">"):
            flush_para()
            if not stack:
                close_lists()
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            out.append("<blockquote>" + render_blocks(quote) + "</blockquote>")
            continue

        # Ueberschrift ## ...
        m = re.match(r"^(#{2,4})\s+(.*)$", stripped)
        if m:
            flush_para(); close_lists()
            out.append(f"<h4>{inline(m.group(2))}</h4>")
            i += 1
            continue

        # Horizontale Linie
        if re.match(r"^-{3,}$", stripped):
            flush_para(); close_lists()
            out.append('<hr class="rule">')
            i += 1
            continue

        # Listenpunkt (beliebige Verschachtelung ueber Einrueckung)
        m = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if m:
            flush_para()
            indent = len(m.group(1))
            while stack and indent < stack[-1]:
                out.append("</li></ul>"); stack.pop()
            if stack and indent == stack[-1]:
                out.append("</li>")                 # Geschwister-<li> schliessen
            elif not stack or indent > stack[-1]:
                out.append("<ul>"); stack.append(indent)
            out.append("<li>" + inline(m.group(2)))  # <li> bleibt offen
            i += 1
            continue

        # Leerzeile -> Absatz/Listen beenden
        if not stripped:
            flush_para(); close_lists()
            i += 1
            continue

        # Fortsetzungstext: innerhalb einer Liste -> an das aktuelle <li> haengen
        if stack:
            out.append(" " + inline(stripped))
        else:
            para.append(stripped)
        i += 1

    flush_para(); close_lists()
    return "\n".join(out)


def extract_formulation(md_path):
    text = open(md_path, encoding="utf-8").read()
    # Alles ab "## Verteidigung" (Fix + Loesungsweg) abschneiden.
    cut = re.search(r"^##\s+Verteidigung", text, flags=re.M)
    if cut:
        text = text[:cut.start()]
    lines = text.splitlines()
    # Titelzeile (# ...) entfernen -- Titel kommt aus den Metadaten.
    body = [ln for k, ln in enumerate(lines) if not (k == 0 and ln.startswith("# "))]
    # fuehrende Leerzeilen weg
    while body and not body[0].strip():
        body.pop(0)
    # verwaiste Trennlinie(n)/Leerzeilen am Ende (der '---' vor "Verteidigung") weg
    while body and (not body[-1].strip() or re.match(r"^-{3,}$", body[-1].strip())):
        body.pop()
    return render_blocks(body)


def difficulty_rank(niveau):
    return {"leicht": 1, "leicht–mittel": 2, "mittel": 3, "mittel–schwer": 4}.get(niveau, 3)


def build():
    cards, rows = [], []
    for idx, (path, vuln, owasp, port, niveau) in enumerate(CHALLENGES, 1):
        md = os.path.join(HERE, path, "challenge.md")
        anchor = os.path.basename(path)
        formulation = extract_formulation(md)
        rank = difficulty_rank(niveau)
        folder_label = path if not path.startswith("../") else path
        rows.append(f"""      <tr>
        <td class="num">{idx:02d}</td>
        <td><a href="#{anchor}">{html.escape(vuln)}</a></td>
        <td>{html.escape(owasp)}</td>
        <td><code>:{port}</code></td>
        <td><span class="pips p{rank}" title="{html.escape(niveau)}">{'★' * rank}{'☆' * (4 - rank)}</span></td>
      </tr>""")
        cards.append(f"""  <article class="card" id="{anchor}">
    <div class="meta">
      <span class="badge num">#{idx:02d}</span>
      <span class="badge owasp">{html.escape(owasp)}</span>
      <span class="badge port">Port :{port}</span>
      <span class="badge niv p{rank}">{html.escape(niveau)}</span>
    </div>
    <h2>{html.escape(vuln)}</h2>
    <div class="body">
{formulation}
    </div>
    <p class="folder">Ordner: <a href="{html.escape(folder_label)}/"><code>{html.escape(folder_label)}/</code></a>
       &middot; Start: <code>cd {html.escape(folder_label)} &amp;&amp; python app.py</code></p>
    <p class="top"><a href="#top">&uarr; nach oben</a></p>
  </article>""")

    page = TEMPLATE.format(rows="\n".join(rows), cards="\n".join(cards), count=len(CHALLENGES))
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print(f"[OK] index.html geschrieben ({len(CHALLENGES)} Challenges).")


TEMPLATE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Challenges &ndash; Hacking mit Python</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rye&family=Special+Elite&display=swap" rel="stylesheet">
<style>
 :root{{
   --parch:#f4ecd8; --card:#fffbf0; --ink:#2b2119; --muted:#6b5b45;
   --line:#d6c7a1; --leather:#92400e; --leather-d:#7c2d12; --accent:#b45309;
   --code-bg:#efe3c4;
 }}
 *{{box-sizing:border-box}}
 body{{margin:0;background:var(--parch);color:var(--ink);
   font-family:"Special Elite","Courier New",monospace;line-height:1.55;
   background-image:radial-gradient(circle at 20% 10%,rgba(146,64,14,.05),transparent 60%);}}
 .wrap{{max-width:900px;margin:0 auto;padding:0 16px 4rem;}}
 header.hero{{text-align:center;padding:2.4rem 1rem 1.4rem;}}
 h1{{font-family:"Rye",serif;font-weight:400;font-size:clamp(1.8rem,6vw,3rem);
   margin:.2rem 0;color:var(--leather-d);letter-spacing:.5px;}}
 .sub{{color:var(--muted);margin:.2rem 0 0;}}
 .warn{{background:var(--leather-d);color:#fde68a;padding:.7rem 1rem;border-radius:8px;
   font-size:.92rem;margin:1.2rem auto;max-width:900px;}}
 .warn b{{color:#fff;}}
 h2{{font-family:"Rye",serif;font-weight:400;color:var(--leather-d);
   font-size:1.4rem;margin:.1rem 0 .8rem;}}
 h4{{font-family:"Rye",serif;font-weight:400;color:var(--accent);
   font-size:1.02rem;margin:1.1rem 0 .3rem;}}
 table.overview{{width:100%;border-collapse:collapse;background:var(--card);
   border:1px solid var(--line);border-radius:10px;overflow:hidden;margin:1.4rem 0 2.2rem;}}
 table.overview th,table.overview td{{border-bottom:1px solid var(--line);
   padding:.55rem .7rem;text-align:left;font-size:.92rem;}}
 table.overview th{{background:#efe3c4;font-family:"Rye",serif;font-weight:400;}}
 table.overview tr:last-child td{{border-bottom:0;}}
 td.num,.badge.num{{font-variant-numeric:tabular-nums;color:var(--muted);}}
 a{{color:var(--accent);text-decoration:none;}}
 a:hover{{text-decoration:underline;}}
 .card{{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--leather);
   border-radius:10px;padding:1.2rem 1.3rem;margin:1.4rem 0;
   box-shadow:0 2px 0 rgba(0,0,0,.04);}}
 .meta{{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.3rem;}}
 .badge{{font-size:.76rem;padding:.15rem .5rem;border-radius:999px;
   border:1px solid var(--line);background:#fff;color:var(--muted);white-space:nowrap;}}
 .badge.owasp{{background:#fef3c7;color:#92400e;border-color:#fcd34d;}}
 .badge.port{{background:#ecfccb;color:#3f6212;border-color:#bef264;}}
 .badge.niv.p1{{background:#dcfce7;color:#166534;}}
 .badge.niv.p2{{background:#fef9c3;color:#854d0e;}}
 .badge.niv.p3{{background:#ffedd5;color:#9a3412;}}
 .badge.niv.p4{{background:#fee2e2;color:#991b1b;}}
 .pips{{letter-spacing:1px;color:var(--accent);}}
 .body p{{margin:.5rem 0;}}
 .body ul{{margin:.4rem 0 .6rem;padding-left:1.3rem;}}
 .body li{{margin:.2rem 0;}}
 code{{background:var(--code-bg);padding:0 .25rem;border-radius:3px;
   font-family:"Courier New",monospace;font-size:.9em;}}
 pre{{background:#2b2119;color:#f4ecd8;padding:.8rem 1rem;border-radius:8px;
   overflow:auto;font-size:.85rem;}}
 pre code{{background:none;color:inherit;padding:0;}}
 blockquote{{margin:.6rem 0;padding:.4rem .9rem;border-left:4px solid var(--line);
   background:#faf4e4;color:var(--muted);border-radius:0 6px 6px 0;}}
 blockquote pre{{margin:.3rem 0;}}
 hr.rule{{border:0;border-top:1px dashed var(--line);margin:1rem 0;}}
 .folder{{font-size:.85rem;color:var(--muted);border-top:1px dashed var(--line);
   padding-top:.7rem;margin-top:1rem;}}
 .top{{font-size:.8rem;margin:.3rem 0 0;}}
 footer{{text-align:center;color:var(--muted);font-size:.82rem;margin-top:2.5rem;}}
 @media (prefers-color-scheme: dark){{
   :root:not([data-theme="light"]){{
     --parch:#1c1813; --card:#241f18; --ink:#ece3cf; --muted:#b3a384;
     --line:#4a3f2c; --code-bg:#3a3122;
   }}
   :root:not([data-theme="light"]) table.overview th{{background:#2f2819;}}
   :root:not([data-theme="light"]) blockquote{{background:#2a241a;}}
   :root:not([data-theme="light"]) .badge{{background:#2f2819;}}
 }}
</style>
</head>
<body>
<a id="top"></a>
<div class="wrap">
  <header class="hero">
    <h1>&#129312; Challenges</h1>
    <p class="sub">Kapere die Seite &ndash; {count} verwundbare Mini-Ziele aus dem Kurs
       &bdquo;Hacking mit Python&ldquo;</p>
  </header>

  <div class="warn">
    <b>Grenze:</b> Nur gegen die <b>eigene</b> oder eine ausdr&uuml;cklich freigegebene
    Instanz im Kurs-Netz. Keine fremden/&ouml;ffentlichen Systeme. Payloads harmlos halten
    (<code>alert</code>, <code>whoami</code>), kein DoS, keine echten Daten abflie&szlig;en
    lassen. Nur w&auml;hrend der &Uuml;bungstermine.
  </div>

  <table class="overview">
    <thead><tr><th>#</th><th>Challenge</th><th>OWASP</th><th>Port</th><th>Niveau</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>

{cards}

  <footer>
    Diese Seite wird aus den <code>challenge.md</code>-Dateien erzeugt
    (<code>python build_index.py</code>) und zeigt bewusst <b>nur die Aufgaben</b> &ndash;
    der Abschnitt &bdquo;Verteidigung / Fix&ldquo; samt L&ouml;sungsweg bleibt in den
    Ordnern. &middot; Hacking mit Python &middot; Cowboy-Forum-Lab
  </footer>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    build()
