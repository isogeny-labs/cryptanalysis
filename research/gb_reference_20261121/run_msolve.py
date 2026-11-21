#!/usr/bin/env python3
"""Run msolve on exported systems, under the lead-testing watchdog.

For every DIR/<id>.ms: `msolve -g 2` (reduced Gröbner basis, grevlex, the
same order `f4_fp` uses) in its own process group, killed above the memory
ceiling or the wall budget (`tools/lead_sweep.py watched_run`, the trunk's
kill-on-OOM watchdog).  The output basis is parsed and the planted solution
(`<id>.sol.json`), if any, is evaluated on every element: a basis element
that does not vanish there makes the row `planted_ok: false`.  An
inconsistent system (basis [1]) is recorded as such.

msolve's verbose log (-v 2) is kept per system; the widest F4 matrix it
reports is extracted as `max_cols` where the log has it.

Usage: run_msolve.py DIR OUT.jsonl [--threads 1] [--mem-gib 12] [--wall 600]
        [--trunk /home/user/workspace]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

TERM = re.compile(r"([+-]?)\s*(\d*)\s*\*?\s*((?:x\d+(?:\^\d+)?\*?)*)")


def eval_poly(s: str, val: dict[str, int], p: int) -> int:
    """Evaluate a polynomial string like '3*x0^2*x1-5*x2+7' mod p."""
    s = s.replace(" ", "")
    if s and s[0] not in "+-":
        s = "+" + s
    total = 0
    for sign, body in re.findall(r"([+-])([^+-]+)", s):
        c = 1
        for f in body.split("*"):
            if re.fullmatch(r"\d+", f):
                c = c * int(f) % p
            else:
                v, _, e = f.partition("^")
                c = c * pow(val[v], int(e) if e else 1, p) % p
        total = (total + (c if sign == "+" else -c)) % p
    return total


def parse_basis(text: str) -> list[str]:
    body = "\n".join(ln for ln in text.splitlines() if not ln.startswith("#")).strip()
    body = body[: body.rfind("]") + 1] if "]" in body else body
    body = body.strip().lstrip("[").rstrip("]").rstrip(":").rstrip("]")
    return [t.strip() for t in body.replace("\n", "").split(",") if t.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("out")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--mem-gib", type=float, default=12)
    ap.add_argument("--wall", type=float, default=600)
    ap.add_argument("--trunk", default="/home/user/workspace")
    ap.add_argument("--only", default="", help="substring filter on ids")
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.trunk) / "tools"))
    from lead_sweep import watched_run  # noqa: E402

    d = Path(a.dir)
    logs = d / "msolve-logs"
    logs.mkdir(exist_ok=True)
    version = subprocess.run(["dpkg-query", "-W", "-f=${Version}", "msolve"],
                             capture_output=True, text=True).stdout.strip() or "unknown"
    with open(a.out, "a") as out:
        for ms in sorted(d.glob("*.ms")):
            if a.only and a.only not in ms.name:
                continue
            sid = ms.name[: -len(".ms")]
            gb = logs / f"{sid}.gb"
            log = logs / f"{sid}.log"
            cmd = ["msolve", "-f", str(ms), "-o", str(gb), "-g", "2",
                   "-t", str(a.threads), "-v", "2"]
            st = watched_run(cmd, log, a.mem_gib, a.wall)
            row = {"id": sid, "engine": "msolve", "msolve_version": version,
                   "threads": a.threads, "ms_sha256": hashlib.sha256(ms.read_bytes()).hexdigest(),
                   "status": st["status"], "wall_s": st["wall_seconds"],
                   "peak_rss_gib": st["peak_rss_gib"], "exit_code": st.get("exit_code")}
            logtxt = log.read_text(errors="replace") if log.exists() else ""
            mm = re.search(r"max\. matrix data\s+(\d+)\s*x\s*(\d+)", logtxt)
            row["max_rows"], row["max_cols"] = (int(mm.group(1)), int(mm.group(2))) if mm else (None, None)
            for key, pat in (("zero_reductions", r"#zero reductions\s+(\d+)"),
                             ("rows_reduced", r"#rows reduced\s+(\d+)"),
                             ("msolve_elapsed_s", r"overall\(elapsed\)\s+([\d.]+)")):
                mk = re.search(pat, logtxt)
                row[key] = float(mk.group(1)) if mk else None
            if st["status"] == "ok" and gb.exists():
                basis = parse_basis(gb.read_text())
                row["basis_len"] = len(basis)
                row["inconsistent"] = basis == ["1"]
                side = d / f"{sid}.sol.json"
                sol = json.loads(side.read_text()).get("solution") if side.exists() else None
                if sol is not None:
                    p = int(ms.read_text().splitlines()[1])
                    val = {f"x{i}": v for i, v in enumerate(sol)}
                    row["planted_ok"] = (not row["inconsistent"]) and all(
                        eval_poly(f, val, p) == 0 for f in basis)
                else:
                    row["planted_ok"] = None
            out.write(json.dumps(row) + "\n")
            out.flush()
            print(json.dumps(row), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
