"""Read-only integrity check of both exact Q1358 pair enumerations."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = load('protocol.json')
    audit_protocol = load('audit_protocol.json')
    for cfg in (protocol, audit_protocol):
        assert cfg['status'].startswith('FROZEN_BEFORE_')
        for name, item in cfg['sources'].items():
            assert sha(item['path']) == item['sha256'], name
    result = load('result.json')
    audit = load('audit_result.json')
    assert result['status'] == 'COMPLETE_EXACT_SIGNED_PAIR_OCCUPANCY'
    assert audit['status'] == 'PASS_INDEPENDENT_DIRECT_PAIR_ENUMERATION'
    assert result['curve_id'] == audit['curve_id'] == protocol['curve_id']
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert audit['audit_protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert audit['result_sha256'] == sha(HERE / 'result.json')
    assert result['signed_pair_combinations'] == audit['combinations'] == 1064**2
    assert result['distinct_partial_sums'] == audit['distinct_partial_sums'] == 1064**2
    assert result['collision_excess'] == audit['collision_excess'] == 0
    assert result['group_additions'] == 2 * 532**2
    assert result['first_duplicate_witnesses'] == [] and audit['first_collision'] is None
    assert result['wall_seconds'] < protocol['wall_cap_seconds']
    assert result['peak_rss_bytes'] < protocol['rss_cap_bytes']
    assert audit['wall_seconds'] < audit_protocol['audit_wall_cap_seconds']
    assert audit['peak_rss_bytes'] < audit_protocol['audit_rss_cap_bytes']
    lean = (HERE / 'lean_check.log').read_text()
    assert "'PairSigns.mirrored_sum' depends on axioms: [propext]" in lean
    assert 'sorry' not in (HERE / 'PairSigns.lean').read_text()
    print(json.dumps({'status': 'PASS_EXACT_PAIR_OCCUPANCY_AND_AUDIT',
                      'curve_id': result['curve_id'],
                      'signed_pair_combinations': result['signed_pair_combinations'],
                      'distinct_partial_sums': result['distinct_partial_sums']}, sort_keys=True))


if __name__ == '__main__':
    main()
