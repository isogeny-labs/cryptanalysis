"""Replay hashes and compare unrestricted roots to archived valid-code census."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cfg = json.loads((HERE / 'protocol.json').read_text())
for name, digest in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == digest, name
current = json.loads((HERE / 'result.json').read_text())
prior = json.loads((ROOT / cfg['prior_census']).read_text())
assert current['status'] == 'COMPLETE_N41_W11_ALLCODE_RESULTANT_CENSUS'
assert current['candidate_id'] is None
assert (current['all_codes'], current['archived_valid_codes']) == (1024, 281)
assert len(current['targets']) == len(prior['rows']) == 25
assert current['total_zero_pairs'] == sum(r['all_code_zero_pairs'] for r in current['targets'])
assert current['total_both_valid_zero_pairs'] == sum(r['both_valid_zero_pairs'] for r in current['targets'])
assert current['total_invalid_zero_pairs'] == sum(r['at_least_one_invalid_zero_pairs'] for r in current['targets'])
for new, old in zip(current['targets'], prior['rows']):
    assert new['index'] == old['index']
    assert new['target_point'] == old['target_point']
    assert new['all_code_zero_pairs'] == len(new['zero_pairs'])
    assert new['both_valid_zero_pairs'] == old['raw_zero_code_pairs']
    assert sorted(set(map(tuple, new['zero_pairs']))) == sorted(set(map(tuple, old['zero_pairs'])))
assert current['targets'][0]['zero_pairs'] == [[253, 63]]
assert all(not row['zero_pairs'] for row in current['targets'][1:])
out = {
    'status': 'PASS_N41_W11_ALLCODE_FILTER_REPLAY',
    'candidate_id': None,
    'result_sha256': sha(HERE / 'result.json'),
    'protocol_sha256': sha(HERE / 'protocol.json'),
    'evaluated_code_pairs': 25 * 1024 * 1024,
    'total_zero_pairs': current['total_zero_pairs'],
    'total_invalid_zero_pairs': current['total_invalid_zero_pairs'],
}
(HERE / 'verification_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
