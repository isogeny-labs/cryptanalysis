"""Read back frozen inputs, producer receipts, audits, and Lean axioms."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda name: json.loads((D / name).read_text())

protocol = read("protocol.json")
assert sha(D / "run.py") == protocol["runner_sha256"]
assert sha(D / "sage_runtime_info.json") == protocol["runtime_info_sha256"]
assert all(sha(ROOT / path) == digest for path, digest in protocol["sources"].items())
run_protocol = read("run_protocol.json")
assert sha(D / "protocol.json") == run_protocol["protocol_sha256"]
assert sha(D / "run_monitored.py") == run_protocol["monitor_sha256"]
receipt = read("run_receipt.json")
assert receipt["status"] == "PRODUCER_COMPLETED" and receipt["exit_code"] == 0
assert receipt["result_sha256"] == sha(D / "result.json")
assert receipt["stdout_sha256"] == sha(D / "run.stdout")
assert receipt["stderr_sha256"] == sha(D / "run.stderr")
result = read("result.json")
assert result["protocol_sha256"] == sha(D / "protocol.json")
for prefix, source, audited, expected in (
    ("audit", "audit_sage.py", "audit_result.json", "PASS_INDEPENDENT_SAGE_QUADRATIC_TRACE_REPLAY"),
    ("odd_audit", "audit_odd_sage.py", "odd_audit_result.json", "PASS_INDEPENDENT_SAGE_ODD_POWER_RANK_REPLAY"),
    ("certificate_audit", "verify_odd_cert_sage.py", "certificate_audit_result.json", "PASS_INDEPENDENT_SAGE_FOUR_POWER_CERTIFICATE"),
):
    protocol_name = {"audit": "audit_protocol.json", "odd_audit": "odd_audit_protocol.json",
                     "certificate_audit": "certificate_audit_protocol.json"}[prefix]
    p = read(protocol_name)
    assert sha(D / "sage_runtime_info.json") == p["runtime_info_sha256"]
    assert all(sha(path) == digest for path, digest in p["sources"].items())
    record = read(audited)
    assert record["status"] == expected
    assert record["protocol_sha256"] == sha(D / protocol_name)
    assert (D / (prefix + ".stderr")).read_bytes() == b""
odd_protocol = read("odd_protocol.json")
assert odd_protocol["runner_sha256"] == sha(D / "odd_trace.py")
assert all(sha(ROOT / path) == digest for path, digest in odd_protocol["sources"].items())
odd = read("odd_result.json")
assert odd["protocol_sha256"] == sha(D / "odd_protocol.json")
assert odd["status"] == "COMPLETE_ODD_TRACE_DIMENSION_SCREEN"
certificate_protocol = read("certificate_protocol.json")
assert certificate_protocol["runner_sha256"] == sha(D / "recover_odd_certificate.py")
assert all(sha(path) == digest for path, digest in certificate_protocol["sources"].items())
certificate = read("odd_certificate.json")
assert certificate["protocol_sha256"] == sha(D / "certificate_protocol.json")
assert certificate["feature_rank"] == 512
assert read("certificate_audit_result.json")["certificate_sha256"] == sha(D / "odd_certificate.json")
lean = (D / "lean.stdout").read_text()
assert (D / "lean.stderr").read_bytes() == b""
assert "'QuadraticTrace.separator_excludes_zero' depends on axioms: [propext]" in lean
assert "'QuadraticTrace.witnessed_zero_blocks_separator' depends on axioms: [propext]" in lean
for name in ("QuadraticTrace.lean", "run.py", "odd_trace.py", "recover_odd_certificate.py"):
    assert "sorry" not in (D / name).read_text() and "admit" not in (D / name).read_text()
out = {"status": "PASS_TERMINAL_READBACK", "candidate_id": None,
       "quadratic_result_sha256": sha(D / "result.json"),
       "odd_result_sha256": sha(D / "odd_result.json"),
       "certificate_sha256": sha(D / "odd_certificate.json"),
       "independent_audits": 3, "lean_axioms": ["propext"]}
(D / "terminal.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"])
