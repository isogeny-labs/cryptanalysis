"""Read-only source, input, resource, and terminal-status receipt audit."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((HERE/"protocol.json").read_text())
prep=json.loads((HERE/"prepare_result.json").read_text())
q=json.loads((HERE/"run_protocol.json").read_text())
r=json.loads((HERE/"run_result.json").read_text())
assert p["status"]=="FROZEN_BEFORE_W33_SPARSE_EXPORT"
assert q["status"]=="FROZEN_BEFORE_SPARSE_DEGREE6_RUN"
assert r["status"]=="COMPLETE_SPARSE_DEGREE6_SUPERVISION"
assert p["curve_id"]==q["curve_id"]==r["curve_id"]
assert prep["protocol_sha256"]==sha(HERE/"protocol.json")
assert r["protocol_sha256"]==sha(HERE/"run_protocol.json")
for name,row in p["sources"].items():
    assert sha(row["path"])==row["sha256"],name
for name,digest in q["sha256"].items():
    assert sha(HERE/name)==digest,name
assert [row["target_index"] for row in prep["rows"]]==[0,1]
assert [row["coordinate_support_total"] for row in prep["rows"]]==[106259,105812]
for row in prep["rows"]:
    index=row["target_index"]
    assert sha(HERE/f"equations_{index}.txt")==row["equation_sha256"]
    assert row["degree_six_raw_entries"]==row["coordinate_support_total"]*596
assert len(r["rows"])==2
for index,row in enumerate(r["rows"]):
    assert row["target_index"]==index
    assert row["stdout_sha256"]==sha(HERE/f"arm_{index}.stdout")
    assert row["stderr_sha256"]==sha(HERE/f"arm_{index}.stderr")
    assert row["parent_wall_seconds"]<=q["parent_limit_seconds_per_arm"]+1
    assert row["peak_child_rss_sample_bytes"]<q["rss_cap_bytes"]
assert r["rows"][0]["status"]=="EXTERNAL_TIMEOUT"
assert r["rows"][0]["parent_stop"]=="EXTERNAL_TIMEOUT"
assert r["rows"][0]["child_result"] is None
assert r["rows"][1]["status"]=="BOUNDED_TIME"
c=r["rows"][1]["child_result"]
assert c==json.loads((HERE/"arm_1.stdout").read_text())
assert c["target_index"]==1 and c["mode"]=="numeric"
assert c["rows_processed"]==c["rank"]==4752
assert c["total_rows"]==78076 and c["zero_rows"]==0
assert not c["constant_in_span"]
assert c["stored_words"]==47915805 and c["maxrss_raw"]<q["rss_cap_bytes"]
assert "ModuleNotFoundError: No module named 'psutil'" in (HERE/"first_attempt_error.txt").read_text()
assert (HERE/"sage_runtime_info.json").stat().st_size>0
print(json.dumps({"status":"PASS_SPARSE_DEGREE6_RECEIPT",
                  "public_rows_processed":c["rows_processed"],
                  "positive_status":r["rows"][0]["status"],
                  "public_status":r["rows"][1]["status"],
                  "run_result_sha256":sha(HERE/"run_result.json")},sort_keys=True))
