"""Freeze the complete three-slot quadratic and sampled norm Sage audit."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = (D / "audit_source_sage.py", D / "protocol.json",
             ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json")
    protocol = {"schema": 1, "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
                "sources": {str(path): sha(path) for path in paths}}
    (D / "source_audit_protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    print(sha(D / "source_audit_protocol.json"))


if __name__ == "__main__":
    main()
