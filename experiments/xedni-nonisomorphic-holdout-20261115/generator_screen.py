"""Check every holdout rank-one nonbase candidate with bounded Sage workers."""
import concurrent.futures
import hashlib
import json
import os
import signal
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(row):
    c = row["candidate"]
    p, u = row["field_prime"], row["u"]
    name = f"p{p}-u{u}"
    command = [str(REPO / "sage"), "-python", str(HERE / "generator.py"),
               str(p), str(u), *map(str, c["centered_point"]), str(c["curve_B"])]
    proc = subprocess.Popen(command, cwd=REPO, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=30)
        status = "completed" if proc.returncode == 0 else "worker_failure"
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        status = "timeout"
    stdout = HERE / "generator-cells" / f"{name}.stdout"
    stderr = HERE / "generator-cells" / f"{name}.stderr"
    stdout.write_bytes(out); stderr.write_bytes(err)
    result = {"field_prime": p, "u": u, "status": status, "exit_code": proc.returncode,
              "stdout_path": str(stdout.relative_to(HERE)), "stdout_sha256": sha(stdout),
              "stderr_path": str(stderr.relative_to(HERE)), "stderr_sha256": sha(stderr)}
    if status == "completed":
        try:
            result["generator"] = json.loads(out.decode().strip().splitlines()[-1])
        except Exception as exc:
            result["status"] = "invalid_output"
            result["parse_error"] = str(exc)
    return result

def main():
    screen = json.loads((HERE / "result.json").read_text())
    qualified = [r for r in screen["rows"] if r["u"] > 1 and
                 r.get("candidate", {}).get("rank_status") == "proved" and
                 r["candidate"]["rank"] == 1 and r["candidate"]["torsion_order"] == 1]
    (HERE / "generator-cells").mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(check, qualified))
    print(json.dumps({"schema": "xedni-nonisomorphic-holdout-generators-v1",
                      "screen_sha256": sha(HERE / "result.json"),
                      "source_sha256": sha(Path(__file__)),
                      "worker_sha256": sha(HERE / "generator.py"),
                      "rows": rows}, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
