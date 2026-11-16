"""Rebuild the pinned Lean obstruction and check its kernel axiom audit."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
FORMAL = HERE / 'formal'
source = (FORMAL / 'TorsionSection.lean').read_text()
for forbidden in ('sorry', 'admit', 'sorryAx', 'axiom '):
    assert forbidden not in source, forbidden
names = ('torsion_relation_fails', 'no_additive_section',
         'no_relation_preserving_lift', 'zmod_no_relation_preserving_lift')
for name in names:
    assert f'theorem {name} ' in source
    assert f'#print axioms {name}' in source
run = subprocess.run(['lake', 'build', 'TorsionSection'], cwd=FORMAL,
                     capture_output=True, text=True)
assert run.returncode == 0, run.stdout + run.stderr
check = subprocess.run(['lake', 'env', 'lean', 'TorsionSection.lean'], cwd=FORMAL,
                       capture_output=True, text=True)
output = check.stdout + check.stderr
assert check.returncode == 0, output
for name in names:
    assert f"'XedniTorsionSection.{name}' depends on axioms:" in output, name
assert 'sorryAx' not in output
assert 'Build completed successfully' in run.stdout + run.stderr
lock = json.loads((FORMAL / 'lake-manifest.json').read_text())
assert '021c46bdd042f67b538b9f9871d556a93713a9a9' in json.dumps(lock)
assert (FORMAL / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.35.0-rc4'
print(json.dumps({'status': 'PASS', 'checked_theorems': len(names),
                  'source_sha256': hashlib.sha256(source.encode()).hexdigest()}, sort_keys=True))
