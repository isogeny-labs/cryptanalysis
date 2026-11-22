#!/usr/bin/env python3
"""Derive the direct-Semaev presentation of an exported PKM tower system.

`pkm_tower_pilot --export DIR` writes the chain presentation for m >= 3:

    S3(x_1, x_2, u_0), S3(u_0, x_3, u_1), ..., S3(u_{m-3}, x_m, x_R)

followed by the tower equations, over n = m*t + (m-2) variables, the u_k
being x{m*t + k}.  Eliminating u_0, ..., u_{m-3} by successive resultants
gives S_{m+1}(x_1, ..., x_m, x_R) in the same variables, so the direct system
is {S_{m+1}} plus the same tower equations, over n = m*t variables.  The
planted solution restricted to the first m*t coordinates is still a zero
(checked here by evaluation, in Singular, before anything is written).

Usage:  direct_semaev.py SRC.ms OUT_DIR [--timeout S]

Writes OUT_DIR/<id>-direct.ms and <id>-direct.sol.json, and prints one JSON
line (sizes, Singular seconds, sha256).  A Singular failure or timeout is
reported as such and writes nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def read_ms(path: Path):
    lines = path.read_text().splitlines()
    variables = lines[0].split(",")
    p = int(lines[1])
    polys = [ln.rstrip(",") for ln in lines[2:] if ln.strip()]
    return variables, p, polys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out_dir")
    ap.add_argument("--timeout", type=float, default=3600)
    a = ap.parse_args()
    src = Path(a.src)
    m_t = re.search(r"-m(\d+)-[a-z]+-t(\d+)-", src.name)
    if not m_t:
        print(json.dumps({"src": src.name, "status": "skip", "why": "no m/t in name"}))
        return 0
    m, t = int(m_t.group(1)), int(m_t.group(2))
    if m < 3:
        print(json.dumps({"src": src.name, "status": "skip", "why": "m = 2: direct == chain"}))
        return 0
    variables, p, polys = read_ms(src)
    n = len(variables)
    assert n == m * t + (m - 2), (n, m, t)
    chain, towers = polys[: m - 1], polys[m - 1 :]
    us = [f"x{m * t + k}" for k in range(m - 2)]
    sol_path = src.with_suffix("").with_suffix(".sol.json")
    sol = json.loads(sol_path.read_text()).get("solution") if sol_path.exists() else None

    # Successive elimination: R := chain[0]; R := Res_{u_k}(R, chain[k+1]).
    script = [f"ring r = {p}, ({','.join(variables)}), dp;", "option(redSB);"]
    script += [f"poly c{k} = {c};" for k, c in enumerate(chain)]
    script.append("poly R = c0;")
    for k, u in enumerate(us):
        script.append(f"R = resultant(R, c{k + 1}, {u});")
    if sol is not None:
        subs = ",".join(f"{v},{s}" for v, s in zip(variables, sol))
        script.append(f"poly chk = subst(R, {subs});")
        script.append('print("CHECK"); print(chk);')
    script.append('print("NTERMS"); print(size(R)); print("DEG"); print(deg(R));')
    script.append('short = 0; print("POLY"); print(R); print("END");')
    script.append("quit;")
    with tempfile.NamedTemporaryFile("w", suffix=".sing", delete=False) as f:
        f.write("\n".join(script) + "\n")
        sing = f.name
    started = time.monotonic()
    try:
        out = subprocess.run(["Singular", "-q", sing], capture_output=True, text=True,
                             timeout=a.timeout)
    except subprocess.TimeoutExpired:
        print(json.dumps({"src": src.name, "status": "timeout", "seconds": a.timeout}))
        return 0
    secs = time.monotonic() - started
    txt = out.stdout
    if out.returncode != 0 or "POLY" not in txt:
        print(json.dumps({"src": src.name, "status": "singular_error",
                          "stderr": out.stderr[-400:], "stdout": txt[-400:]}))
        return 0
    if sol is not None:
        chk = txt.split("CHECK", 1)[1].split("NTERMS", 1)[0].strip()
        if chk != "0":
            print(json.dumps({"src": src.name, "status": "planted_violation", "check": chk}))
            return 1
    nterms = int(txt.split("NTERMS", 1)[1].split("DEG", 1)[0].strip())
    deg = int(txt.split("DEG", 1)[1].split("POLY", 1)[0].strip())
    poly = "".join(txt.split("POLY", 1)[1].split("END", 1)[0].split())
    keep = variables[: m * t]
    text = ",".join(keep) + f"\n{p}\n" + ",\n".join([poly] + towers) + "\n"
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = src.name[: -len(".ms")] + "-direct"
    (out_dir / f"{stem}.ms").write_text(text)
    sha = hashlib.sha256(text.encode()).hexdigest()
    side = {"id": stem, "p": p, "n_vars": len(keep), "n_equations": 1 + len(towers),
            "variables": keep, "solution": sol[: m * t] if sol else None,
            "ms_sha256": sha, "derived_from": src.name,
            "derived_from_sha256": hashlib.sha256(src.read_bytes()).hexdigest()}
    (out_dir / f"{stem}.sol.json").write_text(json.dumps(side) + "\n")
    print(json.dumps({"src": src.name, "status": "ok", "id": stem, "semaev_terms": nterms,
                      "semaev_degree": deg, "singular_seconds": round(secs, 3),
                      "ms_sha256": sha}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
