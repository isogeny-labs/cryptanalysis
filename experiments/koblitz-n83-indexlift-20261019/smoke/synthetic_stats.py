"""Local check of verify_receipt.py's statistics path on synthetic rows (no timing of this experiment).

Usage: python3 smoke/synthetic_stats.py <mode> <archived rank-probe panel>

Rows are run 39214027289's archived rows, renamed: cR -> cP, cP -> cPaa, rT -> rT; kP -> kP, kPaa -> kPI.
mode `archived`: cPI -> cPI and cPIT (the archived lift_scan cold rows, so the expected primary is the
archived (K + cP) / (K + cPI)); cPIX is cPI with its cold time times 1.34 (a planted slowdown).
mode `null`: cPI, cPIT and cPIX are copies of the archived cP rows (the same cold code as cR), cPIX times
1.34. scan_selftest_ms (not in the archived fields) is set to 1,880 ms (6 ms for cPIT); cPIT's cold
time is not changed. The gates are not re-run here (the points differ from this panel).
"""
import copy
import json
import sys
from pathlib import Path

E = Path(__file__).resolve().parent.parent
RP = E.parent / 'koblitz-n83-rankprobe-20261019'
sys.path.insert(0, str(E))
import verify_receipt as v  # noqa: E402

mode, archive = sys.argv[1], Path(sys.argv[2])
runs, problems, missing = v.load(archive, json.loads((RP / 'schedule.json').read_text()),
                                 json.loads((RP / 'protocol.json').read_text()), False)
assert not problems and not missing
out = []
for r in runs:
    a = r['arm']
    if r['kind'] == 'ic_rank':
        if a in ('kP', 'kPaa'):
            out.append(dict(copy.deepcopy(r), arm={'kP': 'kP', 'kPaa': 'kPI'}[a]))
        continue
    if a == 'rT':
        out.append(r)
    elif a == 'cR':
        out.append(dict(copy.deepcopy(r), arm='cP'))
    elif a == 'cP':
        out.append(dict(copy.deepcopy(r), arm='cPaa'))
        if mode == 'null':
            for name in ('cPI', 'cPIT', 'cPIX'):
                out.append(dict(copy.deepcopy(r), arm=name))
    elif a == 'cPI' and mode == 'archived':
        for name in ('cPI', 'cPIT', 'cPIX'):
            out.append(dict(copy.deepcopy(r), arm=name))
for r in out:
    if r['arm'] == 'cPIX':
        r['f'] = dict(r['f'], cold_ms=r['f']['cold_ms'] * 1.34)
    if r['kind'] != 'rho_tuned':  # the archived producer did not report this field
        r['f'] = dict(r['f'], scan_selftest_ms=6.0 if r['arm'] == 'cPIT' else 1880.0)
protocol = json.loads((E / 'protocol.json').read_text())
stats = v.statistics_block(out, protocol)
decision, controls = v.decide({'all': True}, stats)
print(json.dumps({'mode': mode, 'decision': decision, 'controls': controls,
                  'primary': stats['primary_e2e_shared_cP_over_cPI'],
                  'own_rank': stats['secondary_e2e_own_kP_cP_over_kPI_cPI'],
                  'aa_e2e': stats['aa_e2e_shared_cP_over_cPaa']['estimate'],
                  'aa_cold': stats['aa_cold_cP_over_cPaa']['estimate'],
                  'sharing': stats['sharing_rank_attempt_kPI_over_kP'],
                  'planted': stats['planted_cold_cPIX_over_cPI']['estimate'],
                  'S_e2e_cold': stats.get('S_e2e_cold')}, indent=1, sort_keys=True))
