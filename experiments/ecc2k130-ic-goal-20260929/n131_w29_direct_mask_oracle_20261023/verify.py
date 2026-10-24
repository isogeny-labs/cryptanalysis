"""Read-only terminal audit of the N131 mask-decoder component."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/"n41_n131_fivepair_w9_w29_20261017/n131_control.json"
SAMPLE=HERE.parent/"n41_n131_fivepair_w9_w29_20261017/sample_audit_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((HERE/"protocol.json").read_text())
result=json.loads((HERE/"result.json").read_text())
audit=json.loads((HERE/"audit_result.json").read_text())
assert protocol["status"]=="FROZEN"
assert protocol["source_sha256"]==sha(SOURCE)
assert protocol["sample_audit_sha256"]==sha(SAMPLE)
assert protocol["script_sha256"]==sha(HERE/"run_sage.py")
assert protocol["runtime_info_sha256"]==sha(HERE/"sage_runtime_info.json")
assert result["protocol_sha256"]==audit["protocol_sha256"]==sha(HERE/"protocol.json")
assert audit["producer_sha256"]==sha(HERE/"result.json")
assert audit["auditor_sha256"]==sha(HERE/"audit_sage.py")
assert result["status"]=="PASS_N131_W29_DIRECT_MASK_ORACLE_COMPONENT"
assert audit["status"]=="PASS_INDEPENDENT_N131_GROUP_AND_SOURCE_AUDIT"
assert result["source_product_rank"]==28
assert result["left_valid_codes"]==128
assert result["s3_root_calls"]==len(result["rows"])==256
assert audit["source_valid_orbit_distinct_masks"]==128
assert audit["pair_root_sets_checked"]==128
assert audit["positive_target_reciprocal"]==protocol["target_reciprocal"]
assert result["positive_left_mask"]==protocol["left_masks"][0]==3
assert result["positive_right_mask"]==protocol["right_positive_mask"]==18
assert result["valid_source_candidates"]==1
positive=[r for r in result["rows"] if r["left_mask"]==3
          and r["left_root"]==protocol["left_positive_reciprocal"]]
assert len(positive)==1
assert positive[0]["valid_source_candidates"]==[
    {"mask":18,"root":protocol["right_positive_reciprocal"]}]
assert sum(len(r["valid_source_candidates"]) for r in result["rows"])==1
target_dependent_seconds=sum(r["query_ns"] for r in result["rows"])/1e9
assert 0<target_dependent_seconds<result["query_seconds"]
projected_calls=2*68308992
assert projected_calls==136617984
projected_seconds=target_dependent_seconds*projected_calls/256
assert 40000<projected_seconds<41000
lean=(HERE/"lean.stdout").read_text()
assert (HERE/"lean.stderr").read_text()==""
for theorem in ("fixed_seed_product_additive","frobenius_product_additive"):
    assert f"'SourceProductLinear.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
print(json.dumps({"status":"PASS_TERMINAL_AUDIT",
                  "source_product_rank":28,"checked_left_codes":128,
                  "target_dependent_seconds":target_dependent_seconds,
                  "projected_one_key_root_calls":projected_calls,
                  "projected_one_key_target_seconds":projected_seconds},sort_keys=True))
