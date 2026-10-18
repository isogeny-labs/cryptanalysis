"""Replay exact ANF identities and bounded unpinned N41 solver receipts."""
import hashlib
import json
import random
from pathlib import Path

import solve

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def checked_sources(name):
    data = read(name)
    for source, expected in data['sources'].items():
        path = Path(source)
        if not path.is_absolute():
            path = WORKSPACE / path
        assert sha(path) == expected, source
    return data


cfg = checked_sources('verify_protocol.json')
base = checked_sources('protocol.json')
degree = checked_sources('deglex_protocol.json')
checked_sources('runner_v2_protocol.json')
assert base['n41_curve_id'] == degree['n41_curve_id']
assert base['n131_curve_id'] == degree['n131_curve_id']

for case, name, protocol, stem in (
        ('n41_positive', 'n41_positive_run_result.json', base, 'n41_positive'),
        ('n41_positive', 'n41_positive_run_v2_result.json', base, 'n41_positive_v2'),
        ('n41_positive', 'n41_positive_deglex_run_result.json', degree, 'n41_positive_deglex'),
        ('n41_ordinary', 'n41_ordinary_deglex_run_result.json', degree, 'n41_ordinary_deglex')):
    row = read(name)
    assert row['case'] == case
    assert row['protocol_sha256'] == sha(HERE / ('deglex_protocol.json'
                                             if 'deglex' in name else 'protocol.json'))
    assert row['stdout_sha256'] == sha(HERE / (stem+'.stdout'))
    assert row['stderr_sha256'] == sha(HERE / (stem+'.stderr'))
    assert row['candidate_id'] is None
    if name == 'n41_positive_run_result.json':
        assert row['status'] == 'MONITOR_FAILURE'
        assert row['monitor_error'] == 'PermissionError'
        assert row['sampled_peak_combined_rss_bytes'] == 0
    else:
        assert row['status'] == 'BOUNDED_UNKNOWN' and row['stop_reason'] == 'WALL_CAP'
        assert 120 <= row['wall_seconds'] < 122
        assert 0 < row['sampled_peak_combined_rss_bytes'] < protocol['rss_cap_bytes']

rng = random.Random(cfg['sample_seed'])
checks = {}
for case in ('n41_positive', 'n41_ordinary', 'n131_positive_48'):
    F, bases, terms, point, free_a, free_b, fixed_a, fixed_b, known, _curve = solve.load_case(case, base)
    apowers = solve.power_maps(F, [bases[0][j] for j in free_a],
                               solve.product(bases[0], fixed_a))
    bpowers = solve.power_maps(F, [bases[1][j] for j in free_b],
                               solve.product(bases[1], fixed_b))
    coeffs = solve.coeff_map(F, terms, apowers, bpowers, len(free_a))
    assert max(mask.bit_count() for mask in coeffs) <= 4
    cases = [(rng.randrange(1 << len(free_a)),
              rng.randrange(1 << len(free_b))) for _ in range(cfg['samples_per_case'])]
    if known:
        cases.append(known)
    for acode, bcode in cases:
        assignment = sum(((acode >> j) & 1) << k for k, j in enumerate(free_a))
        assignment |= sum(((bcode >> j) & 1) << (len(free_a)+k)
                          for k, j in enumerate(free_b))
        actual = solve.evaluate(F, terms,
                                solve.product(bases[0], acode),
                                solve.product(bases[1], bcode))
        assert solve.eval_anf(coeffs, assignment) == actual
        if known and (acode, bcode) == known:
            assert actual == 0
    checks[case] = {'field_coefficients': len(coeffs),
                    'evaluations': len(cases),
                    'target_point': point}

result = {'status': 'PASS_EXACT_RESULTANT_ANF_REPLAY',
          'candidate_id': None, 'cases': checks,
          'sample_seed': cfg['sample_seed'],
          'protocol_sha256': sha(HERE / 'verify_protocol.json')}
assert not (HERE / 'verification_result.json').exists()
(HERE / 'verification_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, sort_keys=True))
