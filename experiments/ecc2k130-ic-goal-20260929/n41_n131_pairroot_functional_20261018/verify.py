"""Replay source hashes, build controls, and both fixed-conflict probes."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name in ('n41_protocol.json', 'n131_protocol.json', 'build_protocol_v2.json',
             'source_build_protocol.json', 'probe_protocol.json', 'source_probe_protocol.json'):
    path = here/name
    protocol = json.loads(path.read_text())
    for source, digest in protocol['sources'].items():
        assert sha(source) == digest, (name, source)

for mode, count, qcount in [('n41', 71, 1), ('n131', 514, 2)]:
    result = json.loads((here/f'{mode}_result.json').read_text())
    assert result['status'] == 'PASS_FUNCTIONAL_ROOT_AUDIT'
    assert result['source_count'] == count and len(result['queries']) == qcount
    assert result['protocol_sha256'] == sha(here/f'{mode}_protocol.json')
    for query in result['queries']:
        assert query['case_counts'] == {'four_roots': count}
        assert all(len(row['pair_roots']) == 2 and len(row['target_roots']) == 4
                   for row in query['sources'])
assert [q['sample_source_pair_hits'] for q in
        json.loads((here/'n131_result.json').read_text())['queries']] == [[[512, 513]], []]

for prefix, status, protocol in [('', 'PASS_N41_FUNCTIONAL_PAIR_ROOT_CIRCUIT', 'build_protocol_v2.json'),
                                 ('source_', 'PASS_N41_SOURCE_FUNCTIONAL_ROOT_CIRCUIT', 'source_build_protocol.json')]:
    result = json.loads((here/f'{prefix}build_result.json').read_text())
    assert result['status'] == status
    assert result['protocol_sha256'] == sha(here/protocol)
    assert result['formula_sha256'] == sha(here/f'{prefix}formula.xcnf')
    assert result['input_wires_sha256'] == sha(here/f'{prefix}input_wires.json')
    assert len(result['controls_checked']) == 33
    assert all(row['pair_zero'] and row['s3_zero'] and
               row['preceding_zero'] == (row['kind'] == 'positive')
               for row in result['controls_checked'])

for prefix, variant in [('', 'functional'), ('source_', 'source_functional')]:
    result = json.loads((here/f'{prefix}probe_result.json').read_text())
    assert result['status'] == 'COMPLETED_FROZEN_ABBA_PROBE'
    assert result['protocol_sha256'] == sha(here/f'{prefix}probe_protocol.json')
    arms = result['arm_results']
    assert [row['arm'] for row in arms] == ['quadratic', variant, variant, 'quadratic']
    assert all(row['status'] == 'INDETERMINATE_CONFLICT_CAP' and
               row['reported_conflicts'] >= 20000 and row['monitor_error'] is None
               for row in arms)
    for i,j in ((1,0),(2,3)):
        decision_ratio = arms[i]['reported_decisions']/arms[j]['reported_decisions']
        wall_ratio = arms[i]['wall_seconds']/arms[j]['wall_seconds']
        assert decision_ratio > 0.8 or wall_ratio > 1.25
        print(prefix or 'full_', 'pair', i,j, 'decision_ratio', round(decision_ratio,4),
              'wall_ratio', round(wall_ratio,4))

lean = (here/'lean_check.log').read_text()
assert (here/'lean_exit_code.txt').read_text().strip() == '0'
assert all(f"'{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
           for name in ('FunctionalRoots.source_normalization',
                        'FunctionalRoots.target_normalization',
                        'FunctionalRoots.two_branch_completeness'))
assert not any(token in (here/'FunctionalRoots.lean').read_text() for token in ('sorry', 'admit', 'sorryAx'))
print('PASS_FUNCTIONAL_ROOT_EVIDENCE_REPLAY')
