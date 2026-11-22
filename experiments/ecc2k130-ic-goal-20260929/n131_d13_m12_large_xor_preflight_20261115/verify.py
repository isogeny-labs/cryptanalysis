"""Read-only verification of the frozen N131 large-matrix preflight."""

import gzip
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
RUN = BASE / "large_matrix_R1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    protocol = read(BASE / "protocol.json")
    result = read(RUN / "result.json")
    audit = read(RUN / "independent_terminal_audit.json")
    comparison = read(BASE / "comparison.json")
    attempt = read(BASE / "source_attempt.json")
    formula = BASE / "query.xcnf"
    runtime = BASE / "sage_runtime_info.json"
    assert read(runtime)["status"] == "verified"
    assert protocol["source_sha256"]["formula"] == sha(formula)
    assert protocol["source_sha256"]["source_attempt"] == sha(BASE / "source_attempt.json")
    assert protocol["source_sha256"]["runner"] == sha(BASE / "run.py")
    assert protocol["source_sha256"]["sage_runtime"] == sha(runtime)
    assert protocol["source_sha256"]["solver"] == sha(Path("/opt/homebrew/bin/cryptominisat5"))
    assert attempt["query_details"]["target_formula_sha256"] == sha(formula)
    assert result["source_sha256"]["protocol"] == sha(BASE / "protocol.json")
    assert result["source_sha256"]["stdout"] == sha(RUN / "cryptominisat.stdout.txt")
    assert result["source_sha256"]["stderr"] == sha(RUN / "cryptominisat.stderr.txt")
    assert result["status"] == audit["status"] == "CENSORED_TIME"
    assert audit["source_sha256"]["result"] == sha(RUN / "result.json")
    assert audit["source_sha256"]["auditor"] == sha(BASE / "audit.py")
    assert audit["large_matrix_admitted"] is True
    assert (audit["large_matrix_rows"], audit["large_matrix_columns"]) == (36627, 38097)
    assert result["solver_model_line_count"] == 0
    assert result["combined_peak_rss_bytes"] == 2137423872
    assert 120 <= result["solver_wall_seconds"] < 121
    assert comparison["status"] == "PASS_SAME_FORMULA_SEED_AND_TRACE_COMPARISON"
    assert comparison["source_sha256"]["audit"] == sha(RUN / "independent_terminal_audit.json")
    assert comparison["source_sha256"]["script"] == sha(BASE / "compare.py")
    assert comparison["identical_formula_sha256"] == sha(formula)
    baseline = gzip.decompress((BASE / "baseline_stdout.txt.gz").read_bytes())
    assert hashlib.sha256(baseline).hexdigest() == \
        attempt["query_details"]["attempts"][0]["stdout_sha256"]
    assert "24K" in audit["last_restart_line"]
    print("PASS_N131_LARGE_XOR_PREFLIGHT", audit["status"],
          result["combined_peak_rss_bytes"])


if __name__ == "__main__":
    main()
