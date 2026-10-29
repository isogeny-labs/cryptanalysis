"""Apply the frozen V4 two-cycle rule before right-side observation."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    extension_path = HERE / 'quadratic_extension_protocol.json'
    extension = json.loads(extension_path.read_text())
    first_path = HERE / 'predictions.json'
    assert extension['status'] == 'FROZEN_SIMPLE_QUADRATIC_EXTENSION_BEFORE_RIGHT_OBSERVATION'
    assert extension['first_predictions_sha256'] == digest(first_path)
    assert extension['protocol_sha256'] == digest(HERE / 'protocol.json')
    first = json.loads(first_path.read_text())
    assert first['status'] == 'PASS_SHORTCUT_PREDICTIONS'
    unresolved = {(p, i, j) for p, i, j in extension['unresolved_left_places']}
    assert len(unresolved) == extension['target_count'] == 3
    rows = []
    for source in first['rows']:
        row = dict(source)
        key = row['prime'], row['left_place_index'], row['right_place_index']
        if row['predicted_right_relative_degrees'] is None:
            assert key in unresolved
            if any(f['degree'] == 2 and f['multiplicity'] == 1
                   for f in row['left_factors']):
                row['predicted_right_relative_degrees'] = [2, 2]
                row['status'] = 'PREDICTED_SIMPLE_QUADRATIC_V4'
            unresolved.remove(key)
        rows.append(row)
    assert not unresolved
    out = {'status': 'PASS_SIMPLE_QUADRATIC_EXTENSION', 'rows': rows,
           'first_predictions_sha256': digest(first_path),
           'quadratic_extension_protocol_sha256': digest(extension_path),
           'source_sha256': digest(Path(__file__))}
    (HERE / 'extended_predictions.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'simple_quadratic': sum(r['status'] == 'PREDICTED_SIMPLE_QUADRATIC_V4'
                                              for r in rows),
                      'unresolved': sum(r['predicted_right_relative_degrees'] is None
                                        for r in rows)}, sort_keys=True))


if __name__ == '__main__':
    main()
