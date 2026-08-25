#!/usr/bin/env python3
"""
Build a standalone, shareable HTML page from an Obsidian character note.

    python3 build.py "Emilia Lynn Ravnskov.md" -o index.html

Reads the note's [!infobox] callout plus its ## sections and emits a single
self-contained file: CSS inlined, portrait embedded as a data URI, no external
requests. Drop the result on GitHub Pages, Netlify, or email it.
"""
import argparse, base64, html, mimetypes, re, sys
from pathlib import Path

# ---------- tiny markdown inline renderer -------------------------------
def inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", t)
    return t

def parse(note: Path):
    lines = note.read_text(encoding="utf-8").split("\n")
    # Strip the blockquote marker and AT MOST one space: a wider strip would
    # destroy the leading empty cell that marks a table continuation row.
    quoted = [re.sub(r"^> ?", "", l) for l in lines if l.startswith(">")]
    body   = [l for l in lines if not l.startswith(">")]

    # ----- infobox: ###### headers introduce blocks; `a | b |` rows are data
    title, image, blocks = None, None, []
    for l in quoted:
        if l.startswith("[!"):
            continue
        if l.startswith("######"):
            head = l.lstrip("#").strip()
            if title is None:
                title = head            # first ###### is the character name
            else:
                blocks.append({"head": head, "rows": []})
        elif l.startswith("!["):
            m = re.search(r"!\[\[(.+?)\]\]", l)
            if m:
                image = m.group(1)
        elif "|" in l and set(l.strip()) - set("-| "):
            # Split on the raw pipes; a blank first cell means "same label as
            # the row above" (how the note stacks multiple relatives, heights…).
            cells = [c.strip() for c in l.split("|")]
            if cells and not cells[-1]:
                cells.pop()                      # trailing pipe, not a cell
            label = cells[0].strip("*").strip() if cells else ""
            values = [c for c in cells[1:] if c]
            if not blocks:
                continue
            if label:
                blocks[-1]["rows"].append({"label": label, "values": values})
            elif blocks[-1]["rows"]:
                blocks[-1]["rows"][-1]["values"] += values   # continuation row

    # ----- body: ## headings and paragraphs
    sections, cur = [], None
    for l in body:
        if l.startswith("## "):
            cur = {"head": l[3:].strip(), "paras": []}
            sections.append(cur)
        elif l.strip() and cur:
            cur["paras"].append(l.strip())
    return title, image, blocks, sections

def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"

CSS = """
:root{
  --paper:#f3f0f7; --surface:#fbfafd; --ink:#231d2b; --ink-soft:#574d63;
  --mist:#857c92; --amethyst:#6d4a94; --amethyst-ink:#fbfafd;
  --brass:#9a7a3e; --rule:#ded6e6;
  --display:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua","URW Palladio L","P052",Georgia,serif;
  --body:Charter,"Bitstream Charter","Charis SIL",Georgia,Cambria,serif;
  --ui:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
}
@media (prefers-color-scheme:dark){
  :root{
    --paper:#15111a; --surface:#1e1826; --ink:#ded8e6; --ink-soft:#a99fb7;
    --mist:#8b8298; --amethyst:#b192d8; --amethyst-ink:#17121d;
    --brass:#c6a463; --rule:#332b3d;
  }
}
:root[data-theme="dark"]{
  --paper:#15111a; --surface:#1e1826; --ink:#ded8e6; --ink-soft:#a99fb7;
  --mist:#8b8298; --amethyst:#b192d8; --amethyst-ink:#17121d;
  --brass:#c6a463; --rule:#332b3d;
}
:root[data-theme="light"]{
  --paper:#f3f0f7; --surface:#fbfafd; --ink:#231d2b; --ink-soft:#574d63;
  --mist:#857c92; --amethyst:#6d4a94; --amethyst-ink:#fbfafd;
  --brass:#9a7a3e; --rule:#ded6e6;
}

*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:var(--body);font-size:1.0625rem;line-height:1.68;
  -webkit-text-size-adjust:100%}
.page{max-width:62rem;margin:0 auto;padding:3.5rem 1.5rem 6rem}

/* ---- nameplate ---- */
.nameplate{border-bottom:1px solid var(--rule);padding-bottom:1.4rem;margin-bottom:2.2rem}
.eyebrow{font-family:var(--ui);font-size:.7rem;font-weight:600;letter-spacing:.14em;
  text-transform:uppercase;color:var(--brass);margin:0 0 .6rem}
.nameplate h1{font-family:var(--display);font-weight:600;font-size:clamp(2.1rem,5vw,3.1rem);
  line-height:1.1;margin:0;text-wrap:balance;letter-spacing:-.01em}
.alias{font-family:var(--display);font-style:italic;color:var(--mist);
  font-size:1.15rem;margin:.5rem 0 0}

/* ---- the wiki float: infobox left, prose wraps, then reclaims full width ---- */
.article::after{content:"";display:block;clear:both}
.infobox{float:left;width:21rem;margin:.3rem 2.25rem 1.5rem 0;
  background:var(--surface);border:1px solid var(--rule);border-radius:3px;
  overflow:hidden;font-family:var(--ui)}
.infobox figure{margin:0}
.infobox img{display:block;width:100%;height:auto}
.ib-name{background:var(--amethyst);color:var(--amethyst-ink);font-family:var(--display);
  font-size:1.15rem;text-align:center;padding:.65rem 1rem;margin:0;font-weight:600}
.ib-head{font-size:.68rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  color:var(--ink-soft);background:color-mix(in srgb,var(--amethyst) 9%,transparent);
  padding:.5rem 1rem;margin:0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.ib-row{display:grid;grid-template-columns:8.5rem 1fr;gap:.75rem;
  padding:.42rem 1rem;font-size:.82rem;line-height:1.45;align-items:baseline}
.ib-row+.ib-row{border-top:1px solid color-mix(in srgb,var(--rule) 55%,transparent)}
.ib-row dt{color:var(--ink-soft);font-weight:600}
.ib-row dd{margin:0;color:var(--ink)}
.ib-row dd span{display:block}
.ib-sub{padding:.5rem 1rem .3rem;font-size:.68rem;font-weight:700;
  letter-spacing:.13em;text-transform:uppercase;color:var(--mist);
  border-top:1px solid color-mix(in srgb,var(--rule) 55%,transparent)}
.stars{color:var(--brass);letter-spacing:.18em;font-size:.9rem}

/* ---- prose ---- */
.article h2{font-family:var(--display);font-weight:600;font-size:1.6rem;
  margin:2.4rem 0 .9rem;padding-bottom:.35rem;border-bottom:1px solid var(--rule);
  text-wrap:balance}
.article h2:first-of-type{margin-top:0}
.article p{margin:0 0 1.05rem;hyphens:auto}
.article strong{font-weight:600;color:var(--ink)}
.article em{color:var(--ink-soft)}

footer{clear:both;margin-top:3.5rem;padding-top:1.2rem;border-top:1px solid var(--rule);
  font-family:var(--ui);font-size:.75rem;color:var(--mist)}

@media (max-width:46rem){
  .page{padding:2.25rem 1.15rem 4rem}
  .infobox{float:none;width:auto;margin:0 0 2rem}
  .ib-row{grid-template-columns:7.5rem 1fr}
}
@media print{
  body{background:#fff;color:#000}
  .infobox{break-inside:avoid}
}
"""

def render(title, image_uri, blocks, sections, source_name, fragment=False):
    def rows(b):
        out = []
        for r in b["rows"]:
            if not r["values"]:
                out.append(f"<div class='ib-sub'>{inline(r['label'])}</div>")
                continue
            vals = "".join(
                f"<span class='stars'>{'★' * v.count('🟊')}</span>" if "🟊" in v
                else f"<span>{inline(v)}</span>"
                for v in r["values"]) or "<span>&mdash;</span>"
            out.append(f"<div class='ib-row'><dt>{inline(r['label'])}</dt><dd>{vals}</dd></div>")
        return "".join(out)

    ib = [f"<h2 class='ib-name'>{html.escape(title)}</h2>"]
    if image_uri:
        ib.append(f"<figure><img src='{image_uri}' alt='Portrait of {html.escape(title)}'></figure>")
    for b in blocks:
        if b["rows"]:
            ib.append(f"<h3 class='ib-head'>{html.escape(b['head'])}</h3><dl>{rows(b)}</dl>")

    body, skipped = [], []
    for s in sections:
        if not s["paras"]:
            skipped.append(s["head"]); continue
        paras = "".join(f"<p>{inline(p)}</p>" for p in s["paras"])
        body.append(f"<h2>{html.escape(s['head'])}</h2>{paras}")

    page = f"""<main class="page">
  <header class="nameplate">
    <p class="eyebrow">Character Profile</p>
    <h1>{html.escape(title)}</h1>
    <p class="alias">Known to most simply as Mia</p>
  </header>
  <div class="article">
    <aside class="infobox">{''.join(ib)}</aside>
    {''.join(body)}
  </div>
  <footer>Generated from <code>{html.escape(source_name)}</code>.</footer>
</main>"""

    if fragment:
        return f"<style>{CSS}</style>\n{page}", skipped

    doc = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="Character profile: {html.escape(title)}.">
<style>{CSS}</style>
</head><body>
{page}
</body></html>"""
    return doc, skipped

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("note", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("index.html"))
    ap.add_argument("--fragment", action="store_true",
                    help="emit style+markup only, for embedding in another page")
    a = ap.parse_args()

    title, image, blocks, sections = parse(a.note)
    uri = ""
    if image:
        img = next((p for p in a.note.parent.rglob(image)), None) \
           or next((p for p in a.note.parent.parent.rglob(image)), None)
        if img:
            uri = data_uri(img)
        else:
            print(f"  ! portrait not found: {image}", file=sys.stderr)

    doc, skipped = render(title, uri, blocks, sections, a.note.name, a.fragment)
    a.out.write_text(doc, encoding="utf-8")
    print(f"  {a.out}  ({len(doc)/1024:.0f} KB, self-contained)")
    for s in skipped:
        print(f"  ! skipped empty section: ## {s}", file=sys.stderr)

if __name__ == "__main__":
    main()
