"""Freeze the compact source and archived 41-orientation public workload."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = (
        "n41_s3_rationality_propagation_20261017/circuit.py",
        "n41_s3_rationality_propagation_20261017/build.py",
        "n41_s3_rationality_propagation_20261017/protocol.json",
        "n41_s3_rationality_propagation_20261017/verification.json",
        "n41_sixpair_target_orbit_20261016/join_result.json",
        "n41_sixpair_target_orbit_20261016/join_audit.json",
        "n41_sixpair_target_orbit_20261016/orbit_audit.json",
        "n41_w8_fixed_sum_table_20261009/geometry.json",
    )
    orbit_audit = json.loads((ROOT / paths[6]).read_text())
    assert orbit_audit["status"] == "PASS_N41_FROBENIUS_TARGET_ORBIT"
    p = {
        "schema": 1,
        "candidate_id": None,
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "public_raw_point": orbit_audit["public_raw_point"],
        "input_law": "one public subgroup point with a 41-conjugate raw target selector and six free source slots",
        "circuit_sha256": sha(D / "circuit.py"),
        "builder_sha256": sha(D / "build.py"),
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "sources": {name: sha(ROOT / name) for name in paths},
    }
    (D / "protocol.json").write_text(json.dumps(p, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: p[key] for key in ("curve_id", "public_raw_point")}, sort_keys=True))


if __name__ == "__main__":
    main()
