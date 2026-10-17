"""Freeze the dual-tree circuit inputs before building the public formula."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_paths = (
        "n41_s3_rationality_propagation_20261017/circuit.py",
        "n41_s3_rationality_propagation_20261017/build.py",
        "n41_s3_rationality_propagation_20261017/protocol.json",
        "n41_s3_rationality_propagation_20261017/verification.json",
        "n41_sixpair_shared_target_20261017/join_audit_result.json",
        "n41_w8_fixed_sum_table_20261009/geometry.json",
    )
    hit = json.loads((ROOT / source_paths[4]).read_text())
    protocol = {
        "schema": 1,
        "candidate_id": None,
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "public_raw_point": hit["raw_target"],
        "first_links": [[int(v) for v in link] for link in ((0, 1, 6), (2, 3, 7),
                                                              (4, 5, 8), (6, 7, 9), (9, 8, 10))],
        "second_links": [[int(v) for v in link] for link in ((0, 3, 6), (1, 4, 7),
                                                               (2, 5, 8), (6, 7, 9), (9, 8, 10))],
        "input_law": "six free source code masks and pair outputs on one frozen public target",
        "sources": {path: sha(ROOT / path) for path in source_paths},
        "circuit_sha256": sha(D / "circuit.py"),
        "builder_sha256": sha(D / "build.py"),
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
    }
    (D / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: protocol[key] for key in (
        "public_raw_point", "first_links", "second_links")}, sort_keys=True))


if __name__ == "__main__":
    main()
