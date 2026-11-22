"""Verify frozen inputs, monitor receipts, archived failures, and exact decisions."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


for name, expected in (("protocol_n41.json", "FROZEN_BEFORE_N41_BLOCK_NORM"),
                       ("protocol_n41_v2.json", "FROZEN_BEFORE_N41_BLOCK_NORM_V2"),
                       ("protocol_n131.json", "FROZEN_BEFORE_N131_BLOCK_NORM"),
                       ("protocol_n131_v3.json", "FROZEN_BEFORE_N131_BLOCK_NORM_V3"),
                       ("protocol_scaling.json", "FROZEN_BEFORE_N131_BLOCK_NORM_SCALING")):
    protocol = load(name)
    assert protocol["status"] == expected and protocol["worker_count"] == 1
    assert protocol["rss_cap_bytes"] == 4294967296
    for source in protocol["sources"].values():
        assert sha(source["path"]) == source["sha256"]


for number, case, supervisor in ((1, "n41", "supervise.py"),
                                  (2, "n131", "supervise_v2.py")):
    attempt = load(f"attempt{number}/attempt.json")
    assert attempt["status"] == "PARENT_MONITOR_FAILURE_CHILD_COMPLETED"
    assert attempt["supervisor_sha256"] == sha(HERE / supervisor)
    for name, digest in attempt["sources"].items():
        assert sha(HERE / f"attempt{number}" / name) == digest
    child = load(f"attempt{number}/{case}_result.json")
    assert child["status"] == f"PASS_{case.upper()}_BLOCK_NORM_GATE"


for case, protocol in (("n41", "protocol_n41_v2.json"),
                       ("n131", "protocol_n131_v3.json")):
    worker = load(f"{case}_result.json")
    receipt = load(f"{case}_supervisor.json")
    assert worker["status"] == receipt["status"] == f"PASS_{case.upper()}_BLOCK_NORM_GATE"
    assert receipt["protocol_sha256"] == sha(HERE / protocol)
    supervisor_script = "supervise_v2.py" if case == "n41" else "supervise_v3.py"
    assert receipt["supervisor_sha256"] == sha(HERE / supervisor_script)
    assert receipt["result_sha256"] == sha(HERE / f"{case}_result.json")
    assert receipt["stdout_sha256"] == sha(HERE / f"{case}.stdout")
    assert receipt["stderr_sha256"] == sha(HERE / f"{case}.stderr")
    assert receipt["sampled_peak_combined_rss_bytes"] < 4294967296
    assert receipt["rss_samples"] > 0 and receipt["stop_reason"] is None
    assert receipt["wall_seconds"] < (120 if case == "n41" else 590)
    assert worker["script_sha256"] == sha(HERE / "blocknorm_sage.py")
    assert worker["protocol_sha256"] == sha(HERE / f"protocol_{case}.json")


n41 = load("n41_result.json")
assert [(r["gate"]["gcd_degree"], r["direct_hits"])
        for r in n41["data"]["rows"]] == [(1, [[253, 63]]), (0, [])]
assert n41["data"]["vanisher_degree"] == 281
n131 = load("n131_result.json")
assert [(r["gate"]["norm_degree"], r["gate"]["gcd_degree"],
         r["individual_retained_codes"]) for r in n131["data"]["rows"]] == [
             (64, 1, [3]), (64, 0, [])]
per_code_reference = json.loads(Path(load("protocol_n131.json")["sources"]["n131_reference"]["path"]).read_text())
assert per_code_reference["status"] == "COMPLETE_W33_GCD_AUDIT"
for row in n131["data"]["rows"]:
    refs = sorted((r for r in per_code_reference["rows"] if
                   r["target_index"] == row["target_index"]), key=lambda r: r["p_code"])
    assert [r["p_code"] for r in refs] == list(range(16))
    assert [(degree > 0 or degree == -1) for degree in row["individual_gcd_degrees"]] == [
        not r["reject"] for r in refs]
reference = json.loads(Path(load("protocol_scaling.json")["sources"]["reference"]["path"]).read_text())
assert reference["status"] == "COMPLETE_N131_NATIVE_REFERENCE"
scaling = load("scaling_result.json")
receipt = load("scaling_supervisor.json")
assert scaling["status"] == receipt["status"] == "PASS_N131_BLOCK_NORM_SCALING"
assert receipt["protocol_sha256"] == sha(HERE / "protocol_scaling.json")
assert receipt["supervisor_sha256"] == sha(HERE / "supervise_scaling.py")
assert receipt["result_sha256"] == sha(HERE / "scaling_result.json")
assert receipt["stdout_sha256"] == sha(HERE / "scaling.stdout")
assert receipt["stderr_sha256"] == sha(HERE / "scaling.stderr")
assert receipt["rss_samples"] > 0 and receipt["stop_reason"] is None
assert receipt["sampled_peak_combined_rss_bytes"] < 4294967296
assert receipt["wall_seconds"] < 590
assert scaling["script_sha256"] == sha(HERE / "scaling_sage.py")
assert scaling["protocol_sha256"] == sha(HERE / "protocol_scaling.json")
for row in scaling["rows"]:
    target = row["target_index"]
    refs = sorted((r for r in reference["rows"] if r["target_index"] == target and
                   r["p_code"] < 64), key=lambda r: r["p_code"])
    assert [r["p_code"] for r in refs] == list(range(64))
    assert [(degree > 0) for degree in row["individual_gcd_degrees"]] == [
        not r["reject"] for r in refs]
    for block in row["block_rows"]:
        n = block["size"]
        assert n in (4, 8, 16, 32, 64)
        assert block["norm_degree"] == 4 * n
        assert block["retain"] == any(not r["reject"] for r in refs[:n])
        assert block["retained_first_codes"] == [r["p_code"] for r in refs[:n] if not r["reject"]]
        assert block["block_seconds"] > 0 and block["individual_prefix_seconds"] > 0
print(json.dumps({"status": "PASS_BLOCK_NORM_ARCHIVE", "n41_rows": 2,
                  "n131_rows": 2, "scaling_rows": 10, "preserved_failed_parent_attempts": 2},
                 sort_keys=True))
