#!/bin/sh
# Install the aio man pages.
# Usage: ./install_man.sh          -> ~/.local/share/man
#        ./install_man.sh --system -> /usr/share/man

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$1" = "--system" ]; then
    MANDIR=/usr/share/man
else
    MANDIR="${HOME}/.local/share/man"
fi

mkdir -p "$MANDIR/man1" "$MANDIR/man7"

for page in "$DIR"/man/*.1; do
    [ -e "$page" ] || continue
    install -m 644 "$page" "$MANDIR/man1/"
    echo "Installed $(basename "$page")"
done

for page in "$DIR"/man/*.7; do
    [ -e "$page" ] || continue
    install -m 644 "$page" "$MANDIR/man7/"
    echo "Installed $(basename "$page")"
done

echo
echo "Man pages installed to $MANDIR"
echo "View with: man aio / man aio-cli / man aio-suite"
