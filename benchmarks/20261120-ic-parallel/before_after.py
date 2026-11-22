"""Wall time of one `ic bench` cell, previous binary vs this one, at the
lead-testing registry's phase-3 settings, with a count-for-count identity
check of the two reports (instance, every integer counter, recovered logs).

usage: before_after.py OLD_BIN NEW_BIN OUT_DIR
"""
import json, subprocess, sys, time, os
OLD, NEW, OUT = sys.argv[1:4]
COMMON = "--repeats 8 --seed 20261104 --max-trials 8000000 --max-cofactor 8 --solver-budget-seconds 600 --rho-runs 16"
CELLS = {
    "prime-24": "--bits 24 --factor-base prime-abscissa:size=256 --oracle mitm",
    "char2-27": "--char2-degree 27 --factor-base binary-subspace:dimension=9 --oracle mitm",
    "char2-29": "--char2-degree 29 --factor-base binary-subspace:dimension=9 --oracle mitm",
    "koblitz-43": "--koblitz-degree 43 --factor-base koblitz-orbit:divisor=1 --oracle mitm-frobenius",
}
sys.path.insert(0, os.path.dirname(__file__))
rows = []
for name, args in CELLS.items():
    rec = {"cell": name, "args": args + " " + COMMON}
    for arm, b in (("previous", OLD), ("this", NEW)):
        f = f"{OUT}/{name}-{arm}.json"
        if os.path.exists(f):
            os.remove(f)
        t0 = time.monotonic()
        subprocess.run([b, "bench", *args.split(), *COMMON.split(), "--json", "--out", f],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        rec[f"{arm}_wall_s"] = round(time.monotonic() - t0, 3)
        rec[f"{arm}_all_verified"] = json.load(open(f))["all_verified"]
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "same_counts.py"),
                        f"{OUT}/{name}-previous.json", f"{OUT}/{name}-this.json"],
                       capture_output=True, text=True)
    rec["same_counts"] = r.stdout.startswith("IDENTICAL")
    rec["speedup"] = round(rec["previous_wall_s"] / rec["this_wall_s"], 1)
    rows.append(rec)
    print(json.dumps(rec), flush=True)
json.dump(rows, open(f"{OUT}/before_after.json", "w"), indent=1)
