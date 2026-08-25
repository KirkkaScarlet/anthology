# Publishing

Standalone web pages generated from notes, served by GitHub Pages at
<https://kirkkascarlet.github.io/Publishing/>.

One repo, many unrelated things. **This folder is also an Obsidian vault** —
open it directly in Obsidian and write in `notes/`.

    notes/    what you write       (the vault; new notes land here)
    docs/     what gets published  (generated — never hand-edit)
    build.sh  notes/ -> docs/

Each page gets its own directory under `docs/` and its own URL path; the
generated `docs/index.html` lists them. Obsidian is configured to hide `docs/`,
so you only ever see your own writing in the file explorer.

## Adding a page

A note publishes itself. Set `publish:` in its properties — from Obsidian's
Properties panel, so you never leave the vault:

    ---
    publish: emilia
    eyebrow: Character Profile
    subtitle: Known to most simply as Mia
    ---

- **publish** — the URL path (`/Publishing/<publish>/`). Required; a note
  without it is ignored, so drafts stay unpublished by default.
- **eyebrow** — small label above the title. Omit for "Character Profile";
  set it empty to drop the label entirely.
- **subtitle** — italic line under the title. Optional.
- **side** — `left` or `right`, overriding the infobox callout. Optional.

Then:

    ./build.sh
    git add -A && git commit -m "Add <slug>" && git push

`build.sh` rebuilds every published note and regenerates the index. It is safe
to re-run; it only writes the files it generates. Removing `publish:` from a
note unpublishes it on the next build.

## Editing an existing page

The **source of truth is the note in `notes/`**, not the HTML. Edit it in
Obsidian, run `./build.sh`, push. Never hand-edit anything under `docs/`; the
next build overwrites it.

## What the converter reads

`build.py` turns an Obsidian-style character note into a page. It understands
the note as Obsidian already writes it, with no extra syntax:

- the first `######` inside the `[!infobox]` callout becomes the page title
- `![[Image.png]]` inside the callout becomes the portrait, embedded as a data URI
- each later `######` starts a labelled block (Bio, Physical Info, …)
- `**Label** | value |` rows become infobox entries; a row whose **first cell is
  empty** stacks another value under the previous label — that is how the note
  expresses multiple relatives, or human vs. dragon height
- a row with a label but no value renders as a sub-heading
- `##` headings outside the callout become the body sections
- `[!infobox|left]` / `[!infobox|right]` controls which side it floats to

Empty sections are skipped with a warning rather than emitting a blank heading.

For a one-off, bypassing the vault scan:

    python3 build.py note.md -o out.html --subtitle "An epithet"
    python3 build.py note.md -o out.html --side left    # override the callout
    python3 build.py note.md --fragment -o embed.html   # style + markup only

## Design notes

- Output is a **single file** — CSS inlined, images embedded, zero external
  requests. It works on Pages, from a USB stick, or as an email attachment.
- The infobox is **floated**, so body text wraps beside it and then reclaims the
  full width below. Obsidian's `[!column]` callout cannot do this: it is a CSS
  grid, and a grid track runs the full height of the callout. The same effect
  inside Obsidian comes from the `wiki-infobox` CSS snippet in this vault.
- Pages follow the reader's light/dark preference.
- On narrow screens the infobox unfloats to full width.
- `🟊` in a note renders as `★`, which has far better font coverage.

## Requirements

Python 3, standard library only. No build tooling, no dependencies.
