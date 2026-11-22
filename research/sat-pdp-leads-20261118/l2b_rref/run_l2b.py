#!/usr/bin/env python3
"""L2b runner (PROTOCOL.md): per base CNF and shuffle k in {0,1,2}, arm A =
cadical on the shuffled base CNF (L2's shuffle seed), arm C = cadical on the
shuffled RREF-augmented CNF, back to back on one worker. One JSON row per
(file, k, arm). SAT models that the printed output leaves incomplete are
re-verified with --elim=0 on the same shuffled CNF (L2 deviation, now built in).

Usage: run_l2b.py --inst DIR --cadical BIN --out rows.jsonl [--workers 3]
"""
import argparse, json, os, subprocess, sys, tempfile
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../l2_sbva"))
import run_l2 as R  # noqa: E402

A = None


def solve(path, sh):
    r, model = R.cadical(path)
    if r["answer"] == "SAT":
        ok = all(any(l in model for l in c) for c in sh)
        r["model_ok_printed"] = ok
        if not ok:  # printed model incomplete (eliminated vars): re-solve to verify
            out = subprocess.run([A.cadical, "--elim=0", path], capture_output=True, text=True,
                                 timeout=R.CAP).stdout
            m = set()
            for line in out.splitlines():
                if line.startswith("v "):
                    m.update(int(x) for x in line.split()[1:] if x != "0")
            ok = "s SATISFIABLE" in out and all(any(l in m for l in c) for c in sh)
            r["model_rechecked"] = True
        r["model_ok"] = ok
    return r


def job(task):
    base, rref, k, isdec = task
    rows = []
    with tempfile.TemporaryDirectory() as td:
        for arm, fname, seed in (("A", base, f"l2-shuffle-{base}-{k}"),
                                 ("C", rref, f"l2b-shuffle-{rref}-{k}")):
            nv, cls = R.read_cnf(os.path.join(A.inst, fname))
            sh = R.shuffle_cnf(nv, cls, seed)
            p = os.path.join(td, arm + ".cnf")
            R.write_cnf(p, nv, sh)
            r = solve(p, sh)
            exp = "SAT" if isdec else "UNSAT"
            rows.append({"file": base, "k": k, "arm": arm, "decomposable": isdec, "vars": nv,
                         "clauses": len(cls), **r, "answer_ok": r["answer"] in (exp, "UNKNOWN")})
    return rows


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", required=True); ap.add_argument("--cadical", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--workers", type=int, default=3)
    A = ap.parse_args()
    R.A = A  # R.cadical reads A.cadical
    man = json.load(open(os.path.join(A.inst, "manifest.json")))
    insts = sorted(man["instances"], key=lambda e: (-e["l"], e["enc"], e["idx"]))
    tasks = [(e["file"], e["rref_file"], k, e["decomposable"]) for k in range(3) for e in insts]
    with Pool(A.workers, initializer=lambda a: (globals().__setitem__("A", a), setattr(R, "A", a)),
              initargs=(A,)) as pool, open(A.out, "w") as fo:
        for rows in pool.imap_unordered(job, tasks):
            for r in rows:
                fo.write(json.dumps(r, separators=(",", ":")) + "\n")
            fo.flush()
            print(rows[0]["file"], rows[0]["k"], [(r["arm"], r["answer"], r["conflicts"]) for r in rows], flush=True)


if __name__ == "__main__":
    main()
