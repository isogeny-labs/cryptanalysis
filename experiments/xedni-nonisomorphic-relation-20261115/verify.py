"""Verify frozen rank-one relation census, independent audit, and Lean proof."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/"xedni-nonisomorphic-family-screen-20261115"
DIRECT=HERE.parent/"xedni-direct-relation-control-20261115"/"formal"/"DirectRelation.lean"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/"protocol.json").read_text())
    result=json.loads((HERE/"result.json").read_text())
    audit=json.loads((HERE/"audit.json").read_text())
    checks=((PARENT/"result.json","screen_result_sha256","screen_sha256"),
            (PARENT/"post-result.json","post_result_sha256","post_sha256"),
            (PARENT/"audit.json","post_audit_sha256","post_audit_sha256"),
            (DIRECT,"direct_relation_theorem_sha256","direct_theorem_sha256"))
    for path,pkey,rkey in checks:assert sha(path)==protocol[pkey]==result[rkey]
    assert result["protocol_sha256"]==sha(HERE/"protocol.json")
    assert result["source_sha256"]==sha(HERE/"run.py")
    assert result["status"]==audit["status"]=="PASS"
    totals=result["totals"]
    assert totals=={"queries":1471112,"candidate_pair_membership_tests":1954522,
                    "rational_relation_tests":516,"public_relation_tests":516,
                    "rational_relations":38,"rank_screen_candidates":24,
                    "rank_exact_unknown":2,"generator_proof_cells":2}
    assert len(result["fields"])==audit["fields"]==8
    status=Counter()
    hits=[]
    for field in result["fields"]:
        q=field["subgroup_order"]
        assert field["candidate_pair_membership_tests"]==q*q*len(field["models"])
        assert sha(HERE/field["raw_path"])==field["raw_sha256"]
        assert field["first_relation"]==field["relation_hits"][0]
        assert sum(m["counts"]["rational_relation"] for m in field["models"])==len(field["relation_hits"])
        for m in field["models"]:
            assert sum(m["counts"].get(s,0) for s in protocol["status_order"])==q*q
            assert m["counts"]["rational_relation_tests"]==m["counts"]["public_relation_tests"]
            assert m["counts"]["rational_relation_tests"]==m["counts"]["admitted_nonrelation"]+m["counts"]["rational_relation"]
            status.update({s:m["counts"].get(s,0) for s in protocol["status_order"]})
        for hit in field["relation_hits"]:
            t1,t2=hit["t"]
            assert hit["query_index_one_based"]==t1*q+t2+1
            assert hit["k"][0]+2*hit["k"][1]==0
            assert hit["recovered_scalar"]==((t1+2*t2)*pow(3,-1,q))%q==17
            hits.append(hit)
    assert len(hits)==38
    assert status=={"identity":8530,"duplicate":4260,"outside_cap":1941216,
                    "admitted_nonrelation":478,"rational_relation":38}
    assert audit["queries"]==totals["queries"]
    assert audit["membership_tests"]==totals["candidate_pair_membership_tests"]
    assert audit["rational_relation_tests"]==totals["rational_relation_tests"]
    assert audit["public_relation_tests"]==totals["public_relation_tests"]
    assert audit["rational_relations"]==audit["scalar_replays"]==totals["rational_relations"]
    assert not (HERE/"run.stderr").read_text() and not (HERE/"audit.stderr").read_text()
    assert (HERE/"sage-runtime-info.json").is_file()
    formal=HERE/"formal"
    assert (formal/"lean-toolchain").read_text().strip()=="leanprover/lean4:v4.35.0-rc4"
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in (formal/"lake-manifest.json").read_text()
    lean=(formal/"RankOneRelation.lean").read_text()
    assert not re.search(r"\b(?:sorry|admit|sorryAx|native_decide)\b",lean)
    build=(formal/"build-output.txt").read_text()
    assert "Build completed successfully (3138 jobs)" in build
    assert "'XedniNonisomorphicRelation.rank_one_relation_iff' depends on axioms: [propext]" in build
    assert "'XedniNonisomorphicRelation.recover_of_relation' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
    seal=HERE/"SEAL.sha256"
    if seal.exists():
        for line in seal.read_text().splitlines():
            expected,rel=line.split("  ",1)
            assert sha(HERE/rel)==expected,rel
    print(json.dumps({"status":"PASS","queries":totals["queries"],
                      "membership_tests":totals["candidate_pair_membership_tests"],
                      "relation_tests":totals["rational_relation_tests"],
                      "rational_relations":totals["rational_relations"],
                      "checked_theorems":2},sort_keys=True,indent=2))

if __name__=="__main__":main()
