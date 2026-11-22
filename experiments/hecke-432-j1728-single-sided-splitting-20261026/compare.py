"""Audit sealed single-sided predictions against independent right checks."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def key(row):
    return (row['prime'], row['right_place_index'],
            tuple(row['right_ideal_generators']), row['base_residue_degree'])


def main():
    protocol_path = HERE / 'protocol.json'
    prediction_path = HERE / 'transferred_predictions.json'
    seal_path = HERE / 'observation_protocol.json'
    observation_path = HERE / 'observations.json'
    control_path = HERE / 'right_kummer_protocol.json'
    right_kummer_path = HERE / 'right_kummer_observations.json'
    seal = json.loads(seal_path.read_text())
    control = json.loads(control_path.read_text())
    predictions = json.loads(prediction_path.read_text())
    observations = json.loads(observation_path.read_text())
    right_kummer = json.loads(right_kummer_path.read_text())
    assert seal['status'] == 'FROZEN_AFTER_LEFT_PREDICTIONS_BEFORE_RIGHT_OBSERVATION'
    assert seal['protocol_sha256'] == digest(protocol_path) == predictions['protocol_sha256']
    assert seal['transferred_predictions_sha256'] == digest(prediction_path)
    assert observations['observation_protocol_sha256'] == digest(seal_path)
    assert control['observation_sha256'] == digest(observation_path)
    assert control['transferred_predictions_sha256'] == digest(prediction_path)
    assert right_kummer['right_kummer_protocol_sha256'] == digest(control_path)
    assert predictions['status'] == 'PASS_ALL_RIGHT_PREDICTIONS_FROM_LEFT'
    assert observations['status'] == 'PASS_RIGHT_OBSERVATIONS'
    assert right_kummer['status'] == 'PASS_RIGHT_KUMMER_CHECK'
    predicted = {key(r): r for r in predictions['rows']}
    observed = {key(r): r for r in observations['rows']}
    supplemental = {key(r): r for r in right_kummer['rows']}
    assert len(predicted) == len(predictions['rows'])
    assert len(observed) == len(observations['rows'])
    assert len(supplemental) == len(right_kummer['rows'])
    assert set(predicted) == set(observed)
    rows = []
    for identity in sorted(predicted):
        p, j, _, f_base = identity
        a, b = predicted[identity], observed[identity]
        if b['status'] == 'SQUAREFREE':
            assert identity not in supplemental
            actual = b['observed_right_relative_degrees']
            observation_method = 'RIGHT_QUARTIC_SQUAREFREE_REDUCTION'
        else:
            assert b['status'] == 'REPEATED_RIGHT_REDUCTION'
            c = supplemental.pop(identity)
            assert c['status'] == 'RIGHT_KUMMER_CLASSIFIED'
            actual = c['observed_right_relative_degrees']
            observation_method = 'RIGHT_KUMMER_UNIT_CHARACTERS'
        predicted_degrees = a['predicted_right_relative_degrees']
        rows.append({'prime': p, 'right_place_index': j, 'base_residue_degree': f_base,
                     'prediction_method': a['method'],
                     'observation_method': observation_method,
                     'predicted_right_relative_degrees': predicted_degrees,
                     'observed_right_relative_degrees': actual,
                     'status': 'MATCH' if predicted_degrees == actual else 'MISMATCH'})
    assert not supplemental
    counts = Counter(r['status'] for r in rows)
    methods = Counter((r['prediction_method'], r['observation_method']) for r in rows)
    out = {'status': 'PASS_ALL_SINGLE_SIDED_TRANSFERS' if counts == {'MATCH': len(rows)}
           else 'FAILED_SINGLE_SIDED_TRANSFERS',
           'protocol_sha256': digest(protocol_path),
           'prediction_sha256': digest(prediction_path),
           'observation_sha256': digest(observation_path),
           'right_kummer_sha256': digest(right_kummer_path),
           'source_sha256': digest(Path(__file__)),
           'counts': dict(counts),
           'method_counts': [{'prediction_method': a, 'observation_method': b, 'rows': n}
                             for (a, b), n in sorted(methods.items())],
           'rows': rows}
    (HERE / 'comparison.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'counts': out['counts'],
                      'method_counts': out['method_counts']}, sort_keys=True))


if __name__ == '__main__':
    main()
