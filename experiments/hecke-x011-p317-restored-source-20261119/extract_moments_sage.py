"""Evaluate hash-pinned Hecke functions at the restored source point."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
from sage.all import GF

H = Path(__file__).resolve().parent
P = json.loads((H/"protocol.json").read_text())
archive = Path(os.environ.get("ARCHIVE_ROOT", "/Volumes/SSD990/cryptanalysis"))
source_path = archive/"experiments/hecke-d1407-f6-20261023/regularized/tools/hecke11.py"
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == P["regularized_hecke_source_sha256"]
spec = importlib.util.spec_from_file_location("hecke11_regularized_p317", source_path)
hecke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hecke)
funcs,jfun = hecke.build([2,5])
R = hecke.Reduced(317,funcs,jfun,[2,5])
Q = R.E(16,60)
assert R.j(Q) == R.Fp(-121)
moments = {}
for ell in [2,5]:
    moments[str(ell)] = {
        "x": [int(R.funcs[(ell,"x",k)](Q[0],Q[1])) for k in range(1,ell+2)],
        "xy": [int(R.funcs[(ell,"xy",k)](Q[0],Q[1])) for k in range(ell+1)],
        "a_ell": int(hecke.E0.ap(ell)),
    }
cache_path = archive/"experiments/hecke-d79-function-cache-20261027/artifacts/hecke13-131d0dc58a1a92a5c8f7aa2f79870dbd3b906accd17e019ee0e72d054ebc86ac.json"
raw = cache_path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == P["degree13_function_artifact_sha256"]
cache = json.loads(raw)
assert cache["source_sha256"] == P["degree13_function_artifact_source_sha256"]
F = GF(317)
values = {}
for item in cache["funcs"]:
    ell,kind,k = item["key"]
    assert ell == 13
    val = sum(F(n)/F(d)*F(16)**a*F(60)**b for a,b,(n,d) in item["terms"])
    values[(kind,k)] = int(val)
assert len(values) == 28
moments["13"] = {"x":[values["x",k] for k in range(1,15)],
                 "xy":[values["xy",k] for k in range(14)],
                 "a_ell":int(hecke.E0.ap(13))}
output = {"schema":"x011-p317-restored-moments-v1","p":317,"point":[16,60],
          "source_sha256":P["regularized_hecke_source_sha256"],
          "degree13_artifact_sha256":P["degree13_function_artifact_sha256"],
          "moments":moments}
(H/"moments.json").write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
print(json.dumps({"degrees":list(moments),"a_ell":{k:v["a_ell"] for k,v in moments.items()}},sort_keys=True))
