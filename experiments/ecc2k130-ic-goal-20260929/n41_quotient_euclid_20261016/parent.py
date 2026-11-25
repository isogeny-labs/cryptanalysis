"""Frozen one-worker parent for the N41 quotient Euclid gate."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUTS = {
    "source": HERE / "run.cpp", "ring": HERE / "quotient.hpp",
    "helpers": HERE / "oracle_helpers.hpp", "binary": HERE / "run",
    "tensor": ROOT / "n41_target_chart_symbolic_tensor_20261014/coefficients.bin",
    "codes": ROOT / "n41_triproduct_tensor_20261014/codes.txt",
    "source_roots": ROOT / "n41_native_rootproduct_span_20261014/input.txt",
    "oracle": ROOT / "n41_implicit_span_norm_20261016/oracle_result.json",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / "protocol.json"
    p = json.loads(protocol_path.read_text())
    assert p["sources"] == {k: sha(v) for k, v in INPUTS.items()} | {
        "parent": sha(HERE / "parent.py")}
    command = [str(INPUTS["binary"]), str(INPUTS["tensor"]),
               str(INPUTS["codes"]), str(INPUTS["source_roots"]),
               str(HERE / "result.json")]
    started = time.monotonic_ns()
    peak_rss = 0
    with (HERE / "stdout.log").open("x") as out, (HERE / "stderr.log").open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err)
        process = psutil.Process(child.pid)
        while True:
            try:
                peak_rss = max(peak_rss, process.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            code = child.poll()
            if code is not None:
                status = "EXIT_0" if code == 0 else "EXIT_NONZERO"
                break
            if peak_rss > p["memory_cap_bytes"]:
                child.kill()
                child.wait()
                status, code = "PARENT_RSS_CAP", None
                break
            if time.monotonic_ns() - started > p["wall_cap_seconds"] * 10**9:
                child.kill()
                child.wait()
                status, code = "PARENT_TIME_CAP", None
                break
            time.sleep(0.05)
    result = HERE / "result.json"
    receipt = {"status": status, "exit_code": code,
               "wall_ns": time.monotonic_ns() - started,
               "wall_cap_seconds": p["wall_cap_seconds"],
               "memory_cap_bytes": p["memory_cap_bytes"],
               "rss_poll_seconds": 0.05, "peak_polled_rss_bytes": peak_rss,
               "command": command,
               "child_ru_maxrss_raw": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
               "protocol_sha256": sha(protocol_path),
               "stdout_sha256": sha(HERE / "stdout.log"),
               "stderr_sha256": sha(HERE / "stderr.log"),
               "result_sha256": sha(result) if result.exists() else None}
    with (HERE / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2, sort_keys=True)
        out.write("\n")
    print(status, receipt["wall_ns"] / 1e9)


if __name__ == "__main__":
    main()
