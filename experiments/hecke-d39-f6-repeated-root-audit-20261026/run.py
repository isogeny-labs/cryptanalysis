"""Run the bounded checked-Sage scan into a unique, retained attempt directory."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

HERE = Path(__file__).resolve().parent
SAGE = os.environ.get("HECKE_SAGE", "/Volumes/SSD990/cryptanalysis/sage")
CAP_SECONDS = 120


def text(value):
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
attempt = HERE / "runs" / f"{stamp}-{uuid4().hex[:8]}"
attempt.mkdir(parents=True, exist_ok=False)

runtime = subprocess.run([SAGE, "--runtime-info"], capture_output=True, text=True)
(attempt / "runtime-info.json").write_text(runtime.stdout)
(attempt / "runtime-info.stderr").write_text(runtime.stderr)
if runtime.returncode:
    receipt = {
        "attempt": attempt.name,
        "runtime_exit_code": runtime.returncode,
        "exit_code": runtime.returncode,
        "timeout": False,
        "cap_seconds": CAP_SECONDS,
        "wall_seconds": 0.0,
    }
    (attempt / "launch.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    raise SystemExit(runtime.returncode)

output = attempt / "scan.json"
command = [SAGE, "-python", str(HERE / "scan.py"), "--output", str(output)]
start = time.monotonic()
try:
    result = subprocess.run(command, cwd=HERE, capture_output=True, text=True,
                            timeout=CAP_SECONDS)
    exit_code, timed_out = result.returncode, False
    stdout, stderr = result.stdout, result.stderr
except subprocess.TimeoutExpired as exc:
    exit_code, timed_out = None, True
    stdout, stderr = text(exc.stdout), text(exc.stderr)
(attempt / "scan.stdout").write_text(stdout)
(attempt / "scan.stderr").write_text(stderr)
receipt = {
    "attempt": attempt.name,
    "command": command,
    "runtime_exit_code": runtime.returncode,
    "exit_code": exit_code,
    "timeout": timed_out,
    "cap_seconds": CAP_SECONDS,
    "wall_seconds": time.monotonic() - start,
}
(attempt / "launch.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
if timed_out:
    raise SystemExit(124)
if exit_code:
    raise SystemExit(exit_code)
