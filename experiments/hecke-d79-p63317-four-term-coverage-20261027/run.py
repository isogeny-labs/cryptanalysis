"""Frozen four-distinct-source coverage search in the p63317 subgroup."""
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT / item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('PARENT_PIN_MISMATCH:' + name)
    return json.loads(raw)


def main():
    prior = pinned('triple-audit.json')
    logs = pinned('class-logs.json')
    assert prior['status'] == 'PASS' and prior['triple_uncovered_points'] == 28
    assert logs['q'] == PLAN['q'] and len(logs['q_logs']) == 40
    q = PLAN['q']
    a = logs['q_logs']
    start = time.perf_counter_ns()
    triple = {}
    patterns = 0
    for i in range(40):
        for j in range(i + 1, 40):
            for k in range(j + 1, 40):
                for si in (-1, 1):
                    for sj in (-1, 1):
                        for sk in (-1, 1):
                            v = (si * a[i] + sj * a[j] + sk * a[k]) % q
                            triple.setdefault(v, []).append((i, si, j, sj, k, sk))
                            patterns += 1
    missing = [v for v in range(q) if v not in triple]
    if patterns != 79040 or len(triple) != prior['triple_coverage_points'] or len(missing) != 28:
        raise ValueError('TRIPLE_COVERAGE_MISMATCH')
    build_ns = time.perf_counter_ns() - start
    rows = []
    for target in missing:
        t = time.perf_counter_ns()
        probes = 0
        witness = None
        for l in range(40):
            for sl in (-1, 1):
                probes += 1
                residual = (target - sl * a[l]) % q
                for i, si, j, sj, k, sk in triple.get(residual, ()):
                    if l not in (i, j, k):
                        witness = [i, si, j, sj, k, sk, l, sl]
                        break
                if witness is not None:
                    break
            if witness is not None:
                break
        elapsed = time.perf_counter_ns() - t
        rows.append({'scalar': target, 'status': 'FOUND' if witness else 'CAP80_NO_RELATION',
                     'probes': probes, 'witness': witness, 'search_ns': elapsed})
    # Compute the complete family independently of the residual stopping rule.
    four_set = set()
    four_patterns = 0
    for i in range(40):
        for j in range(i + 1, 40):
            for k in range(j + 1, 40):
                for l in range(k + 1, 40):
                    for mask in range(16):
                        four_set.add(sum((1 if mask & (1 << bit) else -1) * a[index]
                                         for bit, index in enumerate((i, j, k, l))) % q)
                        four_patterns += 1
    result = {'schema': 'hecke-d79-p63317-four-term-coverage-v1', 'p': PLAN['p'],
              'q': q, 'status': 'ALL_RESIDUALS_FOUND' if all(r['status'] == 'FOUND' for r in rows)
              else 'RESIDUAL_MISS', 'triple_patterns': patterns, 'triple_coverage_points': len(triple),
              'triple_residual_scalars': missing, 'triple_build_ns': build_ns,
              'residual_rows': rows, 'four_patterns': four_patterns,
              'four_coverage_points': len(four_set),
              'four_uncovered_scalars': [v for v in range(q) if v not in four_set],
              'candidate_id': None, 'target_online_ms': None}
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'], 'triple_missing': len(missing),
                      'four_coverage': len(four_set), 'four_missing': len(result['four_uncovered_scalars'])}))


if __name__ == '__main__':
    main()
