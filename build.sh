#!/usr/bin/env bash
# Regenerate index.html from the Obsidian note.
# The markdown in the vault stays the source of truth — edit there, run this,
# commit the result.
set -euo pipefail
cd "$(dirname "$0")"

NOTE="${1:-$HOME/Documents/Tabletop/Worldbuilds/Saribas/Non-Saribas Content/Emilia Lynn Ravnskov.md}"

if [[ ! -f "$NOTE" ]]; then
  echo "Note not found: $NOTE" >&2
  echo "Pass the path explicitly:  ./build.sh /path/to/note.md" >&2
  exit 1
fi

python3 build.py "$NOTE" -o index.html
