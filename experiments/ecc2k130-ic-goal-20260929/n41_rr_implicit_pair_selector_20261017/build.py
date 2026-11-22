"""Exact N41 RR rows selected by pair code and two sign bits."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sys.path.insert(0, str(ROOT))
from vd_z_s3_sixleaf_circuit import Field, KaratsubaCircuit
from build_n131_v20_sixleaf_circuit import replay_all_wires, check_formula

SOURCE = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
N = 41
WITNESS = (12, 122, 116, 47, 128, 34)
COEFF = (1, 1200046331721, 51193325258, 197579618746,
         1789122703940, 761080510426, 107927970499)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_row(field, x, y):
    x2 = field.mul(x, x)
    return (field.mul(x2, y), field.mul(x2, x), x2, x,
            field.mul(x, y), y, 1)


def load_source():
    lines = SOURCE.read_text().splitlines()
    head = lines[0].split()
    assert head[:3] == ['ECC2K41', '6', '160']
    target = tuple(map(int, head[3:5]))
    rows = {}
    for line in lines[1:]:
        parts = line.split()
        assert parts[0] == 'S'
        slot, state = map(int, parts[1:3])
        assert (slot, state) not in rows
        rows[slot, state] = {'code': tuple(map(int, parts[7:9])),
                             'signs': tuple(map(int, parts[5:7])),
                             'point': tuple(map(int, parts[9:11]))}
    assert len(rows) == 960
    for slot in range(6):
        for code in range(40):
            group = [rows[slot, 4 * code + s] for s in range(4)]
            assert [r['signs'] for r in group] == [(0, 0), (0, 1), (1, 0), (1, 1)]
            assert len({r['code'] for r in group}) == 1
    return target, rows


def sign_anf(field, rows):
    """Coefficients for 1, sign_a, sign_b, sign_a*sign_b, per code/row."""
    table = {}
    for slot in range(6):
        for code in range(40):
            values = [point_row(field, *rows[slot, 4 * code + s]['point'])
                      for s in range(4)]
            v00, v01, v10, v11 = values
            terms = tuple(tuple(column) for column in zip(
                v00,
                tuple(a ^ b for a, b in zip(v00, v10)),
                tuple(a ^ b for a, b in zip(v00, v01)),
                tuple(a ^ b ^ c ^ d for a, b, c, d in zip(v00, v01, v10, v11))))
            for state in range(4):
                sa, sb = rows[slot, 4 * code + state]['signs']
                restored = tuple(base ^ (da if sa else 0) ^ (db if sb else 0) ^
                                 (dab if sa and sb else 0)
                                 for base, da, db, dab in terms)
                assert restored == values[state]
            table[slot, code] = terms
    return table


def require_field_linear(circ, field, coeff, row):
    terms = [[] for _ in range(N)]
    for vector, constant in zip(coeff, row):
        for bit, wire in enumerate(vector):
            image = field.mul(constant, 1 << bit)
            while image:
                low = image & -image
                terms[low.bit_length() - 1].append(wire)
                image ^= low
    for wires in terms:
        circ.require_zero([circ.xor(wires)])


def sequential_onehot(circ, options):
    assert len(options) >= 2
    flags = [circ.variable() for _ in range(len(options) - 1)]
    circ.clauses.append(' '.join(map(str, options)) + ' 0')
    circ.clauses.append(f'-{options[0]} {flags[0]} 0')
    for i in range(1, len(options) - 1):
        circ.clauses.append(f'-{options[i]} {flags[i]} 0')
        circ.clauses.append(f'-{flags[i - 1]} {flags[i]} 0')
        circ.clauses.append(f'-{options[i]} -{flags[i - 1]} 0')
    circ.clauses.append(f'-{options[-1]} -{flags[-1]} 0')
    return flags


def build(target, rows, table):
    field = Field(N, [0, 3])
    circ = KaratsubaCircuit(N, [0, 3])
    coeff = [[circ.variable() for _ in range(N)] for _ in range(7)]
    codes = [[circ.variable() for _ in range(40)] for _ in range(6)]
    signs = [[circ.variable() for _ in range(2)] for _ in range(6)]
    prefix = [sequential_onehot(circ, group) for group in codes]
    charts = [circ.variable() for _ in range(7)]
    chart_prefix = sequential_onehot(circ, charts)
    for chart, wire in enumerate(charts):
        for prior in range(chart):
            for bit in coeff[prior]:
                circ.clauses.append(f'-{wire} -{bit} 0')
        for bit, value in enumerate(coeff[chart]):
            circ.clauses.append(f'-{wire} {value if bit == 0 else -value} 0')

    code_cols = {(slot, code): set(rows[slot, 4 * code]['code'])
                 for slot in range(6) for code in range(40)}
    conflicts = 0
    for left in range(6):
        for right in range(left + 1, 6):
            for a in range(40):
                for b in range(40):
                    if code_cols[left, a] & code_cols[right, b]:
                        circ.clauses.append(f'-{codes[left][a]} -{codes[right][b]} 0')
                        conflicts += 1

    tx, ty = target
    target_row = point_row(field, tx, ty ^ tx)
    require_field_linear(circ, field, coeff, target_row)
    assert all(rows[slot, state]['point'][0] != tx
               for slot in range(6) for state in range(160))
    assert not any(rows[l, a]['point'][0] == rows[r, b]['point'][0]
                   and not (set(rows[l, a]['code']) & set(rows[r, b]['code']))
                   for l in range(6) for r in range(l + 1, 6)
                   for a in range(160) for b in range(160))

    for slot in range(6):
        sa, sb = signs[slot]
        sab = circ.and_(sa, sb)
        chosen = []
        for coordinate in range(6):
            components = []
            for term in range(4):
                bits = [circ.xor(codes[slot][code]
                                 for code in range(40)
                                 if (table[slot, code][coordinate][term] >> bit) & 1)
                        for bit in range(N)]
                components.append(bits)
            selected = [circ.xor((components[0][bit],
                                  circ.and_(sa, components[1][bit]),
                                  circ.and_(sb, components[2][bit]),
                                  circ.and_(sab, components[3][bit])))
                        for bit in range(N)]
            chosen.append(selected)
        total = circ.constant(0)
        for coordinate in range(6):
            total = circ.add(total, circ.mul(coeff[coordinate], chosen[coordinate]))
        circ.require_zero(circ.add(total, coeff[6]))
    return circ, {'coeff': coeff, 'codes': codes, 'signs': signs,
                  'prefix': prefix, 'charts': charts, 'chart_prefix': chart_prefix,
                  'target_row': target_row, 'column_conflict_clauses': conflicts}


def witness_control(circ, meta, rows):
    field = Field(N, [0, 3])
    for slot, state in enumerate(WITNESS):
        row = point_row(field, *rows[slot, state]['point'])
        value = 0
        for coefficient, entry in zip(COEFF, row):
            value ^= field.mul(coefficient, entry)
        assert value == 0
    value = 0
    for coefficient, entry in zip(COEFF, meta['target_row']):
        value ^= field.mul(coefficient, entry)
    assert value == 0
    initial = {}
    for j, coefficient in enumerate(COEFF):
        for bit, wire in enumerate(meta['coeff'][j]):
            initial[wire] = bool((coefficient >> bit) & 1)
    for slot, state in enumerate(WITNESS):
        code, remainder = divmod(state, 4)
        for j, wire in enumerate(meta['codes'][slot]):
            initial[wire] = j == code
        for j, wire in enumerate(meta['prefix'][slot]):
            initial[wire] = j >= code
        sa, sb = rows[slot, state]['signs']
        initial[meta['signs'][slot][0]] = bool(sa)
        initial[meta['signs'][slot][1]] = bool(sb)
        assert remainder == 2 * sa + sb
    for j, wire in enumerate(meta['charts']):
        initial[wire] = j == 0
    for j, wire in enumerate(meta['chart_prefix']):
        initial[wire] = True
    values = replay_all_wires(circ, initial)
    result = check_formula(circ, values)
    assert result['satisfied'], result
    return {'state_ids': WITNESS, 'coefficient_values': COEFF,
            'checked_assignments': len(values), **result}


def main():
    start = time.monotonic()
    protocol = json.loads((D / 'protocol.json').read_text())
    assert sha(SOURCE) == protocol['source_sha256']
    assert sha(Path(__file__)) == protocol['builder_sha256']
    target, rows = load_source()
    assert list(target) == protocol['target']
    table = sign_anf(Field(N, [0, 3]), rows)
    circ, meta = build(target, rows, table)
    control = witness_control(circ, meta, rows)
    formula = D / 'formula.xcnf'
    circ.write(formula)
    result = {'status': 'BUILD_AND_ALL_960_STATE_COVERAGE_PASS',
              'protocol_sha256': sha(D / 'protocol.json'),
              'formula_sha256': sha(formula),
              'formula_bytes': formula.stat().st_size,
              'variables': circ.next_var - 1,
              'cnf_clauses': len(circ.clauses),
              'native_xor_rows': len(circ.xors),
              'and_gates': circ.and_count,
              'column_conflict_clauses': meta['column_conflict_clauses'],
              'coverage_states': len(rows), 'control': control,
              'wall_s': time.monotonic() - start,
              'peak_self_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (D / 'build_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'variables', 'cnf_clauses',
                                            'native_xor_rows', 'and_gates',
                                            'formula_bytes', 'wall_s')}))


if __name__ == '__main__':
    main()
