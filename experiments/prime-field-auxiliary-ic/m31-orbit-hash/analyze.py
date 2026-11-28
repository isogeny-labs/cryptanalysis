"""Check matched public M31 orbit-hash panels and print paired medians."""
import csv
import statistics as stats
from pathlib import Path

HERE = Path(__file__).resolve().parent
for panel, seeds in (("raw", {0, 1, 2}), ("confirm", {3, 4, 5})):
    rows = list(csv.DictReader((HERE / f"{panel}.csv").open()))
    assert len(rows) == 96, (panel, len(rows))
    for basis in ("auxiliary", "plain"):
        keyed = {}
        for row in rows:
            if row["basis"] == basis:
                key = (int(row["seed"]), int(row["repeat"]), row["configuration"])
                assert key not in keyed
                keyed[key] = row
        assert len(keyed) == 48
        assert {key[0] for key in keyed} == seeds
        for seed in seeds:
            for repeat in range(8):
                control = keyed[seed, repeat, "control"]
                orbit = keyed[seed, repeat, "orbit"]
                for field in ("basis_sha256", "scalar", "entries", "trials", "relations"):
                    assert control[field] == orbit[field], (panel, basis, seed, repeat, field)
                assert control["scalar"] == "123456789"
                assert int(control["native_calls"]) > 0 and int(orbit["native_calls"]) > 0
                assert int(control["native_fallbacks"]) == int(orbit["native_fallbacks"]) == 0
        print(panel, basis)
        for metric in ("charged_wall_ns", "charged_cpu_ns", "table_ns"):
            pairs = [(keyed[seed, repeat, "control"], keyed[seed, repeat, "orbit"])
                     for seed in sorted(seeds) for repeat in range(8)]
            ratios = [int(o[metric]) / int(c[metric]) for c, o in pairs]
            print(metric, "control_ms", round(stats.median(int(c[metric]) for c, _ in pairs) / 1e6, 3),
                  "orbit_ms", round(stats.median(int(o[metric]) for _, o in pairs) / 1e6, 3),
                  "paired_orbit_control", round(stats.median(ratios), 4),
                  "wins", sum(r < 1 for r in ratios), "/24")
