"""Verify frozen screen, post-selection, Sage replay, Lean proof, and seal."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    proto=json.loads((HERE/"protocol.json").read_text())
    postproto=json.loads((HERE/"post-protocol.json").read_text())
    screen=json.loads((HERE/"result.json").read_text())
    post=json.loads((HERE/"post-result.json").read_text())
    audit=json.loads((HERE/"audit.json").read_text())
    selection=PARENT/"xedni-large-order-admission-20261115"/"result.json"
    parent=PARENT/"xedni-fixed-curve-admission-20261115"/"result.json"
    assert proto["input_selection_result_sha256"]==screen["input_sha256"]==sha(selection)
    assert screen["protocol_sha256"]==sha(HERE/"protocol.json")
    assert screen["source_sha256"]==sha(HERE/"screen.py")
    assert screen["worker_sha256"]==sha(HERE/"worker.py")
    assert postproto["parent_screen_result_sha256"]==post["parent_screen_sha256"]==sha(HERE/"result.json")
    assert postproto["parent_fixed_admission_result_sha256"]==post["parent_admission_sha256"]==sha(parent)
    assert post["post_protocol_sha256"]==sha(HERE/"post-protocol.json")
    assert post["source_sha256"]==sha(HERE/"post.py")
    assert post["worker_sha256"]==sha(HERE/"post_worker.py")
    assert len(screen["rows"])==24
    assert screen["status_counts"]=={"completed":22,"rank_unknown":2}
    ranks=Counter(r["candidate"].get("rank") for r in screen["rows"])
    assert ranks=={1:9,2:5,3:5,4:3,None:2}
    for row in screen["rows"]:
        assert row["status"] in ("completed","rank_unknown")
        assert row["exit_code"]==0
        assert sha(HERE/row["stdout_path"])==row["stdout_sha256"]
        assert sha(HERE/row["stderr_path"])==row["stderr_sha256"]
        assert not (HERE/row["stderr_path"]).read_bytes()
        assert json.loads((HERE/row["stdout_path"]).read_text().strip().splitlines()[-1])==row["candidate"]
        assert row["candidate"]["torsion_order"]==1
        assert row["candidate"]["point_nontorsion"]
    assert {(r["field_prime"],r["u"]) for r in screen["rows"] if r["status"]=="rank_unknown"}=={(571,2),(593,3)}
    assert len(post["post_cells"])==2
    for cell in post["post_cells"]:
        assert cell["status"]=="completed" and cell["exit_code"]==0
        assert sha(HERE/cell["stdout_path"])==cell["stdout_sha256"]
        assert sha(HERE/cell["stderr_path"])==cell["stderr_sha256"]
        assert not (HERE/cell["stderr_path"]).read_bytes()
        assert cell["result"]["rank"]==1 and cell["result"]["torsion_order"]==1
        assert cell["result"]["point_is_signed_generator"]
        assert cell["result"]["point_index_up_to_20"]==1
    assert {(c["field_prime"],c["u"]) for c in post["post_cells"]}=={(571,3),(677,3)}
    assert post["totals"]=={"queries":1471112,"pair_tests":1954522,
                            "baseline_pairs":592,"union_pairs":736,"additional_pairs":144}
    assert len(post["fields"])==8
    for f in post["fields"]:
        assert f["pair_tests"]==f["subgroup_order"]**2*f["qualified_models"]
        assert f["union_pairs"]==f["baseline_pairs"]+f["additional_pairs"]
        assert sha(HERE/f["raw_path"])==f["raw_sha256"]
        if f["field_prime"] in (571,677):
            assert f["qualified_models"]==2 and f["union_pairs"]==153 and f["additional_pairs"]==72
        else:
            assert f["qualified_models"]==1 and f["additional_pairs"]==0
    assert audit["status"]=="PASS"
    for key in ("queries","pair_tests","baseline_pairs","union_pairs","additional_pairs"):
        assert audit[key]==post["totals"][key]
    assert audit["screen_rows"]==24 and audit["rank_proved"]==22
    assert audit["rank_unknown"]==2 and audit["qualified_nonbase_rank_one"]==2
    assert not (HERE/"screen.stderr").read_text()
    assert not (HERE/"post.stderr").read_text()
    assert not (HERE/"audit.stderr").read_text()
    assert (HERE/"sage-runtime-info.json").is_file()
    formal=HERE/"formal"
    assert (formal/"lean-toolchain").read_text().strip()=="leanprover/lean4:v4.35.0-rc4"
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in (formal/"lake-manifest.json").read_text()
    lean=(formal/"UnionCount.lean").read_text()
    assert not re.search(r"\b(?:sorry|admit|sorryAx|native_decide)\b",lean)
    build=(formal/"build-output.txt").read_text()
    assert "Build completed successfully (3138 jobs)" in build
    for name in ("pair_union_card_599","pair_union_card_353"):
        assert f"'XedniNonisomorphicFamily.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
    seal=HERE/"SEAL.sha256"
    if seal.exists():
        for line in seal.read_text().splitlines():
            expected,rel=line.split("  ",1)
            assert sha(HERE/rel)==expected,rel
    print(json.dumps({"status":"PASS","screen_rows":24,"rank_proved":22,
                      "rank_unknown":2,"qualified_nonbase_rank_one":2,
                      "queries":1471112,"union_pairs":736,
                      "additional_pairs":144,"checked_theorems":2},sort_keys=True,indent=2))

if __name__=="__main__":main()
