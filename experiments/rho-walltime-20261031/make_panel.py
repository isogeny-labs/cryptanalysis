#!/usr/bin/env python3
"""Freeze the plain-rho wall-time panels and their Tier 1 manifests (PROTOCOL.md).

    CRYPTANALYSIS_LIB=.../libcryptanalysis.so python3 make_panel.py --reference BIN --candidate BIN \
        --outdir DIR --cgroup PATH --provider P --instance-id ID --receipt PATH [--repetitions R] [--workdir W]

One panel and one manifest per subgroup size.  Curves are y^2 = x^3 + a x + b over F_p with
a, b nonzero (so j != 0 and j != 1728: no GLV structure, ca_curve_solve runs the negation-map
rho), p a random prime of bits+3 bits, r the largest prime factor of #E with exactly `bits`
bits and cofactor <= 16.  Targets k*G are built with the reference binary's --fixture mode
(the candidate must produce identical points); the scalars never reach a timed process.
expected_result is the FNV-1a hash of the true scalars, computed here, not by either binary."""
import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "bindings" / "python"))
import cryptanalysis as ca  # noqa: E402

SEED, SIZES, CURVES, TARGETS, WALK_SEED = 20261101, (28, 32, 36, 40), 20, 5, 7


def sample_curve(rng: random.Random, bits: int):
    while True:
        p = ca.next_prime(rng.getrandbits(bits + 3) | (1 << (bits + 2)))
        a, b = rng.randrange(1, p), rng.randrange(1, p)
        N = ca.Group.ec_count_points(p, a, b)
        r = max(q for q, _ in ca.factorize(N))
        if r.bit_length() == bits and N // r <= 16 and ca.is_prime(r):
            return p, a, b, N, r


def fnv(scalars):
    h = 0xcbf29ce484222325
    for k in scalars:
        for byte in range(8):
            h ^= (k >> (8 * byte)) & 0xFF
            h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return f"{h:016x}"


def main():
    ap = argparse.ArgumentParser()
    for a in ("--reference", "--candidate", "--outdir", "--cgroup", "--provider", "--instance-id", "--receipt"):
        ap.add_argument(a, required=True)
    ap.add_argument("--variant", help="third arm (candidate with the old DP spacing); adds manifest_<bits>_var.json")
    ap.add_argument("--cpu", type=int, default=0)
    ap.add_argument("--mem-nodes", default="0")
    ap.add_argument("--repetitions", type=int, default=15)
    ap.add_argument("--workdir", default=str(HERE.parents[1]))
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    for bits in SIZES:
        rng = random.Random(f"{SEED}:rho:{bits}")
        lines, ks = [], []
        for _ in range(CURVES):
            p, ca_, cb, N, r = sample_curve(rng, bits)
            for t in range(TARGETS):
                k = random.Random(f"{SEED}:{p}:{ca_}:{cb}:{t}").randrange(1, r)
                lines.append(f"{p} {ca_} {cb} {r} {k}")
                ks.append(k)
        fx = out / f"fixture_{bits}.txt"
        fx.write_text("\n".join(lines) + "\n")
        arms = [a.reference, a.candidate] + ([a.variant] if a.variant else [])
        pts = [subprocess.run([b, "--fixture", str(fx)], check=True, capture_output=True, text=True).stdout for b in arms]
        if any(x != pts[0] for x in pts):
            sys.exit(f"{bits}: the arms' fixtures differ")
        fx.unlink()
        panel = out / f"panel_{bits}.txt"
        panel.write_text(pts[0])
        first = pts[0].split("\n")[0].split()
        for tag, other in (("", a.candidate), ("_var", a.variant)):
            if tag and not a.variant:
                continue
            man = {
                "schema": 1, "workdir": a.workdir, "repetitions": a.repetitions, "timeout_s": 900,
                "isolation": {"tier": "tier1", "cpus": str(a.cpu), "execution_cpu": a.cpu, "mem_nodes": a.mem_nodes,
                              "cgroup": a.cgroup,
                              "allocation": {"provider": a.provider, "instance_id": a.instance_id, "receipt": a.receipt}},
                "artifacts": [a.receipt, "bench_rho_panel.c", panel.name],
                "measurement_boundary": "after every group and target is set up: ca_curve_solve on each panel target plus its replay check, summed",
                "pair_fields": ["targets", "first_x", "first_y", "seed"],
                "result_field": "result",
                "cases": [{
                    "id": f"rho-generic-{bits}{tag}",
                    "expected_fields": {"targets": str(len(ks)), "first_x": first[4], "first_y": first[5], "seed": str(WALK_SEED)},
                    "expected_result": fnv(ks),
                    "reference": [Path(a.reference).name, panel.name, str(WALK_SEED)],
                    "candidate": [Path(other).name, panel.name, str(WALK_SEED)],
                }],
            }
            (out / f"manifest_{bits}{tag}.json").write_text(json.dumps(man, indent=1) + "\n")
        print(f"{bits} bits: {len(ks)} targets, expected result {fnv(ks)}")


if __name__ == "__main__":
    main()
