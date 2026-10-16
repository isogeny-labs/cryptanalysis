"""Bounded parent and immutable-input check for fused native N131 query."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUTS = {
    "source": HERE / "native_unfused.cpp",
    "helpers": HERE / "native_helpers.hpp",
    "binary": HERE / "native_unfused",
    "charts": HERE / "public_charts.txt",
    "preimages": ROOT / "n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json",
    "support": ROOT / "n131_w20_sevenpair_gate_20261010/support_w20.tsv",
    "valid": ROOT / "n131_w20_code_trace_bitset_20261014/valid_bitmap.bin",
    "runtime": HERE / "sage_runtime_info.json",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "unfused_protocol.json").read_text())
    assert protocol["sources"] == {key: sha(path) for key, path in INPUTS.items()} | {
        "runner": sha(HERE / "unfused_run.py")}
    pre = json.loads(INPUTS["preimages"].read_text())
    assert pre["workload_id"] == protocol["workload_id"]
    assert INPUTS["charts"].read_text().splitlines() == [
        str(row["reciprocal_x_z"]) for row in pre["preimages"]]
    command = [str(INPUTS["binary"]), str(INPUTS["charts"]), str(INPUTS["support"]),
               str(INPUTS["valid"]), str(HERE / "unfused_result.json"),
               str(protocol["wall_cap_seconds"]), str(protocol["rss_cap_bytes"])]
    start = time.monotonic_ns()
    with (HERE / "unfused_stdout.log").open("x") as out, \
         (HERE / "unfused_stderr.log").open("x") as err:
        try:
            p = subprocess.run(command, stdout=out, stderr=err,
                               timeout=protocol["wall_cap_seconds"], check=False)
            status = "EXIT_0" if p.returncode == 0 else "EXIT_NONZERO"
            code = p.returncode
        except subprocess.TimeoutExpired:
            status, code = "PARENT_TIME_CAP", None
    receipt = {"status": status, "exit_code": code,
               "wall_ns": time.monotonic_ns() - start,
               "child_ru_maxrss_raw": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
               "protocol_sha256": sha(HERE / "unfused_protocol.json"),
               "stdout_sha256": sha(HERE / "unfused_stdout.log"),
               "stderr_sha256": sha(HERE / "unfused_stderr.log"),
               "result_sha256": sha(HERE / "unfused_result.json")
               if (HERE / "unfused_result.json").exists() else None}
    with (HERE / "unfused_receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2, sort_keys=True)
        out.write("\n")
    print(status, receipt["wall_ns"] / 1e9)


if __name__ == "__main__":
    main()
