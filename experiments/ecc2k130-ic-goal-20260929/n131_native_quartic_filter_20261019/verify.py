"""Terminal replay of the frozen N131 native quartic-filter evidence."""
import hashlib
import gzip
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
read=lambda name:json.loads((HERE/name).read_text())
protocols=["reference_protocol.json","baseline_protocol.json","batch_protocol.json",
           "o2nv_protocol.json","unit_protocol.json"]
for name in protocols:
    protocol=read(name)
    assert protocol["candidate_id"] is None
    for source in protocol["sources"].values():
        assert sha(source["path"])==source["sha256"],(name,source["path"])

reference=read("reference_result.json")
assert reference["status"]=="COMPLETE_N131_NATIVE_REFERENCE"
assert reference["protocol_sha256"]==sha(HERE/"reference_protocol.json")
assert reference["script_sha256"]==sha(HERE/"reference_sage.py")
assert reference["input_sha256"]==sha(HERE/"input_extended.tsv")
assert reference["requested_rows"]==len(reference["rows"])==258
assert [(x["target_index"],x["p_code"]) for x in reference["rows"]]==[
    (ti,code) for ti in (0,1) for code in [*range(128),16722]]
assert [(x["target_index"],x["p_code"],x["gcd_degree"])
        for x in reference["rows"] if not x["reject"]]==[(0,3,1)]

input_lines=(HERE/"input_extended.tsv").read_text().splitlines()
assert input_lines[0]=="N131_NATIVE_QUARTIC 2 13 258"
assert input_lines[1]=="POS 3 16722"
assert len(input_lines)==2+26+258
coefficients=json.loads(Path(read("reference_protocol.json")["sources"]["coefficients"]["path"]).read_text())
expected_terms=[f'C {ti} {i} {j} {c}' for ti,row in enumerate(coefficients["rows"][:2])
                for i,j,c in row["terms"]]
assert input_lines[2:28]==expected_terms
for line,row in zip(input_lines[28:],reference["rows"]):
    assert line==f'T {row["target_index"]} {row["p_code"]} {int(row["reject"])}'

runs={name:json.loads((HERE/name).read_text()) for name in
      ("baseline_run.stdout","batch_run.stdout","o2nv_run.stdout")}
for name,row in runs.items():
    assert row["status"]=="COMPLETE_SAMPLE",name
    assert row["controls_checked"]==258 and row["positive_pair_checked"] is True
    assert row["sample_target_index"]==1
    assert row["sample_requested"]==row["sample_checked"]==1048576
    assert row["sample_unresolved"]==0 and row["exceptional_degree_count"]==0
    assert row["peak_rss_raw"]<4294967296 and row["wall_seconds"]<120
    assert row["sample_seconds"]>0

unit=json.loads((HERE/"unit_frozen.stdout").read_text())
assert unit=={"status":"PASS_NATIVE_FIELD_AND_PLANTED_ROOTS",
              "multiplication_checks":200,"square_checks":200,"inverse_checks":200,
              "planted_roots_preserved":100,"perturbed_rejected":100}
compiler=read("compiler_probe.json")
assert compiler["source_sha256"]==sha(HERE/"native_batch.cpp")
assert [row["label"] for row in compiler["attempts"]]==["o2","o3"]
for row in compiler["attempts"]:
    assert row["status"]=="COMPILER_FAILURE" and row["exit_code"]!=0
    assert row["stdout_sha256"]==sha(HERE/f'compiler_{row["label"]}.stdout')
    stderr=gzip.decompress((HERE/f'compiler_{row["label"]}.stderr.gz').read_bytes())
    assert row["stderr_sha256"]==hashlib.sha256(stderr).hexdigest()
    assert b"Segmentation fault: 11" in stderr

lean=read("lean_check.json")
assert lean["status"]=="LEAN_BUILD_PASS"
assert lean["module_sha256"]==sha(HERE/"SourceProductLinear.lean")
assert "sorryAx" not in (HERE/"lean.stdout").read_text()
assert (HERE/"lean.stderr").read_text()==""
result={"status":"PASS_N131_NATIVE_QUARTIC_GATE","reference_cases":258,
        "planted_roots":100,"public_prefix_codes":1048576,
        "sample_seconds":{name:row["sample_seconds"] for name,row in runs.items()},
        "candidate_id":None}
(HERE/"verification_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
