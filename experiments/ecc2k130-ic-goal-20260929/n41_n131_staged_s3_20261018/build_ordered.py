"""Add the exact code0 < code1 rule to the staged-S3 N41 XCNF."""
import hashlib
import json
import resource
import time
from pathlib import Path

here = Path(__file__).resolve().parent
p = json.loads((here/'ordered_build_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, digest in p['sources'].items():
    assert sha(path) == digest, path
assert not (here/'ordered_formula.xcnf').exists()
started = time.monotonic()
baseline = Path(p['baseline_formula'])
wires = json.loads(Path(p['input_wires']).read_text())
a, b = wires['codes'][:2]
assert len(a) == len(b) == 8
with baseline.open('r') as src:
    header = src.readline().split()
assert header[:2] == ['p', 'cnf']
old_vars, old_constraints = map(int, header[2:])
next_var = old_vars+1
clauses = []
gates = []


def gate(inputs, truth):
    global next_var
    output = next_var
    next_var += 1
    gates.append((tuple(inputs), truth, output))
    for mask in range(1 << len(inputs)):
        values = [(mask >> i) & 1 for i in range(len(inputs))]
        result = truth(values)
        clause = [(-lit if value else lit) for lit, value in zip(inputs, values)]
        clause.append(output if result else -output)
        clauses.append(clause)
    return output


def land(*args):
    return gate(args, lambda values: all(values))


def lor(*args):
    return gate(args, lambda values: any(values))


def equal(x, y):
    return gate((x, y), lambda values: values[0] == values[1])


eq = equal(a[7], b[7])
lt = land(-a[7], b[7])
for bit in range(6, -1, -1):
    term = land(eq, -a[bit], b[bit])
    lt = lor(lt, term)
    eq = land(eq, equal(a[bit], b[bit]))
clauses.append([lt])


def evaluate(x, y):
    assignment = {wire: (x >> i) & 1 for i, wire in enumerate(a)}
    assignment.update({wire: (y >> i) & 1 for i, wire in enumerate(b)})
    def literal_value(lit):
        value = assignment[abs(lit)]
        return value if lit > 0 else 1-value
    for inputs, truth, output in gates:
        assignment[output] = int(truth([literal_value(lit) for lit in inputs]))
    assert all(any(literal_value(lit) for lit in clause) for clause in clauses[:-1])
    return assignment[lt]


for x in range(256):
    for y in range(256):
        assert evaluate(x, y) == int(x < y)

panel = json.loads(Path(p['panel']).read_text())
states = json.loads(Path(p['states']).read_text())
bits = [i for i in range(9) if i != 5]
controls = []
for row in panel:
    codes = []
    for slot in (0, 1):
        mask = states['states'][slot][row['state_ids'][slot]]['masks'][0]
        codes.append(sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits)))
    controls.append({'kind': row['kind'], 'codes': codes,
                     'accepted_by_order': bool(evaluate(*codes))})
assert sum(row['kind'] == 'positive' for row in controls) == 1
assert all(row['accepted_by_order'] for row in controls if row['kind'] == 'positive')

with baseline.open('rb') as src, (here/'ordered_formula.xcnf').open('xb') as dst:
    src.readline()
    dst.write(f'p cnf {next_var-1} {old_constraints+len(clauses)}\n'.encode())
    for chunk in iter(lambda: src.read(1 << 20), b''):
        dst.write(chunk)
    for clause in clauses:
        dst.write((' '.join(map(str, clause))+' 0\n').encode())
finished = time.monotonic()
out = {'status': 'PASS_N41_STAGED_S3_ORDERED_CIRCUIT',
       'candidate_id': None, 'curve_id': p['curve_id'],
       'baseline_variables': old_vars, 'baseline_constraints': old_constraints,
       'new_variables': next_var-1, 'new_constraints': old_constraints+len(clauses),
       'comparator_gates': len(gates), 'comparator_clauses': len(clauses),
       'exhaustive_code_pairs_checked': 256*256, 'controls': controls,
       'formula_sha256': sha(here/'ordered_formula.xcnf'),
       'formula_bytes': (here/'ordered_formula.xcnf').stat().st_size,
       'protocol_sha256': sha(here/'ordered_build_protocol.json'),
       'wall_seconds': finished-started,
       'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(here/'ordered_build_result.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
print(json.dumps({k: out[k] for k in ('status', 'new_variables',
                                      'new_constraints', 'comparator_gates',
                                      'comparator_clauses', 'wall_seconds')}))
