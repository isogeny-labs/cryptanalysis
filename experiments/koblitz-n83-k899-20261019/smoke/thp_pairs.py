"""Local diagnostic only: interleaved cold pairs (and optional rank pair) with glibc THP for malloc."""
import json, sys, time
sys.path.insert(0, '<worktree>/experiments/koblitz-n83-k899-20261019/diag')
import run_diag as rd
from pathlib import Path
S = Path('<scratch>')
out = S / 'k899-thp' / 'raw'
binary = S / 'k899-bin' / 'ic_online_rankprobe_r770'
t899 = S / 'k899-diag-local' / 'factor_logs_n83_K899.json'
point = [int(v) for v in json.loads((rd.RP / 'protocol.json').read_text())['design']['q0_point']]
thp = {'GLIBC_TUNABLES': 'glibc.malloc.hugetlb=1'}
plan = []
for rep in range(int(sys.argv[1])):
    plan += [('c600_%d' % rep, 600, dict(thp, KIC_LOG_TABLE_IN=str(rd.TABLE600))),
             ('c899_%d' % rep, 899, dict(thp, KIC_LOG_TABLE_IN=str(t899)))]
if len(sys.argv) > 2:
    rank = {'KIC_RANK_CANON': 'lift', 'KIC_RANK_ORDER': 'feistel', 'KIC_RANK_PROBE': 'target', 'KIC_RANK_SOLVE': 'frame'}
    plan += [('k600', 600, dict(thp, **rank)), ('k899', 899, dict(thp, **rank))]
for tag, k, env in plan:
    code, wall, s, rec = rd.run(binary, rd.BASES[k], point, rd.SEED, env, int(sys.argv[3]) if len(sys.argv) > 3 else 2, out, tag)
    row = {'tag': tag, 'exit': code, 'index_ms': s['timing_ms']['index_build'], 'setup_ms': s['setup_complete_ns'] / 1e6,
           'online_ns_per_probe': rec['online_ms'] * 1e6 / rec['probes'], 'scalar': rec['recovered_scalar'],
           'rss': s['peak_rss_bytes']}
    if s.get('rank_attempt_ns'):
        ns, p = s['rank_attempt_ns'], s['rank_attempt_probes']
        row.update(rank_ms=s['timing_ms']['rank_stage'], rank_ns_per_probe=sum(ns) / sum(p),
                   first50=sum(ns[:50]) / sum(p[:50]))
    print(json.dumps(row), flush=True)
