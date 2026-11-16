#!/usr/bin/env python3
"""Record analysis values verbatim; no qualification or baseline promotion."""
import json, statistics, subprocess
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
RECORD = ROOT / 'benchmarks/records/20261116T1701Z-ic-vector-inverse-anchor-factorial-001.json'
a = json.loads((P / 'analysis.json').read_text())
assert a['status'] == 'pass'
assert not json.loads(RECORD.read_text())['metrics'], 'do not duplicate metrics'
note = ('Unsigned exploratory measurements; qualificationnull and invalid for promotion. '
        'Context plus pipeline through oracle cleanup excludes prior inputs/startup and later '
        'context/report destruction. All A/A failures retained; Python replay separate.')

def metric(name, value, unit, better='neutral', n=None, spread=None, baseline=None, reference=None):
    argv = ['python3', 'tools/benchrec.py', 'metric', str(RECORD), '--name', name,
            '--value', str(value), '--unit', unit, '--better', better, '--note', note]
    if n is not None:
        argv += ['--n', str(n)]
    if spread:
        argv += ['--spread-low', str(spread[0]), '--spread-high', str(spread[1])]
    if baseline is not None:
        argv += ['--baseline', str(baseline)]
    if reference is not None:
        argv += ['--reference', str(reference), '--reference-kind', 'matched_rho']
    subprocess.run(argv, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

for c in a['cases']:
    prefix = f"n{c['n']}_"
    rows = [r for r in a['rows'] if r['index'] == c['index']]
    for interval, key in [('primary', 'through_cleanup_contrasts'), ('collector', 'contrasts')]:
        for contrast, values in c[key].items():
            metric(prefix + interval + '_' + contrast, values['median'], 'ratio', 'higher',
                   len(rows), values['bootstrap95'])
    m = c['methods']['vector16-inverse']
    anchor = c['methods']['anchor-vector16-const']
    metric(prefix + 'candidate_primary_mean', m['mean_context_plus_computation_s'], 'wall_s',
           'lower', len(rows), baseline=anchor['mean_context_plus_computation_s'],
           reference=statistics.mean(r['references']['rho-negation']['context_plus_compute_s'] for r in rows))
    metric(prefix + 'candidate_collector_mean', m['mean_collector_s'], 'wall_s',
           'lower', len(rows), baseline=anchor['mean_collector_s'],
           reference=statistics.mean(r['references']['rho-negation']['compute_s'] for r in rows))
    for counter in ['elements', 'padded_lanes']:
        metric(prefix + 'actual_inverse_vector_' + counter,
               sum(r['methods']['vector16-inverse']['query_counters']['walk_batch_inverse_vector_' + counter] for r in rows),
               'count', n=len(rows))

metric('aa_failed_controls', len(a['aa_failed_rows']), 'count', n=len(a['rows']))
metric('capped_ic_arms', a['capped_arms'], 'count', n=360)
replay = json.loads((P / 'independent-arithmetic-timing001.json').read_text())
metric('replayed_target_answers', replay['pipeline_answers'] + replay['rho_answers'], 'count', n=600)
metric('replayed_aa_answers', replay['aa_answers'], 'count', n=240)
metric('replayed_walk_states', json.loads((P / 'independent-walk-timing001.json').read_text())['checks'], 'count', n=2560)
print(json.dumps({'metrics': len(json.loads(RECORD.read_text())['metrics'])}))
