#!/usr/bin/env bash
# Native check of the handbook-idea Lean corpus: full build, forbidden-token
# scan, and `#print axioms` for every theorem. Writes receipts/ beside it.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.elan/bin:$PATH"
mkdir -p receipts
{
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "toolchain: $(cat lean-toolchain)"
  echo "lean: $(lean --version)"
  echo "lake: $(lake --version)"
  echo "git: $(git -C ../../.. rev-parse HEAD 2>/dev/null || echo unknown)"
} > receipts/environment.txt
# Root module imports every idea module.
{
  echo "import HandbookIC.Core"
  for f in $(ls HandbookIC/Ideas/*.lean 2>/dev/null | sort); do
    m=$(basename "$f" .lean); echo "import HandbookIC.Ideas.$m"
  done
} > HandbookIC.lean
lake build 2>&1 | tee receipts/build.log
echo "build exit: ${PIPESTATUS[0]}" | tee -a receipts/build.log
# Forbidden tokens (comments included).
if grep -rnE 'sorry|admit|\baxiom\b|native_decide|unsafe|partial|implemented_by|extern' HandbookIC/ HandbookIC.lean > receipts/forbidden-tokens.txt; then
  echo "FORBIDDEN TOKENS FOUND"; cat receipts/forbidden-tokens.txt; exit 1
fi
echo "none" > receipts/forbidden-tokens.txt
# Axiom audit: every theorem in every module.
python3 - <<'PY' > receipts/axioms.lean
import re, pathlib
files = sorted(pathlib.Path('HandbookIC').glob('**/*.lean')) 
print('import HandbookIC')
for f in files:
    text = f.read_text()
    ns = None
    for line in text.splitlines():
        m = re.match(r'\s*namespace\s+(\S+)', line)
        if m: ns = m.group(1)
        m = re.match(r'\s*(?:protected\s+)?theorem\s+([A-Za-z0-9_.\']+)', line)
        if m:
            name = m.group(1)
            print(f'#print axioms {ns + "." + name if ns else name}')
PY
lake env lean receipts/axioms.lean 2>&1 | tee receipts/axioms.log
echo "axioms exit: ${PIPESTATUS[0]}" | tee -a receipts/axioms.log
python3 - <<'PY'
import re, pathlib
log = pathlib.Path('receipts/axioms.log').read_text()
allowed = {'propext', 'Classical.choice', 'Quot.sound'}
bad = []
n = 0
for line in log.splitlines():
    m = re.match(r"'(.+)' depends on axioms: \[(.*)\]", line)
    if m:
        n += 1
        axs = {a.strip() for a in m.group(2).split(',') if a.strip()}
        if not axs <= allowed: bad.append((m.group(1), axs))
    elif re.match(r"'(.+)' does not depend on any axioms", line):
        n += 1
summary = {'theorems_audited': n, 'outside_standard_foundations': bad}
pathlib.Path('receipts/axioms-summary.json').write_text(__import__('json').dumps(summary, indent=1, default=list))
print(summary)
if bad: raise SystemExit(1)
PY
echo "CHECK PASSED"
