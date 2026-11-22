"""Read-only source, count, query-stream, and positive-control receipt check."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_INDEX'
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    full = json.loads((HERE / 'full_result.json').read_text())
    xrun = json.loads((HERE / 'x_result.json').read_text())
    audit = json.loads((HERE / 'audit_result.json').read_text())
    n41 = json.loads((HERE / 'n41_control_result.json').read_text())
    for result in (full, xrun, audit, n41):
        assert result['protocol_sha256'] == sha(cfg_path)
    assert full['status'] == xrun['status'] == 'COMPLETE_EXACT_PAIR_LOOKUP'
    assert (full['index_entries'], xrun['index_entries']) == (1132096, 566048)
    assert full['signed_pairs_covered'] == xrun['signed_pairs_covered'] == 1132096
    assert full['group_additions'] == xrun['group_additions'] == 566048
    assert full['x_keyset_sha256'] == xrun['x_keyset_sha256'] == audit['x_keyset_sha256']
    assert full['ordinary_query_key_stream_sha256'] == xrun['ordinary_query_key_stream_sha256']
    assert full['ordinary_target_query_count'] == xrun['ordinary_target_query_count'] == 1024
    assert full['ordinary_hits'] == xrun['ordinary_hits'] == []
    assert audit['status'] == 'PASS_INDEPENDENT_FOUR_SIGN_KEYSET_AND_QUERY_REPLAY'
    assert audit['point_keys'] == 1132096 and audit['x_keys'] == 566048
    assert audit['ordinary_x_key_hits'] == 0
    assert n41['status'] == 'PASS_N41_PUBLIC_TARGET_XPAIR_HIT'
    assert [0, 130] in n41['matching_left_state_ids']
    assert n41['x_rejected_families'] <= n41['target_conditioned_family_queries']
    for result in (full, xrun, audit, n41):
        assert result['peak_rss_bytes'] <= cfg['rss_cap_bytes']
    for result in (full, xrun):
        assert result['total_script_seconds'] <= cfg['build_wall_cap_seconds']
    print(json.dumps({'status': 'REPLAY_PASS',
                      'full_entries': full['index_entries'],
                      'x_entries': xrun['index_entries'],
                      'n41_hit': n41['matching_left_state_ids'],
                      'n131_ordinary_queries': full['ordinary_target_query_count']},
                     sort_keys=True))


if __name__ == '__main__':
    main()
