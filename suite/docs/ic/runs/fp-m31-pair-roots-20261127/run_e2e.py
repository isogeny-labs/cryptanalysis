#!/usr/bin/env python3
import hashlib
import json
import pathlib
import subprocess
import sys
import time

baseline = pathlib.Path(sys.argv[1]).resolve()
candidate = pathlib.Path(sys.argv[2]).resolve()
input_path = pathlib.Path(sys.argv[3]).resolve()
output = pathlib.Path(sys.argv[4]).resolve()
p = 2147483647
generator = (1, 814455902)
target = (2144058214, 807222724)


def add(left, right):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if left == right:
        slope = (3 * x1 * x1 + 2) * pow(2 * y1, p - 2, p) % p
    else:
        slope = (y2 - y1) * pow((x2 - x1) % p, p - 2, p) % p
    x3 = (slope * slope - x1 - x2) % p
    return x3, (slope * (x1 - x3) - y1) % p


def mul(point, scalar):
    result = None
    while scalar:
        if scalar & 1:
            result = add(result, point)
        point = add(point, point)
        scalar >>= 1
    return result


def run(arm, binary):
    command = [str(binary), "auxiliary", "--input", str(input_path),
               "--torus-depth", "7", "--without-auxiliary", "--summands", "4",
               "--seed", "9961743651143974399", "--walk-lanes", "64",
               "--max-queries", "100000", "--max-relations", "512",
               "--max-proof-nodes", "4194304", "--profile-phases"]
    started = time.time_ns()
    try:
        completed = subprocess.run(command, text=True, capture_output=True,
                                   timeout=180, check=False)
        stdout = completed.stdout.strip()
        # Older ca-ic binaries returned 1 even after emitting a valid solved
        # report.  Parse the report independently of the process status so a
        # frozen baseline remains replayable; retain returncode in the row.
        try:
            report = json.loads(stdout)
        except json.JSONDecodeError:
            report = None
        scalar = report.get("certificate", {}).get("scalar") if report else None
        independent_replay = scalar is not None and mul(generator, scalar) == target
        return {"arm": arm, "command": command, "returncode": completed.returncode,
                "wall_ns": time.time_ns() - started, "timeout": False,
                "stdout": stdout, "stderr": completed.stderr, "report": report,
                "independent_python_scalar_replay": independent_replay}
    except subprocess.TimeoutExpired as error:
        return {"arm": arm, "command": command, "returncode": None,
                "wall_ns": time.time_ns() - started, "timeout": True,
                "stdout": error.stdout or "", "stderr": error.stderr or "",
                "report": None, "independent_python_scalar_replay": False}


rows = [run("candidate", candidate), run("baseline", baseline)]
document = {
    "schema": "m31-pair-root-e2e/v1",
    "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
    "binary_sha256": {
        "baseline": hashlib.sha256(baseline.read_bytes()).hexdigest(),
        "candidate": hashlib.sha256(candidate.read_bytes()).hexdigest(),
    },
    "rows": rows,
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(document, indent=2) + "\n")
print(json.dumps({"output": str(output),
                  "statuses": [row["report"].get("status") if row["report"] else None
                               for row in rows],
                  "replays": [row["independent_python_scalar_replay"] for row in rows],
                  "timeouts": [row["timeout"] for row in rows]}))
