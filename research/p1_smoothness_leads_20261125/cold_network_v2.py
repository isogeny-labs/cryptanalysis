"""Replay the frozen 7001*G target correction and audit scalar leakage."""

import contextlib
import io
import json

import cold_network


TARGET_SCALAR = 7001


def main():
    cold_network.TARGET_SCALAR = TARGET_SCALAR
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        cold_network.main()
    result = json.loads(capture.getvalue())
    assert result["target_scalar_verification_only"] == TARGET_SCALAR
    assert len(result["arms"]) == 6

    scan_sets = {}
    for arm in result["arms"]:
        visited = set()
        for scalar in range(1, result["curve_order"]):
            if scalar == TARGET_SCALAR:
                continue
            visited.add(scalar)
            if len(visited) == arm["relation"]["attempts"]:
                break
        scan_sets[arm["index"]] = visited

    for route_name, indices in (
        ("base_reference", [0]),
        ("strongest_single_arm", [5]),
        ("five_arm_network", [1, 2, 3, 4, 5]),
    ):
        route = result[route_name]
        descent = route["target_descent"]
        overlaps = []
        for call in range(descent["calls"]):
            offset, arm_position = divmod(call, len(indices))
            arm_index = indices[arm_position]
            scalar = (TARGET_SCALAR + offset) % result["curve_order"]
            if scalar in scan_sets[arm_index]:
                overlaps.append({
                    "arm_index": arm_index,
                    "offset": offset,
                    "known_scalar": scalar,
                })
        route["known_scalar_descent_overlaps"] = overlaps
        route["independent_of_scanned_points"] = not overlaps

    result["cold_target_amendment"] = "COLD_NETWORK_V2_PROTOCOL.md"
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
