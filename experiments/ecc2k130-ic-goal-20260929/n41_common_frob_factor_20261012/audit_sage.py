"""Independent checked-Sage replay of the five-pair transformed-target hit."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, Zmod

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
BASE = GOAL / "n41_w7_entropy_cubic_20261011/w8"
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
R = 549756390943


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix_row(value):
    if isinstance(value, list):
        return {int(item["column"]): int(item["coefficient_mod_r"]) % R for item in value}
    return {int(k): int(v) % R for k, v in value.items()}


def rank(rows):
    pivots = {}
    for entry in rows:
        work = {k: v for k, v in entry.items() if v}
        while work:
            pivot = min(work)
            if pivot not in pivots:
                inverse = pow(work[pivot], -1, R)
                pivots[pivot] = {k: v*inverse % R for k, v in work.items()}
                break
            factor = work[pivot]
            for k, v in pivots[pivot].items():
                work[k] = (work.get(k, 0)-factor*v) % R
                if not work[k]:
                    work.pop(k, None)
    return len(pivots)


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    files = {"source": HERE / "audit_sage.py", "pairs": SOURCE,
             "geometry": BASE / "geometry.json", "fixture": BASE / "fixture.json",
             "target": HERE / "target.json", "join_receipt": HERE / "result.json",
             "stdout": HERE / "stdout.log", "sage_runtime": HERE / "sage_runtime_info.json"}
    assert protocol["status"] == "FROZEN_BEFORE_INDEPENDENT_REPLAY"
    assert protocol["sha256"] == {name: sha(path) for name, path in files.items()}
    receipt = json.loads((HERE / "result.json").read_text())
    assert receipt["status"] == "HIT_PENDING_INDEPENDENT_REPLAY" and receipt["stop_reason"] is None
    hit = receipt["hit_line"].split()
    assert hit[0] == "HIT" and len(hit) == 14
    ids = list(map(int, hit[1:6]))
    assert len(ids) == 5 and len(set(ids)) == 5
    geometry = json.loads((BASE / "geometry.json").read_text())
    fixture = json.loads((BASE / "fixture.json").read_text())
    target_data = json.loads((HERE / "target.json").read_text())
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    def dec(n):
        return field(ring([(n >> i) & 1 for i in range(41)]))
    def enc(a):
        return sum(int(bit) << i for i, bit in enumerate(a.polynomial().list()))
    def xy(point):
        return [enc(point[0]), enc(point[1])]
    def frob(point, shift):
        return curve(point[0]**(1 << shift), point[1]**(1 << shift))
    public = curve(*map(dec, target_data["public_point"]))
    transformed = curve(*map(dec, target_data["transformed_target"]))
    assert xy(public) == fixture["public_target_transported"]
    assert transformed+frob(transformed, 7) == public
    assert R*public == curve(0) and R*transformed == curve(0)
    source = {}
    with SOURCE.open() as stream:
        assert stream.readline().split() == ["ECC2K41_ALLSEED4", "4", "4"]
        for line in stream:
            row = line.split()
            if row[0] == "S" and int(row[1]) == 0 and int(row[2]) in ids:
                source[int(row[2])] = tuple(map(int, row[3:]))
    assert set(source) == set(ids)
    rows = {int(item["mask"]): item for item in geometry["rows"]}
    raw = {m: curve(*map(dec, row["raw_point"])) for m, row in rows.items()}
    diag = {m: raw[m]+frob(raw[m], 1) for m in raw}
    projected = {m: 4*raw[m] for m in raw}
    assert all(point != curve(0) and R*point == curve(0) for point in projected.values())
    selected, columns, running = [], set(), curve(0)
    for sid in ids:
        a, b, ca, cb, sa, sb, x, y = source[sid]
        assert a < b and rows[a]["column"] == ca and rows[b]["column"] == cb
        assert ca != cb and ca not in columns and cb not in columns
        columns.update([ca, cb])
        pair = (-diag[a] if sa else diag[a])+(-diag[b] if sb else diag[b])
        assert xy(pair) == [x, y]
        running += 4*pair
        selected.append({"state_id": sid, "masks": [a,b], "columns": [ca,cb],
                         "sign_bits": [sa,sb], "raw_pair_point": [x,y],
                         "projected_pair_point": xy(4*pair)})
    assert len(columns) == 10 and running == transformed
    assert running+frob(running, 7) == public
    lambda_poly = PolynomialRing(Zmod(R), "L")
    L = lambda_poly.gen()
    roots = [int(root) for root, _ in (L*L+L+2).roots()]
    reps = {}
    for mask, row in sorted(rows.items()):
        reps.setdefault(int(row["column"]), mask)
    sample = projected[reps[min(reps)]]
    eigenvalues = [lam for lam in roots if lam*sample == frob(sample, 1)]
    assert len(eigenvalues) == 1 and eigenvalues[0] == target_data["lambda_mod_r"]
    lam = eigenvalues[0]
    common = ((1+lam)*(1+pow(lam,7,R))) % R
    coefficients = defaultdict(int)
    for entry in selected:
        for mask, sign in zip(entry["masks"], entry["sign_bits"]):
            col = int(rows[mask]["column"])
            base = projected[reps[col]]
            matches = []
            for shift in range(41):
                moved = frob(base, shift)
                if moved == projected[mask]: matches.append((shift, 1))
                if -moved == projected[mask]: matches.append((shift, -1))
            assert len(matches) == 1
            shift, orientation = matches[0]
            coefficients[col] = (coefficients[col]+(-1 if sign else 1)*orientation*
                                 common*pow(lam,shift,R)) % R
    assert len(coefficients) == 10 and all(coefficients.values())
    row_point = curve(0)
    for col, value in coefficients.items():
        row_point += value*projected[reps[col]]
    assert row_point == public
    prior_paths = [GOAL / name / "audit_result.json" for name in (
        "n41_w8_sixpair_mitm_20261011", "n41_w8_ninepair_join_control_20261012",
        "n41_w8_tenpair_xquotient_20261012")]
    prior_paths += [GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/audit_result.json",
                    GOAL / "n131_w18_bucketed_public_20261012/bucket_audit_result.json"]
    prior = [matrix_row(json.loads(path.read_text())["relation_row"]) for path in prior_paths]
    prefix_path = GOAL / "n41_source_prefix_joint_20261012/sage_audit_result.json"
    prefix = json.loads(prefix_path.read_text())
    d3 = next(item for item in prefix["relations"] if item["label"] == "d3_random3")
    prior.append(matrix_row(d3["relation_row"]))
    rank_before = rank(prior)
    rank_after = rank(prior+[dict(coefficients)])
    assert rank_before == 6 and rank_after == 7
    result = {"status": "PASS_INDEPENDENT_N41_COMMON_FROBENIUS_PUBLIC_RELATION",
              "curve_id": protocol["curve_id"], "public_point": xy(public),
              "transformed_target": xy(transformed), "source_pair_states": selected,
              "distinct_folded_columns": len(columns),
              "factor_mod_r": target_data["factor_mod_r"],
              "lambda_mod_r": lam, "relation_row": {str(k): str(v) for k,v in coefficients.items()},
              "rank_before": rank_before, "rank_after": rank_after,
              "prior_row_sha256": {str(path): sha(path) for path in prior_paths+[prefix_path]},
              "protocol_sha256": sha(HERE / "audit_protocol.json")}
    with (HERE / "audit_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result["status"], rank_before, rank_after)


if __name__ == "__main__":
    main()
