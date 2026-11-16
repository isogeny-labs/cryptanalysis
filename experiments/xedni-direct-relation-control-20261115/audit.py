"""Independent first-hit replay of the public reduced two-point relation."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BAND=HERE.parent/"xedni-crt-band-panel-20261115"
SHIFT=HERE.parent/"xedni-point-lift-shift-20261115"
ARITH=HERE.parent/"xedni-crt-prime-panel-20261115"/"audit.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol=json.loads((HERE/"protocol.json").read_text())
    band=json.loads((BAND/"result.json").read_text())
    shift=json.loads((SHIFT/"result.json").read_text())
    assert protocol["schema"]=="xedni-direct-relation-control-protocol-v1"
    for key,path in (("parent_band_result_sha256",BAND/"result.json"),
                     ("shift_result_sha256",SHIFT/"result.json"),
                     ("arithmetic_audit_source_sha256",ARITH),
                     ("shift_audit_source_sha256",SHIFT/"audit.py")):
        assert sha(path)==protocol[key],key
    assert band["status"]==shift["status"]=="PASS"
    assert [f["field_prime"] for f in band["fields"]]==protocol["fields"]
    assert [f["field_prime"] for f in shift["fields"]]==protocol["fields"]
    spec=importlib.util.spec_from_file_location("xedni_direct_arith",ARITH)
    arith=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arith)
    base=[0,0,0,-1,-2]
    output=[]
    total=0
    for old,new in zip(band["fields"],shift["fields"],strict=True):
        p,r=old["field_prime"],old["subgroup_order"]
        assert r==new["subgroup_order"]
        G,Q=tuple(old["generator"]),tuple(old["public_target"])
        assert old["generator"]==new["generator"]
        assert old["public_target"]==new["public_target"]
        assert old["fixture_scalar"]==new["fixture_scalar"]
        assert arith.mul(r,G,base,p) is None
        sampled=[arith.add(Q,arith.neg(arith.mul(t,G,base,p),base,p),base,p)
                 for t in range(r)]
        first=None
        direct_count=0
        admissible=0
        for index in range(r*r):
            t1,t2=divmod(index,r)
            U,V=sampled[t1],sampled[t2]
            if U is None or V is None or U==V:
                continue
            admissible+=1
            direct=arith.add(U,arith.mul(2,V,base,p),base,p) is None
            direct_count+=direct
            if direct and first is None:
                recovered=((t1+2*t2)*pow(3,-1,r))%r
                assert arith.mul(recovered,G,base,p)==Q
                first={"t":[t1,t2],"query_index_one_based":index+1,
                       "recovered_scalar":recovered}
        assert admissible==old["counts"]["admissible_pairs"]==new["counts"]["admissible_pairs"]
        assert direct_count==r-1
        # Independently scan both raw streams for the same first direct event.
        probe_prefixes=[]
        for folder,record in ((BAND,old),(SHIFT,new)):
            rawhash=hashlib.sha256()
            seen=0
            first_saved=None
            probes_so_far=0
            first_rational_probes=None
            for shard in record["row_shards"]:
                raw=gzip.open(folder/"rows"/shard,"rb").read()
                rawhash.update(raw)
                for line in raw.splitlines():
                    row=json.loads(line)
                    t1,t2=divmod(seen,r)
                    assert row["t"]==[t1,t2]
                    probes_so_far+=row.get("attempts_7",0)+row.get("attempts_11",0)
                    if row["reduced_relation"] and first_saved is None:
                        first_saved={"t":[t1,t2],"query_index_one_based":seen+1}
                    if row["rational_relation"] and first_rational_probes is None:
                        first_rational_probes=probes_so_far
                    seen+=1
            assert seen==r*r and rawhash.hexdigest()==record["rows_sha256"]
            assert first_saved is not None
            assert first_saved["t"]==first["t"]
            assert first_saved["query_index_one_based"]==first["query_index_one_based"]
            probe_prefixes.append(first_rational_probes)
        for record in (old,new):
            hit=record["first_rational_relation"]
            if hit is not None:
                assert first["query_index_one_based"]<=hit["query_index_one_based"]
        output.append({"field_prime":p,"subgroup_order":r,"queries":r*r,
                       "admissible_pairs":admissible,"direct_relation_count":direct_count,
                       "first_direct":first,
                       "first_centered_rational":old["first_rational_relation"],
                       "first_centered_rational_probes":probe_prefixes[0],
                       "first_shifted_rational":new["first_rational_relation"],
                       "first_shifted_rational_probes":probe_prefixes[1]})
        total+=r*r
    assert total==protocol["max_queries"]
    print(json.dumps({"schema":"xedni-direct-relation-control-result-v1","status":"PASS",
                      "protocol_sha256":sha(HERE/"protocol.json"),
                      "source_sha256":sha(Path(__file__)),
                      "queries_checked":total,"fields":output},sort_keys=True,indent=2))


if __name__=="__main__":
    main()
