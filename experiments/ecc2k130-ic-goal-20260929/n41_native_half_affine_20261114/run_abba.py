"""Run a frozen alternating native half-affine versus per-root rank comparison."""
import hashlib
import json
import platform
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "n41_cubic_product_inverse_20261024"
PROTOCOL = HERE / "protocol.json"
RESULT = HERE / "abba_result.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    p = json.loads(PROTOCOL.read_text())
    assert not RESULT.exists(), "refuse to overwrite frozen run"
    paths = {
        "input_sha256": BASE / "n41_quotient_native_input_20261025.tsv",
        "half_affine_source_sha256": HERE / "native_half_affine.cpp",
        "rank_source_sha256": BASE / "n41_quotient_native_20261025.cpp",
    }
    for label, path in paths.items():
        assert digest(path) == p[label], label
    bins = {}
    builds = []
    for name, source in (("half_affine", paths["half_affine_source_sha256"]),
                         ("rank", paths["rank_source_sha256"])):
        binary = HERE / ("native_" + name)
        cmd = ["c++", "-O3", "-std=c++17", "-Wall", "-Wextra",
               str(source), "-o", str(binary)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        builds.append({"command": cmd, "exit_code": proc.returncode,
                       "stdout": proc.stdout, "stderr": proc.stderr})
        assert proc.returncode == 0, proc.stderr
        bins[name] = binary
    rows = []
    for name in p["order"]:
        cmd = [str(bins[name]), str(paths["input_sha256"])]
        if name == "rank":
            cmd.append("--rank")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        row = json.loads(proc.stdout)
        assert row["families"] == p["expected"]["families"]
        assert row["gate_hits"] == p["expected"]["gate_hits"]
        assert row["hit"] == p["expected"]["source_hit"]
        if name == "rank":
            assert row["queries"] == p["expected"]["rank_queries"]
        else:
            assert row["half_survivors"] == p["expected"]["half_survivors"]
            assert row["retained"] == p["expected"]["retained"]
        rows.append({"name": name, "command": cmd, "exit_code": proc.returncode,
                     "result": row})
    archive = json.loads((BASE / "affine_gate_result.json").read_text())
    for row in rows:
        if row["name"] == "half_affine":
            result = row["result"]
            assert result["half_survivors"] == archive["half_survivors"]
            assert result["retained"] == archive["families_retained"]
            assert result["hit"] == archive["source_product_hits"][0]
            for half in range(2):
                for rank, count in enumerate(result["rank_hist"][half]):
                    assert count == int(archive["half_rank_histograms"][half].get(str(rank), 0))
    out = {"status": "PASS_N41_NATIVE_HALF_AFFINE_ABBA",
           "protocol_sha256": digest(PROTOCOL), "platform": platform.platform(),
           "compiler_version": subprocess.run(["c++", "--version"], capture_output=True,
                                               text=True).stdout.splitlines()[0],
           "builds": builds, "binary_sha256": {name: digest(path) for name, path in bins.items()},
           "rows": rows, "archived_sage_result_sha256": digest(BASE / "affine_gate_result.json")}
    RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": out["status"],
                      "query_s": [(row["name"], row["result"]["query_s"]) for row in rows]}))


if __name__ == "__main__":
    run()
