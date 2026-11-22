"""Compare sealed V4 shortcut predictions with direct right-polynomial evidence."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def key(row):
    return row['prime'], row['right_place_index'], tuple(row['right_ideal_generators'])


def main():
    protocol_path = HERE / 'protocol.json'
    prediction_path = HERE / 'combined_predictions.json'
    seal_path = HERE / 'observation_protocol.json'
    observation_path = HERE / 'observations.json'
    taylor_control_path = HERE / 'taylor_protocol.json'
    taylor_path = HERE / 'taylor_result.json'
    predictions = json.loads(prediction_path.read_text())
    seal = json.loads(seal_path.read_text())
    observations = json.loads(observation_path.read_text())
    taylor_control = json.loads(taylor_control_path.read_text())
    taylor = json.loads(taylor_path.read_text())
    assert predictions['status'] == 'PASS_COMPLETE_SHORTCUT_PREDICTIONS'
    assert seal['status'] == 'FROZEN_AFTER_SHORTCUT_PREDICTIONS_BEFORE_RIGHT_OBSERVATION'
    assert seal['protocol_sha256'] == predictions['protocol_sha256'] == digest(protocol_path)
    assert seal['combined_predictions_sha256'] == digest(prediction_path)
    assert observations['observation_protocol_sha256'] == digest(seal_path)
    assert taylor_control['observation_sha256'] == digest(observation_path)
    assert taylor_control['sealed_prediction_sha256'] == digest(prediction_path)
    assert taylor['taylor_protocol_sha256'] == digest(taylor_control_path)
    assert observations['status'] == 'PASS_RIGHT_OBSERVATIONS'
    assert taylor['status'] == 'PASS_TAYLOR_CLASSIFICATION'
    predicted = {key(r): r for r in predictions['rows']}
    observed = {key(r): r for r in observations['rows']}
    resolved = {key(r): r for r in taylor['rows']}
    assert len(predicted) == len(predictions['rows'])
    assert len(observed) == len(observations['rows'])
    assert len(resolved) == len(taylor['rows'])
    assert set(predicted) == set(observed)
    rows = []
    for identity in sorted(predicted):
        a, b = predicted[identity], observed[identity]
        assert a['base_residue_degree'] == b['base_residue_degree']
        if b['status'] == 'SQUAREFREE':
            assert identity not in resolved
            degrees = b['observed_right_relative_degrees']
            method = 'RIGHT_SQUAREFREE_REDUCTION'
        else:
            assert b['status'] == 'REPEATED_REDUCTION'
            c = resolved.pop(identity)
            assert c['status'] == 'TAYLOR_CLASSIFIED'
            assert all(v['normalized_polynomial_identity_checked'] for v in c['clusters'])
            degrees = c['observed_right_relative_degrees']
            method = 'RIGHT_NORMALIZED_TAYLOR'
        rows.append({'prime': identity[0], 'right_place_index': identity[1],
                     'base_residue_degree': b['base_residue_degree'],
                     'prediction_method': a['method'], 'observation_method': method,
                     'predicted_relative_degrees': a['predicted_right_relative_degrees'],
                     'observed_relative_degrees': degrees,
                     'status': 'MATCH' if a['predicted_right_relative_degrees'] == degrees
                     else 'MISMATCH'})
    assert not resolved
    counts = Counter(r['status'] for r in rows)
    predictions_by_method = Counter(r['prediction_method'] for r in rows)
    observations_by_method = Counter(r['observation_method'] for r in rows)
    out = {'status': 'PASS_PROSPECTIVE_V4_FACTOR_SHORTCUTS'
           if counts == {'MATCH': len(rows)} else 'FAIL_PROSPECTIVE_V4_FACTOR_SHORTCUTS',
           'protocol_sha256': digest(protocol_path),
           'sealed_predictions_sha256': digest(prediction_path),
           'observations_sha256': digest(observation_path),
           'taylor_result_sha256': digest(taylor_path),
           'source_sha256': digest(Path(__file__)),
           'counts': dict(counts),
           'prediction_method_counts': dict(predictions_by_method),
           'observation_method_counts': dict(observations_by_method),
           'rows': rows}
    (HERE / 'comparison.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'counts': out['counts'],
                      'prediction_method_counts': out['prediction_method_counts'],
                      'observation_method_counts': out['observation_method_counts']},
                     sort_keys=True))


if __name__ == '__main__':
    main()
