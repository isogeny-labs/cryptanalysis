"""Combine frozen V4 factor shortcuts and left Kummer fallback."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'protocol.json'
    first_path = HERE / 'predictions.json'
    extension_path = HERE / 'quadratic_extension_protocol.json'
    extended_path = HERE / 'extended_predictions.json'
    fallback_control_path = HERE / 'fallback_protocol.json'
    fallback_path = HERE / 'fallback_predictions.json'
    first = json.loads(first_path.read_text())
    extension = json.loads(extension_path.read_text())
    extended = json.loads(extended_path.read_text())
    fallback_control = json.loads(fallback_control_path.read_text())
    fallback = json.loads(fallback_path.read_text())
    assert first['status'] == 'PASS_SHORTCUT_PREDICTIONS'
    assert extension['first_predictions_sha256'] == digest(first_path)
    assert extended['quadratic_extension_protocol_sha256'] == digest(extension_path)
    assert fallback_control['extended_predictions_sha256'] == digest(extended_path)
    assert fallback['fallback_protocol_sha256'] == digest(fallback_control_path)
    assert fallback['status'] == 'PASS_LEFT_KUMMER_FALLBACK'
    assert first['protocol_sha256'] == digest(protocol_path)
    extra = {(r['prime'], r['left_place_index'], r['right_place_index']): r
             for r in fallback['rows']}
    assert len(extra) == len(fallback['rows'])
    rows = []
    for source in extended['rows']:
        key = source['prime'], source['left_place_index'], source['right_place_index']
        degrees = source['predicted_right_relative_degrees']
        method = source['status']
        if degrees is None:
            item = extra.pop(key)
            assert item['status'] == 'PREDICTED_LEFT_KUMMER'
            assert item['base_residue_degree'] == source['base_residue_degree']
            degrees, method = item['predicted_right_relative_degrees'], item['status']
        assert degrees in ([1, 1, 1, 1], [2, 2])
        rows.append({'prime': key[0], 'left_place_index': key[1],
                     'right_place_index': key[2],
                     'right_ideal_generators': source['right_ideal_generators'],
                     'base_residue_degree': source['base_residue_degree'],
                     'predicted_right_relative_degrees': degrees, 'method': method})
    assert not extra
    assert len({(r['prime'], r['right_place_index']) for r in rows}) == len(rows)
    out = {'status': 'PASS_COMPLETE_SHORTCUT_PREDICTIONS', 'rows': rows,
           'protocol_sha256': digest(protocol_path),
           'first_predictions_sha256': digest(first_path),
           'quadratic_extension_protocol_sha256': digest(extension_path),
           'extended_predictions_sha256': digest(extended_path),
           'fallback_protocol_sha256': digest(fallback_control_path),
           'fallback_predictions_sha256': digest(fallback_path),
           'source_sha256': digest(Path(__file__))}
    (HERE / 'combined_predictions.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'rows': len(rows),
                      'method_counts': dict(Counter(r['method'] for r in rows))}, sort_keys=True))


if __name__ == '__main__':
    main()
