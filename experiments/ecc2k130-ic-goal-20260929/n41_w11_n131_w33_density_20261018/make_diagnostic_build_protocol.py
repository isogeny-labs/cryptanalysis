"""Freeze the known-code diagnostic formula variants before generation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'diagnostic_build_protocol.json'
assert not out.exists()
fixture = ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n41_model_fixture.json'
paths = [HERE / 'make_diagnostic_formulas.py',
         HERE / 'n41_formula.xcnf', HERE / 'n41_input_wires.json',
         HERE / 'n41_build_result.json', HERE / 'n41_query_result.json',
         fixture, HERE / 'sage_runtime_info.json']
record = {'status': 'FROZEN_BEFORE_N41_W11_KNOWN_CODE_DIAGNOSTIC_BUILD',
          'candidate_id': None,
          'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'input_law': 'same frozen ordinary N41 public point; first three or all five source codes fixed to the independently verified archived relation; pair-root branches free',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
