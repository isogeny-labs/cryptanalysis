"""Read-only terminal audit of the frozen N41 oracle experiments."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent/"n41_n131_fivepair_w9_w29_20261017/join_input.tsv"


def read(name):
    return json.loads((HERE/name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


first_p = read("protocol.json")
first = read("result.json")
first_a = read("audit_result.json")
batch_p = read("batch_protocol.json")
batch = read("batch_result.json")
batch_a = read("batch_audit_result.json")
signature_p = read("decoder_protocol.json")
signature = read("decoder_result.json")
mask_p = read("mask_decoder_protocol.json")
mask = read("mask_decoder_result.json")
paired_p = read("paired_protocol.json")
paired = read("paired_result.json")

assert sha(INPUT) == first_p["input_sha256"] == batch_p["input_sha256"]
for p, script_field, script in ((first_p,"script_sha256","oracle_sage.py"),
                                (batch_p,"batch_script_sha256","batch_sage.py"),
                                (signature_p,"decoder_script_sha256","decoder_sage.py"),
                                (mask_p,"mask_decoder_script_sha256","mask_decoder_sage.py"),
                                (paired_p,"bench_script_sha256","paired_bench_sage.py")):
    assert sha(HERE/script) == p[script_field]
    assert sha(HERE/"sage_runtime_info.json") == p["runtime_info_sha256"]
for p,r,name in ((first_p,first,"protocol.json"),
                 (batch_p,batch,"batch_protocol.json"),
                 (signature_p,signature,"decoder_protocol.json"),
                 (mask_p,mask,"mask_decoder_protocol.json"),
                 (paired_p,paired,"paired_protocol.json")):
    assert r["protocol_sha256"] == sha(HERE/name)
assert first_a["protocol_sha256"] == sha(HERE/"protocol.json")
assert first_a["producer_sha256"] == sha(HERE/"result.json")
assert batch_a["protocol_sha256"] == sha(HERE/"batch_protocol.json")
assert batch_a["producer_sha256"] == sha(HERE/"batch_result.json")
assert paired["reference_sha256"] == sha(HERE/"batch_audit_result.json")
assert batch_a["eligible_pair_states"] == first_a["eligible_pair_states"] == 79424
assert first_a["s3_group_bridge_checks"] == 79424
assert first_a["exceptional_chart_pairs"] == 0
assert len(first["queries"]) == len(first_a["queries"]) == 17
assert len(batch["rows"]) == len(signature["rows"]) == len(mask["rows"]) == 256
assert batch["root_calls"] == signature["root_calls"] == mask["root_calls"] == 36352
assert mask["source_product_rank"] == 8
assert mask["right_coordinate_index_entries"] == 0
for i, (a,b,c) in enumerate(zip(batch["rows"],signature["rows"],mask["rows"])):
    assert a["suffix_ids"] == b["suffix_ids"] == c["suffix_ids"]
    assert a["matches"] == b["matches"] == c["matches"]
    assert a["matches"] == ([[0,130]] if i == 0 else [])
assert batch_a["positive_rows"] == [{"index":0,"matches":[[0,130]]}]
assert paired_p["order"] == ["index","decoder","decoder","index"]
assert [a["method"] for a in paired["arms"]] == paired_p["order"]
assert all(a["positive_key_indices"] == [0] and a["root_calls"] == 36352
           for a in paired["arms"])
assert abs(paired["index_mean_seconds"]-
           (paired["arms"][0]["seconds"]+paired["arms"][3]["seconds"])/2) < 1e-9
assert abs(paired["decoder_mean_seconds"]-
           (paired["arms"][1]["seconds"]+paired["arms"][2]["seconds"])/2) < 1e-9
lean = (HERE/"lean.stdout").read_text()
assert (HERE/"lean.stderr").read_text() == ""
for theorem in ("complete", "sound", "exact"):
    assert f"'OracleComplete.{theorem}' does not depend on any axioms" in lean
assert "'OracleComplete.quadratic_code_decode' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
assert 83612805*142 == 11873018310
assert 2*68308992 == 136617984
print(json.dumps({"status":"PASS_TERMINAL_AUDIT",
                  "verified_keys":256,"eligible_pair_states":79424,
                  "root_calls_per_key":142,
                  "paired_index_mean_seconds":paired["index_mean_seconds"],
                  "paired_decoder_mean_seconds":paired["decoder_mean_seconds"],
                  "full_N41_join_oracle_root_projection":11873018310},sort_keys=True))
