"""Read-only hash and result audit for the implicit W9 pair oracle."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    for name in ('panel_protocol.json', 'query_protocol.json',
                 'audit_protocol.json', 'work_protocol.json'):
        row = load(name)
        for source, expected in row['source_sha256'].items():
            path = Path(source)
            if not path.is_absolute():
                path = ROOT / path
            assert sha(path) == expected, source
    panel = (HERE / 'panel.tsv').read_text().splitlines()
    assert len(panel) == 385
    assert panel[0].split()[:5] == ['P', '3', '233', '283', '152']
    assert [line.split()[0] for line in panel[1:]] == ['M'] * 384
    assert [int(line.split()[1]) for line in panel[1:]] == [0]*128+[1]*128+[2]*128
    query = load('query_result.json')
    audit = load('audit_result.json')
    work = load('work_result.json')
    assert query['status'] == 'COMPLETE_PENDING_INDEPENDENT_REPLAY'
    assert query['candidate_id'] is None
    assert query['exit_code'] == 0 and query['stop_reason'] is None
    assert query['monitor_error'] is None and query['case_count'] == 385
    assert query['parent_wall_seconds'] < load('query_protocol.json')['query_wall_cap_seconds']
    assert query['sampled_peak_combined_rss_bytes'] < load('query_protocol.json')['rss_cap_bytes']
    assert query['stdout_sha256'] == sha(HERE / 'query.stdout')
    assert query['stderr_sha256'] == sha(HERE / 'query.stderr')
    assert not (HERE / 'query.stderr').read_bytes()
    assert query['protocol_sha256'] == sha(HERE / 'query_protocol.json')
    assert query['total_lines'] == ['TOTAL 385 109340 1 1']
    assert audit['status'] == 'PASS_INDEPENDENT_N41_IMPLICIT_PAIR_PANEL'
    assert audit['positive_cases'] == 1 and audit['target_derived_cases'] == 384
    assert audit['all_pair_hits'] == 1 and audit['first_positive_state_ids'] == [0, 130]
    assert audit['query_result_sha256'] == sha(HERE / 'query_result.json')
    assert audit['audit_protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert audit['auditor_sha256'] == sha(HERE / 'audit_sage.py')
    assert work['status'] == 'EXACT_SERIAL_POLICY_WORK_FLOOR'
    assert work['reference_join_lookups'] == 83612805
    assert work['reference_join_hash_matches'] == 2
    assert work['minimum_complete_miss_keys'] == 83612803
    assert work['first_slot_states'] == 284
    assert work['minimum_first_state_checks'] == 23746036052
    assert work['protocol_sha256'] == sha(HERE / 'work_protocol.json')
    assert 'depends on axioms: [propext]' in (HERE / 'lean.stdout').read_text()
    assert not (HERE / 'lean.stderr').read_bytes()
    print(json.dumps({'status': 'PASS_W9_IMPLICIT_PAIR_ORACLE_RECEIPTS',
                      'panel_cases': 385, 'independent_pair_hits': 1,
                      'minimum_full_path_serial_checks':
                      work['minimum_first_state_checks']}, sort_keys=True))


if __name__ == '__main__':
    main()
