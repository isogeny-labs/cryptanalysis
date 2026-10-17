"""Freeze the six-slot public query before formula construction."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = (
        "n41_s3_direct_orbit_20261017/circuit.py",
        "n41_s3_rationality_propagation_20261017/circuit.py",
        "n41_sixpair_shared_target_20261017/circuit.py",
        "n41_three_code_nested_norm_20261015/three_norm.py",
        "n41_three_code_nested_norm_20261015/terminal_verify_v2.json",
        "n41_w8_fixed_sum_table_20261009/geometry.json",
        "n41_sixpair_shared_target_20261017/join_audit_result.json",
        "n131_w20_selector_elimination_v2_20261013/selector.py",
        "n41_basis_aware_quartic_20261011/replay.py",
    )
    hit = json.loads((ROOT / sources[6]).read_text())
    protocol = {"schema": 1, "version": 2, "candidate_id": None,
                "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
                "public_raw_point": hit["raw_target"],
                "input_law": "one public raw point, all six source codes free, left three roots eliminated by a nested norm",
                "circuit_sha256": sha(D / "circuit.py"),
                "builder_sha256": sha(D / "build.py"),
                "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
                "sources": {path: sha(ROOT / path) for path in sources},
                "previous_failure_sha256": sha(D / "build_v1_failure.json"),
                "single_worker": True, "parent_wall_cap_s": 600,
                "rss_cap_bytes": 4 * (1 << 30)}
    (D / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"protocol_sha256": sha(D / "protocol.json"),
                      "public_raw_point": hit["raw_target"]}))


if __name__ == "__main__":
    main()
