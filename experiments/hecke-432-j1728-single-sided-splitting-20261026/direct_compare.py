"""Compare sealed left-only predictions with right-polynomial evidence only."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def identity(row):
    return row['prime'], row['right_place_index'], tuple(row['right_ideal_generators'])


def main():
    protocol_path = HERE / 'protocol.json'
    prediction_path = HERE / 'transferred_predictions.json'
    seal_path = HERE / 'observation_protocol.json'
    observation_path = HERE / 'observations.json'
    taylor_protocol_path = HERE / 'taylor_protocol.json'
    taylor_path = HERE / 'taylor_result.json'
    seal = json.loads(seal_path.read_text())
    taylor_protocol = json.loads(taylor_protocol_path.read_text())
    predictions = json.loads(prediction_path.read_text())
    observations = json.loads(observation_path.read_text())
    taylor = json.loads(taylor_path.read_text())
    assert seal['status'] == 'FROZEN_AFTER_LEFT_PREDICTIONS_BEFORE_RIGHT_OBSERVATION'
    assert seal['protocol_sha256'] == digest(protocol_path) == predictions['protocol_sha256']
    assert seal['transferred_predictions_sha256'] == digest(prediction_path)
    assert observations['observation_protocol_sha256'] == digest(seal_path)
    assert taylor_protocol['observation_sha256'] == digest(observation_path)
    assert taylor_protocol['protocol_sha256'] == digest(protocol_path)
    assert taylor['taylor_protocol_sha256'] == digest(taylor_protocol_path)
    assert predictions['status'] == 'PASS_ALL_RIGHT_PREDICTIONS_FROM_LEFT'
    assert observations['status'] == 'PASS_RIGHT_OBSERVATIONS'
    assert taylor['status'] == 'PASS_RIGHT_TAYLOR_CLASSIFICATION'
    predicted = {identity(r): r for r in predictions['rows']}
    observed = {identity(r): r for r in observations['rows']}
    corrected = {identity(r): r for r in taylor['rows']}
    assert len(predicted) == len(predictions['rows'])
    assert len(observed) == len(observations['rows'])
    assert len(corrected) == len(taylor['rows'])
    assert set(predicted) == set(observed)
    rows = []
    for key in sorted(predicted):
        left, right = predicted[key], observed[key]
        assert left['base_residue_degree'] == right['base_residue_degree']
        if right['status'] == 'SQUAREFREE':
            assert key not in corrected
            degrees = right['observed_right_relative_degrees']
            method = 'RIGHT_SQUAREFREE_REDUCTION'
        else:
            assert right['status'] == 'REPEATED_RIGHT_REDUCTION'
            correction = corrected.pop(key)
            assert correction['status'] == 'TAYLOR_CLASSIFIED'
            assert correction['normalized_polynomial_identity_checked'] is True
            assert correction['g_value_valuation'] >= 2
            assert correction['g_derivative_valuation'] >= 1
            degrees = correction['observed_right_relative_degrees']
            method = 'RIGHT_NORMALIZED_TAYLOR'
        rows.append({'prime': key[0], 'right_place_index': key[1],
                     'base_residue_degree': right['base_residue_degree'],
                     'prediction_method': left['method'], 'observation_method': method,
                     'predicted_relative_degrees': left['predicted_right_relative_degrees'],
                     'observed_relative_degrees': degrees,
                     'status': 'MATCH' if left['predicted_right_relative_degrees'] == degrees
                     else 'MISMATCH'})
    assert not corrected
    counts = Counter(r['status'] for r in rows)
    methods = Counter(r['observation_method'] for r in rows)
    out = {'status': 'PASS_ALL_DIRECT_RIGHT_POLYNOMIAL_CHECKS'
           if counts == {'MATCH': len(rows)} else 'FAILED_DIRECT_RIGHT_POLYNOMIAL_CHECKS',
           'protocol_sha256': digest(protocol_path),
           'sealed_prediction_sha256': digest(prediction_path),
           'observation_sha256': digest(observation_path),
           'taylor_result_sha256': digest(taylor_path),
           'source_sha256': digest(Path(__file__)),
           'counts': dict(counts), 'observation_method_counts': dict(methods), 'rows': rows}
    (HERE / 'direct_comparison.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'counts': out['counts'],
                      'observation_method_counts': out['observation_method_counts']},
                     sort_keys=True))


if __name__ == '__main__':
    main()
