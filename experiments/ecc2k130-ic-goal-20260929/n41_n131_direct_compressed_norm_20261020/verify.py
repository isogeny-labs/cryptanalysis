"""Read-only audit of frozen inputs and direct compressed norm results."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name in ("n41", "n131", "build_bench"):
    protocol=HERE/f"{name}_protocol.json"
    result=HERE/f"{name}_result.json"
    p=json.loads(protocol.read_text())
    r=json.loads(result.read_text())
    for path, expected in p["sources"].items():
        assert sha(path)==expected, (name,path)
    assert r["protocol_sha256"]==sha(protocol)
    assert r["candidate_id"] is None
    assert r["curve_id"]==p["curve_id"]
    assert r["status"].startswith("PASS_")
    assert r["total_wall_seconds"] < p["wall_cap_seconds"]

n41=json.loads((HERE/"n41_result.json").read_text())
n131=json.loads((HERE/"n131_result.json").read_text())
bench=json.loads((HERE/"build_bench_result.json").read_text())
prior=json.loads((HERE.parent/"n41_n131_symbolic_affine_block_norm_20261019/compress_result.json").read_text())
prior131=json.loads((HERE.parent/"n41_n131_symbolic_affine_block_norm_20261019/n131_transfer_result.json").read_text())
assert [(r["prefix"],r["gcd_degree"]) for r in n41["rows"]] == [
    (r["prefix"],r["gcd_degree"]) for r in prior["rows"]]
assert all(r["explicit_product_equal"] for r in n41["rows"]+n131["rows"])
for target in ("constructed_w20_subset_positive","frozen_public_raw_point"):
    old={(r["prefix"],r["gcd_degree"]) for r in prior131["rows"] if r["target"]==target and r["prefix"] in (0,1)}
    new={(r["prefix"],r["gcd_degree"]) for r in n131["rows"] if r["target"]==target and r["width"]==4}
    assert old==new
assert len(n41["rows"])==16 and len(n131["rows"])==12
assert all(r["coefficient_identity"] and r["expanded_terms"]==1386 and
           r["compressed_terms"]==258 for r in bench["rows"])
log=(HERE/"lean_check.log").read_text()
assert "error:" not in log and "sorryAx" not in log
assert "'QuadraticBlockNorm.quartic_decomposition' depends on axioms: [propext, Classical.choice, Quot.sound]" in log
assert "'QuadraticBlockNorm.quartic_norm_step' depends on axioms: [propext, Classical.choice, Quot.sound]" in log
assert "sorry" not in (HERE/"QuadraticBlockNorm.lean").read_text()
print(json.dumps({"status":"PASS_DIRECT_COMPRESSED_NORM_AUDIT",
                  "n41_rows":len(n41["rows"]),"n131_rows":len(n131["rows"]),
                  "paired_build_rows":len(bench["rows"]),"lean":"checked"},sort_keys=True))
