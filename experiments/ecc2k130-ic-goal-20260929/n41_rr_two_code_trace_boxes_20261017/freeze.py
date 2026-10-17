"""Freeze two-code box input and one-worker execution envelope."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = (
        "n41_n131_sixpair_rr_root_span_20261016/run.py",
        "n41_w8_fixed_sum_table_20261009/geometry.json",
        "n41_sixpair_shared_target_20261017/join_audit_result.json",
    )
    hit = json.loads((ROOT / sources[2]).read_text())
    protocol = {"schema": 1, "candidate_id": None,
                "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
                "target": hit["raw_target"],
                "fixed_slots": [2, 3, 4, 5],
                "lexical_box": [[2, 5], [2, 6], [3, 5], [3, 6]],
                "witness_pair": [hit["pair_rows"][0]["masks"][0],
                                 hit["pair_rows"][1]["masks"][0]],
                "runner_sha256": sha(D / "run.py"),
                "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
                "sources": {path: sha(ROOT / path) for path in sources},
                "single_worker": True, "wall_cap_s": 600,
                "rss_cap_bytes": 4 * (1 << 30)}
    (D / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    run_protocol = {"protocol_sha256": sha(D / "protocol.json"),
                    "monitor_sha256": sha(D / "run_monitored.py"),
                    "runtime_info_sha256": sha(D / "sage_runtime_info.json")}
    (D / "run_protocol.json").write_text(json.dumps(run_protocol, sort_keys=True, indent=2) + "\n")
    audit_sources = [D / "audit_sage.py", D / "result.json",
                     ROOT / sources[1], ROOT / sources[2]]
    (D / "audit_protocol.json").write_text(json.dumps({
        "schema": 1,
        "sources": {str(path): sha(path) for path in audit_sources},
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
    }, sort_keys=True, indent=2) + "\n")
    symbolic_sources = (
        "n41_n131_sixpair_rr_root_span_20261016/run.py",
        "n41_n131_rr_quadratic_trace_20261017/run.py",
        "n41_w8_fixed_sum_table_20261009/geometry.json",
        "n41_sixpair_shared_target_20261017/join_audit_result.json",
        "n41_rr_two_code_trace_boxes_20261017/run.py",
        "n41_rr_two_code_trace_boxes_20261017/result.json",
    )
    (D / "symbolic_protocol.json").write_text(json.dumps({
        "schema": 1, "candidate_id": None,
        "runner_sha256": sha(D / "symbolic_cube.py"),
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "sources": {path: sha(ROOT / path) for path in symbolic_sources},
    }, sort_keys=True, indent=2) + "\n")
    certificate_sources = (
        "n41_n131_rr_quadratic_trace_20261017/run.py",
        "n41_n131_sixpair_rr_root_span_20261016/run.py",
        "n41_rr_two_code_trace_boxes_20261017/result.json",
        "n41_rr_two_code_trace_boxes_20261017/audit_result.json",
    )
    (D / "certificate_protocol.json").write_text(json.dumps({
        "schema": 1, "candidate_id": None,
        "runner_sha256": sha(D / "recover_certificate.py"),
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "sources": {path: sha(ROOT / path) for path in certificate_sources},
    }, sort_keys=True, indent=2) + "\n")
    certificate_audit_sources = [D / "audit_certificate_sage.py", D / "certificate.json",
                                 D / "result.json", ROOT / sources[1], ROOT / sources[2]]
    (D / "certificate_audit_protocol.json").write_text(json.dumps({
        "schema": 1,
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "sources": {str(path): sha(path) for path in certificate_audit_sources},
    }, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"protocol_sha256": run_protocol["protocol_sha256"],
                      "witness_pair": protocol["witness_pair"]}))


if __name__ == "__main__":
    main()
