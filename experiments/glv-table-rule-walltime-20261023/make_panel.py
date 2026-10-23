#!/usr/bin/env python3
"""Freeze the wall-time panels and their Tier 1 manifests (PROTOCOL.md).

    CRYPTANALYSIS_LIB=.../libcryptanalysis.so python3 make_panel.py --reference BIN --candidate BIN \
        --outdir DIR --cpu N --cgroup PATH --provider P --instance-id ID --receipt PATH [--repetitions R]

Samples curves exactly as experiments/glv-table-rule-20261022/run.py does (seed 20261024,
fresh), draws targets, builds the public points with the reference binary's --fixture
mode (checking the candidate gives identical points), and writes panel_<family>.txt
(no scalars) plus manifest_<family>.json whose expected_result is the FNV-1a hash of
the true scalars, computed here, not by either binary."""
import argparse, json, random, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "experiments" / "glv-table-rule-20261022"))
from run import sample_curve  # noqa: E402

SEED, SIZES, CURVES, TARGETS, WALK_SEED = 20261024, (28, 30, 32, 34), 25, 4, 7


def fnv(scalars):
    h = 0xcbf29ce484222325
    for k in scalars:
        for byte in range(8):
            h ^= (k >> (8 * byte)) & 0xff
            h = (h * 0x100000001b3) & 0xffffffffffffffff
    return f"{h:016x}"


def main():
    ap = argparse.ArgumentParser()
    for a in ("--reference", "--candidate", "--outdir", "--cgroup", "--provider", "--instance-id", "--receipt"):
        ap.add_argument(a, required=True)
    ap.add_argument("--cpu", type=int, required=True)
    ap.add_argument("--mem-nodes", default="0")
    ap.add_argument("--repetitions", type=int, default=15)
    ap.add_argument("--workdir", default=str(HERE.parents[1]))
    a = ap.parse_args()
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    for fam in ("j1728", "j0"):
        lines, ks = [], []
        for bits in SIZES:
            rng = random.Random(f"{SEED}:{fam}:{bits}")
            for ci in range(CURVES):
                p, ca_, cb, N, r = sample_curve(rng, fam, bits)
                for t in range(TARGETS):
                    k = random.Random(f"{SEED}:{p}:{ca_}:{cb}:{t}").randrange(1, r)
                    lines.append(f"{p} {ca_} {cb} {r} {k}"); ks.append(k)
        fx = out / f"fixture_{fam}.txt"; fx.write_text("\n".join(lines) + "\n")
        pts = [subprocess.run([b, "--fixture", str(fx)], check=True, capture_output=True, text=True).stdout for b in (a.reference, a.candidate)]
        if pts[0] != pts[1]:
            sys.exit(f"{fam}: reference and candidate fixtures differ")
        panel = out / f"panel_{fam}.txt"; panel.write_text(pts[0])
        fx.unlink()   # the scalars stay only in this script's derivation, not on disk beside the panel
        first = pts[0].split("\n")[0].split()
        man = {
            "schema": 1, "workdir": a.workdir, "repetitions": a.repetitions, "timeout_s": 600,
            "isolation": {"tier": "tier1", "cpus": str(a.cpu), "execution_cpu": a.cpu, "mem_nodes": a.mem_nodes,
                          "cgroup": a.cgroup,
                          "allocation": {"provider": a.provider, "instance_id": a.instance_id, "receipt": a.receipt}},
            "artifacts": [a.receipt, str(HERE / "bench_glv_panel.c"), str(panel)],
            "measurement_boundary": "after every group and target is set up: ca_curve_solve on each panel target plus its replay check, summed",
            "pair_fields": ["targets", "first_x", "first_y", "seed"],
            "result_field": "result",
            "cases": [{
                "id": f"glv-table-{fam}-28-34",
                "expected_fields": {"targets": str(len(ks)), "first_x": first[4], "first_y": first[5], "seed": str(WALK_SEED)},
                "expected_result": fnv(ks),
                "reference": [a.reference, str(panel), str(WALK_SEED)],
                "candidate": [a.candidate, str(panel), str(WALK_SEED)],
            }],
        }
        (out / f"manifest_{fam}.json").write_text(json.dumps(man, indent=1) + "\n")
        print(f"{fam}: {len(ks)} targets, expected result {fnv(ks)}")


if __name__ == "__main__":
    main()
