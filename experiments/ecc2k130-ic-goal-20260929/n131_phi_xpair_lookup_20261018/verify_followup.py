"""Read-only check of supplementary coset and first-attempt provenance."""
import json
from pathlib import Path

from verify import sha

HERE = Path(__file__).resolve().parent


def main():
    cfg = json.loads((HERE / 'protocol.json').read_text())
    full = json.loads((HERE / 'full_result.json').read_text())
    xrun = json.loads((HERE / 'x_result.json').read_text())
    result = json.loads((HERE / 'coset_audit.json').read_text())
    assert result['status'] == 'PASS_EXACT_RAW_LIFT_COSET_AUDIT'
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['geometry_sha256'] == cfg['sources']['geometry']['sha256']
    assert result['script_sha256'] == sha(HERE / 'coset_audit_sage.py')
    assert result['query_key_stream_sha256'] == full['ordinary_query_key_stream_sha256'] == xrun['ordinary_query_key_stream_sha256']
    assert result['signed_pair_torsion_classes'] == 4
    assert result['torsion_eligible_queries_per_endpoint'] == [256] * 4
    for record_name, source_name, protocol_name in (
        ('attempt1_failure.json', 'n41_control_attempt1_sage.py', 'protocol_attempt1.json'),
        ('coset_attempt1_failure.json', 'coset_audit_attempt1_sage.py', None),
    ):
        record = json.loads((HERE / record_name).read_text())
        key = ('n41_control_source_sha256' if record_name == 'attempt1_failure.json'
               else 'script_sha256')
        assert record[key] == sha(HERE / source_name)
        if protocol_name:
            assert record['protocol_sha256'] == sha(HERE / protocol_name)
        assert record['exit_code'] == 1
    print(json.dumps({'status': 'FOLLOWUP_REPLAY_PASS',
                      'torsion_eligible_queries': sum(result['torsion_eligible_queries_per_endpoint']),
                      'preserved_failed_sources': 2}, sort_keys=True))


if __name__ == '__main__':
    main()
