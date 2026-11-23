"""Check the exact cofactor classes of all frozen N41 signed pair states."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
GEOMETRY = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(n):
        return field(ring([(int(n) >> i) & 1 for i in range(41)]))

    def enc(a):
        return sum(int(bit) << i for i, bit in enumerate(a.polynomial().list()))

    def key(point):
        return "O" if point == curve(0) else f"{enc(point[0])},{enc(point[1])}"

    geometry = json.loads(GEOMETRY.read_text())
    raw = {int(row["mask"]): curve(*map(dec, row["raw_point"])) for row in geometry["rows"]}
    diagonal_torsion = {mask: R*(point+curve(point[0]**2, point[1]**2))
                        for mask, point in raw.items()}
    source_classes = Counter()
    source_class_points = {}
    checks = 0
    with SOURCE.open() as stream:
        assert stream.readline().split() == ["ECC2K41_ALLSEED4", "4", "4"]
        for line in stream:
            row = line.split()
            if row[0] != "S" or row[1] != "0":
                continue
            _, slot, sid, a, b, ca, cb, sa, sb, x, y = row
            a, b, sa, sb = int(a), int(b), int(sa), int(sb)
            torsion = (-diagonal_torsion[a] if sa else diagonal_torsion[a]) + \
                      (-diagonal_torsion[b] if sb else diagonal_torsion[b])
            source_classes[key(torsion)] += 1
            source_class_points[key(torsion)] = torsion
            if checks < 32:
                assert R*curve(dec(x), dec(y)) == torsion
                checks += 1
    public = curve(dec(920359962848), dec(755404565011))
    assert R*public == curve(0)
    classes = list(source_class_points.values())
    result = {
        "status": "PASS_N41_SOURCE_COFACTOR_CLASS_AUDIT",
        "target_class": key(R*public),
        "diagonal_classes": dict(Counter(key(value) for value in diagonal_torsion.values())),
        "source_classes": dict(source_classes),
        "source_state_total": sum(source_classes.values()),
        "sample_direct_scalar_checks": checks,
        "triple_classes_possible": sorted({key(a+b+c) for a in classes for b in classes for c in classes}),
        "input_sha256": {"source": sha(SOURCE), "geometry": sha(GEOMETRY)},
    }
    output = HERE / "coset_result.json"
    with output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
