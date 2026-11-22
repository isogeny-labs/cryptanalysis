"""Build the W29 exact-source circuit for the second N131 raw lift."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_fivepair_w9_w29_20261017'
TRACE = ROOT / 'n41_n131_trace_parity_20261017'
SPEC = importlib.util.spec_from_file_location('w29_second_lift', PRIOR / 'circuit_n131_3p2.py')
design = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


lift = json.loads((HERE / 'lift_targets.json').read_text())['rows'][1]
target = lift['raw1_reciprocal_x']
assert target == lift['raw0'][0] and design.F.mul(target, lift['raw1'][0]) == 1
assert design.previous.trace(target) == 0
base, base_wires, base_counts = design.build(target)
trace, trace_wires, trace_counts = design.build(target)
assert base_counts == trace_counts
parity_wires = [wire for row in trace_wires['out']
                for wire, tr in zip(row, design.TRACE) if tr]
assert len(parity_wires) == 10
trace.require_zero([trace.xor(parity_wires)])
old_counts = (len(base.clauses), len(base.xors), base.next_var - 1)
new_counts = (len(trace.clauses), len(trace.xors), trace.next_var - 1)
assert new_counts == (old_counts[0] + 1, old_counts[1] + 1, old_counts[2] + 1)
paths = {'raw1_baseline': HERE / 'n131_raw1_baseline.xcnf',
         'raw1_trace': HERE / 'n131_raw1_trace.xcnf'}
base.write(paths['raw1_baseline'])
trace.write(paths['raw1_trace'])
raw0 = json.loads((TRACE / 'build_n131_result.json').read_text())
assert old_counts == (raw0['baseline_counts']['clauses'],
                      raw0['baseline_counts']['xor_rows'],
                      raw0['baseline_counts']['variables'])
assert new_counts == (raw0['trace_counts']['clauses'],
                      raw0['trace_counts']['xor_rows'],
                      raw0['trace_counts']['variables'])
result = {'status': 'PASS_N131_SECOND_LIFT_FORMULAS_BUILT',
          'curve_id': lift['curve_id'], 'target_raw_point': lift['raw1'],
          'target_reciprocal_x': target, 'public_subgroup_point': lift['subgroup_point'],
          'trace_parity': 0, 'global_parity_input_wires': len(parity_wires),
          'baseline_counts': base_counts,
          'trace_counts': {'clauses': new_counts[0], 'xor_rows': new_counts[1],
                           'variables': new_counts[2]},
          'formula_sha256': {name: sha(path) for name, path in paths.items()},
          'source_sha256': {name: sha(path) for name, path in
                            {'script': Path(__file__), 'circuit': PRIOR / 'circuit_n131_3p2.py',
                             'previous_circuit': Path(design.previous.__file__),
                             'lift_targets': HERE / 'lift_targets.json',
                             'raw0_build': TRACE / 'build_n131_result.json',
                             'runtime': HERE / 'sage_runtime_info.json'}.items()}}
with (HERE / 'build_n131_raw1_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'], 'target_reciprocal_x': target,
                  'baseline_counts': base_counts, 'trace_counts': result['trace_counts'],
                  'formula_sha256': result['formula_sha256']}))
