"""Run the frozen exact shear-versus-metric lattice control."""

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "protocol.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(coeff, points):
    return tuple(sum(a * point[j] for a, point in zip(coeff, points))
                 for j in range(2))


def main():
    protocol = json.loads(PROTOCOL.read_text())
    instance = protocol["instance"]
    points = [tuple(p) for p in instance["points"]]
    radius = instance["coefficient_radius"]
    relation = tuple(instance["known_relation"])
    assert evaluate(relation, points) == (0, 0)
    assert relation != (0, 0, 0)
    assert max(map(abs, relation)) <= radius

    box = list(itertools.product(range(-radius, radius + 1), repeat=3))
    image = {coeff: evaluate(coeff, points) for coeff in box}
    values = set(image.values())
    first_by_value = {}
    collision = None
    for coeff in box:
        value = image[coeff]
        if value in first_by_value and collision is None:
            earlier = first_by_value[value]
            difference = tuple(a - b for a, b in zip(coeff, earlier))
            assert any(difference)
            assert max(map(abs, difference)) <= 2 * radius
            assert evaluate(difference, points) == (0, 0)
            collision = {"first": list(earlier), "second": list(coeff),
                         "difference": list(difference), "value": list(value)}
        first_by_value.setdefault(value, coeff)
    assert collision is not None
    assert all(max(map(abs, v)) <= 2 * radius for v in values)

    box_count = len(box)
    metric_count = (4 * radius + 1) ** 2
    assert box_count == protocol["frozen_predictions"]["coefficient_box_count"]
    assert metric_count == protocol["frozen_predictions"]["metric_center_count"]
    assert (metric_count < box_count) is protocol["frozen_predictions"]["metric_collision_condition"]

    rows = []
    for N in instance["shear_parameters"]:
        inverse_coordinates = {(x - N * y, y) for x, y in values}
        assert len(inverse_coordinates) == len(values)
        assert all((a + N * b, b) in values for a, b in inverse_coordinates)
        K = max(max(abs(a), abs(b)) for a, b in inverse_coordinates)
        coordinate_count = (2 * K + 1) ** 2
        coordinate_condition = coordinate_count < box_count
        if N >= 2:
            assert coordinate_condition is protocol["frozen_predictions"]["coordinate_collision_condition_for_N_ge_2"]
        rows.append({"shear_N": N, "coordinate_radius_K": K,
                     "coordinate_cover_count": coordinate_count,
                     "coordinate_collision_condition": coordinate_condition,
                     "metric_cover_count": metric_count,
                     "metric_collision_condition": metric_count < box_count})

    result = {"schema": "xedni-shear-metric-result-v1",
              "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(HERE / "run.py"),
              "coefficient_box_count": box_count,
              "distinct_value_count": len(values),
              "known_relation": list(relation), "collision_control": collision,
              "rows": rows, "status": "PASS"}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
