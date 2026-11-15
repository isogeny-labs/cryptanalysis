"""Independent finite-field replay of the saved CRT coefficient probe counts."""

import gzip
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def centered(value, prime):
    return min((value, value - prime), key=lambda n: abs(n))


def candidates(prime):
    return sorted(itertools.product(range(prime), repeat=3),
                  key=lambda triple: (sum(abs(centered(x, prime)) for x in triple),
                                      max(abs(centered(x, prime)) for x in triple),
                                      tuple(centered(x, prime) for x in triple)))


def curve_data(points, coefficients, prime):
    (x1, y1), (x2, y2) = points
    a1, a2, a3 = coefficients
    x1 %= prime
    y1 %= prime
    x2 %= prime
    y2 %= prime
    value1 = (y1 * y1 + a1 * x1 * y1 + a3 * y1 - x1 ** 3 - a2 * x1 * x1) % prime
    value2 = (y2 * y2 + a1 * x2 * y2 + a3 * y2 - x2 ** 3 - a2 * x2 * x2) % prime
    a4 = ((value1 - value2) * pow((x1 - x2) % prime, -1, prime)) % prime
    a6 = (value1 - a4 * x1) % prime
    b2 = a1 * a1 + 4 * a2
    b4 = a1 * a3 + 2 * a4
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    discriminant = -b2 * b2 * b8 - 8 * b4 ** 3 - 27 * b6 * b6 + 9 * b2 * b4 * b6
    return a4, a6, discriminant % prime


def count_points(coefficients, prime, character):
    a1, a2, a3, a4, a6 = coefficients
    total = prime + 1
    for x in range(prime):
        right = (x ** 3 + a2 * x * x + a4 * x + a6) % prime
        discriminant = ((a1 * x + a3) ** 2 + 4 * right) % prime
        total += character[discriminant]
    return total


def find_candidate(points, prime, wanted_order, order, character):
    for index, free in enumerate(order, start=1):
        a4, a6, discriminant = curve_data(points, free, prime)
        if discriminant == 0:
            continue
        candidate = (*free, a4, a6)
        if count_points(candidate, prime, character) == wanted_order:
            return candidate, index
    return None, len(order)


def main():
    protocol_path = HERE / "cost-protocol.json"
    protocol = json.loads(protocol_path.read_text())
    parent_input = protocol["inputs"]
    raw = gzip.open(HERE / parent_input["parent_rows"], "rb").read()
    assert sha(raw) == parent_input["parent_rows_uncompressed_sha256"]
    rows = [json.loads(line) for line in raw.splitlines()]
    order = {prime: candidates(prime) for prime in (7, 11)}
    characters = {}
    for prime in order:
        squares = {x * x % prime for x in range(1, prime)}
        characters[prime] = [0 if x == 0 else 1 if x in squares else -1
                             for x in range(prime)]
    totals = {"attempts_7": 0, "attempts_11_strict": 0, "attempts_11_weak": 0}
    replayed = 0
    for row in rows:
        points = row["lifted_points"]
        dx = points[0][0] - points[1][0]
        if dx % 7 == 0 or dx % 11 == 0:
            assert "attempts_7" not in row
            continue
        candidate7, attempts7 = find_candidate(points, 7, 4, order[7], characters[7])
        assert candidate7 is not None
        assert row["attempts_7"] == attempts7
        assert row["chosen_residues_7"] == list(candidate7)
        candidate11, attempts11 = find_candidate(points, 11, 6, order[11], characters[11])
        assert candidate11 is not None
        assert row["attempts_11_strict"] == attempts11
        assert row["chosen_residues_11"] == list(candidate11)
        assert "attempts_11_weak" not in row
        totals["attempts_7"] += attempts7
        totals["attempts_11_strict"] += attempts11
        replayed += 1

    summary = json.loads((HERE / "cost-result.json").read_text())
    assert len(rows) == summary["complete_scan"]["admissible_pairs"]
    assert replayed == summary["complete_scan"]["accepted_pairs"]
    for name, total in totals.items():
        assert total == summary["complete_scan"][name]
    result = {"schema": "xedni-crt-search-probe-audit-v1", "status": "PASS",
              "protocol_sha256": sha(protocol_path.read_bytes()),
              "source_sha256": sha(Path(__file__).read_bytes()),
              "parent_rows_audited": len(rows), "full_searches_replayed": replayed,
              "independent_probe_totals": totals}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
