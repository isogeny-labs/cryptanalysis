"""Check coordinate separation on the frozen complete geometric fiber."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    path = ROOT/'hecke-432-geometric-fiber-20261025'/'evaluation.json'
    prior_path = ROOT/'hecke-432-geometric-fiber-20261025'/'audit.json'
    evaluation = json.loads(path.read_text())
    prior = json.loads(prior_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_Y_PRIMITIVE_SCREEN'
    assert evaluation['status'] == 'COMPLETE_GEOMETRIC_E_FIBER'
    assert prior['status'] == 'PASS_INDEPENDENT_GEOMETRIC_FIBER_AUDIT'
    assert len(evaluation['rows']) == prior['path_count'] == 24
    assert all(row['status'] == 'PASS' and row['E_point'] is not None
               for row in evaluation['rows'])
    xkeys = [tuple(row['E_point'][0]) for row in evaluation['rows']]
    ykeys = [tuple(row['E_point'][1]) for row in evaluation['rows']]
    assert len(set(ykeys)) == 24
    assert len(set(xkeys)) == 12
    assert Counter(Counter(xkeys).values()) == Counter({2: 12})
    assert Counter(Counter(ykeys).values()) == Counter({1: 24})
    out = {
        'status': 'PASS_Y_COORDINATE_SEPARATES_FULL_FIBER',
        'path_count': 24,
        'distinct_y_coordinates': 24,
        'distinct_x_coordinates': 12,
        'x_multiplicity_histogram': {'2': 12},
        'y_multiplicity_histogram': {'1': 24},
        'evaluation_sha256': sha256(path.read_bytes()).hexdigest(),
        'independent_arithmetic_audit_sha256': sha256(prior_path.read_bytes()).hexdigest(),
        'protocol_sha256': sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
    }
    (HERE/'fiber_result.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
