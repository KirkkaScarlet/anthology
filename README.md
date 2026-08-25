# Emilia Lynn Ravnskov — character page

A single self-contained HTML page, published with GitHub Pages.

## How it works

The **source of truth is the Obsidian note**, not the HTML:

    Saribas/Non-Saribas Content/Emilia Lynn Ravnskov.md

Edit there as normal, then regenerate:

    ./build.sh

That rewrites `index.html` — one file with the CSS inlined and the portrait
embedded as a data URI, so there is nothing else to upload and nothing to break.
Commit and push, and GitHub Pages serves the new version.

Pass a different note explicitly if you ever move it:

    ./build.sh "/some/other/note.md"

## What the converter reads

It understands the note exactly as Obsidian already writes it — no extra syntax:

- the first `######` inside the `[!infobox]` callout becomes the page title
- `![[Image.png]]` inside the callout becomes the portrait
- each later `######` starts a labelled block (Bio, Physical Info, …)
- `**Label** | value |` rows become infobox entries; a row whose **first cell is
  empty** stacks another value under the previous label (multiple relatives,
  human vs. dragon height, and so on)
- a row with a label but no value renders as a sub-heading
- `##` headings outside the callout become the body sections

Empty sections are skipped with a warning rather than emitting a blank heading.

## Notes

- The layout floats the infobox left so body text wraps beside it and then
  reclaims the full width below — the thing Obsidian's `[!column]` callout
  cannot do, because a grid track runs the full height of the callout.
- The page is theme-aware: it follows the reader's light/dark preference.
- On narrow screens the infobox unfloats to full width.
- `🟊` in the note is rendered as `★`, which has far better font coverage.
