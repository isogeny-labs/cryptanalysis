"""Generate finite kernel and minor certificates for p68437 support-five ranks."""
import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent.parent
PLAN = json.loads((ROOT / 'inputs.json').read_text())
POST = json.loads((ROOT / 'post_run.json').read_text())
POST_AUDIT = json.loads((ROOT / 'post_audit.json').read_text())
RESULT_RAW = (ROOT / 'result.json').read_bytes()
AUDIT_RAW = (ROOT / 'audit.json').read_bytes()
if hashlib.sha256(RESULT_RAW).hexdigest() != POST['result_sha256']:
    raise ValueError('RESULT_PIN_MISMATCH')
if hashlib.sha256(AUDIT_RAW).hexdigest() != POST_AUDIT['audit_sha256']:
    raise ValueError('AUDIT_PIN_MISMATCH')
RESULT = json.loads(RESULT_RAW)
AUDIT = json.loads(AUDIT_RAW)
if AUDIT['status'] != 'PASS':
    raise ValueError('AUDIT_NOT_PASS')

def parent(name):
    item = PLAN['frozen'][name]
    raw = (REPO / item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('PARENT_PIN_MISMATCH:' + name)
    return json.loads(raw)

CLASSES = parent('class-result.json')
ANALYSIS = parent('analysis.json')

def row(raw):
    return {int(k): int(v) for k, v in raw.items() if v}

def independent(rows, p):
    pivots, choice = {}, []
    for r in rows:
        v = {i: x % p for i, x in r.items() if x % p}
        while v:
            i = min(v)
            if i not in pivots:
                z = v[i]
                pivots[i] = {j: x*pow(z, -1, p) % p for j, x in v.items()}
                choice.append(r)
                break
            z = v[i]
            for j, x in pivots[i].items():
                y = (v.get(j, 0)-z*x) % p
                if y:
                    v[j] = y
                else:
                    v.pop(j, None)
    return choice


def minor_inverse(rows, p):
    n = len(rows)
    M = [[r.get(j, 0) % p for j in range(40)] for r in rows]
    pivots = []
    rank = 0
    for col in range(40):
        pivot = next((i for i in range(rank, n) if M[i][col]), None)
        if pivot is None:
            continue
        M[rank], M[pivot] = M[pivot], M[rank]
        inv = pow(M[rank][col], -1, p)
        M[rank] = [x*inv % p for x in M[rank]]
        for i in range(n):
            if i != rank and M[i][col]:
                z = M[i][col]
                M[i] = [(a-z*b) % p for a, b in zip(M[i], M[rank])]
        pivots.append(col)
        rank += 1
    assert rank == n
    minor = [[r.get(col, 0) % p for col in pivots] for r in rows]
    A = [r[:] + [int(i == j) for j in range(n)] for i, r in enumerate(minor)]
    for col in range(n):
        pivot = next(i for i in range(col, n) if A[i][col])
        A[col], A[pivot] = A[pivot], A[col]
        inv = pow(A[col][col], -1, p)
        A[col] = [x*inv % p for x in A[col]]
        for i in range(n):
            if i != col and A[i][col]:
                z = A[i][col]
                A[i] = [(a-z*b) % p for a, b in zip(A[i], A[col])]
    inverse = [r[n:] for r in A]
    assert all(sum(minor[i][k]*inverse[k][j] for k in range(n)) % p == int(i == j)
               for i in range(n) for j in range(n))
    return pivots, minor, inverse, M


def modular_kernels(rows, modulus):
    chosen = independent(rows, modulus)
    pivots, _, _, reduced = minor_inverse(chosen, modulus)
    free = [i for i in range(40) if i not in pivots]
    vectors = []
    for column in free:
        v = [0]*40
        v[column] = 1
        for r, pivot in enumerate(pivots):
            v[pivot] = -reduced[r][column] % modulus
        vectors.append(v)
    assert all(sum(r.get(i, 0)*v[i] for i in range(40)) % modulus == 0
               for r in rows for v in vectors)
    return free, vectors


def rational_kernels(rows):
    M = [[Fraction(r.get(j, 0)) for j in range(40)] for r in rows]
    pivots = []
    rank = 0
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
    free = [i for i in range(40) if i not in pivots]
    vectors = []
    for column in free:
        v = [Fraction(0) for _ in range(40)]
        v[column] = 1
        for r, pivot in enumerate(pivots):
            v[pivot] = -M[r][column]
        den = math.lcm(*(x.denominator for x in v))
        vector = [int(den*x) for x in v]
        assert vector[column] == den and den > 0
        vectors.append(vector)
    assert all(sum(r.get(i, 0)*v[i] for i in range(40)) == 0
               for r in rows for v in vectors)
    return rank, free, vectors


def lit(xs):
    return "[" + ", ".join(map(str, xs)) + "]"


def mat(xs):
    return "[\n" + "\n".join("  " + lit(r) + ("," if i+1 < len(xs) else "")
                              for i, r in enumerate(xs)) + "\n]"



def rows_for_case(p, label):
    case = next(x for x in CLASSES['cases'] if x['p'] == p)
    analysis = next(x for x in ANALYSIS['cases'] if x['p'] == p)
    rows = [row(x['row']) for x in case['base_rows']]
    rows += [row(x['row']) for x in analysis['direct_candidates']]
    rows += [row(x['row']) for x in analysis['hecke_candidates']]
    if label in ('direct', 'both'):
        rows += [row(x['row']) for x in RESULT['arms']['direct']['candidates']]
    if label in ('hecke', 'both'):
        rows += [row(x['row']) for x in RESULT['arms']['hecke']['candidates']]
    return rows, case['largest_prime_factor']

def emit(p, label, auxiliary):
    rows, q = rows_for_case(p, label)
    qchoice = independent(rows, q)
    auxchoice = independent(rows, auxiliary)
    rankz, freez, kernelsz = rational_kernels(rows)
    if len(auxchoice) != rankz or len(qchoice) > rankz:
        raise ValueError('RANK_CERTIFICATE_MISMATCH')
    freeq, kernelsq = modular_kernels(rows, q)
    name = 'RankP' + str(p) + label.capitalize()
    lines = ['module', '', 'public import Init', '', 'namespace ' + name, '',
             'set_option maxRecDepth 65536', 'set_option maxHeartbeats 0', '',
             'public def entry (M : List (List Nat)) (i j : Nat) : Nat :=',
             '  (M.getD i []).getD j 0',
             'public def entryZ (M : List (List Int)) (i j : Nat) : Int :=',
             '  (M.getD i []).getD j 0', '']
    lines += ['public def allRowsQ : List (List Nat) := ' +
              mat([[r.get(i, 0) % q for i in range(40)] for r in rows]),
              'public def kernelsQ : List (List Nat) := ' + mat(kernelsq),
              'public def freeQ : List Nat := ' + lit(freeq),
              'public def dotQ (a b : List Nat) : Nat :=',
              f'  ((a.zip b).foldl (fun s x => s + x.1 * x.2) 0) % {q}',
              'public theorem all_rows_annihilate_q_kernels :',
              '    kernelsQ.all (fun k => allRowsQ.all (fun r => dotQ r k == 0)) = true := by decide',
              f'public theorem q_kernels_free_identity : ∀ i j : Fin {len(freeq)},',
              '    entry kernelsQ i.val (freeQ.getD j.val 0) =',
              '      if i.val == j.val then 1 else 0 := by decide', '']
    if kernelsz:
        chunked = len(rows) > 500 and len(kernelsz) == 1
        if chunked:
            lines += ['public def kernelZ : List Int := ' + lit(kernelsz[0]),
                      'public def kernelsZ : List (List Int) := [kernelZ]']
        else:
            lines += ['public def kernelsZ : List (List Int) := ' + mat(kernelsz)]
        lines += ['public def freeZ : List Nat := ' + lit(freez),
                  'public def dotZ (a b : List Int) : Int :=',
                  '  (a.zip b).foldl (fun s x => s + x.1 * x.2) 0']
        if chunked:
            chunks = [rows[i:i+32] for i in range(0, len(rows), 32)]
            for i, chunk in enumerate(chunks):
                lines += [f'public def zChunk{i} : List (List Int) := ' +
                          mat([[r.get(j, 0) for j in range(40)] for r in chunk]),
                          f'public theorem zChunk{i}_checked :',
                          f'    zChunk{i}.all (fun r => dotZ r kernelZ == 0) = true := by decide']
            lines += ['public def allRowsZ : List (List Int) := ' +
                      ' ++ '.join(f'zChunk{i}' for i in range(len(chunks))),
                      'public theorem all_rows_annihilate_z_kernels :',
                      '    kernelsZ.all (fun k => allRowsZ.all (fun r => dotZ r k == 0)) = true := by',
                      '  simp [kernelsZ, allRowsZ, List.all_append, ' +
                      ', '.join(f'zChunk{i}_checked' for i in range(len(chunks))) + ']']
        else:
            lines += ['public def allRowsZ : List (List Int) := ' +
                      mat([[r.get(i, 0) for i in range(40)] for r in rows]),
                      'public theorem all_rows_annihilate_z_kernels :',
                      '    kernelsZ.all (fun k => allRowsZ.all (fun r => dotZ r k == 0)) = true := by decide']
        lines += [f'public theorem z_kernels_free_diagonal : ∀ i j : Fin {len(freez)},',
                  '    entryZ kernelsZ i.val (freeZ.getD j.val 0) =',
                  '      if i.val == j.val then entryZ kernelsZ i.val (freeZ.getD i.val 0) else 0 := by decide',
                  f'public theorem z_kernels_diagonal_nonzero : ∀ i : Fin {len(freez)},',
                  '    entryZ kernelsZ i.val (freeZ.getD i.val 0) ≠ 0 := by decide', '']
    for mod, choice, suffix in ((q, qchoice, 'Q'), (auxiliary, auxchoice, 'Aux')):
        n = len(choice)
        pivots, minor, inverse, _ = minor_inverse(choice, mod)
        lines += [f'public def selected{suffix} : List (List Nat) := ' +
                  mat([[r.get(i, 0) % mod for i in range(40)] for r in choice])]
        if suffix != 'Q':
            lines += [f'public def allRows{suffix} : List (List Nat) := ' +
                      mat([[r.get(i, 0) % mod for i in range(40)] for r in rows])]
        lines += [f'public theorem selected{suffix}_in_all :',
                  f'    selected{suffix}.all (fun r => allRows{suffix}.contains r) = true := by decide',
                  f'public def pivots{suffix} : List Nat := ' + lit(pivots),
                  f'public def minor{suffix} : List (List Nat) := ' + mat(minor),
                  f'public def inverse{suffix} : List (List Nat) := ' + mat(inverse),
                  f'public theorem minor{suffix}_matches : ∀ i j : Fin {n},',
                  f'    entry minor{suffix} i.val j.val =',
                  f'      entry selected{suffix} i.val (pivots{suffix}.getD j.val 0) := by decide',
                  f'public theorem inverse{suffix}_certificate : ∀ i j : Fin {n},',
                  f'    ((List.range {n}).foldl (fun total k =>',
                  f'      total + entry minor{suffix} i.val k * entry inverse{suffix} k j.val) 0) % {mod} =',
                  '      if i.val == j.val then 1 else 0 := by decide', '']
    names = ['all_rows_annihilate_q_kernels', 'q_kernels_free_identity']
    if kernelsz:
        names += ['all_rows_annihilate_z_kernels', 'z_kernels_free_diagonal',
                  'z_kernels_diagonal_nonzero']
    names += [f'{stem}{suffix}' for suffix in ('Q', 'Aux')
              for stem in ('selected', 'minor', 'inverse')]
    for theorem in names:
        if theorem.startswith('selected'):
            theorem += '_in_all'
        elif theorem.startswith('minor'):
            theorem += '_matches'
        elif theorem.startswith('inverse'):
            theorem += '_certificate'
        lines.append('#print axioms ' + theorem)
    lines += ['', 'end ' + name, '']
    text = '\n'.join(lines)
    target = HERE / (name + '.lean')
    if ARGS.write:
        target.write_text(text)
    elif target.read_text() != text:
        raise ValueError('GENERATED_MODULE_MISMATCH:' + name)
    print(name, 'rows', len(rows), 'rankQ', len(qchoice), 'rankZ', rankz)

parser = argparse.ArgumentParser()
parser.add_argument('--write', action='store_true')
ARGS = parser.parse_args()
emit(68437, 'direct', 3)
emit(68437, 'hecke', 11)
emit(68437, 'both', 11)
