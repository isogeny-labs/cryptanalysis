"""Independent Sage replay of the frozen three-pair positive control."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
GEOMETRY = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
CONTROL = HERE / "control_fast_stdout.log"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lines = CONTROL.read_text().splitlines()
    assert lines[0] == "FIELD_SELFTEST_PASS 100000"
    target_line = lines[1].split()
    hit_line = lines[-1].split()
    assert target_line[0] == "CONTROL_TARGET" and hit_line[0] == "HIT"
    ids = list(map(int, target_line[3:]))
    assert ids == list(map(int, hit_line[1:4])) == [15842, 1006, 22805]
    target_xy = list(map(int, target_line[1:3]))
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(n):
        return field(ring([(int(n) >> i) & 1 for i in range(41)]))

    def enc(a):
        return sum(int(bit) << i for i, bit in enumerate(a.polynomial().list()))

    def xy(point):
        return [enc(point[0]), enc(point[1])]

    def frob(point):
        return curve(point[0]**2, point[1]**2)

    rows = {int(row["mask"]): row for row in json.loads(GEOMETRY.read_text())["rows"]}
    raw = {mask: curve(*map(dec, row["raw_point"])) for mask, row in rows.items()}
    states = {}
    with SOURCE.open() as stream:
        assert stream.readline().split() == ["ECC2K41_ALLSEED4", "4", "4"]
        for line in stream:
            row = line.split()
            if row[0] == "S" and row[1] == "0" and int(row[2]) in ids:
                states[int(row[2])] = list(map(int, row[3:]))
    assert set(states) == set(ids)
    columns = set()
    points = []
    for sid in ids:
        a, b, ca, cb, sa, sb, x, y = states[sid]
        assert rows[a]["column"] == ca and rows[b]["column"] == cb
        assert ca != cb and ca not in columns and cb not in columns
        columns.update((ca, cb))
        p = raw[a]+frob(raw[a])
        q = raw[b]+frob(raw[b])
        pair = (-p if sa else p)+(-q if sb else q)
        assert xy(pair) == [x, y]
        points.append(pair)
    assert len(columns) == 6
    target = curve(*map(dec, target_xy))
    assert sum(points, curve(0)) == target
    result = {"status": "PASS_INDEPENDENT_THREEPAIR_CONTROL_REPLAY",
              "target_xy": target_xy, "state_ids": ids, "distinct_columns": len(columns),
              "input_sha256": {"source": sha(SOURCE), "geometry": sha(GEOMETRY),
                               "control_stdout": sha(CONTROL)}}
    with (HERE / "control_replay_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
