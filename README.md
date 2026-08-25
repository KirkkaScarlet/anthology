# Anthology

An Obsidian vault that publishes itself to the web with
[Quartz v5](https://quartz.jzhao.xyz).

Live: <https://kirkkascarlet.github.io/anthology>

This vault is for standalone pages — things that are not part of another
worldbuild. Open this folder directly in Obsidian; write in `content/`.

## Publishing a page

A note goes live only if its frontmatter says so:

    ---
    title: Alexis Ravnskov
    publish: true
    ---

No `publish: true`, no page. Drafts are private by default — that is the
`explicit-publish` plugin, the same gate the Asteria site uses.

The **URL comes from the file path**, not from a property. Folders become URL
segments, and a folder's `index.md` becomes the folder's own page.

## One folder per entry

Each entry — a character, a small worldbuild, whatever — gets its own folder,
holding its pages and its own images:

    content/
      index.md                        ->  /anthology/          (this landing page)
      Alexis Ravnskov/
        index.md                      ->  /anthology/alexis-ravnskov/
        attachments/                      images for this entry only
        Emilia Lynn Ravnskog.md           no publish: -> stays private

Entries are independent. Deleting a folder removes an entry cleanly, with no
dangling images or links left behind elsewhere.

To give an entry more pages, add siblings next to its `index.md`:

    Alexis Ravnskov/Gameplay.md       ->  /anthology/alexis-ravnskov/gameplay

That is also how you would build Fandom-style sections: each is a real page
with a real URL, no JavaScript needed.

Folder and file names are slugified for the URL, so `Alexis Ravnskov/` stays
readable in Obsidian while the URL reads `/alexis-ravnskov/`. Renaming a note
or folder changes its URL.

## Deploying

Push to `main`. GitHub Actions builds the site and deploys it — there is no
build output in this repo.

    git add -A && git commit -m "..." && git push

## Preview locally

    npx quartz build --serve      # http://localhost:8080

First time on a new machine:

    npm ci
    npx quartz plugin install

## Theme

The site uses `quartz-themes` with `its-theme` / `ttrpg-dnd`, which is the
Quartz port of the ITS Theme this vault uses in Obsidian. That is why an
`[!infobox|right]` callout renders as a floated wiki infobox on the site
without any custom CSS — body text wraps beside it and reclaims the full
width below.

Write ordinary Obsidian markdown. Headings, lists, tables, callouts,
wikilinks, and embeds all render; there is no per-page configuration.

## Layout

    content/      what you write, and what gets published
    quartz/       Quartz itself — don't edit
    quartz.config.yaml
                  site settings: title, baseUrl, theme, plugins
    public/       build output (gitignored)
