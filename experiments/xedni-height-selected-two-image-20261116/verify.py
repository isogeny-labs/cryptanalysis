"""Check sealed height-selected lift receipts and independently replay the audit."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

H = Path(__file__).resolve().parent
seal = (H / 'SEAL.sha256').read_text().splitlines()
names = []
for line in seal:
    digest, name = line.split('  ', 1)
    assert hashlib.sha256((H / name).read_bytes()).hexdigest() == digest, name
    names.append(name)
assert len(names) == len(set(names))
assert set(names) == {p.name for p in H.iterdir() if p.is_file() and p.name != 'SEAL.sha256'}
result = json.loads((H / 'run-result.json').read_text())
assert result['status'] == 'complete'
assert result['counts'] == {
    'candidate_attempts': 41392, 'candidate_failure': 0, 'candidate_pass': 41392,
    'chosen_curves': 512, 'distinct_x_queries': 511, 'equal_x_queries': 1,
    'public_hits': 22, 'public_vector_attempts': 6656, 'queries': 512,
    'rational_control_pass': 512, 'rational_hits': 0,
}
assert (H / 'run.stderr').read_bytes() == b''
assert b'TypeError' in (H / 'run-first.stderr').read_bytes()
assert (H / 'run-first.stdout').read_bytes() == b''
replay = subprocess.run([sys.executable, str(H / 'audit.py')],
                        capture_output=True, text=True, check=True)
assert replay.stderr == '' and replay.stdout == (H / 'audit.stdout').read_text()
assert (H / 'audit.stderr').read_bytes() == b''
assert json.loads(replay.stdout) == json.loads((H / 'audit.json').read_text())
assert json.loads(replay.stdout)['status'] == 'PASS'
print(json.dumps({'status': 'PASS', 'sealed_files': len(seal),
                  'candidate_attempts': 41392, 'vector_attempts': 6656,
                  'public_hits': 22, 'rational_hits': 0}, sort_keys=True))
