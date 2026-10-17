"""Bind frozen protocol, executable, comparison logs, audit, and proof output."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
run = json.loads((D / 'run_result.json').read_text())
bench = json.loads((D / 'bench_result.json').read_text())
audit = json.loads((D / 'audit_result.json').read_text())
assert run['status'] == 'HIT_PENDING_INDEPENDENT_REPLAY'
assert audit['status'] == 'PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION'
assert run['protocol_sha256'] == bench['protocol_sha256'] == sha(D / 'protocol.json')
assert sha(D / 'sign_join') == run['binary_sha256']
assert sha(D / 'bench.py') == bench['bench_source_sha256']
assert all(r['exit_code'] == 0 for r in bench['rows'])
paths = ['RESULT.md', 'PROOF_MAP.md', 'NegationQuotient.lean', 'lean-toolchain',
         'lean.stdout', 'lean.stderr', 'sign_join.cpp', 'sign_join',
         'freeze.py', 'run.py', 'audit_sage.py', 'bench.py', 'protocol.json',
         'sage_runtime_info.json', 'run_result.json', 'run.stdout', 'run.stderr',
         'audit_result.json', 'bench_result.json']
for row in bench['rows']:
    paths += [f"bench_{row['order']}_{row['variant']}.stdout",
              f"bench_{row['order']}_{row['variant']}.stderr"]
record = {'schema': 1, 'status': 'PASS_COMPONENT',
          'source_input_sha256': json.loads((D / 'protocol.json').read_text())['input_sha256'],
          'files': {p: sha(D / p) for p in paths}}
(D / 'terminal.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(json.dumps({'terminal_sha256': sha(D / 'terminal.json'), 'file_count': len(paths)}))
