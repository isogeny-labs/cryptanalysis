#!/usr/bin/env python3
"""Branch C: solve the same PKM m = 2 tower systems four ways.

Input: the pilot's rows (`--out`) and exported systems (`--export`).  Each
row carries V (tower.v), the target curve, x_R and the export id.

Solvers, all returning the set of unordered pairs {x1, x2} in V with
S3(x1, x2, x_R) = 0:

  enum      for x1 in V: the quadratic S3(x1, X, x_R) in X, its roots,
            membership by hash set.  Pure Python (slowest language here,
            so its wall time is an upper bound for this method).
  univ      eliminate both tower blocks: F(x) = prod_{v in V} (x - v)
            (product tree), R(X) = Res_x(S3(x, X, x_R), F(x)) =
            prod_v S3(v, X, x_R) (product tree), g = gcd(R, F), roots of g.
            python-flint (FLINT nmod_poly, fast multiplication).
  msolve    msolve 0.6.5 on the exported .ms file (reduced Groebner basis,
            grevlex, one thread); wall time, and whether the basis is {1}.
  f4        the pilot's own f4_fp row (wall ms, max_cols) for the same
            system, read from the row.

The pilot rows are F4's; the other three are run here.  Every solver's
pair set is checked against `enum` (and the planted pair against all), so
a wrong solver fails loudly.  Output: one JSON line per system.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import flint


def s3_quadratic(v, r, a, b, p):
    """Coefficients (c0, c1, c2) of S3(v, X, r) as a polynomial in X."""
    c2 = (r - v) * (r - v) % p
    c1 = (-2 * r * r * v - 2 * r * (v * v + a) - 2 * a * v - 4 * b) % p
    c0 = (r * r * v * v - 2 * r * (a * v + 2 * b) + a * a - 4 * b * v) % p
    return c0, c1, c2


def tonelli(n, p):
    n %= p
    if n == 0:
        return 0
    if pow(n, (p - 1) // 2, p) != 1:
        return None
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, c, t, r = s, pow(z, q, p), pow(n, q, p), pow(n, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p
            i += 1
        bb = pow(c, 1 << (m - i - 1), p)
        m, c, t, r = i, bb * bb % p, t * bb * bb % p, r * bb % p
    return r


def solve_enum(V, r, a, b, p):
    vs = set(V)
    out = set()
    for v in V:
        c0, c1, c2 = s3_quadratic(v, r, a, b, p)
        if c2 == 0:
            roots = [(-c0) * pow(c1, p - 2, p) % p] if c1 else []
        else:
            d = (c1 * c1 - 4 * c2 * c0) % p
            s = tonelli(d, p)
            if s is None:
                roots = []
            else:
                inv = pow(2 * c2, p - 2, p)
                roots = [(-c1 + s) * inv % p, (-c1 - s) * inv % p]
        for x2 in roots:
            if x2 in vs:
                out.add(tuple(sorted((v, x2))))
    return out


def prod_tree(polys, p):
    polys = list(polys)
    if not polys:
        return flint.nmod_poly([1], p)
    while len(polys) > 1:
        nxt = [polys[i] * polys[i + 1] for i in range(0, len(polys) - 1, 2)]
        if len(polys) % 2:
            nxt.append(polys[-1])
        polys = nxt
    return polys[0]


def solve_univ(V, r, a, b, p):
    F = prod_tree((flint.nmod_poly([(-v) % p, 1], p) for v in V), p)
    R = prod_tree((flint.nmod_poly(list(s3_quadratic(v, r, a, b, p)), p) for v in V), p)
    g = R.gcd(F)
    x2s = [int(z) for z, _ in g.roots()] if g.degree() > 0 else []
    vs = set(V)
    out = set()
    for x2 in x2s:
        # x1 from S3(x1, x2, r) = 0 (symmetric): a quadratic, then membership
        c0, c1, c2 = s3_quadratic(x2, r, a, b, p)
        if c2 == 0:
            roots = [(-c0) * pow(c1, p - 2, p) % p] if c1 else []
        else:
            sq = tonelli((c1 * c1 - 4 * c2 * c0) % p, p)
            inv = pow(2 * c2, p - 2, p)
            roots = [] if sq is None else [(-c1 + sq) * inv % p, (-c1 - sq) * inv % p]
        for z in roots:
            if z in vs:
                out.add(tuple(sorted((z, x2))))
    return out


def run_msolve(path, timeout):
    out = Path(str(path) + ".gb")
    t0 = time.perf_counter()
    try:
        cp = subprocess.run(["msolve", "-f", str(path), "-g", "2", "-t", "1", "-o", str(out)],
                            capture_output=True, text=True, timeout=timeout)
        wall = time.perf_counter() - t0
        txt = out.read_text() if out.exists() else ""
        body = "".join(l for l in txt.splitlines() if not l.startswith("#"))
        unit = body.replace(" ", "") == "[1]:"
        return {"msolve_wall_s": wall, "msolve_rc": cp.returncode, "msolve_unit": unit,
                "msolve_basis_chars": len(txt), "msolve_timed_out": False}
    except subprocess.TimeoutExpired:
        return {"msolve_wall_s": timeout, "msolve_timed_out": True}


def main():
    rows_path, export_dir = Path(sys.argv[1]), Path(sys.argv[2])
    msolve_timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 120
    for line in rows_path.read_text().splitlines():
        row = json.loads(line)
        if "summary" in row or row.get("control") != "tower" or row.get("m") != 2:
            continue
        V = row["tower"]["v"]
        p, r = row["p"], row["x_r"]
        a, b = row["curve"]["a"], row["curve"]["b"]
        rec = {k: row[k] for k in ("kind", "t", "target", "target_index", "V_size", "log2_V", "export_id")}
        rec["iso_degrees"] = row.get("iso_degrees")
        rec["f4_ms"], rec["f4_max_cols"], rec["f4_timed_out"] = row["ms"], row["max_cols"], row["timed_out"]
        t0 = time.perf_counter(); e = solve_enum(V, r, a, b, p); rec["enum_wall_s"] = time.perf_counter() - t0
        t0 = time.perf_counter(); u = solve_univ(V, r, a, b, p); rec["univ_wall_s"] = time.perf_counter() - t0
        rec["pairs"] = sorted(e)
        rec["univ_agrees"] = (u == e)
        if row["target"] == "planted":
            t = row["t"]
            sol = json.loads((export_dir / (row["export_id"] + ".sol.json")).read_text())["solution"]
            rec["planted_found"] = tuple(sorted((sol[0], sol[t]))) in e
        rec.update(run_msolve(export_dir / (row["export_id"] + ".ms"), msolve_timeout))
        if not rec.get("msolve_timed_out"):
            rec["msolve_agrees_on_consistency"] = rec["msolve_unit"] == (len(e) == 0)
        print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main()
