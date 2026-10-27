"""Independent checked-Sage replay of direct class-point relations and ranks."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
OUTPUT = json.loads((HERE / "result.json").read_text())


def load(entry):
    raw = (ROOT / entry["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
    return json.loads(raw)


def sparse(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


def rank(rows, field, width):
    if not rows:
        return 0
    return int(matrix(field, len(rows), width,
                      lambda i, j: rows[i].get(j, 0)).rank())


def main():
    data = load(INPUTS["class_receipt"])
    search = load(INPUTS["search_receipt"])
    assert all(load(e)["status"] == "PASS" for e in INPUTS["validation_receipts"])
    p = INPUTS["p"]
    field = GF(p)
    E = EllipticCurve(field, [0, -1, 1, -10, -20])
    assert int(E.cardinality()) == INPUTS["curve_order"]
    points = [E([field(x), field(y)]) for x, y in data["class_points"]]
    assert len(points) == INPUTS["class_size"] == 39
    base = [sparse(x["row"]) for x in data["base_rows"]]
    closed = [sparse(x["class_part"]) for x in data["degree13_sources"]
              if x["status"] == "CLASS_CLOSED"]
    hecke = [sparse(c["row"]) for c in search["candidates"]]
    assert len(base) == 18 and len(closed) == 5 and len(hecke) == 80
    candidates, selected, selected_rows = [], [], []
    counts = {"1": 0, "2": 0, "3": 0}
    path = [{"selected": 0, "rank_qq": 18, "rank_mod61": 18}]
    qfield = GF(INPUTS["rank_modulus"])
    for support in range(1, INPUTS["support_max"]+1):
        for inds in itertools.combinations(range(len(points)), support):
            for rest in itertools.product(INPUTS["coefficient_order"], repeat=support-1):
                signs = (1,) + rest
                total = E(0)
                for i, sign in zip(inds, signs):
                    total += int(sign)*points[i]
                if total != E(0):
                    continue
                row = dict(zip(inds, signs))
                idx = len(candidates)
                candidates.append({"indices": list(inds), "coefficients": list(signs),
                                   "row": {str(i): int(v) for i, v in row.items()}})
                counts[str(support)] += 1
                if rank(base+selected_rows+[row], qfield, 39) > rank(base+selected_rows, qfield, 39):
                    selected.append(idx)
                    selected_rows.append(row)
                    path.append({"selected": len(selected), "candidate_index": idx,
                                 "rank_qq": rank(base+selected_rows, QQ, 39),
                                 "rank_mod61": rank(base+selected_rows, qfield, 39)})
    direct = [sparse(c["row"]) for c in candidates]
    ranks = {
        "direct_only_qq": rank(direct, QQ, 39),
        "direct_only_mod61": rank(direct, qfield, 39),
        "base_plus_direct_qq": rank(base+direct, QQ, 39),
        "base_plus_direct_mod61": rank(base+direct, qfield, 39),
        "base_plus_closed_qq": rank(base+closed, QQ, 39),
        "base_plus_closed_mod61": rank(base+closed, qfield, 39),
        "base_plus_hecke_qq": rank(base+closed+hecke, QQ, 39),
        "base_plus_hecke_mod61": rank(base+closed+hecke, qfield, 39),
        "base_plus_direct_plus_hecke_qq": rank(base+closed+direct+hecke, QQ, 39),
        "base_plus_direct_plus_hecke_mod61": rank(base+closed+direct+hecke, qfield, 39)
    }
    assert candidates == OUTPUT["candidates"]
    assert selected == OUTPUT["selected_candidate_indices"]
    assert path == OUTPUT["rank_path"]
    assert counts == OUTPUT["candidate_counts"]
    assert ranks == OUTPUT["ranks"]
    receipt = {"schema": "hecke-d79-class-generic-rank-validation-v1",
               "status": "PASS", "p": p, "curve_order": int(E.cardinality()),
               "candidates_replayed": len(candidates), "selected_replayed": len(selected),
               "counts": counts, "ranks": ranks}
    (HERE / "validation.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": "PASS", "candidates": len(candidates),
                      "selected": len(selected)}, sort_keys=True))


if __name__ == "__main__":
    main()
