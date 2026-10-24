"""Freeze the compact alternate-association circuit."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


base=json.loads((HERE/"build_protocol.json").read_text())
sources=dict(base["sources"])
for path in (HERE/"build_compact.py",HERE/"build_protocol.json",
             HERE/"build_result.json",HERE/"join_rows.json"):
    sources[str(path)]=sha(path)
record=dict(base)
record["status"]="FROZEN_BEFORE_COMPACT_JOINT_RIGHT_S3_BUILD"
record["method"]="explicit pair3 source quadratic and two association S3 links; omit the preceding quartic"
record["sources"]=sources
assert not (HERE/"compact_build_protocol.json").exists()
with (HERE/"compact_build_protocol.json").open("x") as out:
    json.dump(record,out,sort_keys=True,indent=2)
    out.write("\n")
print(json.dumps({"status":record["status"],"sources":len(sources)}))
