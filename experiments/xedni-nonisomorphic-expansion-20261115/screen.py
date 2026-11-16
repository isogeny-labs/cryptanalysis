"""Run all frozen Sage cells with per-cell process-group timeouts."""
import concurrent.futures
import hashlib
import json
import os
import signal
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SAGE = REPO / "sage"
INPUT = HERE.parent / "xedni-nonisomorphic-family-screen-20261115" / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cell(args, cap):
    p, q, m, u = args
    name = f"p{p}-u{u}"
    command = [str(SAGE), "-python", str(HERE / "worker.py"),
               str(p), str(q), str(m), str(u)]
    proc = subprocess.Popen(command, cwd=REPO, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=cap)
        status = "completed" if proc.returncode == 0 else "worker_failure"
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        status = "timeout"
    stdout = HERE / "cells" / f"{name}.stdout"
    stderr = HERE / "cells" / f"{name}.stderr"
    stdout.write_bytes(out)
    stderr.write_bytes(err)
    row = {"field_prime":p,"subgroup_order":q,"multiplier_m":m,"u":u,
           "status":status,"stdout_sha256":sha(stdout),"stderr_sha256":sha(stderr),
           "stdout_path":str(stdout.relative_to(HERE)),"stderr_path":str(stderr.relative_to(HERE)),
           "exit_code":proc.returncode}
    if status == "completed":
        try:
            row["candidate"] = json.loads(out.decode().strip().splitlines()[-1])
            if row["candidate"]["rank_status"] != "proved":
                row["status"] = "rank_unknown"
        except Exception as exc:
            row["status"] = "invalid_output"
            row["parse_error"] = str(exc)
    return row


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert sha(INPUT) == protocol["parent_result_sha256"]
    selected = [r for r in json.loads(INPUT.read_text())["rows"] if r["u"] == 1]
    args = []
    for item in selected:
        p, q, m = item["field_prime"], item["subgroup_order"], item["multiplier_m"]
        for u in protocol["u_values"]: args.append((p,q,m,u))
    assert len(args)==protocol["candidate_count"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=protocol["max_concurrent_sage_workers"]) as pool:
        futures=[pool.submit(run_cell,args0,protocol["per_candidate_cap_seconds"]) for args0 in args]
        rows=[future.result() for future in futures]
    print(json.dumps({"schema":"xedni-nonisomorphic-expansion-result-v1",
                      "protocol_sha256":sha(HERE/"protocol.json"),
                      "source_sha256":sha(Path(__file__)),
                      "worker_sha256":sha(HERE/"worker.py"),
                      "input_sha256":sha(INPUT),"rows":rows,
                      "status_counts":{s:sum(r["status"]==s for r in rows)
                                       for s in sorted({r["status"] for r in rows})}},
                     sort_keys=True,indent=2))


if __name__=="__main__":main()
