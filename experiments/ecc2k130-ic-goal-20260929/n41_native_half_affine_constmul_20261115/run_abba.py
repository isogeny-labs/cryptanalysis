"""Compare a frozen constant-multiply affine gate with both prior kernels."""

import hashlib
import json
import platform
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
BASE = EXP / "n41_cubic_product_inverse_20261024"
PREV = EXP / "n41_native_half_affine_20261114"
PROTOCOL = HERE / "protocol.json"
RESULT = HERE / "abba_result.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads(PROTOCOL.read_text())
    assert not RESULT.exists(), "frozen result already exists"
    paths = {
        "input": BASE / "n41_quotient_native_input_20261025.tsv",
        "constmul": HERE / "native_constmul.cpp",
        "prior_affine": PREV / "native_half_affine.cpp",
        "direct_rank": BASE / "n41_quotient_native_20261025.cpp",
        "sage_audit": BASE / "affine_gate_result.json",
        "runner": Path(__file__),
    }
    for key, path in paths.items():
        assert digest(path) == p["sha256"][key], key
    bins, builds = {}, {}
    for name in ("constmul", "prior_affine", "direct_rank"):
        binary = HERE / ("native_" + name)
        command = ["c++", "-O3", "-std=c++17", "-Wall", "-Wextra",
                   str(paths[name]), "-o", str(binary)]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        builds[name] = {"command": command, "exit_code": proc.returncode,
                        "stdout": proc.stdout, "stderr": proc.stderr}
        assert proc.returncode == 0, proc.stderr
        bins[name] = binary
    sage_audit = json.loads(paths["sage_audit"].read_text())
    rows = []
    for name in p["order"]:
        command = [str(bins[name]), str(paths["input"])]
        if name == "direct_rank":
            command.append("--rank")
        proc = subprocess.run(command, capture_output=True, text=True,
                              check=False, timeout=30)
        assert proc.returncode == 0, proc.stderr
        result = json.loads(proc.stdout)
        assert result["families"] == 248640
        assert result["gate_hits"] == 1
        assert result["hit"] == [0, 24, 37, 2, 10]
        if name == "direct_rank":
            assert result["queries"] == 1989120
        else:
            assert result["half_survivors"] == [258, 237]
            assert result["retained"] == 495
            assert result["source_checks"] == 3960
            assert result["half_survivors"] == sage_audit["half_survivors"]
            assert result["retained"] == sage_audit["families_retained"]
            for half in range(2):
                for rank, count in enumerate(result["rank_hist"][half]):
                    assert count == int(sage_audit["half_rank_histograms"][half].get(str(rank), 0))
        rows.append({"name": name, "command": command,
                     "binary_sha256": digest(bins[name]), "result": result,
                     "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
                     "stderr": proc.stderr})
    out = {"status": "PASS_FROZEN_N41_CONSTMUL_ABBA",
           "protocol_sha256": digest(PROTOCOL),
           "platform": platform.platform(),
           "compiler_version": subprocess.run(["c++", "--version"],
                                              capture_output=True, text=True).stdout.splitlines()[0],
           "builds": builds, "rows": rows,
           "claim_boundary": "Exact same-input family census and ordinary-host component timings; no complete IC timing."}
    RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": out["status"],
                      "query_s": [(row["name"], row["result"]["query_s"])
                                  for row in rows]}, sort_keys=True))


if __name__ == "__main__":
    main()
