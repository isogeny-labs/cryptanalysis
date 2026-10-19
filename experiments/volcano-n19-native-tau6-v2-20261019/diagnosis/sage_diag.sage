# Untimed Sage diagnostic for run 39307409409's S0 failure and for protocol v2.
#
#   sage diagnosis/sage_diag.sage --lib libtau6native.so --out sage_diag.json
#
# Records, per shift system, Sage's variety (tau.sage TauField.system + ideal +
# groebner_basis + variety, in Sage's order), the native variety through the
# v2 binding (modulus read lowest degree first), the native variety through
# the v1 binding's modulus (read highest degree first: the reciprocal), and,
# for the S0 sets, a direct S3 evaluation in Sage's field on all 4,096 pairs.
# Sets:
#   s0_v1  the 300 systems of v1 S0 (seed 'volcano-n19-native-tau6-20261019:selftest');
#   s0_v2  the 307 systems of v2 S0 (the 7 v1 mismatches, then seed
#          'volcano-n19-native-tau6-v2-20261019:selftest');
#   multi  every system with two or more solutions (diagnosis/multi_systems.json),
#          for Sage's order of a multi-solution variety.
# No interval is timed; nothing here is a measurement.

import json
import os
import random
import sys

MYDIR = os.path.dirname(os.path.abspath(sys.argv[0]))
V2 = os.path.dirname(MYDIR)
VIC = os.path.join(os.path.dirname(V2), 'volcano-ic')
_argv = sys.argv
sys.argv = [os.path.join(VIC, 'run.sage')]
load(os.path.join(VIC, 'run.sage'))
sys.argv = _argv
load(os.path.join(VIC, 'tau.sage'))
sys.path.insert(0, V2)
import native_binding as nb

a = sys.argv[1:]
LIB = os.path.abspath(a[a.index('--lib') + 1])
OUT = a[a.index('--out') + 1]

V1_S0_MISMATCHES = [(14743, 17), (400912, 3), (465769, 4), (59034, 9), (453846, 18), (480552, 5), (486489, 8)]


def v1_modulus(bits):
    """v1 arm.sage Native.__init__, verbatim."""
    mod = 0
    for i, c in enumerate(bits):
        if c:
            mod |= 1 << (len(bits) - 1 - i)
    return int(mod)


def sage_variety(fld, j, xR, b):
    """v1 arm.sage sage_variety (= tau.sage tauRelation's solve), verbatim."""
    polys = [f for f in fld.system(j, xR, b) if f != 0]
    I = ideal(polys)
    gb = I.groebner_basis()
    sols = I.variety() if gb != [1] else []
    out = []
    for sol in sols:
        ub = sum(int(sol[g]) << i for i, g in enumerate(fld.u))
        wb = sum(int(sol[g]) << i for i, g in enumerate(fld.w))
        out.append((int(ub), int(wb)))
    return out


def third_sage(F, xR, j, k=6):
    z = F.gen()
    xs = [sum((z ** i for i in range(k) if (c >> i) & 1), F(0)) for c in range(1 << k)]
    x2s = [x ** (2 ** j) for x in xs]
    x2sq = [x * x for x in x2s]
    xR2, one = xR * xR, F(1)
    out = []
    for u, x1 in enumerate(xs):
        x1sq = x1 * x1
        for w, x2 in enumerate(x2s):
            p = x1 * x2
            if p * p + xR2 * (x1sq + x2sq[w]) + xR * p + one == 0:
                out.append((u, w))
    return out


fld = TauField(N_BITS, MODULUS, 6)
F = fld.F
modF = int(sum(int(c) << int(i) for i, c in enumerate(F.modulus().list())))
fixed = nb.Native(LIB, N_BITS, nb.modulus_int(MODULUS), 6)
v1 = nb.Native(LIB, N_BITS, v1_modulus(MODULUS), 6)
enc = lambda e: int(e.to_integer()) if hasattr(e, 'to_integer') else int(ZZ(e.polynomial().change_ring(ZZ)(2)))

rng1 = random.Random('volcano-n19-native-tau6-20261019:selftest')
s0_v1 = [(int(rng1.randrange(1, 2 ** N_BITS)), int(t % N_BITS)) for t in range(300)]
rng2 = random.Random('volcano-n19-native-tau6-v2-20261019:selftest')
s0_v2 = list(V1_S0_MISMATCHES) + [(int(rng2.randrange(1, 2 ** N_BITS)), int(t % N_BITS)) for t in range(300)]
multi = [(int(x), int(j)) for x, j, _ in json.load(open(os.path.join(MYDIR, 'multi_systems.json')))['systems']]


def run(systems, with_third):
    rows = []
    for xr, j in systems:
        xR = F.from_integer(xr)
        assert enc(xR) == xr
        r = {'xR': xr, 'j': j, 'sage': sage_variety(fld, j, xR, F(1)),
             'native_fixed': fixed.solve(xr, j), 'native_v1': v1.solve(xr, j)}
        if with_third:
            r['third'] = third_sage(F, xR, j)
        rows.append(r)
    return rows


res = {'sage_version': str(version()), 'modulus_sage': modF, 'modulus_fixed_binding': fixed.modulus(),
       'modulus_v1_binding': v1.modulus(), 'lib': LIB}
for name, systems, th in (('s0_v1', s0_v1, True), ('s0_v2', s0_v2, True), ('multi', multi, False)):
    rows = run(systems, th)
    S = lambda x: sorted(map(tuple, x))
    summ = {'systems': len(rows),
            'sage_eq_native_v1': sum(S(r['sage']) == S(r['native_v1']) for r in rows),
            'sage_eq_native_fixed': sum(S(r['sage']) == S(r['native_fixed']) for r in rows),
            'sage_nonempty': sum(bool(r['sage']) for r in rows),
            'sage_multi': sum(len(r['sage']) > 1 for r in rows),
            'sage_order_eq_native_fixed_order': sum([tuple(x) for x in r['sage']] == [tuple(x) for x in r['native_fixed']]
                                                    for r in rows)}
    if th:
        summ['sage_eq_third'] = sum(S(r['sage']) == S(r['third']) for r in rows)
        summ['native_fixed_eq_third'] = sum(S(r['native_fixed']) == S(r['third']) for r in rows)
        summ['mismatch_sage_vs_v1'] = [r for r in rows if S(r['sage']) != S(r['native_v1'])]
    res[name] = {'summary': summ, 'rows': rows}
    print(name, json.dumps(summ, default=str), flush=True)
json.dump(res, open(OUT, 'w'), separators=(',', ':'), default=str)
