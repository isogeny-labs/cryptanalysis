"""Sage replay of the mixed-affine-seed N131 circuit control."""

import gzip
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010" / "support_w18.tsv"
CORE = ROOT / "n131_w18_four_seed_sevenpair_circuit_20261011" / "circuit.py"
R = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    control = json.loads((HERE / "control_result.json").read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert control["status"] == "PASS_N131_ALL_FOUR_AFFINE_SEEDS_CONSTRUCTED_CONTROL"
    assert control["seed_sequence"] == [212, 213, 214, 215, 212, 213, 214]
    assert control["source_sha256"]["runner"] == sha(HERE / "runner.py")
    assert control["source_sha256"]["circuit"] == sha(CORE)
    with gzip.open(HERE / "control.xcnf.gz", "rb") as stream:
        formula = stream.read()
    assert len(formula) == control["formula"]["xcnf_bytes"]
    assert hashlib.sha256(formula).hexdigest() == control["formula"]["xcnf_sha256"]
    assert control["assignment_check"] == {
        "clauses": control["formula"]["clauses"],
        "native_xor_rows": control["formula"]["native_xor_rows"]}

    polynomial = PolynomialRing(GF(2), "t")
    t = polynomial.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def decode(integer):
        return sum((field(t**bit) for bit in range(131) if integer >> bit & 1),
                   field.zero())

    def point(row):
        return curve([decode(row[0]), decode(row[1])])

    def coordinate(mask):
        return decode(sum(1 << (bit+1) for bit in range(18)
                          if mask >> bit & 1))

    def halftrace(value):
        out, term = field.zero(), value
        for _ in range(66):
            out += term
            term = term**4
        assert out**2 + out == value
        return out

    def options(mask):
        u = halftrace(coordinate(mask))
        assert u != 0
        x = field.one() + 1/u
        rows = curve.lift_x(x, all=True)
        assert len(rows) == 2
        return rows

    columns = {int(a): int(b) for a, b in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    selected = control["selected"]
    assert len(selected) == 7
    folded = []
    running = curve(0)
    for index, row in enumerate(selected):
        a, b = row["masks"]
        assert row["slot"] == index
        assert a ^ b == row["seed"] == control["seed_sequence"][index]
        assert row["folded_columns"] == [columns[a], columns[b]]
        folded.extend(row["folded_columns"])
        unrotated = point(row["unrotated_pair_point"])
        assert unrotated in {P+Q for P in options(a) for Q in options(b)}
        seed = coordinate(a) + coordinate(b)
        h2 = halftrace(seed)**2
        z = 1/unrotated[0]
        product = coordinate(a) * coordinate(b)
        assert product*z + (1+h2)*z*z + h2 == 0
        r = row["rotation"]
        rotated = point(row["rotated_pair_point"])
        assert rotated == curve([unrotated[0]**(2**r),
                                 unrotated[1]**(2**r)])
        running += rotated
        assert running == point(row["partial_sum_point"])
    terminal = point(control["terminal_point"])
    assert len(set(folded + control["terminal_folded_columns"])) == 16
    raw = running + terminal
    assert raw == point(control["raw_point"])
    public = 4*raw
    assert public == point(control["public_point"])
    assert R*public == curve(0)
    assert control["selected_choice_index"] == 0

    result = {"status": "PASS_INDEPENDENT_SAGE_ALL_FOUR_AFFINE_SEEDS",
              "curve_id": control["curve_id"],
              "seed_sequence": control["seed_sequence"],
              "distinct_folded_columns_including_terminal": 16,
              "raw_point": control["raw_point"],
              "public_point": control["public_point"],
              "sha256": {"audit": sha(Path(__file__)),
                         "runner": sha(HERE / "runner.py"),
                         "core_circuit": sha(CORE),
                         "control": sha(HERE / "control_result.json"),
                         "formula_raw": hashlib.sha256(formula).hexdigest(),
                         "formula_archive": sha(HERE / "control.xcnf.gz"),
                         "runtime": sha(HERE / "sage_runtime_info.json"),
                         "support": sha(SUPPORT)}}
    with (HERE / "sage_audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"])


if __name__ == "__main__":
    main()
