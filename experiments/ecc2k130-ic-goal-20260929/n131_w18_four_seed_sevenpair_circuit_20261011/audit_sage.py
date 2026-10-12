"""Independent Sage replay of the seven-pair constructed control."""

import gzip
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIXTURE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011" / "control_fixture.json"
POOL = ROOT / "n131_w18_all_fibers_inverse_20261011" / "protocol.json"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010" / "support_w18.tsv"
R = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    control = json.loads((HERE / "control_result.json").read_text())
    fixture = json.loads(FIXTURE.read_text())
    pool = json.loads(POOL.read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert control["status"] == "PASS_N131_FOUR_SEED_SEVENPAIR_CONSTRUCTED_CONTROL"
    assert control["source_sha256"] == sha(HERE / "circuit.py")
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
        value = field.zero()
        for bit in range(131):
            if integer >> bit & 1:
                value += field(t**bit)
        return value

    def encode(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def point(row):
        return curve([decode(row[0]), decode(row[1])])

    def pair_options(mask):
        w = decode(sum(1 << (bit+1) for bit in range(18) if mask >> bit & 1))
        u, term = field.zero(), w
        for _ in range(66):
            u += term
            term = term**4
        assert u**2 + u == w and u != 0
        x = field.one() + 1/u
        options = curve.lift_x(x, all=True)
        assert len(options) == 2
        return options

    columns = {int(a): int(b) for a, b in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    selected = fixture["selected"][:7]
    recorded = [point(row) for row in control["seven_pair_rotated_points"]]
    assert len(selected) == len(recorded) == 7
    folded = []
    for row, actual in zip(selected, recorded):
        a, b = row["masks"]
        assert a ^ b == 212
        assert [columns[a], columns[b]] == row["folded_columns"]
        folded.extend((columns[a], columns[b]))
        rotation = row["rotation"]
        outcomes = {(curve([P[0] ** (2**rotation), P[1] ** (2**rotation)]) +
                     curve([Q[0] ** (2**rotation), Q[1] ** (2**rotation)]))
                    for P in pair_options(a) for Q in pair_options(b)}
        assert actual in outcomes and actual != curve(0)
    assert len(set(folded)) == 14
    terminal_columns = pool["terminal_pool"][0]["folded_columns"]
    assert not set(folded).intersection(terminal_columns)
    terminal = point(control["terminal_point"])
    assert control["terminal_point"] == pool["terminal_pool"][0]["rotated_raw_point"]
    raw = terminal + sum(recorded, curve(0))
    public = 4 * raw
    assert raw == point(control["control_raw_point"])
    assert public == point(control["control_public_point"])
    assert R * public == curve(0)
    assert control["selected_choice_index"] == 0
    assert encode(1 / (raw-terminal)[0]) != 0

    result = {
        "status": "PASS_INDEPENDENT_SAGE_N131_SEVENPAIR_CONTROL",
        "curve_id": control["curve_id"],
        "source_points": 14,
        "distinct_folded_columns": len(set(folded)),
        "raw_group_sum": control["control_raw_point"],
        "public_point": control["control_public_point"],
        "sha256": {"audit": sha(Path(__file__)),
                   "control": sha(HERE / "control_result.json"),
                   "formula_raw": hashlib.sha256(formula).hexdigest(),
                   "formula_archive": sha(HERE / "control.xcnf.gz"),
                   "runtime": sha(HERE / "sage_runtime_info.json"),
                   "source": sha(HERE / "circuit.py"),
                   "support": sha(SUPPORT)},
    }
    with (HERE / "sage_audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"])


if __name__ == "__main__":
    main()
