#!/usr/bin/env bash
# Rebuild the site from the vault.
#
# Every note in notes/ with a `publish:` property becomes a page; the slug you
# give that property is its URL path. Set it from Obsidian's Properties panel —
# nothing to edit outside the vault. Output goes to docs/, which is what GitHub
# Pages serves; never hand-edit anything in there.
set -euo pipefail
cd "$(dirname "$0")"

# Tell GitHub Pages to serve these files verbatim. Without this, Jekyll
# processes the directory and replaces the generated pages with its own theme.
mkdir -p docs && touch docs/.nojekyll

python3 build.py --all --notes notes -o docs
