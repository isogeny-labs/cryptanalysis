"""Freeze the two-root signed-code panels before the trace screen."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = (
        "n41_n131_sixpair_rr_root_span_20261016/run.py",
        "n41_w8_fixed_sum_table_20261009/geometry.json",
        "n41_sixpair_shared_target_20261017/join_audit_result.json",
        "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json",
        "n41_n131_rr_code_family_span_20261017/audit_result_n131.json",
    )
    protocol = {
        "schema": 1,
        "candidate_id": None,
        "question": "Shared quadratic trace separator for complete signed source-code families",
        "runner_sha256": sha(D / "run.py"),
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "sources": {path: sha(ROOT / path) for path in sources},
        "single_worker": True,
        "wall_cap_s": 600,
        "rss_cap_bytes": 4 * (1 << 30),
    }
    (D / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    run_protocol = {
        "protocol_sha256": sha(D / "protocol.json"),
        "monitor_sha256": sha(D / "run_monitored.py"),
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
    }
    (D / "run_protocol.json").write_text(json.dumps(run_protocol, sort_keys=True, indent=2) + "\n")
    audit_sources = {str(D / "audit_sage.py"): sha(D / "audit_sage.py"),
                     str(D / "result.json"): sha(D / "result.json")}
    audit_sources.update({str(ROOT / path): sha(ROOT / path) for path in sources})
    (D / "audit_protocol.json").write_text(json.dumps({
        "schema": 1, "sources": audit_sources, "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "wall_cap_s": 600, "rss_cap_bytes": 4 * (1 << 30)}, sort_keys=True, indent=2) + "\n")
    odd_sources = {path: sha(ROOT / path) for path in (
        "n41_n131_sixpair_rr_root_span_20261016/run.py",
        "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json",
        "n41_n131_rr_code_family_span_20261017/audit_result_n131.json")}
    (D / "odd_protocol.json").write_text(json.dumps({
        "schema": 1, "candidate_id": None, "runner_sha256": sha(D / "odd_trace.py"),
        "sources": odd_sources, "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "one_worker": True, "wall_cap_s": 600, "rss_cap_bytes": 4 * (1 << 30)
    }, sort_keys=True, indent=2) + "\n")
    (D / "odd_audit_protocol.json").write_text(json.dumps({
        "schema": 1, "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "sources": {str(path): sha(path) for path in (
            D / "audit_odd_sage.py", D / "odd_result.json",
            ROOT / "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json")},
    }, sort_keys=True, indent=2) + "\n")
    (D / "certificate_protocol.json").write_text(json.dumps({
        "schema": 1, "candidate_id": None,
        "runner_sha256": sha(D / "recover_odd_certificate.py"),
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "sources": {str(path): sha(path) for path in (
            D / "run.py", D / "odd_result.json", D / "odd_audit_result.json",
            ROOT / "n41_n131_sixpair_rr_root_span_20261016/run.py",
            ROOT / "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json")},
    }, sort_keys=True, indent=2) + "\n")
    (D / "certificate_audit_protocol.json").write_text(json.dumps({
        "schema": 1, "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "sources": {str(path): sha(path) for path in (
            D / "verify_odd_cert_sage.py", D / "odd_certificate.json",
            ROOT / "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json")},
    }, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"protocol_sha256": run_protocol["protocol_sha256"],
                      "sources": len(sources)}, sort_keys=True))


if __name__ == "__main__":
    main()
