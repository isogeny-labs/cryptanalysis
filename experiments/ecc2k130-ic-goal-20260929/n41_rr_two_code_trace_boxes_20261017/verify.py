"""Read back all source bindings, measured receipts, and independent audits."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda name: json.loads((D / name).read_text())

protocol = read("protocol.json")
assert protocol["runner_sha256"] == sha(D / "run.py")
assert protocol["runtime_info_sha256"] == sha(D / "sage_runtime_info.json")
assert all(sha(ROOT / path) == digest for path, digest in protocol["sources"].items())
run_protocol = read("run_protocol.json")
assert run_protocol["protocol_sha256"] == sha(D / "protocol.json")
assert run_protocol["monitor_sha256"] == sha(D / "run_monitored.py")
receipt = read("run_receipt.json")
assert receipt["status"] == "PRODUCER_COMPLETED" and receipt["stop_reason"] is None
assert receipt["exit_code"] == 0 and receipt["result_sha256"] == sha(D / "result.json")
assert receipt["stdout_sha256"] == sha(D / "run.stdout")
assert receipt["stderr_sha256"] == sha(D / "run.stderr")
result = read("result.json")
assert result["protocol_sha256"] == sha(D / "protocol.json")
assert result["candidate_id"] is None and result["free_slot_count"] == 2
lexical, witness = result["boxes"]
assert lexical["zero_count"] == 0 and lexical["valid_charts"] == 16
assert witness["zero_count"] == 1 and witness["valid_charts"] == 4
assert lexical["trace"]["first_certificate_power_count"] == 25
assert lexical["trace"]["ranks"][23]["augmented_rank"] == 985
assert lexical["trace"]["ranks"][24]["feature_rank"] == 1024
for protocol_name, runner, result_name, status in (
    ("audit_protocol.json", "audit_sage.py", "audit_result.json", "PASS_INDEPENDENT_SAGE_TWO_CODE_BOX_REPLAY"),
    ("symbolic_protocol.json", "symbolic_cube.py", "symbolic_result.json", "COMPLETE_SYMBOLIC_CUBE_COST_SCREEN"),
    ("certificate_protocol.json", "recover_certificate.py", "certificate.json", "PASS_EXPLICIT_N41_25_POWER_CERTIFICATE"),
    ("certificate_audit_protocol.json", "audit_certificate_sage.py", "certificate_audit_result.json", "PASS_INDEPENDENT_SAGE_N41_25_POWER_CERTIFICATE"),
):
    p = read(protocol_name)
    assert p["runtime_info_sha256"] == sha(D / "sage_runtime_info.json")
    assert all(sha(Path(path) if Path(path).is_absolute() else ROOT / path) == digest
               for path, digest in p["sources"].items())
    if "runner_sha256" in p:
        assert p["runner_sha256"] == sha(D / runner)
    r = read(result_name)
    assert r["status"] == status and r["protocol_sha256"] == sha(D / protocol_name)
assert read("audit_result.json")["producer_sha256"] == sha(D / "result.json")
assert read("certificate_audit_result.json")["certificate_sha256"] == sha(D / "certificate.json")
assert read("symbolic_result.json")["direct_sign_ns"] == lexical["direct_sign_ns"]
for name in ("run", "audit", "symbolic", "certificate", "certificate_audit"):
    assert (D / (name + ".stderr")).read_bytes() == b""
out = {"status": "PASS_TWO_CODE_TRACE_BOX_TERMINAL_READBACK",
       "candidate_id": None, "result_sha256": sha(D / "result.json"),
       "audit_sha256": sha(D / "audit_result.json"),
       "certificate_sha256": sha(D / "certificate.json")}
(D / "terminal.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"])
