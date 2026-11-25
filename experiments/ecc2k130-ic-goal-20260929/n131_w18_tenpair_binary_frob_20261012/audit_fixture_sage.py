"""Independent Sage check of the tenth W18 pair and constructed target."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NINE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / "fixture_audit_protocol.json").read_text())
for name, path in {
    "source": HERE / "audit_fixture_sage.py",
    "fixture": HERE / "control_fixture.json",
    "prior_fixture": NINE / "control_fixture.json",
    "prior_sage_audit": NINE / "sage_fixture_result.json",
    "support": SUPPORT,
    "runtime": HERE / "sage_runtime_info.json",
}.items():
    assert sha(path) == protocol["sha256"][name]
fixture = json.loads((HERE / "control_fixture.json").read_text())
prior = json.loads((NINE / "control_fixture.json").read_text())
prior_audit = json.loads((NINE / "sage_fixture_result.json").read_text())
assert prior_audit["status"] == "PASS_INDEPENDENT_SAGE_NINE_PAIR_GROUP_REPLAY"
assert prior_audit["raw_target"] == prior["raw_target"] == fixture["prior_raw_target"]
assert fixture["status"] == "PASS_TENPAIR_CONSTRUCTED_SOURCE_FIXTURE"
assert fixture["selected"][:9] == prior["selected"]
assert len(fixture["selected"]) == 10
columns = {int(mask): int(column) for mask, column in
           (line.split() for line in SUPPORT.read_text().splitlines())}
all_columns = [column for item in fixture["selected"]
               for column in item["folded_columns"]]
assert len(all_columns) == len(set(all_columns)) == 20
last = fixture["selected"][9]
assert last["slot"] == 9 and last["rotation"] == 8
assert last["masks"][0] ^ last["masks"][1] == 212
assert last["folded_columns"] == [columns[m] for m in last["masks"]]

ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**131, name="t", modulus=t**131 + t**13 + t**2 + t + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def dec(value):
    return field(ring([(int(value) >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    result, power = field.zero(), value
    for _ in range(66):
        result += power
        power = power**4
    assert result**2 + result == value
    return result


atom_options = []
for mask in last["masks"]:
    coordinate = dec(mask << 1)
    u = halftrace(coordinate)
    atom_options.append(curve.lift_x(1 + 1/u, all=True))
prior_target = curve(*map(dec, fixture["prior_raw_target"]))
constructed_target = curve(*map(dec, fixture["raw_target"]))
matching = []
for a, b in itertools.product(*atom_options):
    raw = a + b
    if raw == curve(0) or raw[0] in (0, 1):
        continue
    rotated = curve(raw[0]**(1 << 8), raw[1]**(1 << 8))
    if [enc(rotated[0]), enc(rotated[1])] == fixture["last_pair_point"]:
        assert enc(1 / (raw[0] + 1)) == last["unrotated_pair_output_z"]
        matching.append((a, b, rotated))
assert len(matching) == 1
assert prior_target + matching[0][2] == constructed_target
assert enc(1 / (constructed_target[0] + 1)) == fixture["raw_target_z"]
assert 680564733841876926932320129493409985129 * (4 * constructed_target) == curve(0)
result = {
    "status": "PASS_INDEPENDENT_SAGE_TENPAIR_CONSTRUCTED_GROUP_REPLAY",
    "candidate_id": None,
    "source_pairs": 10,
    "distinct_folded_columns": len(all_columns),
    "last_pair_point": fixture["last_pair_point"],
    "raw_target": fixture["raw_target"],
    "projected_target": [enc((4 * constructed_target)[0]),
                         enc((4 * constructed_target)[1])],
    "source_sha256": protocol["sha256"],
}
(HERE / "sage_fixture_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(result["status"], len(all_columns))
