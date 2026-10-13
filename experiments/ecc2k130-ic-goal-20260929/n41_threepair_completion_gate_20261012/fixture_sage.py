"""Construct a disjoint-column positive control at the first shuffled outer family."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
MASK64 = (1 << 64) - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "fixture_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_CONSTRUCTED_CONTROL"
    files = {"script": HERE / "fixture_sage.py", "pairs": SOURCE,
             "runtime": HERE / "sage_runtime_info.json", "binary": HERE / "triple"}
    assert protocol["sha256"] == {name: sha(path) for name, path in files.items()}
    rows = []
    with SOURCE.open() as stream:
        assert stream.readline().split() == ["ECC2K41_ALLSEED4", "4", "4"]
        for line in stream:
            fields = line.split()
            if (fields[0] == "S" and int(fields[1]) == 0 and
                    int(fields[3]) < 64 and int(fields[4]) < 64):
                rows.append(tuple(map(int, fields[2:])))
    assert len(rows) == 1956
    doubles = []
    for i in range(len(rows)):
        ci = {rows[i][3], rows[i][4]}
        for j in range(i + 1, len(rows)):
            if ci.isdisjoint((rows[j][3], rows[j][4])):
                doubles.append((i,j))
    assert len(doubles) == 1583568
    rng = int(protocol["rng_seed"], 16)
    def word():
        nonlocal rng
        rng ^= rng >> 12
        rng ^= (rng << 25) & MASK64
        rng ^= rng >> 27
        rng &= MASK64
        return (rng * 2685821657736338717) & MASK64
    order = list(range(len(doubles)))
    for i in range(len(order), 1, -1):
        j = word() % i
        order[i - 1], order[j] = order[j], order[i - 1]
    outer = doubles[order[0]]
    selected = list(outer)
    columns = {rows[k][3] for k in selected} | {rows[k][4] for k in selected}
    for k, row in enumerate(rows):
        if k in selected:
            continue
        ca, cb = row[3], row[4]
        if ca != cb and ca not in columns and cb not in columns:
            selected.append(k)
            columns.update((ca, cb))
            if len(selected) == 5:
                break
    assert len(selected) == 5 and len(columns) == 10
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1,0,0,0,1])
    def dec(n):
        return field(ring([(n >> bit) & 1 for bit in range(41)]))
    def enc(a):
        return sum(int(bit) << bit_index for bit_index, bit in enumerate(a.polynomial().list()))
    points = []
    for k in selected:
        row = rows[k]
        raw = curve(dec(row[7]), dec(row[8]))
        subgroup = 4 * raw
        assert subgroup != curve(0) and 549756390943 * subgroup == curve(0)
        points.append(subgroup)
    target = sum(points, curve(0))
    assert target != curve(0)
    result = {"status": "PASS_CHECKED_SAGE_CONSTRUCTED_FIVEPAIR_TARGET",
              "curve_id": protocol["curve_id"], "source_count": len(rows),
              "index_entries": len(doubles), "first_shuffled_double_index": order[0],
              "selected_subset_ids": selected,
              "selected_original_ids": [rows[k][0] for k in selected],
              "selected_columns": [[rows[k][3], rows[k][4]] for k in selected],
              "projected_target": [enc(target[0]), enc(target[1])],
              "protocol_sha256": sha(HERE / "fixture_protocol.json")}
    with (HERE / "fixture.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result["status"], selected, result["projected_target"], flush=True)


if __name__ == "__main__":
    main()
