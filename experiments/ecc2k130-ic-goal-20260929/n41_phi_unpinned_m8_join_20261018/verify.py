"""Read-only integrity check for the frozen N41 phi eight-leaf experiment."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                     ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def main():
    protocol = load('protocol.json')
    for name, item in protocol['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    correction = load('identity_correction.json')
    assert correction['status'] == 'PASS_CURVE_IDENTITY_CORRECTION'
    assert correction['original_curve_id'] == protocol['curve_id']
    curve = dict(correction['curve'])
    assert curve['G'] == [455966146946, 419221426429]
    assert correction['corrected_curve_id'] == 'EC1N41Ckb1h' + digest({
        'field': correction['field'], 'curve': curve})[:12]
    for name, key in [('export_result.json', 'export_result_sha256'),
                      ('public_input.tsv', 'public_input_sha256'),
                      ('public_receipt.json', 'public_receipt_sha256'),
                      ('public_audit.json', 'public_audit_sha256'),
                      ('row_result.json', 'row_result_sha256')]:
        assert sha(HERE / name) == correction[key], name

    public = load('public_receipt.json')
    positive = load('positive_receipt.json')
    assert public['status'] == 'COMPLETE_HIT' and public['monitor_misses'] == 0
    assert positive['status'] == 'PRODUCER_FAILURE' and positive['monitor_misses'] == 1
    assert all(rec['protocol_sha256'] == sha(HERE / 'protocol.json')
               for rec in (public, positive))
    for arm, receipt in [('positive', positive), ('public', public)]:
        audit = load(arm + '_audit.json')
        assert audit['status'] == 'PASS_INDEPENDENT_N41_PHI_EIGHT_LEAF_REPLAY'
        assert audit['input_sha256'] == sha(HERE / (arm + '_input.tsv'))
        assert audit['stdout_sha256'] == receipt['stdout_sha256'] == sha(HERE / (arm + '.stdout'))
        assert receipt['stderr_sha256'] == sha(HERE / (arm + '.stderr'))
        assert len(audit['state_ids']) == 8
        assert len(set(audit['folded_columns'])) == 8
        assert len(receipt['hit_lines']) == 1
        native_ids = [int(x) for x in receipt['hit_lines'][0].split()[1:9]]
        assert native_ids == audit['state_ids']
    assert load('public_gate.json')['positive_receipt_sha256'] == sha(HERE / 'positive_receipt.json')
    row = load('row_result.json')
    assert row['status'] == 'PASS_UNPINNED_N41_PHI_EIGHT_COLUMN_RELATION'
    assert row['public_audit_sha256'] == sha(HERE / 'public_audit.json')
    assert row['factor_base_points_before_folding'] == 2132
    assert row['folded_columns'] == 26 and len(row['nonzero_row']) == 8
    assert {item['column'] for item in row['nonzero_row']} == set(load('public_audit.json')['folded_columns'])
    assert row['subgroup_order'] == correction['curve']['r']
    lean = (HERE / 'lean_check.log').read_text()
    assert "'EightJoin.target_lookup' does not depend on any axioms" in lean
    assert "'EightJoin.four_plus_four_is_eight' depends on axioms: [propext]" in lean
    assert 'sorry' not in (HERE / 'EightJoin.lean').read_text()
    print(json.dumps({'status': 'PASS_FROZEN_RECEIPTS_AND_IDENTITY',
                      'curve_id': correction['corrected_curve_id'],
                      'public_wall_ns': public['wall_ns'],
                      'public_sampled_peak_rss_bytes': public['sampled_peak_combined_rss_bytes'],
                      'folded_columns': row['folded_columns']}, sort_keys=True))


if __name__ == '__main__':
    main()
