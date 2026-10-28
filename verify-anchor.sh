#!/bin/sh
# Explorer-basierter Abgleich der vier Proofs; Details siehe VERIFY-BITCOIN-ANCHOR.md.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$HERE/verify-anchor.py" "$@"
