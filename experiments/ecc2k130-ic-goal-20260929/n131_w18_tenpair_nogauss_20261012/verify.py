"""Read-only verification of the archived two-arm solver gate."""

import gzip
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    prepared = json.loads((HERE / "formula_prepare.json").read_text())
    audit = json.loads((HERE / "audit_result.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_MATCHED_SOLVER_ARMS"
    assert audit["status"] == "PASS_MATCHED_TENPAIR_MATRIX_POLICY_AUDIT"
    assert prepared["sha256"] == protocol["formula_sha256"]
    assert audit["source_formula_sha256"] == protocol["formula_sha256"]
    assert protocol["source_sha256"]["runner"] == sha(HERE / "run.py")
    assert protocol["source_sha256"]["source_formula_gzip"] == sha(
        SOURCE / "control.xcnf.gz")
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as stream:
        digest = hashlib.sha256()
        size = 0
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
            size += len(block)
    assert digest.hexdigest() == protocol["formula_sha256"]
    assert size == protocol["formula_bytes"]
    names = {"auditor": "audit.py", "protocol": "protocol.json",
             "prepared": "formula_prepare.json",
             "default_receipt": "default_result.json",
             "nogauss_receipt": "nogauss_result.json",
             "default_stdout": "default.stdout.txt",
             "nogauss_stdout": "nogauss.stdout.txt"}
    for name, digest in audit["sha256"].items():
        assert digest == sha(HERE / names[name]), name
    for arm, expected_matrices in (("default", 5), ("nogauss", 0)):
        receipt = json.loads((HERE / f"{arm}_result.json").read_text())
        output = (HERE / f"{arm}.stdout.txt").read_text(errors="replace")
        counts = [int(match.group(1)) for line in output.splitlines()
                  if (match := re.search(r"\[matrix\] Using (\d+) matrices", line))]
        assert counts == [expected_matrices] * 6
        assert audit["arms"][arm]["matrix_counts_at_six_initializations"] == counts
        assert receipt["status"] == audit["arms"][arm]["status"] == "CENSORED_TIME"
        assert receipt["actual_restart_rows"] == sum(
            line.startswith("c rst") for line in output.splitlines())
        assert receipt["stdout_sha256"] == sha(HERE / f"{arm}.stdout.txt")
        assert receipt["stderr_sha256"] == sha(HERE / f"{arm}.stderr.txt")
        assert not (HERE / f"{arm}.stderr.txt").read_bytes()
    print("PASS_MATCHED_TENPAIR_MATRIX_POLICY_RECEIPTS", flush=True)


if __name__ == "__main__":
    main()
