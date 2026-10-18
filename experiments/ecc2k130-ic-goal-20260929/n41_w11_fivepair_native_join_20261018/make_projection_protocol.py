"""Freeze the exact N131 W33 storage projection from audited subsets."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'projection_protocol.json'
assert not out.exists()
paths = [HERE / 'project_n131.py', HERE / 'audit_result.json',
         ROOT / 'n131_w20_sevenpair_gate_20261010' / 'count_result_v2.json',
         ROOT / 'n131_w20_code_trace_bitset_20261014' / 'native_result.json',
         ROOT / 'n131_w20_code_trace_bitset_20261014' / 'terminal_verification.json',
         ROOT / 'n131_w29_folded_collision_20261018' / 'filter_result.json',
         ROOT / 'n131_w29_folded_collision_20261018' / 'verification_result.json',
         ROOT / 'n41_w11_n131_w33_density_20261018' / 'build_n131.py',
         ROOT / 'n131_w23_sixpair_shared_circuit_20261017' / 'circuit.py']
record = {'status': 'FROZEN_BEFORE_N131_W33_NATIVE_PAIR_STORAGE_PROJECTION',
          'candidate_id': None, 'curve_id': 'EC1N131Ckb1heb5f1998f20b',
          'rss_cap_bytes': 4*1024**3,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
