"""Read the archived M31 timings and verify all nine public certificates."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys


def record(path):
    return json.loads(path.read_text(), parse_float=Decimal)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=Path(__file__).resolve().parents[1]/"snapshot")
    args = parser.parse_args()
    if not __debug__:
        parser.error("the archived verifier requires assertions enabled")
    comparison = args.snapshot.resolve() / "comparison"
    sys.path.insert(0, str(comparison))
    from benchmark import audit

    root = comparison / "field31"
    charges = next(x for x in record(comparison / "setup.json") if x["field_bits"] == 31)
    ref = record(root / "rho/public.json")
    assert ref["factor_base_representatives"] == []
    times = {phase: [] for phase in ("rho", "pair", "search", "total")}
    for seed in range(3):
        for arm in ("rho", "auxiliary", "plain"):
            folder = root / arm / f"seed{seed}"
            public = record(folder / "public.json")
            assert all(public[k] == ref[k] for k in ("p", "n", "a", "b", "P", "Q"))
            assert len(public["factor_base_representatives"]) == (0 if arm == "rho" else 500)
            audit(folder, arm)
            metrics = record(folder / "metrics.json")
            if arm == "rho":
                rho = metrics["solver_seconds"]
                times["rho"].append(rho)
                print(f"rho {seed}: {rho} s")
                continue
            total = metrics["solver_seconds"] + charges[f"{arm}_setup_seconds"]
            times["total"].append(total)
            for phase in ("pair", "search"):
                times[phase].append(metrics[f"{phase}_seconds"])
            print(f"{arm} {seed}: {total:.6f} s, {total/rho:.2f} times rho")
    ceiling = max(times["rho"])
    # PhaseFloor.lean uses units of 0.1 microseconds.
    assert min(times["pair"]) * 10**7 == 601040
    assert min(times["search"]) * 10**7 == 4351190
    assert ceiling * 10**7 == 200969
    for phase in ("pair", "search", "total"):
        low = min(times[phase])
        print(f"min {phase} {low:.6f} s / max rho {ceiling} s = {low/ceiling:.3f}")


if __name__ == "__main__":
    main()
