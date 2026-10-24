"""Independent binary-field replay of the N131 W23 first-two resultant."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELD_SOURCE = Path("/Volumes/SSD990/crypto/research/sat_factor_base_review_20260908/autolab_orbit_extract_20260924/independent_replay.py")
CFG = json.loads((HERE / "n131_bridge_protocol_v2.json").read_text())
result = json.loads((HERE / "n131_h_bridge_result_v2.json").read_text())
fixture = json.loads(Path(CFG["sources"]["fixture"]["path"]).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


assert all(sha(source["path"]) == source["sha256"] for source in CFG["sources"].values())
assert result["status"] == "PASS_N131_W23_FIRST_TWO_RESULTANT_BRIDGE"
spec = importlib.util.spec_from_file_location("independent_field", FIELD_SOURCE)
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
field = source.Field(131, [0, 1, 2, 13])
mul = field.mul
sq = lambda x: mul(x, x)


def power(x, exponent):
    out = 1
    while exponent:
        if exponent & 1:
            out = mul(out, x)
        x = sq(x)
        exponent >>= 1
    return out


def frob(x, count):
    for _ in range(count):
        x = sq(x)
    return x


seed = fixture["seed_mask"] << 1
half = 0
v = seed
for _ in range(66):
    half ^= v
    v = sq(sq(v))
assert sq(half) ^ half == seed
h0 = sq(half)
h1 = frob(h0, fixture["rotations"][1])
p0 = fixture["pairs"][0]["source_product"]
p1 = frob(fixture["pairs"][1]["source_product"], fixture["rotations"][1])
z0 = fixture["pairs"][0]["output_reciprocal"]
z1 = frob(fixture["pairs"][1]["output_reciprocal"], fixture["rotations"][1])
z = fixture["middle_reciprocals"][0]
assert [h0, h1] == result["h_values"]
assert [p0, p1] == result["product_values"]
assert [z0, z1] == result["pair_reciprocals"]
assert z == result["first_two_sum_reciprocal"]
assert mul(1 ^ h0, sq(z0)) ^ mul(p0, z0) ^ h0 == 0
assert mul(1 ^ h1, sq(z1)) ^ mul(p1, z1) ^ h1 == 0
zprod = mul(mul(z0, z1), z)
assert sq(zprod) ^ zprod ^ sq(z0 ^ z1) ^ sq(z) == 0
values = (h0, h1, p0, p1, z)
total = 0
for exponents in result["terms"]:
    term = 1
    for value, exponent in zip(values, exponents):
        term = mul(term, power(value, exponent))
    total ^= term
assert total == result["specialized_resultant_value"] == 0
assert result["term_count"] == len(result["terms"]) == 138
assert result["degree_z"] == 8
audit = {"status": "PASS_INDEPENDENT_N131_W23_RESULTANT_REPLAY",
         "term_count": len(result["terms"]), "degree_z": result["degree_z"],
         "specialized_resultant_value": total,
         "result_sha256": sha(HERE / "n131_h_bridge_result_v2.json"),
         "protocol_sha256": sha(HERE / "n131_bridge_protocol_v2.json"),
         "field_source_sha256": sha(FIELD_SOURCE),
         "auditor_sha256": sha(Path(__file__))}
(HERE / "n131_h_bridge_audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": audit["status"], "term_count": audit["term_count"]}, sort_keys=True))
