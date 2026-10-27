"""Generate finite support and quotient-minor Lean certificates."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
PLAN = json.loads((HERE.parent / 'inputs.json').read_text())
POST = json.loads((HERE.parent / 'post-run.json').read_text())
assert hashlib.sha256((HERE.parent / 'result.json').read_bytes()).hexdigest() == POST['result_sha256']
item = PLAN['frozen']['analysis.json']
raw = (ROOT / item['path']).read_bytes()
assert hashlib.sha256(raw).hexdigest() == item['sha256']
case = next(x for x in json.loads(raw)['cases'] if x['p'] == 63317)
supports = [tuple(x['sources']) for x in case['hecke_candidates']]
assert len(supports) == 237 and len(set(supports)) == 237
assert supports[221] == (17,18,33,36) and supports[226] == (17,23,33,36)
lines = ['module', '', 'public import Init', '', 'namespace RankSourceCompression',
         'public def supports : List (Nat × Nat × Nat × Nat) := [']
lines += ['  (' + ', '.join(map(str,s)) + '),' for s in supports]
lines += [']',
          'set_option maxRecDepth 32768 in',
          'set_option maxHeartbeats 1000000 in',
          'public theorem all_supports_distinct : supports.Nodup := by decide',
          'public theorem all_supports_strict :',
          '    supports.all (fun s => s.1 < s.2.1 && s.2.1 < s.2.2.1 &&',
          '      s.2.2.1 < s.2.2.2) = true := by decide',
          'public theorem quotient_minor :',
          '    ((1620 * 2320 - 922 * 2304 : Int) % 2531) = 1617 := by decide',
          'public theorem quotient_minor_nonzero :',
          '    ((1620 * 2320 - 922 * 2304 : Int) % 2531) ≠ 0 := by decide',
          '#print axioms all_supports_distinct',
          '#print axioms all_supports_strict',
          '#print axioms quotient_minor',
          '#print axioms quotient_minor_nonzero',
          'end RankSourceCompression', '']
(HERE / 'RankSourceCompression.lean').write_text('\n'.join(lines))
print('generated',len(supports),'support tuples')
