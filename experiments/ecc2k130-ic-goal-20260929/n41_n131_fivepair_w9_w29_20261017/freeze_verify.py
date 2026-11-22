"""Freeze terminal audit inputs after both N131 public attempts finish."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


names = ['verify_results.py', 'sage_runtime_info.json',
         'orbit_protocol.json', 'orbit_result.json', 'orbit_audit_result.json',
         'sample_protocol.json', 'sample_result.json', 'sample_audit_result.json',
         'n131_model_control_result.json', 'n131_model_control_result_3p2.json',
         'n131_query_protocol.json',
         'n131_query_result.json', 'n131_ordinary.xcnf',
         'n131_solver.stdout', 'n131_solver.stderr',
         'n131_query_protocol_3p2.json', 'n131_query_result_3p2.json',
         'n131_3p2_ordinary.xcnf', 'n131_3p2_solver.stdout',
         'n131_3p2_solver.stderr', 'topology_audit_result.json',
         'FivePairJoin.lean', 'lean_v2.stdout', 'lean_v2.stderr']
protocol = {'status': 'FROZEN_BEFORE_TERMINAL_AUDIT',
            'source_sha256': {name: sha(HERE / name) for name in names}}
with (HERE / 'verify_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': protocol['status'], 'files': len(names)}))
