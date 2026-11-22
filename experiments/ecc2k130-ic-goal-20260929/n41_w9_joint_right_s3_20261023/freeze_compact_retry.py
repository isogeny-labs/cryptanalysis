"""Freeze a retry after the first compact probe monitor failure."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prior=json.loads((HERE/"compact_probe_protocol.json").read_text())
sources=dict(prior["sources"])
for path in (HERE/"probe_compact_retry.py",HERE/"compact_probe_protocol.json",
             HERE/"compact_probe_failure_v1.json",
             HERE/"compact_probe_0_baseline_result.json",
             HERE/"compact_probe_1_compact.stdout"):
    sources[str(path)]=sha(path)
record=dict(prior)
record["status"]="FROZEN_BEFORE_COMPACT_JOINT_S3_RETRY"
record["sources"]=sources
record["retry_reason"]="The first sandboxed process monitor lost termination authority after the second arm had printed its terminal line."
assert not (HERE/"compact_retry_protocol.json").exists()
with (HERE/"compact_retry_protocol.json").open("x") as out:
    json.dump(record,out,sort_keys=True,indent=2)
    out.write("\n")
print(json.dumps({"status":record["status"],"sources":len(sources)}))
