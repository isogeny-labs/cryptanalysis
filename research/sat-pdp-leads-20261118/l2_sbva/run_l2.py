#!/usr/bin/env python3
"""L2 runner (PROTOCOL.md): for every base CNF and shuffle k in {0,1,2}, run
arm A (cadical on the shuffle) and arm B (sbva then cadical on its output),
back to back on one worker. Writes one JSON row per (file, k, arm).

Usage: run_l2.py --inst DIR --cadical BIN --sbva BIN --out rows.jsonl [--workers 3]
"""
import argparse, json, os, random, re, subprocess, tempfile, time
from multiprocessing import Pool

CAP = 600
A = None  # filled in main


def read_cnf(path):
    nv, cls = 0, []
    with open(path) as f:
        for line in f:
            if line.startswith("p"):
                nv = int(line.split()[2])
            elif line.strip() and not line.startswith("c"):
                cls.append([int(x) for x in line.split()[:-1]])
    return nv, cls


def shuffle_cnf(nv, cls, seed):
    rng = random.Random(seed)
    perm = list(range(1, nv + 1)); rng.shuffle(perm)
    pm = {i + 1: perm[i] for i in range(nv)}
    out = [[(pm[abs(x)] if x > 0 else -pm[abs(x)]) for x in c] for c in cls]
    for c in out:
        rng.shuffle(c)
    rng.shuffle(out)
    return out


def write_cnf(path, nv, cls):
    with open(path, "w") as f:
        f.write(f"p cnf {nv} {len(cls)}\n")
        f.writelines(" ".join(map(str, c)) + " 0\n" for c in cls)


def cadical(path):
    t0 = time.perf_counter()
    try:
        p = subprocess.run([A.cadical, path], capture_output=True, text=True, timeout=CAP)
        out, rc, censored = p.stdout, p.returncode, False
    except subprocess.TimeoutExpired as e:
        out, rc, censored = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), None, True
    wall = time.perf_counter() - t0
    m = re.search(r"^c conflicts:\s+(\d+)", out, re.M)
    model = set()
    for line in out.splitlines():
        if line.startswith("v "):
            model.update(int(x) for x in line.split()[1:] if x != "0")
    ans = {10: "SAT", 20: "UNSAT"}.get(rc, "UNKNOWN")
    return {"answer": ans, "conflicts": int(m.group(1)) if m else None, "wall": wall,
            "censored": censored}, model


def job(task):
    fname, k, isdec = task
    nv, cls = read_cnf(os.path.join(A.inst, fname))
    sh = shuffle_cnf(nv, cls, f"l2-shuffle-{fname}-{k}")
    rows = []
    with tempfile.TemporaryDirectory() as td:
        fa = os.path.join(td, "a.cnf"); write_cnf(fa, nv, sh)
        # arm A
        r, model = cadical(fa)
        if r["answer"] == "SAT":
            r["model_ok"] = all(any(lit in model for lit in c) for c in sh)
        rows.append({"file": fname, "k": k, "arm": "A", "decomposable": isdec, **r})
        # arm B
        fb = os.path.join(td, "b.cnf")
        t0 = time.perf_counter()
        subprocess.run([A.sbva, "-i", fa, "-o", fb, "-t", "60"], capture_output=True, timeout=CAP)
        sb_wall = time.perf_counter() - t0
        with open(fb) as f:
            hdr = next(l for l in f if l.startswith("p")).split()
        r, _ = cadical(fb)
        r["wall_cadical"] = r["wall"]; r["wall_sbva"] = sb_wall; r["wall"] = r["wall"] + sb_wall
        r["sbva_vars"], r["sbva_clauses"] = int(hdr[2]), int(hdr[3])
        rows.append({"file": fname, "k": k, "arm": "B", "decomposable": isdec,
                     "vars": nv, "clauses": len(cls), **r})
    for row in rows:
        exp = "SAT" if isdec else "UNSAT"
        row["answer_ok"] = row["answer"] in (exp, "UNKNOWN")
    return rows


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", required=True); ap.add_argument("--cadical", required=True)
    ap.add_argument("--sbva", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=3)
    A = ap.parse_args()
    man = json.load(open(os.path.join(A.inst, "manifest.json")))
    # interleave: shuffle index outermost, then l descending (long jobs first), then files
    insts = sorted(man["instances"], key=lambda e: (-e["l"], e["enc"], e["idx"]))
    tasks = [(e["file"], k, e["decomposable"]) for k in range(3) for e in insts]
    with Pool(A.workers) as pool, open(A.out, "w") as fo:
        for rows in pool.imap_unordered(job, tasks):
            for r in rows:
                fo.write(json.dumps(r, separators=(",", ":")) + "\n")
            fo.flush()
            print(rows[0]["file"], rows[0]["k"], [(r["arm"], r["answer"], r["conflicts"]) for r in rows], flush=True)


if __name__ == "__main__":
    main()
