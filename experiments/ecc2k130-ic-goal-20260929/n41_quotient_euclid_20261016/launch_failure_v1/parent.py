"""Frozen one-worker parent for the N41 quotient Euclid gate."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

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


def cap_memory():
    limit = 4 * 1024**3
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


def main():
    protocol_path = HERE / "protocol.json"
    p = json.loads(protocol_path.read_text())
    assert p["sources"] == {k: sha(v) for k, v in INPUTS.items()} | {
        "parent": sha(HERE / "parent.py")}
    command = [str(INPUTS["binary"]), str(INPUTS["tensor"]),
               str(INPUTS["codes"]), str(INPUTS["source_roots"]),
               str(HERE / "result.json")]
    started = time.monotonic_ns()
    with (HERE / "stdout.log").open("x") as out, (HERE / "stderr.log").open("x") as err:
        try:
            child = subprocess.run(command, stdout=out, stderr=err,
                                   timeout=p["wall_cap_seconds"], check=False,
                                   preexec_fn=cap_memory)
            status = "EXIT_0" if child.returncode == 0 else "EXIT_NONZERO"
            code = child.returncode
        except subprocess.TimeoutExpired:
            status, code = "PARENT_TIME_CAP", None
    result = HERE / "result.json"
    receipt = {"status": status, "exit_code": code,
               "wall_ns": time.monotonic_ns() - started,
               "wall_cap_seconds": p["wall_cap_seconds"],
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
