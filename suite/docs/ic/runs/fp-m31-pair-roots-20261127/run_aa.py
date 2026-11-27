#!/usr/bin/env python3
import hashlib
import json
import pathlib
import subprocess
import sys
import time

binary = pathlib.Path(sys.argv[1]).resolve()
output = pathlib.Path(sys.argv[2]).resolve()
seeds = [0x8A5CD789635D2DFF, 0xD94F3A6C42B81705]
schedule = ["candidate-a", "candidate-b", "candidate-b", "candidate-a",
            "candidate-b", "candidate-a", "candidate-a", "candidate-b"]


def invoke(arm, summands, seed, target, order):
    command = [str(binary), str(summands), "4096", str(seed), str(target)]
    started = time.time_ns()
    try:
        completed = subprocess.run(command, text=True, capture_output=True,
                                   timeout=60, check=False)
        stdout = completed.stdout.strip()
        report = json.loads(stdout) if completed.returncode == 0 else None
        return {"arm": arm, "summands": summands, "target_index": target,
                "seed": seed, "queries": 4096, "order": order,
                "command": command, "returncode": completed.returncode,
                "wall_ns": time.time_ns() - started, "stdout": stdout,
                "stderr": completed.stderr, "report": report, "timeout": False}
    except subprocess.TimeoutExpired as error:
        return {"arm": arm, "summands": summands, "target_index": target,
                "seed": seed, "queries": 4096, "order": order,
                "command": command, "returncode": None,
                "wall_ns": time.time_ns() - started,
                "stdout": (error.stdout or ""), "stderr": (error.stderr or ""),
                "report": None, "timeout": True}


rows = []
for target, seed in enumerate(seeds):
    for summands in (3, 4):
        for order, arm in enumerate(schedule):
            rows.append(invoke(arm, summands, seed, target, order))

document = {
    "schema": "m31-pair-root-aa/v1",
    "candidate_commit": "569c926eefc79d79a97cc12f6fab15b3ffe82457",
    "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
    "schedule": schedule,
    "rows": rows,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(document, indent=2) + "\n")
print(json.dumps({"output": str(output), "rows": len(rows),
                  "timeouts": sum(row["timeout"] for row in rows),
                  "failures": sum(row["returncode"] not in (0, None) for row in rows)}))
