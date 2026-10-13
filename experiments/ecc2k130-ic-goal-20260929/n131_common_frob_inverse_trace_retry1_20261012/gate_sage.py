"""Independent Sage replay of ten inverse-trace source witnesses."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
SUPPORT=GOAL/"n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
PRIOR_FIXTURE=GOAL/"n131_common_frob_fivepair_20261012/fixture.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol=json.loads((HERE/"gate_protocol.json").read_text())
    files={"script":HERE/"gate_sage.py","fixture":HERE/"fixture.json",
           "prior_fixture":PRIOR_FIXTURE,"support":SUPPORT,
           "runtime":HERE/"sage_runtime_info.json"}
    assert protocol["status"]=="FROZEN_BEFORE_N131_INVERSE_TRACE_SAGE_REPLAY"
    assert protocol["sha256"]=={key:sha(path) for key,path in files.items()}
    assert sha(HERE/"fixture.json")==sha(PRIOR_FIXTURE)
    fixture=json.loads((HERE/"fixture.json").read_text())
    supported={int(mask):int(column) for mask,column in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    assert len(supported)==131307
    ring=PolynomialRing(GF(2),"t")
    t=ring.gen()
    field=GF(2**131,name="t",modulus=t**131+t**13+t**2+t+1)
    checked=[]
    for pair in fixture["masks"]:
        for mask in pair:
            assert mask in supported
            w=field(sum((t**(i+1) for i in range(18) if (mask>>i)&1),ring.zero()))
            inverse=w**-1
            assert w*inverse==1 and inverse.trace()==0
            checked.append({"mask":mask,"folded_column":supported[mask],
                            "inverse_trace":0})
    assert len(checked)==10 and len({item["folded_column"] for item in checked})==10
    result={"status":"PASS_CHECKED_SAGE_N131_FIVEPAIR_INVERSE_TRACE_WITNESSES",
            "curve_id":fixture["curve_id"],"witnesses":checked,
            "support_sha256":sha(SUPPORT),
            "protocol_sha256":sha(HERE/"gate_protocol.json")}
    with (HERE/"gate_result.json").open("x") as out:
        json.dump(result,out,sort_keys=True,indent=2)
        out.write("\n")
    print(result["status"],len(checked),flush=True)


if __name__=="__main__":
    main()
