"""Independent receipt check against pinned rows and source-set completion."""
import hashlib
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post_inputs.json').read_text())
ANALYSIS = json.loads((HERE / 'analysis.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order(p, rep):
    return sorted(range(40), key=lambda i: (
        hashlib.sha256(('hecke-d79-order-v1|%d|%d|%d' % (p, rep, i)).encode()).hexdigest(), i))


def main():
    for name, rel in [('analysis', HERE/'analysis.json'),
                      ('analyzer', HERE/'analyze_order.py'),
                      ('replay_runner', HERE/'replay_order.py'),
                      ('cache_api', ROOT/PLAN['cache_api_path']),
                      ('codec_v2', ROOT/'experiments/hecke-d79-cache-interface-20261027/codec_v2.py')]:
        if sha(rel) != POST['sha256'][name]:
            raise ValueError(name + '_PIN_MISMATCH')
    for name in ('source', 'prefix_runner', 'shared_runner'):
        if sha(ROOT/PLAN[name+'_path']) != PLAN[name+'_sha256']:
            raise ValueError(name + '_PIN_MISMATCH')
    if sha(ROOT/PLAN['artifact_path']) != PLAN['artifact_sha256']:
        raise ValueError('ARTIFACT_PIN_MISMATCH')
    for case in PLAN['cases']:
        p = case['p']
        if sha(ROOT/case['result_path']) != case['result_sha256'] or sha(ROOT/case['analysis_path']) != case['analysis_sha256']:
            raise ValueError('CASE_PIN_MISMATCH')
        prior = json.loads((ROOT/case['analysis_path']).read_text())
        cell = next(x for x in ANALYSIS['cases'] if x['p'] == p)
        active = [frozenset(prior['hecke']['candidates'][i]['sources'])
                  for i in cell['active_candidate_indices']]
        if len(active) != cell['active_candidate_count']:
            raise ValueError('ACTIVE_COUNT_MISMATCH')
        for rep in range(PLAN['policy']['repetitions']):
            seen = set()
            count = None
            for k, source in enumerate(order(p, rep), 1):
                seen.add(source)
                if any(s <= seen for s in active):
                    count = k
                    break
            if count != cell['source_counts'][rep]:
                raise ValueError('PERMUTATION_COUNT_MISMATCH')
        replay = json.loads((HERE/f'replay-p{p}.json').read_text())
        if (replay['status'] != 'PASS' or
            replay['source_count'] != cell['replay_predicted_source_count'] or
            replay['cache']['build_invocations'] != 0 or
            replay['final_rank_qq'] != 40 or replay['final_rank_mod_q'] != 39):
            raise ValueError('REPLAY_RESULT_MISMATCH')
        seen = set()
        for k, step in enumerate(replay['steps'], 1):
            if step['source'] != cell['replay_order'][k-1]:
                raise ValueError('REPLAY_ORDER_MISMATCH')
            seen.add(step['source'])
            expected_candidates = sum(set(x['sources']) <= seen for x in prior['hecke']['candidates'])
            expected_rank = 40 if any(s <= seen for s in active) else 39
            if (step['visited_count'] != k or step['candidates'] != expected_candidates or
                step['rank_qq'] != expected_rank):
                raise ValueError('REPLAY_PREFIX_MISMATCH')
        total_patterns = sum(math.comb(replay['source_count'], s) * (2 ** (s-1))
                             for s in range(1, 5))
        if replay['total_trials'] != total_patterns:
            raise ValueError('TRIAL_COUNT_MISMATCH')
    print(json.dumps({'status':'PASS','cases':len(PLAN['cases']),
                      'permutations_per_case':PLAN['policy']['repetitions']}))


if __name__ == '__main__':
    main()
