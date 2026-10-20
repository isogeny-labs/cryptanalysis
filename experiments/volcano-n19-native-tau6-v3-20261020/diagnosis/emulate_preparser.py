"""Local emulation of v2's crash (no Sage; cloud-agent VM). Not timing evidence.

    python3 diagnosis/emulate_preparser.py --lib PATH/libtau6native.so --out diagnosis/emulate_preparser.json

The exact reproduction runs in the pinned Sage image (diagnosis/digest_repro.sage,
the v3 workflow's untimed sage-smoke job). This script shows the same failure
without Sage, from v2's own source:

1. The relations of a real point. v1's pure-Python tauDlp replay
   (local_replay.py) with the v2/v3 binding on v2 point p00 (whose B and N rows
   crashed in run 39376405326) records every relation it returns.
2. v2's `relation_digests`, taken verbatim from v2 arm.sage with `ast`, is
   compiled as plain Python and called on them. It succeeds: in plain Python
   `row.get(col, 0)` is an int, which is why no pure-Python check could see
   the bug.
3. The same function is compiled again after the one rewrite the Sage
   preparser makes to it: every integer literal n becomes `Integer(n)`.
   `Integer` here is a stand-in with Sage's coercion (Integer op int is an
   Integer; it is not an int subclass). The call raises v2's exact
   `TypeError: Object of type Integer is not JSON serializable`, and an
   instrumented `json` shows it is the third digest (`rows`) after the
   first two succeeded, as in the run's traceback.
4. v3's `relation_digest.relation_digests` on the same relations, given
   plain ints and given stand-in Integers, succeeds and equals the digests of
   step 2.
"""
import argparse
import ast
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.dirname(HERE)
V2 = os.path.join(V3, '..', 'volcano-n19-native-tau6-v2-20261019')
sys.path.insert(0, V3)
sys.path.insert(0, os.path.join(V3, '..', 'volcano-n19-native-tau6-20261019', 'smoke'))
import native_binding as nb  # noqa: E402
import relation_digest as rd  # noqa: E402
import local_replay as L  # noqa: E402


class Integer:
    """Stand-in for sage.rings.integer.Integer: arithmetic with int stays Integer; not an int."""
    __slots__ = ('v',)

    def __init__(self, v):
        self.v = int(v)

    def _w(self, r):
        return Integer(r)

    def __int__(self):
        return self.v

    def __index__(self):
        return self.v

    def __add__(self, o):
        return self._w(self.v + int(o))
    __radd__ = __add__

    def __sub__(self, o):
        return self._w(self.v - int(o))

    def __rsub__(self, o):
        return self._w(int(o) - self.v)

    def __mul__(self, o):
        return self._w(self.v * int(o))
    __rmul__ = __mul__

    def __mod__(self, o):
        return self._w(self.v % int(o))

    def __rmod__(self, o):
        return self._w(int(o) % self.v)

    def __neg__(self):
        return self._w(-self.v)

    def __eq__(self, o):
        return self.v == int(o)

    def __lt__(self, o):
        return self.v < int(o)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return 'Integer(%d)' % self.v


class Preparse(ast.NodeTransformer):
    """The Sage preparser's integer-literal rule: n -> Integer(n)."""

    def visit_Constant(self, node):
        if type(node.value) is int:
            return ast.copy_location(ast.Call(func=ast.Name('Integer', ast.Load()),
                                              args=[ast.Constant(node.value)], keywords=[]), node)
        return node


def v2_function(preparse):
    src = open(os.path.join(V2, 'arm.sage')).read()
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'relation_digests')
    mod = ast.Module(body=[fn], type_ignores=[])
    if preparse:
        mod = Preparse().visit(mod)
    ast.fix_missing_locations(mod)
    calls = []

    class SpyJson:
        @staticmethod
        def dumps(o, **kw):
            calls.append(o)
            return json.dumps(o, **kw)

    import hashlib
    ns = {'json': SpyJson, 'hashlib': hashlib, 'Integer': Integer}
    exec(compile(mod, 'v2-arm.sage:relation_digests' + (' (preparsed)' if preparse else ''), 'exec'), ns)
    return ns['relation_digests'], calls, ast.unparse(mod)


def leaf_types(o, acc):
    if isinstance(o, (list, tuple)):
        for x in o:
            leaf_types(x, acc)
    else:
        acc.add(type(o).__name__)
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    v2panel = json.load(open(os.path.join(V2, 'inputs', 'panel.json')))
    pt = v2panel['points'][0]
    nat = nb.Native(a.lib, L.N, L.MOD, L.K)
    info = json.load(open(os.path.join(L.RHO, 'results', 'runtime-info.json')))
    P = (L.parse_z(info['P'][0]), L.parse_z(info['P'][1]))
    lam = int(info['lambda'])
    table, reps = L.build_base()
    rels = []
    st = L.tau_dlp(nat, P, L.B.mul(pt['scalar'], P), lam, random.Random(pt['rng_seed']), table, len(reps), relog=rels)
    p = L.P_ORD
    out = {'kind': 'local emulation (no Sage); the exact reproduction is diagnosis/digest_repro.sage on the runner',
           'point': pt, 'relations': len(rels), 'log_ok': st['log'] == pt['scalar'] % p, 'gb_calls': st['gb_calls']}

    plain_fn, plain_calls, _ = v2_function(False)
    out['v2_plain_python'] = plain_fn(rels, lam, p)
    out['v2_plain_python_json_calls'] = len(plain_calls)

    prep_fn, prep_calls, prep_src = v2_function(True)
    out['v2_preparsed_source'] = prep_src
    try:
        prep_fn(rels, lam, p)
        out['v2_preparsed'] = {'raised': None}
    except TypeError as e:
        failing = prep_calls[-1]
        out['v2_preparsed'] = {'raised': 'TypeError: %s' % e,
                               'json_dumps_calls_before_failure': len(prep_calls) - 1,
                               'failing_call_is': ['ordered', 'canonical', 'rows'][len(prep_calls) - 1],
                               'leaf_types_of_failing_object': sorted(leaf_types(failing, set())),
                               'first_failing_row': repr(failing[0])}
    v3_int = rd.relation_digests(rels, lam, p)
    v3_sage = rd.relation_digests([[tuple(Integer(x) for x in t) for t in r] for r in rels], Integer(lam), Integer(p))
    out['v3_plain_ints'] = v3_int
    out['v3_with_Integer_inputs'] = v3_sage
    out['v3_equals_v2_plain'] = v3_int == v3_sage == out['v2_plain_python']
    try:
        rd.dumps({'x': object()})
        out['v3_strict_dumps_rejects_unknown'] = False
    except TypeError as e:
        out['v3_strict_dumps_rejects_unknown'] = str(e)
    out['ok'] = (out['v2_preparsed'].get('raised') == 'TypeError: Object of type Integer is not JSON serializable'
                 and out['v2_preparsed'].get('failing_call_is') == 'rows' and out['v3_equals_v2_plain']
                 and out['log_ok'])
    json.dump(out, open(a.out, 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('relations', 'v2_preparsed', 'v3_equals_v2_plain', 'ok')}, indent=1))
    if not out['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
