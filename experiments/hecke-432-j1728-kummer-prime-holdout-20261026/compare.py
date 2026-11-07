"""Audit the prospective prediction seal and compare exact base-place rows."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def key(row):
    return (row['prime'], row['base_place_index'], row['side'],
            tuple(row['ideal_generators']), row['base_residue_degree'])


def main():
    protocol_path = HERE / 'protocol.json'
    seal_path = HERE / 'observation_protocol.json'
    prediction_path = HERE / 'predictions.json'
    observation_path = HERE / 'observations.json'
    protocol = json.loads(protocol_path.read_text())
    seal = json.loads(seal_path.read_text())
    predictions = json.loads(prediction_path.read_text())
    observations = json.loads(observation_path.read_text())
    assert seal['status'] == 'FROZEN_AFTER_PREDICTION_BEFORE_QUARTIC_OBSERVATION'
    assert digest(protocol_path) == seal['protocol_sha256'] == predictions['protocol_sha256']
    assert digest(prediction_path) == seal['prediction_sha256']
    assert digest(seal_path) == observations['observation_protocol_sha256']
    assert predictions['status'] == 'PASS_UNSEEN_PRIME_KUMMER_PREDICTIONS'
    assert observations['status'] == 'PASS_QUARTIC_OBSERVATION'
    assert seal['rational_primes'] == protocol['rational_primes']
    assert seal['target_sides'] == protocol['target_sides']
    predicted = {key(row): row for row in predictions['rows']}
    observed = {key(row): row for row in observations['rows']}
    assert len(predicted) == len(predictions['rows'])
    assert len(observed) == len(observations['rows'])
    assert set(predicted) == set(observed)
    rows = []
    for identity in sorted(predicted):
        prediction, observation = predicted[identity], observed[identity]
        prediction_degrees = prediction['predicted_relative_degrees']
        observation_degrees = observation['observed_relative_degrees']
        if prediction_degrees is None:
            status = 'UNPREDICTED'
        elif observation_degrees is None:
            status = 'UNOBSERVED'
        elif prediction_degrees == observation_degrees:
            status = 'MATCH'
        else:
            status = 'MISMATCH'
        rows.append({'prime': identity[0], 'base_place_index': identity[1],
                     'side': identity[2], 'base_residue_degree': identity[4],
                     'quadratic_characters': [r['quadratic_character']
                                              for r in prediction['radicand_local_data']],
                     'predicted_relative_degrees': prediction_degrees,
                     'observed_relative_degrees': observation_degrees,
                     'observation_status': observation['status'], 'status': status})
    counts = Counter(row['status'] for row in rows)
    by_prime = {str(p): dict(Counter(row['status'] for row in rows if row['prime'] == p))
                for p in seal['rational_primes']}
    out = {'status': 'PASS_ALL_PROSPECTIVE_PREDICTIONS' if counts == {'MATCH': len(rows)}
           else 'PARTIAL_OR_FAILED_PROSPECTIVE_PREDICTIONS',
           'prediction_sha256': digest(prediction_path),
           'observation_sha256': digest(observation_path),
           'observation_protocol_sha256': digest(seal_path),
           'comparison_source_sha256': digest(Path(__file__)),
           'counts': dict(counts), 'by_prime': by_prime, 'rows': rows}
    (HERE / 'comparison.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'counts': out['counts'],
                      'by_prime': out['by_prime']}, sort_keys=True))


if __name__ == '__main__':
    main()
