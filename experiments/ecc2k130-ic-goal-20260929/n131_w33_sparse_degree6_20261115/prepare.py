"""Export exact N131 W33 Boolean coordinate equations for sparse elimination."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/"protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_W33_SPARSE_EXPORT"
for name,row in cfg["sources"].items():
    assert sha(row["path"])==row["sha256"],name
assert not (HERE/"prepare_result.json").exists()
spec=importlib.util.spec_from_file_location("w33_prior",cfg["sources"]["prior_runner"]["path"])
w=importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
b=w.block
source=json.loads(Path(cfg["sources"]["coefficients"]["path"]).read_text())
assert source["curve_id"]==cfg["curve_id"]
field=b.Field(131,(1<<13)|(1<<2)|(1<<1)|1)
positions=[i for i in range(33) if i!=898618 .bit_length()-1]
b.F=field;b.WIDTH=2;b.VARIABLES=34
b.LEFT=b.source_basis(field,898618<<1,positions,0)
b.RIGHT=b.source_basis(field,898618<<1,positions,18)
start=time.monotonic()
rows=[]
for target_index in cfg["target_indices"]:
    terms={(i,j):value for i,j,value in source["rows"][target_index]["terms"]}
    assert len(terms)==13
    anf=b.product_anf(terms,0)
    assert len(anf)==1619 and max(m.bit_count() for m in anf)<=4
    if target_index==0:
        assert b.evaluate_anf(anf,3,16722)==0
    base,equations=b.coordinate_rows(anf)
    path=HERE/f"equations_{target_index}.txt"
    assert not path.exists()
    support_total=0
    with path.open("w") as out:
        print("W33",34,131,1619,target_index,file=out)
        for eq in equations:
            present=[]
            while eq:
                low=eq&-eq
                present.append(base[low.bit_length()-1])
                eq^=low
            assert present
            support_total+=len(present)
            print(len(present),*present,file=out)
    rows.append({"target_index":target_index,"name":source["rows"][target_index]["name"],
                 "equation_sha256":sha(path),"bytes":path.stat().st_size,
                 "coordinate_support_total":support_total,
                 "degree_six_raw_entries":support_total*596})
result={"status":"PASS_W33_SPARSE_EQUATION_EXPORT",
        "curve_id":cfg["curve_id"],"rows":rows,
        "wall_seconds":time.monotonic()-start,
        "protocol_sha256":sha(HERE/"protocol.json"),"script_sha256":sha(__file__)}
(HERE/"prepare_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
