#!/usr/bin/env python3
import hashlib
import json
import pathlib
import subprocess
import sys
import time

baseline = pathlib.Path(sys.argv[1]).resolve()
candidate = pathlib.Path(sys.argv[2]).resolve()
output = pathlib.Path(sys.argv[3]).resolve()
binaries = {"baseline": baseline, "candidate": candidate}
seeds = [0x8A5CD789635D2DFF, 0xD94F3A6C42B81705]
schedule = ["baseline", "candidate", "candidate", "baseline",
            "candidate", "baseline", "baseline", "candidate"]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(arm, summands, queries, seed, target, warmup=False):
    command = [str(binaries[arm]), str(summands), str(queries), str(seed), str(target)]
    started = time.time_ns()
    try:
        completed = subprocess.run(command, text=True, capture_output=True,
                                   timeout=60, check=False)
        stdout = completed.stdout.strip()
        report = json.loads(stdout) if completed.returncode == 0 else None
        return {"arm": arm, "summands": summands, "target_index": target,
                "seed": seed, "queries": queries, "warmup": warmup,
                "command": command, "returncode": completed.returncode,
                "wall_ns": time.time_ns() - started, "stdout": stdout,
                "stderr": completed.stderr, "report": report, "timeout": False}
    except subprocess.TimeoutExpired as error:
        return {"arm": arm, "summands": summands, "target_index": target,
                "seed": seed, "queries": queries, "warmup": warmup,
                "command": command, "returncode": None,
                "wall_ns": time.time_ns() - started,
                "stdout": (error.stdout or ""), "stderr": (error.stderr or ""),
                "report": None, "timeout": True}


rows = []
for arm in ("baseline", "candidate"):
    rows.append(invoke(arm, 3, 64, seeds[0], 0, warmup=True))
for target, seed in enumerate(seeds):
    for summands in (3, 4):
        for order, arm in enumerate(schedule):
            row = invoke(arm, summands, 4096, seed, target)
            row["order"] = order
            rows.append(row)

document = {
    "schema": "m31-pair-root-panel/v1",
    "baseline_commit": "b4e8b162c60c2cd5837d30c51c2d616c12e5d38b",
    "candidate_commit": "569c926eefc79d79a97cc12f6fab15b3ffe82457",
    "binary_sha256": {name: sha256(path) for name, path in binaries.items()},
    "schedule": schedule,
    "rows": rows,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(document, indent=2) + "\n")
print(json.dumps({"output": str(output), "rows": len(rows),
                  "timeouts": sum(row["timeout"] for row in rows),
                  "failures": sum(row["returncode"] not in (0, None) for row in rows)}))
