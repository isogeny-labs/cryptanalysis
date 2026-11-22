"""Audit the receipt and apply the frozen decision rule (protocol.json).

    python3 verify_receipt.py RECEIPT_DIR        (needs numpy; the Sage python has it)

Reads RECEIPT_DIR/runs.jsonl (written by run_schedule.py), checks every gate
and control, computes the primary and the co-reported secondaries, and
writes RECEIPT_DIR/result.json and RECEIPT_DIR/result_table.md. Exit 0 with
any verdict, including invalid; exit 2 only if the receipt cannot be read.
"""
import json
import math
import os
import sys

import numpy as np

import stats

HERE = os.path.dirname(os.path.abspath(__file__))
IC_ARMS = ('B', 'N', 'Naa', 'NX')
COUNT_FIELDS = ('targets', 'gb_calls', 'spurious', 'relations', 'log')


def main():
    rd = sys.argv[1]
    proto = json.load(open(os.path.join(HERE, 'protocol.json')))
    sched = json.load(open(os.path.join(HERE, 'schedule.json')))
    panel = json.load(open(os.path.join(HERE, 'inputs', 'panel.json')))
    info = json.load(open(os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014', 'results', 'runtime-info.json')))
    try:
        runs = {r['row']: r for r in map(json.loads, open(os.path.join(rd, 'runs.jsonl')))}
    except OSError as e:
        print(json.dumps({'verdict': 'invalid', 'reason': 'no receipt: %s' % e}))
        sys.exit(2)
    gates, fails = {}, []

    def gate(name, ok, detail=None):
        gates[name] = {'pass': bool(ok), 'detail': detail}
        if not ok:
            fails.append(name)

    sched_rows = [r for s in sched['segments'] for r in s['rows']]
    missing = [r['row'] for r in sched_rows if r['row'] not in runs or runs[r['row']].get('status') != 'ran'
               or runs[r['row']].get('exit') != 0 or not runs[r['row']].get('result', {}).get('correct')]
    gate('every scheduled row ran, exit 0, verified', not missing, missing)
    res = {k: v.get('result', {}) for k, v in runs.items()}

    st = res.get('S0-selftest', {})
    gate('S0 Sage variety == native == brute force on 300 systems',
         st.get('systems') == 300 and st.get('set_equal') == 300 and st.get('bruteforce_equal') == 300,
         {k: st.get(k) for k in ('systems', 'set_equal', 'bruteforce_equal', 'nonempty', 'multi', 'order_equal_multi')})
    o = res.get('O1-archived', {})
    gate('O1 archived counts and logs (run 38520305068) reproduced on all ten scalars', o.get('all_equal') is True,
         [i.get('compare') for i in o.get('instances', [])])

    cpus = {tuple(r.get('affinity', [])) for r in res.values() if r}
    gate('one pinned CPU for every process', len(cpus) == 1 and all(len(c) == 1 for c in cpus), sorted(cpus))
    shas = {r.get('native_sha256') for k, r in res.items() if r and r.get('arm') in ('N', 'Naa', 'NX', 'O', 'selftest')}
    gate('one native library digest across every native process', len(shas) == 1 and None not in shas, sorted(map(str, shas)))

    pts = [p['id'] for p in panel['points']]
    per = {}
    for p in pts:
        rows = {a: res.get('%s-%s' % (p, a), {}) for a in IC_ARMS + ('rho',)}
        per[p] = rows
        sc = next(x['scalar'] for x in panel['points'] if x['id'] == p)
        counts = {a: tuple(rows[a].get(f) for f in COUNT_FIELDS) for a in IC_ARMS}
        gate('%s counts and log equal across B, N, Naa, NX' % p,
             len(set(counts.values())) == 1 and counts['B'][-1] == sc % proto['curve']['r'],
             {a: list(v) for a, v in counts.items()})
        dig = {a: rows[a].get('relations_digest', {}) for a in IC_ARMS}
        gate('%s relation rows and decompositions equal across B, N, Naa, NX' % p,
             len({d.get('rows_sha256') for d in dig.values()}) == 1 and
             len({d.get('canonical_sha256') for d in dig.values()}) == 1 and None not in
             {d.get('rows_sha256') for d in dig.values()},
             {a: [d.get('rows_sha256'), d.get('canonical_sha256'), d.get('ordered_sha256')] for a, d in dig.items()})
        gate('%s N, Naa, NX ordered decompositions equal (same code)' % p,
             len({dig[a].get('ordered_sha256') for a in ('N', 'Naa', 'NX')}) == 1)
        pl = rows['NX'].get('plant', {})
        gate('%s NX compared every shift system with Sage' % p,
             pl.get('checked_calls') == rows['NX'].get('gb_calls') and pl.get('checked_calls', 0) > 0, pl)
        gate('%s generator equals the archived P' % p,
             all(rows[a].get('P') == info['P'] for a in IC_ARMS))
        gate('%s rho: 64 reps verified' % p, rows['rho'].get('verified_reps') == 64)
        wb = [rows[a].get('warm_batch', {}).get('same_relations') for a in ('N', 'Naa')]
        gate('%s warm batch reproduced the cold relations' % p, wb == [True, True], wb)

    complete = not missing and all(per[p][a] for p in pts for a in IC_ARMS + ('rho',))
    out = {'experiment': proto['id'], 'protocol_frozen_at_utc': proto['frozen_at_utc'], 'gates': gates}
    if complete:
        col = lambda a, f: np.array([float(per[p][a][f]) for p in pts])
        B, N, Naa, NX = (col(a, 'cold_cpu_s') for a in IC_ARMS)
        R = stats.ratio_of_means(B, N)
        aa = float(N.mean() / Naa.mean())
        plant = stats.ratio_of_means(NX, N)
        controls = {'aa_N_over_Naa': aa, 'aa_window': proto['controls']['aa_window'],
                    'aa_pass': proto['controls']['aa_window'][0] <= aa <= proto['controls']['aa_window'][1],
                    'planted_NX_over_N': plant, 'planted_pass': plant[1] > 1}
        rho_cpu = np.array([per[p]['rho']['cpu_s'] for p in pts])
        unit = sum(per[p]['rho']['cpu_s_total'] for p in pts) / sum(per[p]['rho']['group_ops_total'] for p in pts)
        sq = math.sqrt(proto['curve']['r'])
        S = lambda x: float(np.mean(x) / unit / sq)
        sec = {}
        for a in IC_ARMS:
            sec[a] = {f: float(col(a, f).mean()) for f in ('cold_cpu_s', 'setup_cpu_s', 'online_cpu_s', 'cold_wall_s',
                                                          'gb_cpu_s', 'linalg_cpu_s', 'relation_cpu_s')}
            sec[a]['gb_calls_mean'] = float(col(a, 'gb_calls').mean())
            sec[a]['solve_ms_per_call'] = 1e3 * float(col(a, 'gb_cpu_s').sum() / col(a, 'gb_calls').sum())
            sec[a]['launcher_wall_s'] = float(np.mean([runs['%s-%s' % (p, a)]['launcher_wall_s'] for p in pts]))
            sec[a]['S_cold'] = S(col(a, 'cold_cpu_s'))
            sec[a]['S_online'] = S(col(a, 'online_cpu_s'))
            sec[a]['S_setup'] = S(col(a, 'setup_cpu_s'))
            sec[a]['gap_cold_vs_rho_geo'] = stats.geo_ratio(col(a, 'cold_cpu_s'), rho_cpu)
        for a in ('N', 'Naa'):
            wb = [per[p][a]['warm_batch'] for p in pts]
            sec[a]['warm_batch'] = {'label': 'repeated-batch, warm (secondary)',
                                    'setup_cpu_s_mean': float(np.mean([w['setup_cpu_s_mean'] for w in wb])),
                                    'online_cpu_s_mean': float(np.mean([w['online_cpu_s_mean'] for w in wb]))}
        sec['rho'] = {'cpu_s_per_solve': float(rho_cpu.mean()), 'unit_cpu_s_per_group_op': unit,
                      'S_cold': S(rho_cpu), 'steps_mean': float(np.mean([per[p]['rho']['steps_mean'] for p in pts]))}
        sec['ratios'] = {'online_B_over_N': stats.ratio_of_means(col('B', 'online_cpu_s'), col('N', 'online_cpu_s')),
                         'setup_B_over_N': stats.ratio_of_means(col('B', 'setup_cpu_s'), col('N', 'setup_cpu_s')),
                         'cold_wall_B_over_N': stats.ratio_of_means(col('B', 'cold_wall_s'), col('N', 'cold_wall_s')),
                         'launcher_wall_B_over_N': stats.ratio_of_means(
                             [runs['%s-B' % p]['launcher_wall_s'] for p in pts],
                             [runs['%s-N' % p]['launcher_wall_s'] for p in pts]),
                         'per_call_solve_B_over_N': sec['B']['solve_ms_per_call'] / sec['N']['solve_ms_per_call']}
        sec['phase_share_N'] = {'native_solve': sec['N']['gb_cpu_s'] / sec['N']['cold_cpu_s'],
                                'rest_of_relation_search': (sec['N']['relation_cpu_s'] - sec['N']['gb_cpu_s']) / sec['N']['cold_cpu_s'],
                                'linear_algebra': sec['N']['linalg_cpu_s'] / sec['N']['cold_cpu_s'],
                                'setup': sec['N']['setup_cpu_s'] / sec['N']['cold_cpu_s']}
        ok = not fails and controls['aa_pass'] and controls['planted_pass']
        out.update({'primary': {'statistic': 'R = mean cold_cpu_s(B) / mean cold_cpu_s(N), paired bootstrap over points',
                                'point': R[0], 'lo95': R[1], 'hi95': R[2], 'points': len(pts)},
                    'controls': controls, 'secondary': sec,
                    'per_point': {p: {a: {f: per[p][a].get(f) for f in ('cold_cpu_s', 'setup_cpu_s', 'online_cpu_s',
                                                                         'gb_calls', 'targets', 'log')}
                                      for a in IC_ARMS} for p in pts},
                    'verdict': stats.verdict(R[1], R[2]) if ok else 'invalid',
                    'failed': fails + [c for c in ('aa_pass', 'planted_pass') if not controls[c]]})
    else:
        out.update({'verdict': 'invalid', 'failed': fails or ['incomplete']})
    json.dump(out, open(os.path.join(rd, 'result.json'), 'w'), indent=1)
    lines = ['# volcano-n19-native-tau6-20261019 result', '', '**Verdict: %s**' % out['verdict'], '']
    if 'primary' in out:
        pr, c, s = out['primary'], out['controls'], out['secondary']
        lines += ['| quantity | value |', '|---|---|',
                  '| primary R = cold B / cold N (CPU) | %.2f [%.2f, %.2f] |' % (pr['point'], pr['lo95'], pr['hi95']),
                  '| A/A N / Naa | %.4f (window %s) |' % (c['aa_N_over_Naa'], c['aa_window']),
                  '| planted NX / N | %.2f [%.2f, %.2f] |' % tuple(c['planted_NX_over_N']),
                  '| cold CPU s, B / N | %.3f / %.4f |' % (s['B']['cold_cpu_s'], s['N']['cold_cpu_s']),
                  '| S cold B / N / rho | %.1f / %.2f / %.3f |' % (s['B']['S_cold'], s['N']['S_cold'], s['rho']['S_cold']),
                  '| S online B / N | %.1f / %.2f |' % (s['B']['S_online'], s['N']['S_online']),
                  '| cold gap to rho (geo), N | %.1f [%.1f, %.1f] |' % tuple(s['N']['gap_cold_vs_rho_geo']),
                  '| solve ms per call, B / N | %.3f / %.4f |' % (s['B']['solve_ms_per_call'], s['N']['solve_ms_per_call'])]
    lines += ['', 'Failed: %s' % (out.get('failed') or 'none')]
    open(os.path.join(rd, 'result_table.md'), 'w').write('\n'.join(lines) + '\n')
    print(json.dumps({k: out.get(k) for k in ('verdict', 'primary', 'failed')}, indent=1))


if __name__ == '__main__':
    main()
