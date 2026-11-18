#!/usr/bin/env python3
"""L2: emit plain-CNF DIMACS instances of the m = 4 dual-rail point-decomposition
system for CaDiCaL / SBVA.

The system is built by crypto:research/sat_smt_leads_20261115/A-dualrail-m4/dr4.py,
imported unchanged from a sibling crypto checkout (pass --crypto, default
../../../../crypto relative to this file; the commit is recorded in the manifest).
Cells and targets use the same derivation as that pilot's dr4_run.py:
cell = Cell4(l, 2026111500 + l), (non, dec) = cell.targets(8, 4).

Each XOR row x_1 + ... + x_k = c is expanded to CNF by Tseitin chaining with cut
length 4: pieces of at most 4 literals, each piece written as its 2^(4-1) = 8
parity clauses, with one fresh variable linking consecutive pieces. This is the
"CNF part" the leads note asks for. The AND gates and side clauses come from
dr4's render() unchanged.

Output: <out>/l<l>_<enc>_t<idx>.cnf plus <out>/manifest.json (one entry per
instance: l, n, enc, idx, decomposable, vars, clauses, sha256).
"""
import argparse, hashlib, itertools, json, os, subprocess, sys


def xor_to_cnf(vs, rhs, nv, cut=4):
    """Clauses for XOR(vs) = rhs; returns (clauses, new nv)."""
    clauses = []
    vs = list(vs)
    if not vs:
        if rhs:
            clauses.append([])  # 0 = 1: unsatisfiable (does not occur in practice)
        return clauses, nv
    while len(vs) > cut:
        head, vs = vs[:cut - 1], vs[cut - 1:]
        nv += 1
        t = nv  # t = XOR(head)  <=>  XOR(head + [t]) = 0
        clauses += parity(head + [t], False)
        vs = [t] + vs
    clauses += parity(vs, rhs)
    return clauses, nv


def parity(vs, rhs):
    """All clauses forbidding assignments of vs whose XOR != rhs."""
    out = []
    for bits in itertools.product((0, 1), repeat=len(vs)):
        if (sum(bits) & 1) != rhs:  # forbidden assignment -> blocking clause
            out.append([-v if b else v for v, b in zip(vs, bits)])
    return out


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--crypto", default=os.path.join(here, "../../../../crypto"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--l", type=int, nargs="+", default=[3, 4])
    ap.add_argument("--enc", nargs="+", default=["plain", "dual"])
    a = ap.parse_args()
    pilot = os.path.join(os.path.abspath(a.crypto), "research/sat_smt_leads_20261115/A-dualrail-m4")
    sys.path.insert(0, pilot)
    import dr4  # noqa: E402
    commit = subprocess.run(["git", "-C", a.crypto, "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    os.makedirs(a.out, exist_ok=True)
    man = {"crypto_commit": commit, "generator": "dr4.Cell4 / System4.render", "cut": 4,
           "instances": []}
    for l in a.l:
        cell = dr4.Cell4(l, 2026111500 + l)
        non, dec = cell.targets(8, 4)
        tg = [(i, R, False) for i, R in enumerate(non)] + [(8 + i, R, True) for i, R in enumerate(dec)]
        for idx, R, isdec in tg:
            assert cell.decomposable(R) == isdec
            S = dr4.System4(cell, R)
            for enc in a.enc:
                nv, clauses, xors = S.render(enc)
                cls = [list(c) for c in clauses]
                for vs, rhs in xors:
                    c2, nv = xor_to_cnf(vs, bool(rhs), nv)
                    cls += c2
                name = f"l{l}_{enc}_t{idx:02d}.cnf"
                body = f"p cnf {nv} {len(cls)}\n" + "".join(" ".join(map(str, c)) + " 0\n" for c in cls)
                with open(os.path.join(a.out, name), "w") as f:
                    f.write(body)
                man["instances"].append({"file": name, "l": l, "n": cell.n, "enc": enc, "idx": idx,
                                         "decomposable": isdec, "vars": nv, "clauses": len(cls),
                                         "sha256": hashlib.sha256(body.encode()).hexdigest()})
                print(name, nv, len(cls), "SAT-expected" if isdec else "UNSAT-expected", flush=True)
    with open(os.path.join(a.out, "manifest.json"), "w") as f:
        json.dump(man, f, indent=1)


if __name__ == "__main__":
    main()
