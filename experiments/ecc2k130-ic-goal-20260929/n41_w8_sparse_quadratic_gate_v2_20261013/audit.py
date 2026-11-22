"""Independent Python rebuild of selected N41 partial-family signatures."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLE = ROOT / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
REPLAY = ROOT / "n41_basis_aware_quartic_20261011/replay.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_replay():
    spec = importlib.util.spec_from_file_location("n41_independent_replay", REPLAY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def family(states, starts, first, replay):
    field = replay.Field()
    out = set()
    count = 0
    for a in range(starts[first], starts[first] + 16):
        for b in range(starts[first + 1], starts[first + 1] + 16):
            A = states[first][a]
            B = states[first + 1][b]
            if set(A[1]) & set(B[1]):
                continue
            point = replay.add(field, A[0], B[0])
            if point is None or point[0] == 0:
                continue
            reciprocal = field.inv(point[0])
            assert reciprocal & 1 == 0
            out.add(reciprocal)
            count += 1
    return sorted(out), count


def minimum_support(values):
    n = len(values)
    if n > 128:
        raise ValueError("signature width")
    signatures = [(1 << n) - 1]
    signatures += [sum(((x >> bit) & 1) << k for k, x in enumerate(values))
                   for bit in range(1, 41)]
    signatures += [sum((((x >> i) & 1) & ((x >> j) & 1)) << k
                       for k, x in enumerate(values))
                   for i in range(1, 41) for j in range(i + 1, 41)]
    assert len(signatures) == 821
    if 0 in signatures:
        return 1
    mono = set(signatures)
    if len(mono) != len(signatures):
        return 2
    pairs = {}
    for i in range(len(signatures)):
        for j in range(i + 1, len(signatures)):
            value = signatures[i] ^ signatures[j]
            if value in mono:
                return 3
            previous = pairs.get(value)
            if previous is not None and i not in previous and j not in previous:
                return 4
            pairs[value] = (i, j)
    return 5


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    for path, digest in protocol["sources"].items():
        assert sha(Path(path)) == digest, path
    replay = load_replay()
    result = json.loads((HERE / "result.json").read_text())
    requested = {(row["kind"], row["case_id"]): row for row in result["cases"]}
    chosen = [requested[("witness", -1)], requested[("sample", 0)]]
    needed = [set() for _ in range(4)]
    for row in chosen:
        for slot, start in enumerate(row["starts"]):
            needed[slot].update(range(start, start + 16))
    states = [dict() for _ in range(4)]
    with TABLE.open() as stream:
        assert stream.readline().split() == ["ECC2K41_ALLSEED4", "4", "4"]
        for line in stream:
            parts = line.split()
            if parts[0] != "S":
                continue
            slot, sid = int(parts[1]), int(parts[2])
            if sid not in needed[slot]:
                continue
            a, b, ca, cb, sa, sb, x, y = map(int, parts[3:])
            assert a < b and ca != cb and sa in (0, 1) and sb in (0, 1)
            assert replay.on_curve(replay.Field(), (x, y))
            states[slot][sid] = ((x, y), (ca, cb))
    assert all(len(states[i]) == len(needed[i]) for i in range(4))
    checks = []
    for row in chosen:
        for first, side in ((0, "left"), (2, "right")):
            values, count = family(states, row["starts"], first, replay)
            support = minimum_support(values)
            assert len(values) == row[side + "_unique"]
            assert support == row[side + "_min_support_le4"] == 5
            checks.append({"kind": row["kind"], "case_id": row["case_id"],
                           "side": side, "unique_reciprocals": len(values),
                           "valid_partial_points": count,
                           "monomials": 821, "minimum_support_le4": support})
    out = {"status": "PASS_INDEPENDENT_N41_SPARSE_QUADRATIC_AUDIT", "checks": checks}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(out, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(out["status"])


if __name__ == "__main__":
    main()
