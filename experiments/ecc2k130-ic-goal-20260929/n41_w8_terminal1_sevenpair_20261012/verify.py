"""Verify frozen N41 one-state miss and four-sign relation recovery."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n41_w8_sixpair_mitm_20261011"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_query(version, runner, states, status):
    suffix = "" if version == 1 else "_v2"
    protocol_name = "protocol.json" if version == 1 else "protocol_v2.json"
    result_name = "query_result.json" if version == 1 else "query_result_v2.json"
    protocol, result = read(protocol_name), read(result_name)
    assert protocol["terminal_signed_states"] == states
    assert protocol["source_sha256"] == {name: sha(path) for name, path in runner.sources().items()}
    assert result["protocol_sha256"] == sha(HERE / protocol_name)
    assert result["status"] == status
    assert result["target_count"] == result["worker_count"] == 1
    assert result["preflight_group_checks_passed"]
    assert result["wall_ns_exploratory"] < protocol["parent_wall_cap_seconds"]*10**9
    assert result["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
    assert result["stop_reason"] is None and result["exit_code"] == 0
    stdout = HERE / ("join" + suffix + ".stdout.txt")
    stderr = HERE / ("join" + suffix + ".stderr.txt")
    assert result["stdout_sha256"] == sha(stdout)
    assert result["stderr_sha256"] == sha(stderr)
    assert not stderr.read_bytes()
    assert result["hit_lines"] == [line for line in stdout.read_text().splitlines()
                                   if line.startswith("HIT ")]
    return protocol, result


def main():
    one = load("n41_terminal_one_runner", HERE / "run.py")
    four = load("n41_terminal_four_runner", HERE / "run_v2.py")
    p1, q1 = check_query(1, one, 1, "COMPLETE_RESTRICTED_SOURCE_SCAN")
    p4, q4 = check_query(2, four, 4, "HITS_PENDING_SAGE_REPLAY")
    assert p1["curve_id"] == p4["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
    assert p1["public_target_transported"] == p4["public_target_transported"]
    assert p1["raw_target_preimage"] == p4["raw_target_preimage"]
    assert p1["uniform_raw_point_mean_upper_decimal"] == "1.80365492326"
    assert p4["uniform_raw_point_mean_upper_decimal"] == "7.21461969305"
    assert q1["hit_lines"] == []
    assert any(line.startswith("MISS_COMPLETE 2297856 0 ")
               for line in (HERE / "join.stdout.txt").read_text().splitlines())
    assert len(q4["hit_lines"]) == 1
    assert q4["hit_lines"][0].split()[2:9] == ["9", "109", "43", "30", "69", "34", "3"]
    ap, audit = read("audit_protocol_v2.json"), read("sage_audit_result_v2.json")
    assert ap["status"] == "FROZEN_N41_TERMINAL4_SAGE_AUDIT"
    assert ap["sha256"] == {
        "source": sha(HERE / "audit_sage_v2.py"),
        "protocol": sha(HERE / "protocol_v2.json"),
        "query": sha(HERE / "query_result_v2.json"),
        "geometry": sha(ROOT / "n41_w7_entropy_cubic_20261011/w8/geometry.json"),
        "fixture": sha(ROOT / "n41_w7_entropy_cubic_20261011/w8/fixture.json"),
        "input": sha(BASE / "join_input.tsv"),
        "runtime": sha(HERE / "sage_runtime_info.json"),
    }
    assert audit["audit_protocol_sha256"] == sha(HERE / "audit_protocol_v2.json")
    assert audit["status"] == "PASS_INDEPENDENT_N41_TERMINAL4_RELATION"
    assert audit["verified_hits"] == audit["rank_from_empty_matrix"] == 1
    assert audit["replayed"][0]["folded_columns_distinct"] == 14
    assert audit["replayed"][0]["novel_rank"] == 1
    assert audit["replayed"][0]["state_ids"] == [9, 109, 43, 30, 69, 34, 3]
    rp, recovery = read("recovery_protocol_v2.json"), read("recovery_result_v2.json")
    assert rp["status"] == "FROZEN_N41_TERMINAL4_RECOVERY"
    assert rp["sha256"] == {
        "source": sha(HERE / "recover_sage_v2.py"),
        "relations": sha(HERE / "sage_audit_result_v2.json"),
        "prepared_factor_logs": sha(ROOT / "n41_w8_sixpair_logprep_20261011/audit_result.json"),
        "runtime": sha(HERE / "sage_runtime_info.json"),
    }
    assert recovery["recovery_protocol_sha256"] == sha(HERE / "recovery_protocol_v2.json")
    assert recovery["status"] == "PASS_TERMINAL4_N41_TARGET_SCALAR_RECOVERY"
    assert recovery["verified_relation_count"] == recovery["rank_from_empty_matrix"] == 1
    assert recovery["recovered_scalar_mod_r"] == "445577591162"
    assert recovery["independent_scalar_replay"]
    assert not (HERE / "audit_v2.stderr.txt").read_bytes()
    assert not (HERE / "recovery_v2.stderr.txt").read_bytes()
    print(json.dumps({"status": "PASS_N41_TERMINAL4_ONE_TARGET_RECOVERY_CONTROL",
                      "single_state_scan": q1["status"],
                      "four_sign_rank": audit["rank_from_empty_matrix"],
                      "scalar": recovery["recovered_scalar_mod_r"]}, sort_keys=True))


if __name__ == "__main__":
    main()
