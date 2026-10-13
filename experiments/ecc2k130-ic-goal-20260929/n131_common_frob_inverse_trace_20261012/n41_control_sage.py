"""Independent N41 source-equivalence and unpinned-relation source check."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
GEOMETRY=GOAL/"n41_w7_entropy_cubic_20261011/w8/geometry.json"
RELATION=GOAL/"n41_common_frob_factor_20261012/audit_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol=json.loads((HERE/"n41_protocol.json").read_text())
    files={"script":HERE/"n41_control_sage.py","geometry":GEOMETRY,
           "relation":RELATION,"runtime":HERE/"sage_runtime_info.json",
           "source_gate":HERE/"circuit.py"}
    assert protocol["status"]=="FROZEN_BEFORE_N41_SOURCE_EQUIVALENCE"
    assert protocol["sha256"]=={key:sha(path) for key,path in files.items()}
    ring=PolynomialRing(GF(2),"t")
    t=ring.gen()
    field=GF(2**41,name="t",modulus=t**41+t**3+1)
    rows=json.loads(GEOMETRY.read_text())["rows"]
    supported={int(row["mask"]) for row in rows}
    admitted=set()
    for mask in range(1,256):
        w=sum((t**(i+1) for i in range(8) if (mask>>i)&1),ring.zero())
        value=field(w)
        if (value**-1).trace()==0:
            admitted.add(mask)
    assert admitted==supported and len(admitted)==125
    relation=json.loads(RELATION.read_text())
    assert relation["status"]=="PASS_INDEPENDENT_N41_COMMON_FROBENIUS_PUBLIC_RELATION"
    assert relation["rank_after"]==7
    selected=[mask for pair in relation["source_pair_states"] for mask in pair["masks"]]
    assert len(selected)==10 and all(mask in admitted for mask in selected)
    result={"status":"PASS_CHECKED_SAGE_N41_INVERSE_TRACE_SOURCE_AND_PUBLIC_CONTROL",
            "tested_masks":255,"admitted_masks":len(admitted),
            "public_relation_source_masks":selected,
            "public_relation_rank_after":relation["rank_after"],
            "protocol_sha256":sha(HERE/"n41_protocol.json")}
    with (HERE/"n41_control_result.json").open("x") as out:
        json.dump(result,out,sort_keys=True,indent=2)
        out.write("\n")
    print(result["status"],len(admitted),flush=True)


if __name__=="__main__":
    main()
