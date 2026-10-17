"""Freeze the public-formula readback source and exact output."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = ("audit_formula.py", "circuit.py", "build_result.json",
               "public.xcnf", "protocol.json")
    protocol = {"schema": 1, "version": 2,
                "previous_failure_sha256": sha(D / "formula_audit_v1_failure.json"),
                "sources": {str(D / name): sha(D / name)
                            for name in sources}}
    (D / "formula_audit_protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    print(sha(D / "formula_audit_protocol.json"))


if __name__ == "__main__":
    main()
