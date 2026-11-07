"""Audit direct Taylor resolution of all repeated right quartic reductions."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    control_path = HERE / 'taylor_protocol.json'
    result_path = HERE / 'taylor_result.json'
    control = json.loads(control_path.read_text())
    result = json.loads(result_path.read_text())
    predictions = json.loads((HERE / 'transferred_predictions.json').read_text())
    observations = json.loads((HERE / 'observations.json').read_text())
    kummer = json.loads((HERE / 'right_kummer_observations.json').read_text())
    assert control['status'] == 'FROZEN_BEFORE_RIGHT_TAYLOR_REPLAY'
    assert result['status'] == 'PASS_RIGHT_TAYLOR_CLASSIFICATION'
    assert result['taylor_protocol_sha256'] == digest(control_path)
    assert control['protocol_sha256'] == digest(HERE / 'protocol.json')
    assert control['observation_sha256'] == digest(HERE / 'observations.json')
    assert len(result['rows']) == control['site_count'] == len(control['sites']) == 6
    predicted = {(r['prime'], r['right_place_index']): r for r in predictions['rows']}
    observed = {(r['prime'], r['right_place_index']): r for r in observations['rows']}
    extra = {(r['prime'], r['right_place_index']): r for r in kummer['rows']}
    rows = []
    for site, row in zip(control['sites'], result['rows']):
        key = site['prime'], site['right_place_index']
        assert (row['prime'], row['right_place_index']) == key
        assert row['right_ideal_generators'] == site['right_ideal_generators']
        assert row['base_residue_degree'] == site['base_residue_degree']
        assert observed[key]['status'] == 'REPEATED_RIGHT_REDUCTION'
        assert row['normalized_polynomial_identity_checked'] is True
        assert row['g_value_valuation'] >= 2 and row['g_derivative_valuation'] >= 1
        assert row['status'] == 'TAYLOR_CLASSIFIED'
        degrees = row['observed_right_relative_degrees']
        assert degrees == predicted[key]['predicted_right_relative_degrees']
        assert degrees == extra[key]['observed_right_relative_degrees']
        rows.append({'prime': key[0], 'right_place_index': key[1],
                     'relative_degrees': degrees,
                     'discriminant_character': row['discriminant_character'],
                     'status': 'TAYLOR_PREDICTION_KUMMER_MATCH'})
    assert len({(r['prime'], r['right_place_index']) for r in rows}) == len(rows)
    out = {'status': 'PASS_ALL_DOUBLE_ROOT_TAYLOR_CHECKS',
           'taylor_protocol_sha256': digest(control_path),
           'taylor_result_sha256': digest(result_path),
           'prediction_sha256': digest(HERE / 'transferred_predictions.json'),
           'right_kummer_sha256': digest(HERE / 'right_kummer_observations.json'),
           'source_sha256': digest(Path(__file__)), 'rows': rows,
           'matched': len(rows)}
    (HERE / 'taylor_audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'matched': out['matched']}, sort_keys=True))


if __name__ == '__main__':
    main()
