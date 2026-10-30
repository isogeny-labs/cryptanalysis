"""Generate exact finite certificates around four first-hit rank gates."""
import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent.parent
PLAN = json.loads((ROOT / 'inputs.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (REPO / item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    return json.loads(raw)


def row(item):
    return {int(k): int(v) for k, v in item['row'].items() if v}


def choose(rows, p):
    basis, selected = {}, []
    for original in rows:
        work = {j: x % p for j, x in original.items() if x % p}
        while work:
            j = min(work)
            if j not in basis:
                z = work[j]
                basis[j] = {k: x * pow(z, -1, p) % p for k, x in work.items()}
                selected.append(original)
                break
            z = work[j]
            for k, x in basis[j].items():
                y = (work.get(k, 0) - z * x) % p
                if y:
                    work[k] = y
                else:
                    work.pop(k, None)
    return selected


def integer_kernel(rows):
    matrix = [[Fraction(r.get(j, 0)) for j in range(40)] for r in rows]
    pivots = []
    for col in range(40):
        i = len(pivots)
        pivot = next((k for k in range(i, len(matrix)) if matrix[k][col]), None)
        if pivot is None:
            continue
        matrix[i], matrix[pivot] = matrix[pivot], matrix[i]
        z = matrix[i][col]
        matrix[i] = [x/z for x in matrix[i]]
        for k in range(len(matrix)):
            if k != i and matrix[k][col]:
                z = matrix[k][col]
                matrix[k] = [x-z*y for x, y in zip(matrix[k], matrix[i])]
        pivots.append(col)
    free = next(j for j in range(40) if j not in pivots)
    v = [Fraction(0)] * 40
    v[free] = 1
    for i, col in enumerate(pivots):
        v[col] = -matrix[i][free]
    scale = math.lcm(*(x.denominator for x in v))
    result = [int(x*scale) for x in v]
    assert result[free] == scale and all(sum(r.get(j, 0)*result[j] for j in range(40)) == 0 for r in rows)
    return result


def inverse(matrix, p):
    n = len(matrix)
    work = [[x % p for x in r] + [int(i == j) for j in range(n)] for i, r in enumerate(matrix)]
    for j in range(n):
        i = next(i for i in range(j, n) if work[i][j])
        work[i], work[j] = work[j], work[i]
        z = pow(work[j][j], -1, p)
        work[j] = [x*z % p for x in work[j]]
        for i in range(n):
            if i != j and work[i][j]:
                z = work[i][j]
                work[i] = [(x-z*y) % p for x, y in zip(work[i], work[j])]
    return [r[n:] for r in work]


def literal(xs):
    return '[' + ', '.join(map(str, xs)) + ']'


def matrix(xs):
    return '[\n' + ',\n'.join('  ' + literal(r) for r in xs) + '\n]'


def emit(order, label, count, base, direct, hecke, source_order):
    fixed = base + (direct if label == 'support4_plus_direct5' else [])
    def rows_at(n):
        seen = set(source_order[:n])
        return fixed + [row(x) for x in hecke if set(x['sources']) <= seen]
    before, after = rows_at(count-1), rows_at(count)
    kernel = integer_kernel(before)
    modulus = next(p for p in (3, 5, 7, 11, 101, 103, 107) if len(choose(after, p)) == 40)
    selected = choose(after, modulus)
    minor = [[r.get(j, 0) % modulus for j in range(40)] for r in selected]
    inv = inverse(minor, modulus)
    assert all(sum(minor[i][k]*inv[k][j] for k in range(40)) % modulus == int(i == j)
               for i in range(40) for j in range(40))
    name = 'Gate' + order.capitalize() + ('Direct' if label.endswith('direct5') else 'Base')
    chunks = [before[i:i+32] for i in range(0, len(before), 32)]
    lines = ['module', '', 'public import Init', '', 'namespace ' + name,
             'set_option maxRecDepth 65536', 'set_option maxHeartbeats 0',
             'public def kernel : List Int := ' + literal(kernel),
             'public def dot (a b : List Int) : Int := (a.zip b).foldl (fun s x => s + x.1 * x.2) 0']
    for i, chunk in enumerate(chunks):
        lines += [f'public def prior{i} : List (List Int) := ' + matrix([[r.get(j, 0) for j in range(40)] for r in chunk]),
                  f'public theorem prior{i}_annihilated : prior{i}.all (fun r => dot r kernel == 0) = true := by decide']
    lines += ['public theorem kernel_nonzero : kernel.any (· != 0) = true := by decide',
              'public def selected : List (List Nat) := ' + matrix(minor),
              'public def inverse : List (List Nat) := ' + matrix(inv),
              f'public theorem inverse_certificate : ∀ i j : Fin 40,',
              f'  ((List.range 40).foldl (fun s k => s + (selected.getD i.val []).getD k 0 * (inverse.getD k []).getD j.val 0) 0) % {modulus} =',
              '  if i.val == j.val then 1 else 0 := by decide',
              '#print axioms kernel_nonzero']
    lines += [f'#print axioms prior{i}_annihilated' for i in range(len(chunks))]
    lines += ['#print axioms inverse_certificate', 'end ' + name, '']
    (HERE / (name + '.lean')).write_text('\n'.join(lines))
    return {'module': name, 'order': order, 'baseline': label, 'previous_prefix': count-1,
            'first_hit_prefix': count, 'previous_rows': len(before), 'terminal_rows': len(after),
            'auxiliary_prime': modulus, 'kernel_nonzero_coordinate': next(i for i, x in enumerate(kernel) if x)}


def main():
    cls = next(x for x in pinned('class')['cases'] if x['p'] == PLAN['p'])
    support4 = next(x for x in pinned('support4')['cases'] if x['p'] == PLAN['p'])
    support5 = pinned('support5')['arms']
    base = [row(x) for x in cls['base_rows'] + support4['direct_candidates'] + support4['hecke_candidates']]
    direct = [row(x) for x in support5['direct']['candidates']]
    hecke = support5['hecke']['candidates']
    out = []
    for order in PLAN['orders']:
        run = json.loads((ROOT / f'run-{order}.json').read_text())
        source_order = cls['ascending_order' if order == 'ascending' else 'priority_order']
        for label, count in run['stop_source_counts'].items():
            out.append(emit(order, label, count, base, direct, hecke, source_order))
    (HERE / 'certificates.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps(out))


if __name__ == '__main__':
    main()
