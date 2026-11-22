"""Local diagnostic for protocol v2 (no Sage, cloud-agent VM; counts only, not timing).

    python3 smoke/local_v2.py --lib PATH/libtau6native.so --out smoke/local_v2.json

tau.sage's tauDlp control flow in pure Python (v1's smoke/local_replay.py,
reused unchanged: rho_frob.py PyBackend arithmetic) with the per-shift variety
from the binding arm.sage v2 uses (native_binding.Native, modulus from
run.sage's MODULUS read lowest degree first). Two parts:
  - archived: the ten scalars of run 38520305068 with the archived rng seeds;
    targets, gb_calls, spurious, relations and log must equal arms.jsonl
    (what O1 checks on the runner);
  - panel: the 16 v2 points (inputs/panel.json); every log must verify.
Both parts record every shift system with two or more solutions that the
candidate meets (only those can make the order of a variety matter) and
whether it is a shift-0 swap (a, b), (b, a), as v1's smoke/multi_calls.py did.
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, V2)
sys.path.insert(0, os.path.join(V2, '..', 'volcano-n19-native-tau6-20261019', 'smoke'))
sys.path.insert(0, os.path.join(V2, 'diagnosis'))
import native_binding as nb  # noqa: E402
import local_replay as L  # noqa: E402
from s0_v2_local import run_sage_modulus  # noqa: E402

FIELDS = ('targets', 'gb_calls', 'spurious', 'relations', 'log')


class Spy:
    def __init__(self, nat, table):
        self.nat, self.table, self.calls = nat, table, []

    def solve(self, xr, j):
        s = self.nat.solve(xr, j)
        if len(s) > 1:
            self.calls.append({'xr': xr, 'j': j, 'solutions': s,
                               'in_base': [x1 in self.table and x2 in self.table for x1, x2 in s],
                               'swap_pair': len(s) == 2 and j == 0 and s[0] == tuple(reversed(s[1]))})
        return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    m = nb.modulus_int(run_sage_modulus())
    assert m == L.MOD, (m, L.MOD)
    nat = nb.Native(a.lib, L.N, m, L.K)
    info = json.load(open(os.path.join(L.RHO, 'results', 'runtime-info.json')))
    proto = json.load(open(os.path.join(L.RHO, 'protocol.json')))
    arch = {r['instance']: r for r in map(json.loads, open(os.path.join(L.RHO, 'results', 'arms.jsonl')))
            if r['arm'] == 'tau6'}
    P = (L.parse_z(info['P'][0]), L.parse_z(info['P'][1]))
    lam = int(info['lambda'])
    table, reps = L.build_base()
    spy = Spy(nat, table)
    archived = []
    for ii, s in enumerate(proto['scalars']):
        st = L.tau_dlp(spy, P, L.B.mul(int(s), P), lam, random.Random(proto['arms']['tau6']['rng_seed'] % ii),
                       table, len(reps))
        cmp = {f: [st[f], arch[ii][f]] for f in FIELDS}
        archived.append({'instance': ii, 'scalar': int(s), 'compare': cmp,
                         'equal': all(x == y for x, y in cmp.values()) and bool(st['recovered'])})
        print(json.dumps(archived[-1]), flush=True)
    panel = json.load(open(os.path.join(V2, 'inputs', 'panel.json')))
    pts = []
    for pt in panel['points']:
        n0 = len(spy.calls)
        st = L.tau_dlp(spy, P, L.B.mul(pt['scalar'], P), lam, random.Random(pt['rng_seed']), table, len(reps))
        st['multi_calls'] = spy.calls[n0:]
        st.update({'id': pt['id'], 'scalar': pt['scalar'], 'log_ok': st['log'] == pt['scalar'] % L.P_ORD})
        pts.append(st)
        print(json.dumps(st), flush=True)
    out = {'kind': 'local diagnostic (cloud-agent VM, pure-Python driver + the v2 binding); counts only, '
                   'not timing evidence',
           'modulus': m, 'archived': archived, 'archived_all_equal': all(x['equal'] for x in archived),
           'panel': pts, 'panel_all_logs_ok': all(r['log_ok'] and r['recovered'] for r in pts),
           'panel_gb_calls_mean': sum(r['gb_calls'] for r in pts) / len(pts),
           'multi_calls_total': len(spy.calls),
           'non_swap_multi_calls': [c for c in spy.calls if not c['swap_pair']]}
    json.dump(out, open(a.out, 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('archived_all_equal', 'panel_all_logs_ok', 'panel_gb_calls_mean',
                                          'multi_calls_total', 'non_swap_multi_calls')}))


if __name__ == '__main__':
    main()
