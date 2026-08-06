#!/bin/sh
# Regenerate all aio documentation: doxygen HTML, man-page check, index map.
# Equivalent to: aio.py docs all
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "==> Running doxygen"
if command -v doxygen >/dev/null 2>&1; then
    doxygen Doxyfile
else
    echo "doxygen not found; skipping HTML generation."
fi

echo "==> Verifying man pages"
if command -v groff >/dev/null 2>&1; then
    for page in man/*; do
        [ -f "$page" ] || continue
        if groff -man -Tutf8 "$page" >/dev/null 2>&1; then
            echo "  ok  $page"
        else
            echo "  ERR $page (syntax problem)" >&2
        fi
    done
else
    echo "groff not found; skipping man-page verification."
fi

echo "==> Man pages: $(ls man/*.1 man/*.7 2>/dev/null | wc -l) files"
echo "==> Docs map: docs/INDEX.md"
echo "Done. Read docs/INDEX.md for the full map."
