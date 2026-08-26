Templates for new notes, inserted with **Templater** (command palette →
"Templater: Open insert template modal", worth a hotkey).

Nothing here is published. Quartz's `ignorePatterns` skips this folder, which
is why `Entry.md` can carry `publish: true` as part of the text you are
copying without publishing itself.

- **Entry** — a new entry's `index.md`. `tp.file.folder()` fills the title from
  the *folder* name, because the file itself is called `index`.
- **Sub-page** — a section inside an entry. `tp.file.title` fills from the
  filename.

The infobox tables use `| | |` over `|---|---|`. The header row must have the
same number of cells as the delimiter row, or the table will not parse on the
site — Obsidian is lenient about this and the published page is not.
