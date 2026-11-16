"""Independent exhaustive residue audit of public-scalar recovery events."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / 'public-recovery-audit-protocol.json').read_text())
    assert protocol['schema'] == 'xedni-public-recovery-audit-protocol-v1'
    for key, name in [('recovery_protocol_sha256', 'public-recovery-protocol.json'),
                      ('recovery_result_sha256', 'public-recovery-result.json'),
                      ('parent_result_sha256', 'result.json'),
                      ('audit_source_sha256', 'public_recovery_audit.py')]:
        assert protocol[key] == sha(HERE / name), key
    result = json.loads((HERE / 'result.json').read_text())
    recovery = json.loads((HERE / 'public-recovery-result.json').read_text())
    assert recovery['status'] == 'PASS'
    rows = []
    total = 0
    for parent, checked in zip(result['fields'], recovery['fields'], strict=True):
        q = parent['subgroup_order']
        assert q == checked['subgroup_order']
        assert sha(HERE / parent['events_path']) == parent['events_sha256']
        count = 0
        for line in (HERE / parent['events_path']).read_text().splitlines():
            event = json.loads(line)
            a, b = event['vector']
            t1, t2 = event['t']
            solutions = [w for w in range(q)
                         if (a * (w - t1) + b * (w - t2)) % q == 0]
            assert solutions == [event['recovered_scalar']]
            count += 1
        assert count == checked['public_hits_replayed']
        rows.append({'field_prime': parent['field_prime'], 'subgroup_order': q,
                     'unique_solutions_checked': count})
        total += count
    assert total == recovery['total_public_hits_replayed'] == 142
    output = {'schema': 'xedni-public-recovery-audit-v1', 'status': 'PASS',
              'protocol_sha256': sha(HERE / 'public-recovery-audit-protocol.json'),
              'source_sha256': sha(Path(__file__)), 'rows': rows,
              'total_unique_solutions_checked': total,
              'method': 'exhaustive residue enumeration, independent of inversion formula'}
    (HERE / 'public-recovery-audit.json').write_text(
        json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'unique_solutions_checked': total}, sort_keys=True))


if __name__ == '__main__':
    main()
