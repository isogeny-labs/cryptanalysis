"""Bounded checked-Sage parent for an N41 implicit norm trial."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SAGE = ROOT / "sage"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(mode):
    assert mode in ("smoke", "full")
    protocol_path = HERE / (mode + "_protocol.json")
    protocol = json.loads(protocol_path.read_text())
    assert protocol["parent_sha256"] == sha(HERE / "parent.py")
    assert protocol["sage_sha256"] == sha(SAGE)
    command = [str(SAGE), "-python", str(HERE / "run.py"), mode]
    stdout = HERE / (mode + "_stdout.log")
    stderr = HERE / (mode + "_stderr.log")
    started = time.monotonic_ns()
    with stdout.open("x") as out, stderr.open("x") as err:
        try:
            p = subprocess.run(command, stdout=out, stderr=err,
                               timeout=protocol["parent_wall_cap_seconds"], check=False)
            status = "EXIT_0" if p.returncode == 0 else "EXIT_NONZERO"
            code = p.returncode
        except subprocess.TimeoutExpired:
            status, code = "PARENT_TIME_CAP", None
    result_path = HERE / (mode + "_result.json")
    receipt = {"status": status, "exit_code": code, "command": command,
               "wall_ns": time.monotonic_ns() - started,
               "parent_wall_cap_seconds": protocol["parent_wall_cap_seconds"],
               "child_ru_maxrss_raw": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
               "protocol_sha256": sha(protocol_path),
               "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
               "result_sha256": sha(result_path) if result_path.exists() else None}
    with (HERE / (mode + "_receipt.json")).open("x") as out:
        json.dump(receipt, out, indent=2, sort_keys=True)
        out.write("\n")
    print(status, mode, receipt["wall_ns"]/1e9)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    main(sys.argv[1])
