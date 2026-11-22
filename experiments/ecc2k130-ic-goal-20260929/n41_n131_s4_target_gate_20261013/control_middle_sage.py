"""Independent checked-Sage intermediate for the three-pair N41 control."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(field, value):
    return sum((field.gen() ** i for i in range(41) if value >> i & 1), field.zero())


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def main():
    protocol = json.loads((HERE / "source_control_protocol.json").read_text())
    files = {"script": HERE / "control_middle_sage.py",
             "runtime": HERE / "source_sage_runtime_info.json",
             "prior": GOAL / "n41_common_frob_factor_20261012/audit_result.json",
             "s4_audit": HERE / "audit_result.json"}
    assert protocol["status"] == "FROZEN"
    assert protocol["sha256"] == {name: sha(path) for name, path in files.items()}
    raw = json.loads(files["prior"].read_text())["source_pair_states"][:3]
    binary = PolynomialRing(GF(2), "T")
    T = binary.gen()
    field = GF(2**41, "T", modulus=T**41+T**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    points = [curve(*(decode(field, number) for number in item["raw_pair_point"]))
              for item in raw]
    middle = points[0]+points[1]
    target = middle+points[2]
    assert middle and middle[0] and target and target[0]
    middle_reciprocal = encode(1 / middle[0])
    target_reciprocal = encode(1 / target[0])
    s4 = json.loads(files["s4_audit"].read_text())["n41"]
    assert target_reciprocal == s4["target_reciprocal"]
    pair_reciprocals = [encode(1 / point[0]) for point in points]
    assert pair_reciprocals == s4["input_reciprocals"]
    result = {"status": "PASS_THREE_PAIR_GROUP_CONTROL",
              "protocol_sha256": sha(HERE / "source_control_protocol.json"),
              "masks": [item["masks"] for item in raw],
              "pair_reciprocals": pair_reciprocals,
              "middle_reciprocal": middle_reciprocal,
              "target_reciprocal": target_reciprocal,
              "source_columns": [item["columns"] for item in raw]}
    (HERE / "source_control.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
