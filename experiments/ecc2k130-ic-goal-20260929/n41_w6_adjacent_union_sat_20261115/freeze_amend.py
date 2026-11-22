"""Retain the import failure and freeze the local arithmetic helper."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    old = HERE / "protocol.json"
    protocol = json.loads(old.read_text())
    assert protocol["builder_sha256"] == sha(HERE / "build_v1.py")
    error = (HERE / "build.stderr").read_text()
    assert "ModuleNotFoundError: No module named 'independent_replay'" in error
    fail = {"kind": "n41_union_sat_first_build_attempt",
            "status": "PRODUCER_FAILURE_IMPORT",
            "protocol_sha256": sha(old),
            "builder_sha256": sha(HERE / "build_v1.py"),
            "stderr_sha256": sha(HERE / "build.stderr")}
    (HERE / "build_v1_status.json").write_text(json.dumps(fail, indent=2,
                                                        sort_keys=True) + "\n")
    protocol.update({
        "kind": "n41_w6_adjacent_union_s3_formula_protocol_v2",
        "status": "FROZEN_AMENDED_BEFORE_BUILD",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "amends_protocol_sha256": sha(old),
        "amendment_reason": "The historical circuit_sat import points to a missing main-checkout independent_replay.py; pin an identical local helper snapshot before building.",
        "failed_attempt_status_sha256": sha(HERE / "build_v1_status.json"),
        "builder_sha256": sha(HERE / "build.py"),
        "helper_source_sha256": sha(HERE / "independent_replay.py"),
    })
    path = HERE / "protocol_v2.json"
    assert not path.exists()
    path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
