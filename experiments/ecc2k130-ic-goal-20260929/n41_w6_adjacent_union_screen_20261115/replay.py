"""Independent Sage replay of the exact N41 3+3 control and ordinary rows."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "replay_protocol.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_REPLAY"
    assert p["source_sha256"] == sha(__file__)
    for name, digest in p["input_sha256"].items():
        assert sha(HERE / name) == digest
    rows = json.loads((HERE / "union_rows.json").read_text())
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    zero = curve(0)
    r = 549756390943
    lam = 256851699273

    def point(xy):
        return curve(field.from_integer(xy[0]), field.from_integer(xy[1]))

    reps = {}
    for block in rows:
        for row in block["rows"]:
            reps.setdefault(row["column"], point(row["original"]))
    assert len(reps) == 26
    verified_original = 0
    for block in rows:
        for row in block["rows"]:
            source = point(row["original"])
            image = point(row["image"])
            assert image == source + curve(source[0]**2, source[1]**2)
            assert image == ((lam+1) % r)*source
            assert r*source == zero
            current = reps[row["column"]]
            hit = False
            for j in range(41):
                if source == current or source == -current:
                    hit = True
                    break
                current = curve(current[0]**2, current[1]**2)
            assert hit
            verified_original += 1
    outcomes = {}
    for arm in ("control", "ordinary"):
        receipt = json.loads((HERE / f"{arm}_receipt.json").read_text())
        assert receipt["status"] == "VERIFIED_SIX_POINT_ROW"
        target = point(receipt["target"])
        total = zero
        folded = {}
        branches = []
        for slot, chosen in enumerate(receipt["chosen_ids"]):
            source_row = rows[slot]["rows"][chosen % 64]
            image_branch = chosen >= 64
            selected = point(source_row["image"] if image_branch else
                             source_row["original"])
            total += selected
            col = source_row["column"]
            current = reps[col]
            coefficient = None
            for j in range(41):
                if selected == current:
                    coefficient = pow(lam, j, r)
                    break
                if selected == -current:
                    coefficient = -pow(lam, j, r) % r
                    break
                current = curve(current[0]**2, current[1]**2)
            if image_branch:
                source = point(source_row["original"])
                current = reps[col]
                for j in range(41):
                    if source == current:
                        coefficient = (lam+1)*pow(lam, j, r) % r
                        break
                    if source == -current:
                        coefficient = -(lam+1)*pow(lam, j, r) % r
                        break
                    current = curve(current[0]**2, current[1]**2)
            assert coefficient is not None
            assert selected == coefficient*reps[col]
            folded[col] = (folded.get(col, 0) + coefficient) % r
            branches.append(int(image_branch))
        assert total == target and r*target == zero
        outcomes[arm] = {
            "target": receipt["target"],
            "chosen_ids": receipt["chosen_ids"],
            "image_branches": branches,
            "folded_nonzero_coefficients": {str(k): v for k, v in sorted(folded.items()) if v},
            "source_bound_group_sum": "PASS",
            "scalar_orbit_transport": "PASS",
        }
    print(json.dumps({
        "kind": "n41_w6_adjacent_union_independent_sage_replay",
        "status": "PASS_CONTROL_AND_ORDINARY",
        "protocol_sha256": sha(HERE / "replay_protocol.json"),
        "source_rows_orbit_checked": verified_original,
        "outcomes": outcomes,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
