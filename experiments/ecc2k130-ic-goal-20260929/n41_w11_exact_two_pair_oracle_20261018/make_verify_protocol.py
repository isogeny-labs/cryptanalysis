"""Freeze terminal verification of bounded and completed oracle arms."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = HERE / 'verify_protocol.json'
assert not out.exists()
paths = [HERE / 'verify.py', HERE / 'fixture_protocol.json',
         HERE / 'fixture.json', HERE / 'build_protocol.json',
         HERE / 'build_result.json', HERE / 'formula.xcnf',
         HERE / 'query_protocol.json', HERE / 'query_result.json',
         HERE / 'solver.stdout', HERE / 'solver.stderr',
         HERE / 'inverse_protocol.json', HERE / 'inverse_result.json',
         HERE / 'inverse_audit_protocol.json', HERE / 'inverse_audit_result.json',
         HERE / 'work_protocol.json', HERE / 'work_result.json',
         HERE / 'SerialOracleWork.lean', HERE / 'lean_check.log']
record = {'status': 'FROZEN_BEFORE_N41_W11_EXACT_IMPLICIT_ORACLE_VERIFY',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
