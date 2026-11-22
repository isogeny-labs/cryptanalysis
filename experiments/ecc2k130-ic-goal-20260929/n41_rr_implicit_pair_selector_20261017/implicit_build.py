"""RR selector with point rows computed from mask bits and curve arithmetic."""
import hashlib
import json
import resource
import time
from pathlib import Path

import build as previous

D = Path(__file__).resolve().parent
ROOT = D.parent
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009' / 'geometry.json'
N = 41
BITS = (0, 1, 2, 3, 4, 6, 7)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frob(field, value, count):
    for _ in range(count):
        value = field.mul(value, value)
    return value


def halftrace(field, value):
    result = 0
    for _ in range((N + 1) // 2):
        result ^= value
        value = field.mul(field.mul(value, value), field.mul(value, value))
    return result


def mismatch(wires, packed_code):
    return [(-wire if packed_code >> bit & 1 else wire)
            for bit, wire in enumerate(wires)]


def add_endpoint(circ, field, u, sign, halftrace_map):
    inverse_u = [circ.variable() for _ in range(N)]
    circ.require_zero(circ.add(circ.mul(u, inverse_u), circ.constant(1)))
    x = circ.add(circ.constant(1), inverse_u)
    inverse_x = [circ.variable() for _ in range(N)]
    circ.require_zero(circ.add(circ.mul(x, inverse_x), circ.constant(1)))
    rhs = circ.add(x, circ.square(inverse_x))
    z = circ.linear_element(rhs, halftrace_map)
    circ.require_zero(circ.add(circ.add(circ.square(z), z), rhs))
    y = circ.mul(x, circ.add(z, circ.linear_element([sign], [1])))
    return x, y, inverse_u, inverse_x


def build_circuit(target, source_rows, geometry):
    field = previous.Field(N, [0, 3])
    circ = previous.KaratsubaCircuit(N, [0, 3])
    coeff = [[circ.variable() for _ in range(N)] for _ in range(7)]
    charts = [circ.variable() for _ in range(7)]
    chart_prefix = previous.sequential_onehot(circ, charts)
    for chart, wire in enumerate(charts):
        for earlier in range(chart):
            for bit in coeff[earlier]:
                circ.clauses.append(f'-{wire} -{bit} 0')
        for bit, coefficient in enumerate(coeff[chart]):
            circ.clauses.append(f'-{wire} {coefficient if bit == 0 else -coefficient} 0')
    target_row = previous.point_row(field, target[0], target[1] ^ target[0])
    previous.require_field_linear(circ, field, coeff, target_row)

    permitted = geometry['permitted_canonical_a']
    allowed = {sum(((mask >> bit) & 1) << j for j, bit in enumerate(BITS))
               for mask in permitted}
    assert len(permitted) == len(allowed) == 40
    assert all(mask & (1 << 5) == 0 for mask in permitted)
    seed = geometry['fixed_seed_sum_code']
    assert seed == 56
    basis = geometry['blocks'][0]['basis']
    seed_u = 0
    for bit in range(8):
        if seed >> bit & 1:
            seed_u ^= basis[bit]
    assert seed_u == geometry['blocks'][0]['s']
    halftrace_map = [halftrace(field, 1 << bit) for bit in range(N)]
    code_bits = [[circ.variable() for _ in BITS] for _ in range(6)]
    signs = [[circ.variable() for _ in range(2)] for _ in range(6)]
    inverse_wires = []
    forbidden = 0
    for slot in range(6):
        code = code_bits[slot]
        for packed in range(128):
            if packed not in allowed:
                circ.clauses.append(' '.join(map(str, mismatch(code, packed))) + ' 0')
                forbidden += 1
        u_a = circ.linear_element(code, [basis[bit] for bit in BITS])
        u_b = circ.add(u_a, circ.constant(seed_u))
        xa, ya, invua, invxa = add_endpoint(circ, field, u_a, signs[slot][0], halftrace_map)
        xb, yb, invub, invxb = add_endpoint(circ, field, u_b, signs[slot][1], halftrace_map)
        denominator = circ.add(xa, xb)
        inverse_denominator = [circ.variable() for _ in range(N)]
        circ.require_zero(circ.add(circ.mul(denominator, inverse_denominator),
                                   circ.constant(1)))
        slope = circ.mul(circ.add(ya, yb), inverse_denominator)
        x = circ.add(circ.add(circ.square(slope), slope), denominator)
        y = circ.add(circ.add(circ.mul(slope, circ.add(xa, x)), x), ya)
        rotation = geometry['rotations'][slot]
        if rotation:
            images = [frob(field, 1 << bit, rotation) for bit in range(N)]
            x = circ.linear_element(x, images)
            y = circ.linear_element(y, images)
        x2 = circ.square(x)
        row = [circ.mul(x2, y), circ.mul(x2, x), x2, x,
               circ.mul(x, y), y]
        total = circ.constant(0)
        for coordinate in range(6):
            total = circ.add(total, circ.mul(coeff[coordinate], row[coordinate]))
        circ.require_zero(circ.add(total, coeff[6]))
        inverse_wires.append((invua, invxa, invub, invxb, inverse_denominator))

    columns = {int(key): value for key, value in geometry['mask_columns'].items()}
    conflict_clauses = 0
    for left in range(6):
        for right in range(left + 1, 6):
            for a in permitted:
                cols_a = {columns[a], columns[a ^ seed]}
                code_a = sum(((a >> bit) & 1) << j for j, bit in enumerate(BITS))
                for b in permitted:
                    cols_b = {columns[b], columns[b ^ seed]}
                    if cols_a & cols_b:
                        code_b = sum(((b >> bit) & 1) << j for j, bit in enumerate(BITS))
                        literals = mismatch(code_bits[left], code_a) + mismatch(code_bits[right], code_b)
                        circ.clauses.append(' '.join(map(str, literals)) + ' 0')
                        conflict_clauses += 1
    assert conflict_clauses == 690
    assert all(source_rows[slot, state]['point'][0] != target[0]
               for slot in range(6) for state in range(160))
    assert not any(source_rows[l, a]['point'][0] == source_rows[r, b]['point'][0]
                   and not (set(source_rows[l, a]['code']) & set(source_rows[r, b]['code']))
                   for l in range(6) for r in range(l + 1, 6)
                   for a in range(160) for b in range(160))
    return circ, {'coeff': coeff, 'charts': charts, 'chart_prefix': chart_prefix,
                  'code_bits': code_bits, 'signs': signs,
                  'inverse_wires': inverse_wires,
                  'target_row': target_row,
                  'forbidden_code_clauses': forbidden,
                  'column_conflict_clauses': conflict_clauses}


def witness_control(circ, meta, geometry, implicit):
    field = previous.Field(N, [0, 3])
    initial = {}
    for j, coefficient in enumerate(previous.COEFF):
        for bit, wire in enumerate(meta['coeff'][j]):
            initial[wire] = bool(coefficient >> bit & 1)
    for j, wire in enumerate(meta['charts']):
        initial[wire] = j == 0
    for wire in meta['chart_prefix']:
        initial[wire] = True
    basis = geometry['blocks'][0]['basis']
    for item in implicit['witness_natural_signs']:
        slot, code = item['slot'], item['code']
        mask = geometry['permitted_canonical_a'][code]
        for j, bit in enumerate(BITS):
            initial[meta['code_bits'][slot][j]] = bool(mask >> bit & 1)
        initial[meta['signs'][slot][0]] = bool(item['sign_a'])
        initial[meta['signs'][slot][1]] = bool(item['sign_b'])
        u_a = 0
        for bit in range(8):
            if mask >> bit & 1:
                u_a ^= basis[bit]
        u_b = u_a ^ geometry['blocks'][0]['s']
        x_a = field.inv(u_a) ^ 1
        x_b = field.inv(u_b) ^ 1
        values = (field.inv(u_a), field.inv(x_a), field.inv(u_b),
                  field.inv(x_b), field.inv(x_a ^ x_b))
        for wires, value in zip(meta['inverse_wires'][slot], values):
            for bit, wire in enumerate(wires):
                initial[wire] = bool(value >> bit & 1)
    values = previous.replay_all_wires(circ, initial)
    result = previous.check_formula(circ, values)
    assert result['satisfied'], result
    return {'checked_assignments': len(values),
            'witness_state_ids': list(previous.WITNESS), **result}


def main():
    start = time.monotonic()
    protocol = json.loads((D / 'implicit_build_protocol.json').read_text())
    assert protocol['builder_sha256'] == sha(Path(__file__))
    assert protocol['geometry_sha256'] == sha(GEOMETRY)
    assert protocol['source_sha256'] == sha(previous.SOURCE)
    assert protocol['implicit_result_sha256'] == sha(D / 'implicit_result.json')
    implicit = json.loads((D / 'implicit_result.json').read_text())
    assert implicit['status'] == 'ALL_960_IMPLICIT_POINT_OUTPUTS_MATCH'
    target, rows = previous.load_source()
    assert list(target) == protocol['target']
    geometry = json.loads(GEOMETRY.read_text())
    circ, meta = build_circuit(target, rows, geometry)
    control = witness_control(circ, meta, geometry, implicit)
    formula = D / 'implicit_formula.xcnf'
    circ.write(formula)
    result = {'status': 'IMPLICIT_SOURCE_BUILD_AND_WITNESS_PASS',
              'protocol_sha256': sha(D / 'implicit_build_protocol.json'),
              'formula_sha256': sha(formula),
              'formula_bytes': formula.stat().st_size,
              'variables': circ.next_var - 1,
              'cnf_clauses': len(circ.clauses),
              'native_xor_rows': len(circ.xors),
              'and_gates': circ.and_count,
              'source_code_bits_per_slot': 7,
              'source_sign_bits_per_slot': 2,
              'forbidden_code_clauses': meta['forbidden_code_clauses'],
              'column_conflict_clauses': meta['column_conflict_clauses'],
              'control': control,
              'wall_s': time.monotonic() - start,
              'peak_self_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (D / 'implicit_build_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'variables', 'cnf_clauses',
                                            'native_xor_rows', 'and_gates',
                                            'formula_bytes', 'wall_s')}))


if __name__ == '__main__':
    main()
