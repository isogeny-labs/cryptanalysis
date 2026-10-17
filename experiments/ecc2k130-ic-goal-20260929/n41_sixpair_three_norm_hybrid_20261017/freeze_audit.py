"""Bind the independent Sage control replay to the built public formula."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = {str(path): sha(path) for path in (
        D / "audit_sage.py", D / "build_result.json", D / "public.xcnf",
        ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json",
        ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json")}
    protocol = {"schema": 1, "sources": sources,
                "runtime_info_sha256": sha(D / "sage_runtime_info.json")}
    (D / "audit_protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    print(sha(D / "audit_protocol.json"))


if __name__ == "__main__":
    main()
