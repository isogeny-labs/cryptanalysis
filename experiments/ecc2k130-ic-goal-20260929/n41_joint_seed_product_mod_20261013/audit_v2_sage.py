"""Checked-Sage group replay for the root-evaluation search result."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(field, value):
    return sum((field.gen()**i for i in range(41) if value >> i & 1), field.zero())


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def main():
    p = json.loads((HERE / "audit_v2_protocol.json").read_text())
    files = {"auditor": HERE / "audit_v2_sage.py",
             "search_protocol": HERE / "search_v2_protocol.json",
             "search_result": HERE / "search_v2_result.json",
             "independent_prior_audit": HERE / "audit_result.json",
             "sage_runtime": HERE / "sage_runtime_info.json"}
    assert {key: sha(path) for key, path in files.items()} == p["sha256"]
    result = json.loads(files["search_result"].read_text())
    earlier = json.loads(files["independent_prior_audit"].read_text())
    protocol = json.loads(files["search_protocol"].read_text())
    assert result["hit"] == earlier["hit"] and result["decisions"] == earlier["decisions"]
    assert result["status"] == "ALGEBRAIC_HIT_PENDING_GROUP_REPLAY"
    binary = PolynomialRing(GF(2), "T")
    T = binary.gen()
    field = GF(2**41, "T", modulus=T**41 + T**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    hit = result["hit"]
    witness = earlier["group_witness"]
    left = curve(*(decode(field, v) for v in witness["left_point"]))
    right = curve(*(decode(field, v) for v in witness["right_point"]))
    raw = curve(*(decode(field, v) for v in hit["raw_target"]))
    projected = curve(*(decode(field, v) for v in protocol["residual"]))
    assert left + right == raw and 4 * raw == projected
    assert encode(1 / (left[0] + 1)) == hit["left_families"][0]["roots"][0]
    assert encode(1 / (right[0] + 1)) == witness["right_reciprocal"]
    audit = {"status": "PASS_CHECKED_SAGE_V2_SAME_RESIDUAL_GROUP_REPLAY",
             "candidate_id": None, "curve_id": protocol["curve_id"],
             "decisions": result["decisions"], "hit": hit,
             "raw_group_sum": hit["raw_target"],
             "protocol_sha256": sha(HERE / "audit_v2_protocol.json")}
    with (HERE / "audit_v2_result.json").open("x") as out:
        out.write(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(audit["status"], flush=True)


if __name__ == "__main__":
    main()
