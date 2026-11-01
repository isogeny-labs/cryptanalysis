"""Local diagnostic for protocol v3 (no Sage, cloud-agent VM; counts and digests only, not timing).

    python3 smoke/local_v3.py --lib PATH/libtau6native.so --out smoke/local_v3.json

v1's pure-Python tauDlp replay (local_replay.py: rho_frob PyBackend arithmetic)
with the v3 binding (native_binding.Native, run.sage's MODULUS read lowest
degree first) on:
  - the ten archived scalars (what O1 checks on the runner): counts and logs
    must equal run 38520305068's tau6 rows;
  - the two smoke points (v2 p00, p01) and the 20 v3 points: every log must
    verify, and the relation digests of relation_digest.py are recorded.
This is the path v2's local checks also ran; it cannot see preparser effects
(diagnosis/emulate_preparser.py shows why), so the Sage smoke job is the gate.
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.dirname(HERE)
sys.path.insert(0, V3)
sys.path.insert(0, os.path.join(V3, '..', 'volcano-n19-native-tau6-20261019', 'smoke'))
import native_binding as nb  # noqa: E402
import relation_digest as rd  # noqa: E402
import local_replay as L  # noqa: E402

FIELDS = ('targets', 'gb_calls', 'spurious', 'relations', 'log')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    nat = nb.Native(a.lib, L.N, L.MOD, L.K)
    info = json.load(open(os.path.join(L.RHO, 'results', 'runtime-info.json')))
    proto = json.load(open(os.path.join(L.RHO, 'protocol.json')))
    arch = {r['instance']: r for r in map(json.loads, open(os.path.join(L.RHO, 'results', 'arms.jsonl')))
            if r['arm'] == 'tau6'}
    P = (L.parse_z(info['P'][0]), L.parse_z(info['P'][1]))
    lam = int(info['lambda'])
    table, reps = L.build_base()
    out = {'kind': 'local diagnostic (cloud-agent VM, pure-Python driver + the v3 binding); counts and digests only, '
                   'not timing evidence', 'modulus': L.MOD, 'archived': [], 'points': []}
    for ii, s in enumerate(proto['scalars']):
        rels = []
        st = L.tau_dlp(nat, P, L.B.mul(int(s), P), lam, random.Random(proto['arms']['tau6']['rng_seed'] % ii),
                       table, len(reps), relog=rels)
        cmp = {f: [st[f], arch[ii][f]] for f in FIELDS}
        out['archived'].append({'instance': ii, 'equal': all(x == y for x, y in cmp.values()) and st['recovered'],
                                'compare': cmp, 'digest': rd.relation_digests(rels, lam, L.P_ORD)})
    v2 = json.load(open(os.path.join(V3, '..', 'volcano-n19-native-tau6-v2-20261019', 'inputs', 'panel.json')))
    v3 = json.load(open(os.path.join(V3, 'inputs', 'panel.json')))
    for role, pts in (('smoke', [p for p in v2['points'] if p['id'] in ('p00', 'p01')]), ('timed', v3['points'])):
        for pt in pts:
            rels = []
            st = L.tau_dlp(nat, P, L.B.mul(pt['scalar'], P), lam, random.Random(pt['rng_seed']), table, len(reps),
                           relog=rels)
            rec = {'role': role, 'id': pt['id'], 'scalar': pt['scalar'],
                   'log_ok': st['log'] == pt['scalar'] % L.P_ORD and st['recovered'],
                   'digest': rd.relation_digests(rels, lam, L.P_ORD), **{f: st[f] for f in FIELDS},
                   'multi_solution_calls': st['multi_solution_calls']}
            out['points'].append(rec)
            print(json.dumps({k: rec[k] for k in ('role', 'id', 'log_ok', 'gb_calls', 'targets')}), flush=True)
    t = [p for p in out['points'] if p['role'] == 'timed']
    out['archived_all_equal'] = all(x['equal'] for x in out['archived'])
    out['all_logs_ok'] = all(p['log_ok'] for p in out['points'])
    out['timed_gb_calls_mean'] = sum(p['gb_calls'] for p in t) / len(t)
    out['timed_gb_calls_range'] = [min(p['gb_calls'] for p in t), max(p['gb_calls'] for p in t)]
    json.dump(out, open(a.out, 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('archived_all_equal', 'all_logs_ok', 'timed_gb_calls_mean',
                                          'timed_gb_calls_range')}))
    if not (out['archived_all_equal'] and out['all_logs_ok']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
