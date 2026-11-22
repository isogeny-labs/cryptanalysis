"""Independent checked-Sage reconstruction of a public three-pair hit."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, Zmod

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
GEOMETRY = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
RUN = HERE / "fast_run.json"
PROTOCOL = HERE / "fast_protocol.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads(PROTOCOL.read_text())
    receipt = json.loads(RUN.read_text())
    assert receipt["status"] == "UNVERIFIED_HIT" and receipt["stop_reason"] is None
    assert receipt["protocol_sha256"] == sha(PROTOCOL)
    assert protocol["source_hashes_sha256"]["pairs.tsv"] == sha(SOURCE)
    hit = receipt["hit_lines"]
    assert len(hit) == 1
    words = hit[0].split()
    assert words[0] == "HIT" and len(words) == 9
    ids = [int(word) for word in words[1:4]]
    assert len(set(ids)) == 3
    target_xy = protocol["public_target_xy"]
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

    public = curve(*map(dec, target_xy))
    assert R*public == curve(0)
    selected = {}
    with SOURCE.open() as stream:
        assert stream.readline().split() == ["ECC2K41_ALLSEED4", "4", "4"]
        for line in stream:
            row = line.split()
            if row[0] == "S" and int(row[1]) == 0 and int(row[2]) in ids:
                selected[int(row[2])] = tuple(map(int, row[3:]))
    assert set(selected) == set(ids)
    geometry = json.loads(GEOMETRY.read_text())
    rows = {int(row["mask"]): row for row in geometry["rows"]}
    raw = {mask: curve(*map(dec, row["raw_point"])) for mask, row in rows.items()}
    reps = {}
    for mask, row in sorted(rows.items()):
        reps.setdefault(int(row["column"]), mask)
    projected = {mask: 4*point for mask, point in raw.items()}
    columns = set()
    points = []
    state_detail = []
    for sid in ids:
        a, b, ca, cb, sa, sb, x, y = selected[sid]
        assert a < b and rows[a]["column"] == ca and rows[b]["column"] == cb
        assert ca != cb and ca not in columns and cb not in columns
        columns.update((ca, cb))
        point_a, point_b = raw[a]+frob(raw[a]), raw[b]+frob(raw[b])
        pair = (-point_a if sa else point_a)+(-point_b if sb else point_b)
        assert xy(pair) == [x, y] and R*pair == curve(0)
        points.append(pair)
        state_detail.append({"state_id": sid, "masks": [a,b], "columns": [ca,cb],
                             "sign_bits": [sa,sb], "pair_point": [x,y]})
    assert len(columns) == 6
    assert sum(points, curve(0)) == public
    poly = PolynomialRing(Zmod(R), "L")
    L = poly.gen()
    roots = [int(root) for root, _ in (L*L+L+2).roots()]
    sample = projected[reps[min(reps)]]
    eigen = [lam for lam in roots if lam*sample == frob(sample)]
    assert len(eigen) == 1
    lam = eigen[0]
    coeff = defaultdict(int)
    for state in state_detail:
        for mask, sign in zip(state["masks"], state["sign_bits"]):
            col = int(rows[mask]["column"])
            base = projected[reps[col]]
            matches = []
            moved = base
            for shift in range(41):
                if moved == projected[mask]:
                    matches.append((shift, 1))
                if -moved == projected[mask]:
                    matches.append((shift, -1))
                moved = frob(moved)
            assert len(matches) == 1
            shift, orientation = matches[0]
            coeff[col] = (coeff[col]+(-1 if sign else 1)*orientation*
                          (1+lam)*pow(lam, shift, R)) % R
    assert len(coeff) == 6 and all(coeff.values())
    assert sum((value*projected[reps[col]] for col, value in coeff.items()), curve(0)) == public
    result = {
        "status": "PASS_INDEPENDENT_N41_PUBLIC_THREEPAIR_RELATION",
        "curve_id": protocol["curve_id"], "public_point": xy(public),
        "source_pair_states": state_detail, "distinct_folded_columns": len(columns),
        "relation_row": {str(k): str(v) for k,v in sorted(coeff.items())},
        "frobenius_eigenvalue_mod_r": lam,
        "input_sha256": {"run": sha(RUN), "protocol": sha(PROTOCOL),
                         "source": sha(SOURCE), "geometry": sha(GEOMETRY)},
    }
    output = HERE / "replay_result.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], ids, len(columns))


if __name__ == "__main__":
    main()
