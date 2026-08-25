#!/usr/bin/env python3
"""
Build standalone, shareable HTML pages from Obsidian character notes.

    python3 build.py --all                 # every note with a `publish:` property
    python3 build.py note.md -o out.html   # one note, explicitly

A note opts in by setting `publish:` in its frontmatter — editable from
Obsidian's Properties panel, so nothing lives outside the vault:

    ---
    publish: emilia
    eyebrow: Character Profile
    subtitle: Known to most simply as Mia
    ---

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

def split_frontmatter(text: str):
    """Return (properties, remaining_text).

    Deliberately handles only flat `key: value` pairs — that is all a page
    declaration needs, and it keeps this script dependency-free (no PyYAML).
    """
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", text, re.S)
    if not m:
        return {}, text
    props = {}
    for line in m.group(1).split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        props[key.strip()] = val
    return props, text[m.end():]

def parse(note: Path):
    props, text = split_frontmatter(note.read_text(encoding="utf-8"))
    lines = text.split("\n")
    # Strip the blockquote marker and AT MOST one space: a wider strip would
    # destroy the leading empty cell that marks a table continuation row.
    quoted = [re.sub(r"^> ?", "", l) for l in lines if l.startswith(">")]
    body   = [l for l in lines if not l.startswith(">")]

    # ----- infobox: ###### headers introduce blocks; `a | b |` rows are data
    title, image, blocks, side = None, None, [], "left"
    for l in quoted:
        if l.startswith("[!"):
            # `> [!infobox|right]` — honour the side the note asks for
            meta = re.match(r"\[!\w+\|?([^\]]*)\]", l)
            if meta and "right" in meta.group(1).split():
                side = "right"
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
    return title, image, blocks, sections, side, props

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
.infobox.is-right{float:right;margin:.3rem 0 1.5rem 2.25rem}
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

def render(title, image_uri, blocks, sections, source_name,
           fragment=False, eyebrow="Character Profile", subtitle="",
           side="left"):
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

    head = [f"<h1>{html.escape(title)}</h1>"]
    if eyebrow:
        head.insert(0, f"<p class='eyebrow'>{html.escape(eyebrow)}</p>")
    if subtitle:
        head.append(f"<p class='alias'>{inline(subtitle)}</p>")

    page = f"""<main class="page">
  <header class="nameplate">
    {''.join(head)}
  </header>
  <div class="article">
    <aside class="infobox{' is-right' if side == 'right' else ''}">{''.join(ib)}</aside>
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
<meta name="description" content="{html.escape(subtitle or title)}">
<style>{CSS}</style>
</head><body>
{page}
</body></html>"""
    return doc, skipped

INDEX_TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Published pages</title>
<style>
  :root{color-scheme:light dark}
  body{margin:0;padding:4rem 1.5rem;background:Canvas;color:CanvasText;
    font:1rem/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
    display:flex;justify-content:center}
  main{max-width:34rem;width:100%}
  h1{font-size:1.35rem;font-weight:600;margin:0 0 .35rem}
  p{margin:0 0 2rem;opacity:.65;font-size:.9rem}
  ul{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:.15rem}
  a{display:block;padding:.7rem .9rem;border-radius:5px;text-decoration:none;
    color:inherit;border:1px solid transparent}
  a:hover,a:focus-visible{background:color-mix(in srgb,CanvasText 6%,transparent);
    border-color:color-mix(in srgb,CanvasText 14%,transparent);outline:none}
</style>
</head><body>
<main>
  <h1>Published pages</h1>
  <p>Standalone pages generated from notes.</p>
  <ul>
{items}
  </ul>
</main>
</body></html>
"""

def build_one(note: Path, out: Path, fragment=False,
              eyebrow=None, subtitle=None, side=None):
    """Convert one note. Explicit arguments win over the note's properties."""
    title, image, blocks, sections, note_side, props = parse(note)
    side     = side     or props.get("side") or note_side
    eyebrow  = eyebrow  if eyebrow  is not None else props.get("eyebrow", "Character Profile")
    subtitle = subtitle if subtitle is not None else props.get("subtitle", "")

    uri = ""
    if image:
        # Wikilinks resolve vault-wide, so search upward from the note.
        img = next((p for p in note.parent.rglob(image)), None) \
           or next((p for p in note.parent.parent.rglob(image)), None)
        if img:
            uri = data_uri(img)
        else:
            print(f"  ! portrait not found: {image}", file=sys.stderr)

    doc, skipped = render(title, uri, blocks, sections, note.name,
                          fragment, eyebrow, subtitle, side)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    print(f"  {out}  ({len(doc)/1024:.0f} KB, infobox {side})")
    for sec in skipped:
        print(f"  ! {note.name}: skipped empty section: ## {sec}", file=sys.stderr)
    return title


def build_all(notes_dir: Path, out_dir: Path):
    """Build every note carrying a `publish:` property, then the site index."""
    pages, seen = [], {}
    for note in sorted(notes_dir.rglob("*.md")):
        props, _ = split_frontmatter(note.read_text(encoding="utf-8"))
        slug = props.get("publish", "").strip().strip("/")
        if not slug:
            continue
        if slug in seen:
            print(f"  ! duplicate publish slug {slug!r}: {note.name} clashes with "
                  f"{seen[slug].name} — skipping", file=sys.stderr)
            continue
        seen[slug] = note
        title = build_one(note, out_dir / slug / "index.html")
        pages.append((slug, title or slug))

    if not pages:
        print(f"  ! no notes in {notes_dir}/ have a `publish:` property",
              file=sys.stderr)

    items = "\n".join(
        f'    <li><a href="{html.escape(s)}/">{html.escape(t)}</a></li>'
        for s, t in sorted(pages, key=lambda r: r[1].lower()))
    (out_dir / "index.html").write_text(
        INDEX_TEMPLATE.replace("{items}", items), encoding="utf-8")
    print(f"  {out_dir}/index.html  ({len(pages)} page"
          f"{'s' if len(pages) != 1 else ''})")


def main():
    ap = argparse.ArgumentParser(
        description="Build shareable HTML pages from Obsidian notes.")
    ap.add_argument("note", nargs="?", type=Path,
                    help="a single note; omit when using --all")
    ap.add_argument("--all", action="store_true",
                    help="build every note in --notes that has a `publish:` property")
    ap.add_argument("--notes", type=Path, default=Path("notes"),
                    help="vault folder to scan with --all (default: notes)")
    ap.add_argument("-o", "--out", type=Path,
                    help="output file, or output directory with --all "
                         "(default: index.html / docs)")
    ap.add_argument("--fragment", action="store_true",
                    help="emit style+markup only, for embedding in another page")
    ap.add_argument("--eyebrow", default=None,
                    help="override the note's eyebrow (empty string to omit)")
    ap.add_argument("--subtitle", default=None,
                    help="override the note's subtitle")
    ap.add_argument("--side", choices=("left", "right"), default=None,
                    help="override which side the infobox floats to "
                         "(default: whatever the note's callout says)")
    a = ap.parse_args()

    if a.all:
        if a.note:
            ap.error("give a note or --all, not both")
        build_all(a.notes, a.out or Path("docs"))
        return

    if not a.note:
        ap.error("give a note path, or --all to build the whole vault")
    build_one(a.note, a.out or Path("index.html"),
              a.fragment, a.eyebrow, a.subtitle, a.side)


if __name__ == "__main__":
    main()
