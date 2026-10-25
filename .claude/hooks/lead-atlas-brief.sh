#!/bin/bash
# SessionStart: print the ECDLP lead atlas brief from the sibling
# crypto-autoresearcher checkout (knowledge/leads/ecdlp/). It says what has
# already been tried across this repository and its siblings, and whether
# anything changed since the last review. Hook stdout becomes session context.
# Never fatal.
atlas_repo="$(dirname "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}")/crypto-autoresearcher"
if [ -f "$atlas_repo/tools/lead_atlas.py" ]; then
  python3 "$atlas_repo/tools/lead_atlas.py" --brief 2>/dev/null || true
else
  echo "ECDLP lead atlas: clone aburan28/crypto-autoresearcher next to this checkout and run python3 tools/lead_atlas.py --brief before proposing an ECDLP idea."
fi
exit 0
