"""Run every distinct admitted curve under the frozen per-curve wall cap."""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAGE = "/Volumes/SSD990/cryptanalysis/sage"
curves = json.loads((HERE / "result.json").read_text())["curves"]
rows = []
for curve in curves:
    command = [SAGE, "-python", str(HERE / "rank_curve.py"), curve["A"], curve["B"]]
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=30)
        row = {"A": curve["A"], "B": curve["B"], "status": "complete" if run.returncode == 0 else "failed",
               "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
    except subprocess.TimeoutExpired as error:
        row = {"A": curve["A"], "B": curve["B"], "status": "timeout_30s", "returncode": None,
               "stdout": error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else error.stdout,
               "stderr": error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else error.stderr}
    rows.append(row)
    (HERE / "rank-results.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    print(curve["A"], curve["B"], row["status"], flush=True)
