"""Local check of verify_receipt.py's statistics path on synthetic rows (no timing of this experiment).

Usage: python3 smoke/synthetic_stats.py <effect> [<archived rank-cut panel>]

Rows are run 38891404048's archived rows, renamed: cR -> cR, cS -> cP, cRI -> cPI, rT -> rT; kR -> kR and
(a copy) kPaa; kRaa -> kP; kRX -> kPX. The attempts of kP and kPaa are divided by <effect>, so the
expected end-to-end ratio is known. The gates are not re-run here (the points differ from this panel).
"""
import copy, json, sys
from pathlib import Path
E = Path(__file__).resolve().parent.parent
RC = E.parent / 'koblitz-n83-rankcut-20261016'
A = Path(sys.argv[2]) if len(sys.argv) > 2 else RC / 'run_github_38891404048' / 'panel'
sys.path.insert(0, str(E))
import verify_receipt as v  # noqa: E402
effect = float(sys.argv[1])
runs, problems, missing = v.load(A, json.loads((RC / 'schedule.json').read_text()), json.loads((RC / 'protocol.json').read_text()), False)
assert not problems and not missing
out = []
cold_map = {'cR': 'cR', 'cS': 'cP', 'cRI': 'cPI', 'rT': 'rT'}
for r in runs:
    if r['kind'] == 'ic_rank':
        if r['arm'] == 'kR':
            out.append(dict(r, arm='kR'))
            r2 = copy.deepcopy(r); r2['arm'] = 'kPaa'
            out.append(r2)
        elif r['arm'] == 'kRaa':
            out.append(dict(copy.deepcopy(r), arm='kP'))
        elif r['arm'] == 'kRX':
            out.append(dict(r, arm='kPX'))
    elif r['arm'] in cold_map:
        out.append(dict(r, arm=cold_map[r['arm']]))
for r in out:
    if r['arm'] in ('kP', 'kPaa'):
        rest = r['f']['rank_stage_ms'] - sum(r['rank_attempt_ns']) / 1e6
        r['rank_attempt_ns'] = [x / effect for x in r['rank_attempt_ns']]
        r['f'] = dict(r['f'], rank_stage_ms=rest + sum(r['rank_attempt_ns']) / 1e6)
protocol = json.loads((E / 'protocol.json').read_text())
stats = v.statistics_block(out, protocol)
decision, controls = v.decide({'all': True}, stats)
print(json.dumps({'planted_rank_effect': effect, 'decision': decision, 'controls': controls,
                  'primary': stats['primary_e2e_kR_cR_over_kP_cP'], 'aa_e2e': stats['aa_e2e_kP_cP_over_kPaa_cR']['estimate'],
                  'aa_cold': stats['aa_cold_cP_over_cR']['estimate'],
                  'planted': stats['planted_rank_attempt_kPX_over_kP']['estimate']}, indent=1))
