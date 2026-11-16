"""Complete frozen vector-(1,2) relation census for qualified curve family."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/"xedni-nonisomorphic-family-screen-20261115"
DIRECT=HERE.parent/"xedni-direct-relation-control-20261115"/"formal"/"DirectRelation.lean"
BASE=HERE.parent/"xedni-fixed-curve-admission-20261115"/"result.json"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/"protocol.json").read_text())
    screen_path=PARENT/"result.json";post_path=PARENT/"post-result.json";audit_path=PARENT/"audit.json"
    for path,key in ((screen_path,"screen_result_sha256"),(post_path,"post_result_sha256"),
                     (audit_path,"post_audit_sha256"),(DIRECT,"direct_relation_theorem_sha256")):
        assert sha(path)==protocol[key]
    screen=json.loads(screen_path.read_text());post=json.loads(post_path.read_text())
    base=json.loads(BASE.read_text())
    assert len(screen["rows"])==24 and len(post["fields"])==len(base["fields"])==8
    qualified={(r["field_prime"],r["u"]):r["candidate"] for r in screen["rows"]
               if r["u"]>1 and r["candidate"].get("rank_status")=="proved"
               and r["candidate"].get("rank")==1 and r["candidate"].get("torsion_order")==1}
    assert set(qualified)=={(571,3),(677,3)}
    assert all(c["result"]["point_is_signed_generator"] for c in post["post_cells"])
    fields=[];totals=Counter()
    for old,admit in zip(base["fields"],post["fields"]):
        p,q=old["field_prime"],old["subgroup_order"]
        assert p==admit["field_prime"] and q==admit["subgroup_order"]
        m=old["subgroup_multiplier_m"]
        models=[]
        base_map={(k//m)%q:k for k in range(-4,5) if k%m==0}
        assert len(base_map)==old["admitted_offset_count"]
        models.append({"tag":"base","u":None,"curve_B":-2,"map":base_map})
        if (p,3) in qualified:
            cand=qualified[p,3]
            extra_map={(k*3)%q:k for k in range(-4,5)}
            models.append({"tag":"u3","u":3,"curve_B":cand["curve_B"],"map":extra_map})
        assert len(models)==admit["qualified_models"]
        counts=[Counter() for _ in models]
        hits=[];first=None
        raw=HERE/"rows"/f"p{p}.jsonl.gz"
        with raw.open("wb") as fh:
            with gzip.GzipFile(fileobj=fh,mode="wb",filename="",mtime=0) as gz:
                for t1 in range(q):
                    s1=(17-t1)%q
                    for t2 in range(q):
                        s2=(17-t2)%q
                        statuses=[]
                        for j,model in enumerate(models):
                            mapping=model["map"]
                            if s1==0 or s2==0: status="identity"
                            elif s1==s2: status="duplicate"
                            elif s1 not in mapping or s2 not in mapping: status="outside_cap"
                            else:
                                k1,k2=mapping[s1],mapping[s2]
                                counts[j]["rational_relation_tests"]+=1
                                counts[j]["public_relation_tests"]+=1
                                public=(s1+2*s2)%q==0
                                rational=k1+2*k2==0
                                assert public==rational
                                if rational:
                                    status="rational_relation"
                                    recovered=((t1+2*t2)*pow(3,-1,q))%q
                                    assert recovered==17
                                    hit={"field_prime":p,"model":model["tag"],"t":[t1,t2],
                                         "k":[k1,k2],"public_scalars":[s1,s2],
                                         "curve_B":model["curve_B"],"recovered_scalar":recovered,
                                         "query_index_one_based":t1*q+t2+1}
                                    hits.append(hit)
                                    if first is None:first=hit
                                else:status="admitted_nonrelation"
                            counts[j][status]+=1
                            statuses.append(status)
                        gz.write((json.dumps({"t":[t1,t2],"status":statuses},sort_keys=True,separators=(",",":"))+"\n").encode())
        for c in counts:assert sum(c[s] for s in protocol["status_order"])==q*q
        assert sum(c["rational_relation"] for c in counts)==len(hits)
        field={"field_prime":p,"subgroup_order":q,
               "models":[{"tag":model["tag"],"u":model["u"],"curve_B":model["curve_B"],
                          "reduced_scalar_to_rational_coordinate":{str(s):k for s,k in sorted(model["map"].items())},
                          "counts":dict(counts[j])} for j,model in enumerate(models)],
               "relation_hits":hits,"first_relation":first,
               "candidate_pair_membership_tests":q*q*len(models),
               "raw_path":str(raw.relative_to(HERE)),"raw_sha256":sha(raw)}
        fields.append(field)
        totals["queries"]+=q*q
        totals["candidate_pair_membership_tests"]+=field["candidate_pair_membership_tests"]
        totals["rational_relation_tests"]+=sum(c["rational_relation_tests"] for c in counts)
        totals["public_relation_tests"]+=sum(c["public_relation_tests"] for c in counts)
        totals["rational_relations"]+=len(hits)
    totals["rank_screen_candidates"]=24
    totals["rank_exact_unknown"]=2
    totals["generator_proof_cells"]=2
    print(json.dumps({"schema":"xedni-nonisomorphic-relation-result-v1","status":"PASS",
                      "protocol_sha256":sha(HERE/"protocol.json"),"source_sha256":sha(Path(__file__)),
                      "screen_sha256":sha(screen_path),"post_sha256":sha(post_path),
                      "post_audit_sha256":sha(audit_path),"direct_theorem_sha256":sha(DIRECT),
                      "base_admission_sha256":sha(BASE),"fields":fields,"totals":dict(totals)},
                     sort_keys=True,indent=2))

if __name__=="__main__":main()
