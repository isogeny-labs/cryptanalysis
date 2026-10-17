"""Complete projective Riemann--Roch function-selector formula on N41."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

D = Path(__file__).resolve().parent
R = D.parent
sys.path.insert(0, str(R))
from vd_z_s3_sixleaf_circuit import Field, KaratsubaCircuit
from build_n131_v20_sixleaf_circuit import replay_all_wires, check_formula

SOURCE = R / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
N = 41
MOD = (1 << 41) | (1 << 3) | 1
WITNESS = [12, 122, 116, 47, 128, 34]
# Coefficient order: x²y, x³, x², x, xy, y, 1.
WITNESS_COEFFICIENTS = [1, 1200046331721, 51193325258,
                        197579618746, 1789122703940, 761080510426,
                        107927970499]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def point_row(field, x, y):
    x2 = field.mul(x, x)
    return (field.mul(x2, y), field.mul(x2, x), x2, x,
            field.mul(x, y), y, 1)

def load_source():
    lines = SOURCE.read_text().splitlines()
    head = lines[0].split()
    assert head[:3] == ['ECC2K41', '6', '160']
    target = (int(head[3]), int(head[4]))
    rows = {}
    for line in lines[1:]:
        v = line.split()
        assert v[0] == 'S'
        slot, idx = map(int, v[1:3])
        assert (slot, idx) not in rows
        rows[slot, idx] = {'x': int(v[9]), 'y': int(v[10]),
                           'cols': (int(v[7]), int(v[8]))}
    assert len(rows) == 960
    for slot in range(6):
        for idx in range(160):
            assert (slot, idx) in rows
    return target, rows

def add_linear_row(circ, field, coeff, constants, guard=None):
    output_terms = [[] for _ in range(N)]
    for j, constant in enumerate(constants):
        if constant == 0:
            continue
        for k, wire in enumerate(coeff[j]):
            bits = field.mul(constant, 1 << k)
            while bits:
                low = bits & -bits
                output_terms[low.bit_length()-1].append(wire)
                bits ^= low
    for terms in output_terms:
        wire = circ.xor(terms)
        if guard is None:
            circ.require_zero([wire])
        elif wire == -1:
            circ.clauses.append(f'-{guard} 0')
        elif wire != 0:
            circ.clauses.append(f'-{guard} -{wire} 0')

def build(target, rows):
    field = Field(N, [0, 3])
    circ = KaratsubaCircuit(N, [0, 3])
    coeff = [[circ.variable() for _ in range(N)] for _ in range(7)]
    selectors = [[circ.variable() for _ in range(160)] for _ in range(6)]
    charts = [circ.variable() for _ in range(7)]
    circ.clauses.append(' '.join(map(str, charts))+' 0')
    for i in range(7):
        for j in range(i+1, 7):
            circ.clauses.append(f'-{charts[i]} -{charts[j]} 0')
    for chosen, chart in enumerate(charts):
        for prior in range(chosen):
            for wire in coeff[prior]:
                circ.clauses.append(f'-{chart} -{wire} 0')
        for bit, wire in enumerate(coeff[chosen]):
            circ.clauses.append(f'-{chart} {wire if bit == 0 else -wire} 0')

    code_selector = [[circ.variable() for _ in range(40)] for _ in range(6)]
    columns = {}
    for slot in range(6):
        group = selectors[slot]
        circ.clauses.append(' '.join(map(str, group))+' 0')
        for i in range(160):
            for j in range(i+1, 160):
                circ.clauses.append(f'-{group[i]} -{group[j]} 0')
        for c in range(40):
            members = group[4*c:4*c+4]
            gate = code_selector[slot][c]
            for member in members:
                circ.clauses.append(f'-{member} {gate} 0')
            circ.clauses.append(' '.join([f'-{gate}'] + [str(m) for m in members])+' 0')
            observed = {rows[slot, i]['cols'] for i in range(4*c, 4*c+4)}
            assert len(observed) == 1
            columns[slot, c] = set(observed.pop())
    conflict_clauses = 0
    for left in range(6):
        for right in range(left+1, 6):
            for a in range(40):
                for b in range(40):
                    if columns[left, a] & columns[right, b]:
                        circ.clauses.append(f'-{code_selector[left][a]} -{code_selector[right][b]} 0')
                        conflict_clauses += 1

    tx, ty = target
    neg_target = (tx, ty ^ tx)
    target_row = point_row(field, *neg_target)
    add_linear_row(circ, field, coeff, target_row)
    target_x_exclusions = 0
    x_collisions = 0
    for slot in range(6):
        for idx in range(160):
            p = rows[slot, idx]
            x, y = p['x'], p['y']
            assert field.mul(y, y) ^ field.mul(x, y) == field.mul(field.mul(x, x), x) ^ 1
            if x == tx:
                circ.clauses.append(f'-{selectors[slot][idx]} 0')
                target_x_exclusions += 1
            add_linear_row(circ, field, coeff, point_row(field, x, y), selectors[slot][idx])
    for left in range(6):
        for right in range(left+1, 6):
            for a in range(160):
                x = rows[left, a]['x']
                for b in range(160):
                    if x == rows[right, b]['x'] and not (rows[left, a]['cols'][0] in rows[right, b]['cols']
                                                          or rows[left, a]['cols'][1] in rows[right, b]['cols']):
                        circ.clauses.append(f'-{selectors[left][a]} -{selectors[right][b]} 0')
                        x_collisions += 1
    meta = {'coeff': coeff, 'selectors': selectors, 'charts': charts,
            'code_selector': code_selector, 'target_row': target_row,
            'conflict_clauses': conflict_clauses,
            'target_x_exclusions': target_x_exclusions,
            'extra_x_collision_clauses': x_collisions}
    return circ, meta

def witness_control(circ, meta, rows, target):
    field = Field(N, [0, 3])
    chosen = WITNESS_COEFFICIENTS
    for slot, idx in enumerate(WITNESS):
        row = point_row(field, rows[slot, idx]['x'], rows[slot, idx]['y'])
        value = 0
        for a, b in zip(chosen, row):
            value ^= field.mul(a, b)
        assert value == 0
    value = 0
    for a, b in zip(chosen, meta['target_row']):
        value ^= field.mul(a, b)
    assert value == 0
    primary = {}
    for j, value in enumerate(chosen):
        for bit, wire in enumerate(meta['coeff'][j]):
            primary[wire] = (value >> bit) & 1
    for slot, idx in enumerate(WITNESS):
        for state, wire in enumerate(meta['selectors'][slot]):
            primary[wire] = state == idx
        for c, wire in enumerate(meta['code_selector'][slot]):
            primary[wire] = c == idx//4
    for chart, wire in enumerate(meta['charts']):
        primary[wire] = chart == 0
    values = replay_all_wires(circ, primary)
    result = check_formula(circ, values)
    assert result['satisfied'], result
    return {'state_ids': WITNESS, 'coefficient_values': chosen,
            'chart': 0, 'checked_assignments': len(values), **result}

def main():
    started = time.monotonic()
    protocol = json.loads((D/'protocol.json').read_text())
    assert protocol['source_sha256'] == sha(SOURCE)
    assert protocol['builder_sha256'] == sha(Path(__file__))
    target, rows = load_source()
    assert list(target) == protocol['target']
    circ, meta = build(target, rows)
    control = witness_control(circ, meta, rows, target)
    formula = D/'formula.xcnf'
    circ.write(formula)
    result = {'status': 'BUILD_AND_WITNESS_PASS',
              'protocol_sha256': sha(D/'protocol.json'),
              'formula_sha256': sha(formula),
              'formula_bytes': formula.stat().st_size,
              'variables': circ.next_var-1,
              'cnf_clauses': len(circ.clauses),
              'native_xor_rows': len(circ.xors),
              'and_gates': circ.and_count,
              'metadata': {k: meta[k] for k in ('conflict_clauses', 'target_x_exclusions', 'extra_x_collision_clauses')},
              'control': control,
              'wall_s': time.monotonic()-started,
              'peak_self_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (D/'build_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: result[k] for k in ('status','variables','cnf_clauses','native_xor_rows','and_gates','formula_bytes','wall_s','peak_self_rss_bytes')}))

if __name__ == '__main__':
    main()
