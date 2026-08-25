#!/usr/bin/env bash
# Rebuild every page listed in pages.conf, then regenerate the site index.
# Sources live in notes/ (the Obsidian vault); output goes to docs/, which is
# what GitHub Pages serves.  Never hand-edit anything under docs/.
set -euo pipefail
cd "$(dirname "$0")"

built=()

while IFS='|' read -r slug note eyebrow subtitle; do
  [[ -z "${slug// }" || "${slug#\#}" != "$slug" ]] && continue   # skip blanks/comments
  note="${note/#\~/$HOME}"          # tolerate an absolute path too

  if [[ ! -f "$note" ]]; then
    echo "  ! $slug: source not found — $note" >&2
    continue
  fi

  mkdir -p "docs/$slug"
  python3 build.py "$note" -o "docs/$slug/index.html" \
          --eyebrow "$eyebrow" --subtitle "$subtitle"
  built+=("$slug")
done < pages.conf

python3 - "${built[@]}" << 'PY'
import html, re, sys
from pathlib import Path

rows = []
for slug in sys.argv[1:]:
    page = Path("docs") / slug / "index.html"
    m = re.search(r"<title>(.*?)</title>", page.read_text(encoding="utf-8"))
    rows.append((slug, m.group(1) if m else slug))

items = "\n".join(
    f'    <li><a href="{html.escape(s)}/">{html.escape(t)}</a></li>' for s, t in rows)

Path("docs/index.html").write_text(f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Published pages</title>
<style>
  :root{{color-scheme:light dark}}
  body{{margin:0;padding:4rem 1.5rem;background:Canvas;color:CanvasText;
    font:1rem/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
    display:flex;justify-content:center}}
  main{{max-width:34rem;width:100%}}
  h1{{font-size:1.35rem;font-weight:600;margin:0 0 .35rem}}
  p{{margin:0 0 2rem;opacity:.65;font-size:.9rem}}
  ul{{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:.15rem}}
  a{{display:block;padding:.7rem .9rem;border-radius:5px;text-decoration:none;
    color:inherit;border:1px solid transparent}}
  a:hover,a:focus-visible{{background:color-mix(in srgb,CanvasText 6%,transparent);
    border-color:color-mix(in srgb,CanvasText 14%,transparent);outline:none}}
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
""", encoding="utf-8")
print(f"  docs/index.html  ({len(rows)} page{'s' if len(rows) != 1 else ''})")
PY
