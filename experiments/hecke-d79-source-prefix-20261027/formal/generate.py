"""Generate finite Lean certificates for first-hit prefix rank claims."""
import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = BASE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def pinned(path, digest):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    return json.loads(raw)


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


def independent(rows, modulus):
    pivots, chosen = {}, []
    for r in rows:
        v = {i: x % modulus for i, x in r.items() if x % modulus}
        while v:
            i = min(v)
            if i not in pivots:
                z = v[i]
                pivots[i] = {j: x*pow(z, -1, modulus) % modulus for j, x in v.items()}
                chosen.append(r)
                break
            z = v[i]
            for j, x in pivots[i].items():
                y = (v.get(j, 0) - z*x) % modulus
                if y:
                    v[j] = y
                else:
                    v.pop(j, None)
    return chosen


def minor_inverse(rows, modulus):
    n = len(rows)
    M = [[r.get(j, 0) % modulus for j in range(40)] for r in rows]
    pivots = []
    rank = 0
    for col in range(40):
        pivot = next((i for i in range(rank, n) if M[i][col]), None)
        if pivot is None:
            continue
        M[rank], M[pivot] = M[pivot], M[rank]
        z = pow(M[rank][col], -1, modulus)
        M[rank] = [x*z % modulus for x in M[rank]]
        for i in range(n):
            if i != rank and M[i][col]:
                z = M[i][col]
                M[i] = [(a-z*b) % modulus for a, b in zip(M[i], M[rank])]
        pivots.append(col)
        rank += 1
    assert rank == n
    minor = [[r.get(j, 0) % modulus for j in pivots] for r in rows]
    A = [r[:] + [int(i == j) for j in range(n)] for i, r in enumerate(minor)]
    for col in range(n):
        pivot = next(i for i in range(col, n) if A[i][col])
        A[col], A[pivot] = A[pivot], A[col]
        z = pow(A[col][col], -1, modulus)
        A[col] = [x*z % modulus for x in A[col]]
        for i in range(n):
            if i != col and A[i][col]:
                z = A[i][col]
                A[i] = [(a-z*b) % modulus for a, b in zip(A[i], A[col])]
    inverse = [r[n:] for r in A]
    assert all(sum(minor[i][k]*inverse[k][j] for k in range(n)) % modulus == int(i == j)
               for i in range(n) for j in range(n))
    return pivots, minor, inverse


def rational_kernel(rows):
    M = [[Fraction(r.get(j, 0)) for j in range(40)] for r in rows]
    rank = 0
    pivots = []
    for col in range(40):
        pivot = next((i for i in range(rank, len(M)) if M[i][col]), None)
        if pivot is None:
            continue
        M[rank], M[pivot] = M[pivot], M[rank]
        z = M[rank][col]
        M[rank] = [x/z for x in M[rank]]
        for i in range(len(M)):
            if i != rank and M[i][col]:
                z = M[i][col]
                M[i] = [x-z*y for x, y in zip(M[i], M[rank])]
        pivots.append(col)
        rank += 1
    assert rank == 39
    free = next(i for i in range(40) if i not in pivots)
    v = [Fraction(0) for _ in range(40)]
    v[free] = 1
    for i, pivot in enumerate(pivots):
        v[pivot] = -M[i][free]
    den = math.lcm(*(x.denominator for x in v))
    out = [int(den*x) for x in v]
    assert out[free] == den > 0
    assert all(sum(r.get(i, 0)*out[i] for i in range(40)) == 0 for r in rows)
    return out


def lit(xs):
    return '[' + ', '.join(map(str, xs)) + ']'


def mat(rows):
    return '[\n' + '\n'.join('  ' + lit(r) + (',' if i+1 < len(rows) else '')
                           for i, r in enumerate(rows)) + '\n]'


def module(case):
    p, q, aux = case['p'], case['q'], case['auxiliary_prime']
    parent = REPO / f'experiments/hecke-d79-remaining-five-20261027/p{p}'
    receipt = pinned(BASE / f'p{p}-result.json', case['prefix_result_sha256'])
    audit = pinned(BASE / f'p{p}-audit-v2.json', case['prefix_audit_sha256'])
    producer = pinned(parent / 'result.json', case['parent_producer_sha256'])
    analysis = pinned(parent / 'analysis.json', case['parent_analysis_sha256'])
    qlog = pinned(parent / 'q-log-audit.json', case['parent_q_log_sha256'])
    assert audit['status'] == qlog['status'] == 'PASS'
    assert receipt['status'] == 'RANK40_STOP' and audit['source_count'] == receipt['stop_source_count']
    base = [row(x['row']) for x in producer['base_rows']]
    direct = [row(x['row']) for x in analysis['direct']['candidates']]
    candidates = [row(x['row']) for x in receipt['candidates']]
    all_rows = base + direct + candidates
    pre_rows = base + direct + [row(x['row']) for x in receipt['candidates']
                                if max(x['sources']) < receipt['stop_source_count'] - 1]
    assert len(independent(pre_rows, aux)) == 39
    assert len(independent(all_rows, q)) == 39
    assert len(independent(all_rows, aux)) == 40
    kernel = rational_kernel(pre_rows)
    logs = qlog['class_point_logs']
    assert len(logs) == 40 and any(logs)
    assert all(sum(r.get(i, 0)*logs[i] for i in range(40)) % q == 0 for r in all_rows)
    ns = f'RankPrefixP{p}'
    lines = ['module', '', 'public import Init', '', f'namespace {ns}', '',
             'set_option maxRecDepth 65536', 'set_option maxHeartbeats 0', '',
             'public def entry (M : List (List Nat)) (i j : Nat) : Nat :=',
             '  (M.getD i []).getD j 0', '',
             f'public def allRowsQ : List (List Nat) := {mat([[r.get(i,0)%q for i in range(40)] for r in all_rows])}',
             f'public def qLogs : List Nat := {lit(logs)}',
             'public def dotQ (a b : List Nat) : Nat :=',
             f'  ((a.zip b).foldl (fun s x => s + x.1 * x.2) 0) % {q}',
             'public theorem q_logs_annihilate_all_rows :',
             '    allRowsQ.all (fun r => dotQ r qLogs == 0) = true := by decide',
             'public theorem q_logs_nonzero : qLogs.any (fun x => x != 0) = true := by decide', '',
             f'public def preRowsZ : List (List Int) := {mat([[r.get(i,0) for i in range(40)] for r in pre_rows])}',
             f'public def preRowsQ : List (List Nat) := {mat([[r.get(i,0)%q for i in range(40)] for r in pre_rows])}',
             f'public def preKernelZ : List Int := {lit(kernel)}',
             'public def dotZ (a b : List Int) : Int :=',
             '  (a.zip b).foldl (fun s x => s + x.1 * x.2) 0',
             'public theorem pre_rows_annihilate_integer_kernel :',
             '    preRowsZ.all (fun r => dotZ r preKernelZ == 0) = true := by decide',
             f'public theorem pre_kernel_nonzero : preKernelZ.any (fun x => x != 0) = true := by decide', '']
    for label, modulus, expected in [('q', q, 39), ('aux', aux, 40)]:
        chosen = independent(all_rows, modulus)
        assert len(chosen) == expected
        if label == 'q':
            assert all(r in pre_rows for r in chosen)
        pivots, minor, inverse = minor_inverse(chosen, modulus)
        n = expected
        lines += [f'public def {label}SelectedRows : List (List Nat) := {mat([[r.get(i,0)%modulus for i in range(40)] for r in chosen])}',
                  f'public def {label}AllRows : List (List Nat) := {mat([[r.get(i,0)%modulus for i in range(40)] for r in all_rows])}',
                  f'public theorem {label}_selected_in_all :',
                  f'    {label}SelectedRows.all (fun r => {label}AllRows.contains r) = true := by decide',
                  f'public def {label}Pivots : List Nat := {lit(pivots)}',
                  f'public def {label}Minor : List (List Nat) := {mat(minor)}',
                  f'public def {label}Inverse : List (List Nat) := {mat(inverse)}',
                  f'public theorem {label}_minor_matches : ∀ i j : Fin {n},',
                  f'    entry {label}Minor i.val j.val =',
                  f'      entry {label}SelectedRows i.val ({label}Pivots.getD j.val 0) := by decide',
                  f'public theorem {label}_inverse_certificate : ∀ i j : Fin {n},',
                  f'    ((List.range {n}).foldl (fun total k =>',
                  f'      total + entry {label}Minor i.val k * entry {label}Inverse k j.val) 0) % {modulus} =',
                  '      if i.val == j.val then 1 else 0 := by decide', '']
        if label == 'q':
            lines += ['public theorem q_selected_in_pre :',
                      '    qSelectedRows.all (fun r => preRowsQ.contains r) = true := by decide', '']
    lines += ['#print axioms q_logs_annihilate_all_rows', '#print axioms q_logs_nonzero',
              '#print axioms pre_rows_annihilate_integer_kernel',
              '#print axioms pre_kernel_nonzero',
              '#print axioms q_selected_in_all', '#print axioms q_selected_in_pre', '#print axioms q_minor_matches',
              '#print axioms q_inverse_certificate', '#print axioms aux_selected_in_all',
              '#print axioms aux_minor_matches', '#print axioms aux_inverse_certificate',
              '', f'end {ns}', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for case in PLAN['cases']:
        p = case['p']
        path = HERE / f'RankPrefixP{p}.lean'
        content = module(case)
        if args.write:
            path.write_text(content)
        else:
            assert path.read_text() == content
        print('PREFIX_FORMAL_PASS', p, len(content))


if __name__ == '__main__':
    main()
