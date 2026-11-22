"""Read-only check of the public-Q XOR-interface result and replay receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    cfg = load('protocol.json')
    audit_cfg = load('audit_protocol.json')
    for protocol in (cfg, audit_cfg):
        assert protocol['status'].startswith('FROZEN_BEFORE_')
        for name, item in protocol['sources'].items():
            assert sha(item['path']) == item['sha256'], name
    mapping = load('mapping.json')
    result = load('result.json')
    audit = load('audit_result.json')
    assert mapping['status'] == 'PASS_PUBLIC_Q_XOR_INTERFACE_MAP'
    assert mapping['formula_sha256'] == cfg['sources']['formula']['sha256']
    assert mapping['first_three_leaf_variables'] == list(range(2, 32))
    assert mapping['endpoint_selector_variables'] == [1855, 1856]
    assert cfg['interface_variables'] == [1] + mapping['first_three_leaf_variables'] + [1855, 1856]
    assert result['status'] == 'COMPLETE_XOR_INTERFACE_PEEL'
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['native_xor_rows'] == result['peeled_rows'] == 208783
    assert result['residual_rows'] == result['direct_interface_rows'] == 0
    assert result['interface_variables'] == cfg['interface_variables']
    assert result['wall_seconds'] < cfg['wall_cap_seconds']
    assert result['peak_rss_bytes'] < cfg['rss_cap_bytes']
    assert audit['status'] == 'PASS_INDEPENDENT_FULL_XOR_PEEL_AND_REVERSE_REPLAY'
    assert audit['producer_result_sha256'] == sha(HERE / 'result.json')
    assert audit['audit_protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert audit['rows'] == audit['peeled_rows'] == result['peeled_rows']
    assert audit['interface_variables'] == cfg['interface_variables']
    assert audit['full_xor_replay_passes'] == 3
    lean = (HERE / 'lean_check.log').read_text()
    assert "'XorPeel.interface_surjective' depends on axioms: [propext]" in lean
    assert 'sorry' not in (HERE / 'Peel.lean').read_text()
    print(json.dumps({'status': 'PASS_PUBLIC_Q_XOR_INTERFACE_CERTIFICATE',
                      'curve_id': cfg['curve_id'], 'native_xor_rows': result['native_xor_rows'],
                      'peeled_rows': result['peeled_rows'], 'residual_rows': 0,
                      'independent_replays': audit['full_xor_replay_passes']}, sort_keys=True))


if __name__ == '__main__':
    main()
