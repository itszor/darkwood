#!/bin/sh
# Build Darkwood from your own copy of the game:
#     ./build.sh "Darkwood 0.63 (1995)(Tom Cooper)(Disk 1 of 6).hfe" ... (all six .hfe files)
# then: cd recomp && ./darkwood
# The steps are recipe.json's "build", run by SuperSpider's tools/weave.py.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SUPERSPIDER="${SUPERSPIDER:-$HOME/stuff/superspider}"
[ $# -gt 0 ] || { echo "usage: $0 DISC1.hfe ... DISC6.hfe (or a .zip of them)" >&2; exit 2; }
(cd "$SUPERSPIDER" && dune build)
WEAVE_RECIPES="$HERE" exec python3 -I "$SUPERSPIDER/tools/weave.py" build "$@"
