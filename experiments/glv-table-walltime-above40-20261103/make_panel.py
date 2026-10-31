#!/usr/bin/env python3
"""Freeze the GLV table wall-time panels and their Tier 1 manifests (PROTOCOL.md).

    CRYPTANALYSIS_LIB=.../libcryptanalysis.so python3 make_panel.py --reference BIN --candidate BIN \
        --outdir DIR --cgroup PATH --provider P --instance-id ID --receipt PATH [--repetitions R] [--workdir W]

One panel and one manifest per (family, bits) cell: j = 1728 and j = 0 at 42, 44 and 46 bits,
TARGETS curves per cell and one target per curve.  Curves are sampled exactly as
experiments/glv-table-confirm-above40-20261102/run.py (#1332) does, with the new seed 20261103.
Targets k*G are built with the reference binary's --fixture mode (the candidate must produce
identical points); the scalars never reach a timed process.  expected_result is the FNV-1a hash
of the true scalars, computed here, not by either binary."""
import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "bindings" / "python"))
import cryptanalysis as ca  # noqa: E402

SEED, FAMILIES, SIZES, TARGETS, WALK_SEED = 20261103, ("j1728", "j0"), (42, 44, 46), 20, 7


def sample_curve(rng: random.Random, family: str, bits: int):
    """Largest prime factor r of #E with exactly `bits` bits and cofactor <= 16;
    j = 1728: y^2 = x^3 + a x (p = 1 mod 4); j = 0: y^2 = x^3 + b (p = 1 mod 3).
    Copied from experiments/glv-table-confirm-above40-20261102/run.py."""
    while True:
        p = ca.next_prime(rng.getrandbits(bits + 3) | (1 << (bits + 2)))
        if family == "j0":
            if p % 3 != 1:
                continue
            a, b = 0, rng.randrange(1, p)
        else:
            if p % 4 != 1:
                continue
            a, b = rng.randrange(1, p), 0
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
    ap.add_argument("--cpu", type=int, default=0)
    ap.add_argument("--mem-nodes", default="0")
    ap.add_argument("--repetitions", type=int, default=15)
    ap.add_argument("--workdir", default=str(HERE.parents[1]))
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    for fam in FAMILIES:
        for bits in SIZES:
            rng = random.Random(f"{SEED}:{fam}:{bits}")
            lines, ks = [], []
            for _ in range(TARGETS):
                p, ca_, cb, N, r = sample_curve(rng, fam, bits)
                k = random.Random(f"{SEED}:{p}:{ca_}:{cb}:0").randrange(1, r)
                lines.append(f"{p} {ca_} {cb} {r} {k}")
                ks.append(k)
            fx = out / f"fixture_{fam}_{bits}.txt"
            fx.write_text("\n".join(lines) + "\n")
            pts = [subprocess.run([b, "--fixture", str(fx)], check=True, capture_output=True, text=True).stdout
                   for b in (a.reference, a.candidate)]
            if pts[0] != pts[1]:
                sys.exit(f"{fam} {bits}: the arms' fixtures differ")
            fx.unlink()
            panel = out / f"panel_{fam}_{bits}.txt"
            panel.write_text(pts[0])
            first = pts[0].split("\n")[0].split()
            man = {
                "schema": 1, "workdir": a.workdir, "repetitions": a.repetitions, "timeout_s": 900,
                "isolation": {"tier": "tier1", "cpus": str(a.cpu), "execution_cpu": a.cpu, "mem_nodes": a.mem_nodes,
                              "cgroup": a.cgroup,
                              "allocation": {"provider": a.provider, "instance_id": a.instance_id, "receipt": a.receipt}},
                "artifacts": [a.receipt, "bench_glv_panel.c", panel.name],
                "measurement_boundary": "after every group and target is set up: ca_curve_solve on each panel target plus its replay check, summed",
                "pair_fields": ["targets", "first_x", "first_y", "seed"],
                "result_field": "result",
                "cases": [{
                    "id": f"glv-{fam}-{bits}",
                    "expected_fields": {"targets": str(len(ks)), "first_x": first[4], "first_y": first[5], "seed": str(WALK_SEED)},
                    "expected_result": fnv(ks),
                    "reference": [Path(a.reference).name, panel.name, str(WALK_SEED)],
                    "candidate": [Path(a.candidate).name, panel.name, str(WALK_SEED)],
                }],
            }
            (out / f"manifest_{fam}_{bits}.json").write_text(json.dumps(man, indent=1) + "\n")
            print(f"{fam} {bits} bits: {len(ks)} targets, expected result {fnv(ks)}")


if __name__ == "__main__":
    main()
