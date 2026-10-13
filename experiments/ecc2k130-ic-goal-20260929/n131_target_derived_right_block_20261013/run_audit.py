#!/usr/bin/env python3
"""Bounded checked-Sage replay of the target-derived native hit."""

import json
import time
from pathlib import Path

from run_pipeline import HERE, SAGE, run_one, save, sha


def main():
    protocol_path = HERE / "audit_protocol.json"
    protocol = json.loads(protocol_path.read_text())
    assert protocol["status"] == "FROZEN"
    for path, digest in protocol["sources"].items():
        assert sha(Path(path)) == digest, path
    output_path = HERE / "audit_run_status.json"
    assert not output_path.exists() and not (HERE / "audit_result.json").exists()
    deadline = time.monotonic_ns()+protocol["wall_cap_seconds"]*1_000_000_000
    result = run_one([str(SAGE), "-python", str(HERE / "audit_sage.py")],
                     HERE / "audit", deadline, protocol["rss_cap_bytes"])
    result["status"] = ("EXIT_0" if result["exit_code"] == 0 and
                        result["stop_reason"] is None and
                        (HERE / "audit_result.json").exists()
                        else "CENSORED_OR_FAILED")
    result["audit_result_sha256"] = (sha(HERE / "audit_result.json")
                                     if (HERE / "audit_result.json").exists() else None)
    result["audit_protocol_sha256"] = sha(protocol_path)
    save(output_path, result)
    print(result["status"], result["wall_ns"], flush=True)


if __name__ == "__main__":
    main()
