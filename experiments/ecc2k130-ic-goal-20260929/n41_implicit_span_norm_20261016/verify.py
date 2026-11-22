"""Audit the bounded symbolic norm trials against the native residue oracle."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def receipt(prefix, protocol):
    r = read(prefix + "_receipt.json")
    assert r["protocol_sha256"] == sha(HERE / protocol)
    if r.get("result_sha256") is not None:
        assert r["result_sha256"] == sha(HERE / (prefix + "_result.json"))
    return r


def main():
    source_paths = {
        "runner": HERE / "run.py",
        "tensor": ROOT / "n41_target_chart_symbolic_tensor_20261014/coefficients.bin",
        "codes": ROOT / "n41_triproduct_tensor_20261014/codes.txt",
        "source": ROOT / "n41_native_rootproduct_span_20261014/input.txt",
        "runtime": HERE / "sage_runtime_info.json"}
    for mode in ("smoke", "full"):
        p = read(mode + "_protocol.json")
        assert p["source_sha256"] == {k: sha(v) for k, v in source_paths.items()}
        r = receipt(mode, mode + "_protocol.json")
        assert r["status"] == "PARENT_TIME_CAP" and r["result_sha256"] is None
        assert r["wall_ns"] >= p["parent_wall_cap_seconds"]*10**9
    diagnostic = receipt("diagnostic", "diagnostic_protocol.json")
    assert diagnostic["status"] == "PARENT_TIME_CAP"
    trace = (HERE / "diagnostic_trace.log").read_text()
    assert "H_built" in trace and "G_built" in trace and "resultant_done" not in trace
    reduced = read("reduced_result.json")
    reduced_receipt = receipt("reduced", "reduced_protocol.json")
    assert reduced_receipt["status"] == "EXIT_0"
    assert reduced["status"] == "PASS_IMPLICIT_SPAN_NORM_SMOKE"
    assert reduced["span_rank"] == 3 and reduced["span_size"] == 8
    assert reduced["zero_second_codes"] == []
    oracle = read("oracle_result.json")
    codes_lines = source_paths["codes"].read_text().splitlines()
    assert codes_lines[0] == "N41CODES1 40"
    second_values = list(map(int, codes_lines[2].split()))
    assert len(second_values) == len(set(second_values)) == 40
    oracle_sources = read("oracle_protocol.json")["source_sha256"]
    assert oracle_sources == {
        "source": sha(HERE / "oracle.cpp"),
        "helpers": sha(HERE / "oracle_helpers.hpp"),
        "binary": sha(HERE / "oracle"),
        "tensor": sha(source_paths["tensor"]),
        "codes": sha(source_paths["codes"]),
        "source_roots": sha(source_paths["source"]),
        "prior_audit": sha(ROOT / "n41_bivariate_norm_batch_20261014/audit_result.json")}
    oracle_receipt = receipt("oracle", "oracle_protocol.json")
    assert oracle_receipt["status"] == "EXIT_0"
    assert oracle["status"] == "PASS_N41_EXPLICIT_SPAN_RESIDUE_ORACLE"
    assert oracle["allowed_second_codes"] == 39 and len(oracle["panels"]) == 2
    assert [p["ranks"][1]["zero_second_codes"] for p in oracle["panels"]] == [[37], []]
    assert all([v["span_size"] for v in panel["ranks"]] == [8, 128]
               for panel in oracle["panels"])
    assert all(len(v["coefficients"]) == 39 for panel in oracle["panels"]
               for v in panel["ranks"])
    coeff = oracle["panels"][0]["ranks"][0]["coefficients"]
    assert sha_bytes(repr(coeff).encode()) == reduced["symbolic_modulus_residue_sha256"]
    unit = read("unit_native_result.json")
    unit_sources = read("unit_native_protocol.json")["source_sha256"]
    assert unit_sources == {
        "source": sha(HERE / "unit_native.cpp"),
        "helpers": sha(HERE / "oracle_helpers.hpp"),
        "binary": sha(HERE / "unit_native"),
        "tensor": sha(source_paths["tensor"]),
        "codes": sha(source_paths["codes"]),
        "source_roots": sha(source_paths["source"]),
        "oracle_result": sha(HERE / "oracle_result.json")}
    unit_receipt = receipt("unit_native", "unit_native_protocol.json")
    assert unit_receipt["status"] == "EXIT_0"
    assert all(p["leading_degree_q"] == 16 and p["leading_zero_second_codes"] == []
               for p in unit["panels"])
    assert all(unit["panels"][i]["ranks"][j]["coefficients"] ==
               oracle["panels"][i]["ranks"][j]["coefficients"] and
               unit["panels"][i]["ranks"][j]["zero_second_codes"] ==
               oracle["panels"][i]["ranks"][j]["zero_second_codes"]
               for i in range(2) for j in range(2))
    sage_unit = receipt("unit", "unit_protocol.json")
    assert sage_unit["status"] == "PARENT_TIME_CAP"
    output = {"status": "PASS_N41_IMPLICIT_NORM_AUDIT",
              "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
              "first_code_index": 24,
              "rank3_symbolic_resultant_seconds": reduced["resultant_seconds_exploratory"],
              "rank3_explicit_sage_seconds": reduced["explicit_span_seconds_exploratory"],
              "rank3_explicit_native_ns": oracle["panels"][0]["ranks"][0]["query_ns"],
              "rank7_explicit_native_ns": oracle["panels"][0]["ranks"][1]["query_ns"],
              "rank7_symbolic_status": "PARENT_TIME_CAP",
              "leading_unit_on_allowed_codes": True,
              "witness_second_code": 37}
    with (HERE / "verification_v2.json").open("x") as out:
        json.dump(output, out, indent=2, sort_keys=True)
        out.write("\n")
    print(output["status"])


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    main()
