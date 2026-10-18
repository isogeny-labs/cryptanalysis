"""Replay source hashes, independent ranks, and Lean projection theorem."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cfg = json.loads((HERE / 'verification_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    path = Path(name)
    if not path.is_absolute():
        path = WORKSPACE / path
    assert sha(path) == expected, name
result = json.loads((HERE / 'result.json').read_text())
audit = json.loads((HERE / 'audit_result.json').read_text())
assert result['status'] == 'COMPLETE_RESULTANT_TOPDEGREE_RANK'
assert result['candidate_id'] is None
assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
assert audit['status'] == 'PASS_INDEPENDENT_SAGE_TOPDEGREE_RANK'
assert audit['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
assert len(result['rows']) == len(audit['rows']) == 4


def rank(values):
    pivots = {}
    for value in values:
        while value:
            bit = value.bit_length()-1
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    return len(pivots)


for row, independently_checked in zip(result['rows'], audit['rows']):
    degree = row['field_degree']
    assert degree == independently_checked['field_degree']
    assert row['target_index'] == independently_checked['target_index']
    assert row['q_pair_rank'] == independently_checked['q_pair_rank']
    assert row['q_pair_rank'] == rank([p['value'] for p in row['q_pair_pivots']])
    assert row['p_first_pair_coefficient'] != 0 and row['c33'] != 0
    got = [[b['first_free_bits'], b['coefficient_rank']] for b in row['block_ranks']]
    assert got == independently_checked['block_ranks']
    if degree == 41:
        assert row['q_pair_count'] == 45 and row['q_pair_rank'] == 37
        assert got == [[2,37],[3,41],[4,41],[5,41]]
    else:
        assert row['q_pair_count'] == 496 and row['q_pair_rank'] == 131
        assert got == [[2,131],[3,131],[4,131]]
source = (HERE / 'TopDegreeSpan.lean').read_text()
log = (HERE / 'lean_check.log').read_text()
for token in ('sorry', 'admit', 'sorryAx', 'unsafe', '\naxiom '):
    assert token not in source
assert 'error:' not in log and 'sorryAx' not in log
assert "'TopDegreeSpan.full_span_annihilator_zero' depends on axioms:" in log
assert 'propext' in log and 'Classical.choice' in log and 'Quot.sound' in log
out = {'status': 'PASS_TOPDEGREE_RANK_REPLAY', 'candidate_id': None,
       'curve_ids': json.loads((HERE / 'protocol.json').read_text())['curve_ids'],
       'n131_q_pair_rank': 131, 'n131_quartic_rank_from_two_first_bits': 131,
       'n41_q_pair_rank': 37, 'n41_quartic_rank_from_three_first_bits': 41,
       'result_sha256': sha(HERE / 'result.json'),
       'audit_sha256': sha(HERE / 'audit_result.json'),
       'protocol_sha256': sha(HERE / 'verification_protocol.json')}
(HERE / 'verification_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
