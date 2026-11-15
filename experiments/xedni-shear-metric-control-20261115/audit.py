"""Independently replay the finite value set by membership in shifted intervals."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    radius = protocol["instance"]["coefficient_radius"]
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")

    # Independent image calculation: (x,y) is attained exactly when some
    # third coefficient c leaves both x-c and y-c in the input interval.
    values = {(x, y)
              for x in range(-2 * radius, 2 * radius + 1)
              for y in range(-2 * radius, 2 * radius + 1)
              if any(abs(x - c) <= radius and abs(y - c) <= radius
                     for c in range(-radius, radius + 1))}
    assert len(values) == result["distinct_value_count"]
    assert result["coefficient_box_count"] == (2 * radius + 1) ** 3
    assert len(result["rows"]) == len(protocol["instance"]["shear_parameters"])
    for row, N in zip(result["rows"], protocol["instance"]["shear_parameters"]):
        assert row["shear_N"] == N
        K = max(max(abs(x - N * y), abs(y)) for x, y in values)
        assert row["coordinate_radius_K"] == K
        assert row["coordinate_cover_count"] == (2 * K + 1) ** 2
        assert row["metric_cover_count"] == (4 * radius + 1) ** 2
        assert row["coordinate_collision_condition"] == (
            row["coordinate_cover_count"] < result["coefficient_box_count"])
        assert row["metric_collision_condition"] == (
            row["metric_cover_count"] < result["coefficient_box_count"])
    first = result["collision_control"]["first"]
    second = result["collision_control"]["second"]
    difference = result["collision_control"]["difference"]
    assert difference == [b - a for a, b in zip(first, second)]
    assert difference == [1, 1, -1]
    assert difference[0] + difference[2] == 0
    assert difference[1] + difference[2] == 0
    print(json.dumps({"status": "PASS", "distinct_value_count": len(values),
                      "checked_rows": len(result["rows"]),
                      "result_sha256": sha(HERE / "result.json"),
                      "audit_source_sha256": sha(HERE / "audit.py")},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
