"""Combine left reductions and frozen left Kummer fallback before observation."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'protocol.json'
    fallback_path = HERE / 'fallback_protocol.json'
    first_path = HERE / 'predictions.json'
    second_path = HERE / 'fallback_predictions.json'
    fallback_protocol = json.loads(fallback_path.read_text())
    assert fallback_protocol['protocol_sha256'] == digest(protocol_path)
    assert fallback_protocol['first_predictions_sha256'] == digest(first_path)
    first = json.loads(first_path.read_text())
    second = json.loads(second_path.read_text())
    assert first['status'] == 'PASS_SINGLE_SIDED_PREDICTIONS'
    assert second['status'] == 'PASS_LEFT_KUMMER_FALLBACK'
    assert second['fallback_protocol_sha256'] == digest(fallback_path)
    additions = {(r['prime'], r['left_place_index'], r['right_place_index']): r
                 for r in second['rows']}
    assert len(additions) == len(second['rows'])
    rows = []
    for row in first['rows']:
        key = row['prime'], row['left_place_index'], row['right_place_index']
        if row['status'] == 'PREDICTED':
            assert key not in additions
            degrees = row['predicted_right_relative_degrees']
            method = 'LEFT_SQUAREFREE_REDUCTION'
        else:
            assert row['status'] == 'REPEATED_LEFT_REDUCTION'
            supplement = additions.pop(key)
            assert supplement['status'] == 'PREDICTED_BY_LEFT_KUMMER'
            assert supplement['base_residue_degree'] == row['base_residue_degree']
            degrees = supplement['predicted_right_relative_degrees']
            method = 'LEFT_KUMMER_UNIT_CHARACTERS'
        assert degrees in ([1, 1, 1, 1], [2, 2])
        rows.append({'prime': row['prime'], 'right_place_index': row['right_place_index'],
                     'right_ideal_generators': row['right_ideal_generators'],
                     'base_residue_degree': row['base_residue_degree'],
                     'predicted_right_relative_degrees': degrees, 'method': method})
    assert not additions
    assert len({(r['prime'], r['right_place_index']) for r in rows}) == len(rows)
    out = {'status': 'PASS_ALL_RIGHT_PREDICTIONS_FROM_LEFT', 'rows': rows,
           'protocol_sha256': digest(protocol_path),
           'first_predictions_sha256': digest(first_path),
           'fallback_protocol_sha256': digest(fallback_path),
           'fallback_predictions_sha256': digest(second_path),
           'source_sha256': digest(Path(__file__))}
    (HERE / 'transferred_predictions.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'rows': len(rows),
                      'reduction': sum(r['method'] == 'LEFT_SQUAREFREE_REDUCTION' for r in rows),
                      'kummer': sum(r['method'] == 'LEFT_KUMMER_UNIT_CHARACTERS' for r in rows)},
                     sort_keys=True))


if __name__ == '__main__':
    main()
