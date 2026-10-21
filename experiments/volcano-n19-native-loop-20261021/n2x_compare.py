"""The planted arm's comparison of N2 (native trace) with Sage's own run, in plain Python.

arm_n2x.sage runs the baseline arm N's Sage path and the native pipeline on one point and
hands both to these functions; they raise Mismatch on the first difference. They live in
a .py file, never preparsed (so no literal becomes a Sage Integer: the v2 failure mode),
and the local tests (tests/test_n2x_compare.py) run them against a pure-Python model of
tau.sage's tauDlp with planted corruptions.

Everything compared is a Python int, list or None; arm_n2x.sage converts Sage objects
with int() before calling.
"""
import random


class Mismatch(Exception):
    pass


def need(cond, what):
    if not cond:
        raise Mismatch(what)


class RecRandom(random.Random):
    """random.Random with a log of the calls tauDlp makes. The stream is the parent's:
    randrange and shuffle call random.Random's own methods, and random.Random keeps its
    _randbelow (its __init_subclass__ only switches it for subclasses that define
    random() or getrandbits())."""

    def __init__(self, seed):
        self.calls = []
        super().__init__(seed)

    def randrange(self, *a, **k):
        v = super().randrange(*a, **k)
        self.calls.append(('r', int(v)))
        return v

    def shuffle(self, x):
        super().shuffle(x)
        self.calls.append(('s', [int(t) for t in x]))


def tracing_relation(inner, enc, log, rels, canonical):
    """Wrap tauRelation(cur, R, stats, shifts): record R, the shift order it saw, the shift
    systems it solved and the decomposition, and append the decomposition to rels."""
    def f(cur, R, stats, shifts):
        before = int(stats['gb_calls'])
        rel = inner(cur, R, stats, shifts)
        log.append({'R': [int(enc(R[0])), int(enc(R[1]))], 'shifts': [int(j) for j in shifts],
                    'calls': int(stats['gb_calls']) - before, 'rel': None if rel is None else canonical(rel)})
        if rel is not None:
            rels.append(rel)
        return rel
    return f


def assemble_targets(calls, log):
    """Sage's targets in order: [al, be, R or None, shifts, calls, rel or None]. The rng calls of
    one target are randrange, randrange, then shuffle iff R != 0; each shuffle is followed by one
    tauRelation call."""
    out, i, it = [], 0, iter(log)
    while i < len(calls):
        need(i + 1 < len(calls) and calls[i][0] == 'r' and calls[i + 1][0] == 'r', 'rng call pattern at %d' % i)
        al, be = calls[i][1], calls[i + 1][1]
        i += 2
        if i < len(calls) and calls[i][0] == 's':
            t = next(it, None)
            need(t is not None, 'a shuffle without a relation call')
            need(t['shifts'] == calls[i][1], 'shift order seen by tauRelation')
            out.append([al, be, t['R'], t['shifts'], t['calls'], t['rel']])
            i += 1
        else:
            out.append([al, be, None, [], 0, None])
    need(next(it, None) is None, 'relation log longer than the rng log')
    return out


def compare_setup(nat, P, reps, base, lam, Q):
    """P, Q: [x, y]; reps: [[x, y], ...] in column order; base: [[x, px, py, col, e, sign], ...]."""
    need(nat['setup']['P'] == P, 'generator P')
    need(nat['setup']['reps'] == reps, 'orbit representatives')
    need(sorted(nat['setup']['base']) == sorted(base), 'base table')
    need(nat['setup']['v_points'] == len(base) and nat['setup']['orbits'] == len(reps), 'base sizes')
    need(nat['lambda'] == lam, 'lambda')
    need(nat['Q'] == Q, 'Q')
    return {'checked_reps': len(reps), 'checked_base_entries': len(base)}


def compare_targets(nat, targets, counts, recovered, rels):
    """targets from assemble_targets; counts: targets, gb_calls, spurious, relations, log (ints);
    rels: Sage's decompositions as [[c, s, e], [c, s, e]] lists."""
    need(len(targets) == len(nat['targets']) == counts['targets'], 'number of targets')
    out = {'checked_targets': 0, 'checked_calls': 0, 'checked_relations': 0}
    for k, (a, b) in enumerate(zip(targets, nat['targets'])):
        need(a == b, 'target %d: sage %r native %r' % (k, a, b))
        out['checked_targets'] += 1
        out['checked_calls'] += a[4]
        out['checked_relations'] += a[5] is not None
    for f in ('targets', 'gb_calls', 'spurious', 'relations', 'log'):
        need(nat['counts'][f] == counts[f], 'count ' + f)
    need(out['checked_calls'] == counts['gb_calls'], 'calls per target sum to gb_calls')
    need(nat['recovered'] is True and recovered is True, 'recovered')
    need(nat['relations_raw'] == rels, 'ordered relations')
    return out


def rows_and_rhs(targets, lam, p, h):
    """tauDlp's matrix rows (column -> sum sign lam^e mod p, insertion order) and rhs
    (h al mod p, h be mod p), from the assembled targets, as Python ints."""
    rows, rhs = [], []
    for al, be, _, _, _, rel in targets:
        if rel is None:
            continue
        row = {}
        for col, sign, e in rel:
            row[col] = (row.get(col, 0) + sign * pow(lam, e, p)) % p
        rows.append(row)
        rhs.append((h * al % p, h * be % p))
    used = sorted({c for r in rows for c in r})
    return rows, rhs, used


def compare_kernel(nat, used, basis, kidx, log):
    """basis: Sage's M.left_kernel().basis() as lists of ints; kidx: index of the first vector
    with B != 0; log: the log it gives."""
    need(used == nat['used_cols'], 'used columns')
    need(basis == nat['kernel_basis'], 'left kernel echelon basis')
    need(kidx == nat['kernel_index'] and log is not None and log == nat['counts']['log'], 'kernel index and log')
    return {'checked_kernel_vectors': len(basis), 'checked_kernel_entries': sum(len(v) for v in basis),
            'kernel_dimension': len(basis), 'kernel_index': kidx}
