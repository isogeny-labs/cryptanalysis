"""Replay target-scalar recovery from saved public relations and offsets."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / 'public-recovery-protocol.json').read_text())
    assert freeze['schema'] == 'xedni-public-recovery-protocol-v1'
    assert digest(HERE / 'result.json') == freeze['parent_result_sha256']
    assert digest(HERE / 'formal/PublicRecovery.lean') == freeze['lean_source_sha256']
    assert digest(Path(__file__)) == freeze['source_sha256']
    parent = json.loads((HERE / 'result.json').read_text())
    fixture = json.loads((HERE / 'protocol.json').read_text())['target_scalar']
    rows = []
    total = 0
    for field in parent['fields']:
        q = field['subgroup_order']
        path = HERE / field['events_path']
        assert digest(path) == field['events_sha256']
        values = []
        for line in path.read_text().splitlines():
            event = json.loads(line)
            a, b = event['vector']
            t1, t2 = event['t']
            denominator = (a + b) % q
            assert denominator != 0
            recovered = ((a * t1 + b * t2) * pow(denominator, -1, q)) % q
            assert recovered == event['recovered_scalar'] == fixture % q
            values.append(recovered)
        assert len(values) == field['counts']['public_hits']
        rows.append({'field_prime': field['field_prime'], 'subgroup_order': q,
                     'public_hits_replayed': len(values),
                     'recovered_scalar_set': sorted(set(values))})
        total += len(values)
    assert total == 142
    output = {'schema': 'xedni-public-recovery-result-v1', 'status': 'PASS',
              'protocol_sha256': digest(HERE / 'public-recovery-protocol.json'),
              'source_sha256': digest(Path(__file__)), 'fields': rows,
              'total_public_hits_replayed': total,
              'recovery_inputs': ['vector', 'offsets', 'subgroup_order'],
              'fixture_used_for_recovery': False,
              'fixture_used_for_post_recovery_check': True}
    (HERE / 'public-recovery-result.json').write_text(
        json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'public_hits_replayed': total}, sort_keys=True))


if __name__ == '__main__':
    main()
