"""Run the frozen same-target native rho reference across seeds 1..16."""

import hashlib
import json
import platform
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert len(sys.argv) == 2, "pass the built ca binary path"
    binary = Path(sys.argv[1]).resolve()
    assert binary.is_file()
    field = GF(10007)
    curve = EllipticCurve(field, [-3, 7])
    generator = curve(field(4634), field(6322))
    target = curve(field(9780), field(4658))
    assert int(curve.order()) == 10193 and generator.order() == 10193
    assert 7001 * generator == target

    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    commands = []
    for seed in range(1, 17):
        argv = [
            str(binary), "solve", "--alg", "rho", "--group", "ec",
            "--p", "10007", "--a", "10004", "--b", "7",
            "--order", "10193", "--g", "4634,6322", "--h", "9780,4658",
            "--threads", "1", "--seed", str(seed), "--max-ops", "1000000",
        ]
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        started = time.perf_counter()
        proc = subprocess.run(argv, capture_output=True, check=False)
        wall = time.perf_counter() - started
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
        stdout, stderr = proc.stdout.decode(), proc.stderr.decode()
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError:
            result = None
        verified = (
            proc.returncode == 0 and result is not None
            and result.get("status") == "ok"
            and isinstance(result.get("x"), int)
            and result["x"] * generator == target
            and result["x"] == 7001
        )
        commands.append({
            "seed": seed,
            "argv": argv,
            "exit_code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "wall_seconds": wall,
            "cpu_seconds": cpu,
            "result": result,
            "verified": verified,
        })

    successful = [row for row in commands if row["verified"]]
    ops = [row["result"]["ops"] for row in successful]
    report = {
        "binary_path": str(binary),
        "binary_sha256": sha(binary.read_bytes()),
        "source_commit": source_commit,
        "host": platform.platform(),
        "machine": platform.machine(),
        "curve_p_a_b_order": [10007, 10004, 7, 10193],
        "generator_xy": [4634, 6322],
        "target_xy": [9780, 4658],
        "target_scalar_verification_only": 7001,
        "seeds": list(range(1, 17)),
        "runs": commands,
        "summary": {
            "attempts": len(commands),
            "verified": len(successful),
            "failed_or_censored_seeds": [row["seed"] for row in commands if not row["verified"]],
            "ops_min": min(ops) if ops else None,
            "ops_median": statistics.median(ops) if ops else None,
            "ops_max": max(ops) if ops else None,
            "total_wall_seconds": sum(row["wall_seconds"] for row in commands),
            "total_cpu_seconds": sum(row["cpu_seconds"] for row in commands),
        },
    }
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
