"""Replay stopping-time bounds conditional on fixed arrival slots and clock readings."""
import csv
import json
import re
import subprocess
import sys
from decimal import Decimal
from math import comb

from archived_graphs import signed_rank
from archived_loops import HERE, observations, read


def support_size(rows, weights, order):
    rank = signed_rank(rows)
    assert rank == len(rows) - 1
    columns = [0] * 17
    support = []
    for i, (row, weight) in enumerate(zip(rows, weights, strict=True)):
        columns[row["i"]] += row["si"] * weight
        columns[row["j"]] += row["sj"] * weight
        needed = signed_rank(rows[:i] + rows[i + 1:]) == rank
        assert needed == bool(weight % order)
        if needed:
            support.append(i)
    assert all(c % order == 0 for c in columns)
    assert support and support[-1] == len(rows) - 1
    return len(support)


def main():
    if not __debug__:
        raise RuntimeError("Run with Python assertions enabled.")
    positions = subprocess.check_output([sys.executable, str(HERE / "archived_positions.py")])
    assert positions == (HERE / "archived_positions.csv").read_bytes()
    slots = list(csv.DictReader(positions.decode().splitlines()))
    writer = csv.writer(sys.stdout)
    writer.writerow(["seed", "arm", "needed", "accepted", "earliest_query", "mean_query",
                     "preceding_seconds", "following_seconds", "rho_seconds", "lower_ratio"])
    for seed in range(3):
        rho = json.loads(read(f"rho_seed{seed}", "audited.json"), parse_float=Decimal)
        assert rho["audit"]["verified_public_key"]
        for arm in ("v2_chain", "v2_batch"):
            data, rows = observations(arm, seed)
            assert data["recovered"] == rho["recovered"]
            needed = support_size(rows, data["weights"], data["audit"]["certified_full_group_order"])
            queries = [int(s["query"]) for s in slots if s["arm"] == arm and int(s["seed"]) == seed]
            n = len(rows)
            assert len(queries) == n and queries[-1] == data["queries"]
            earliest = queries[needed - 1]
            # A last required slot at k leaves k-1 choices for the other required rows.
            total = sum(q * comb(k-1, needed-1) for k, q in enumerate(queries, 1) if k >= needed)
            mean = Decimal(total) / comb(n, needed)
            log = read(f"{arm}_seed{seed}", "log").decode()
            checkpoints = [(int(q), Decimal(t)) for q, t in re.findall(
                r"^queries (\d+), relations \d+, seconds ([\d.]+)$", log, re.M)]
            assert all(t <= u for (_, t), (_, u) in zip(checkpoints, checkpoints[1:]))
            before = max(t for q, t in checkpoints if q < earliest)
            after = min(t for q, t in checkpoints if q > earliest)
            baseline = rho["end_to_end_seconds"]
            writer.writerow([seed, arm, needed, n, earliest, round(mean), before, after,
                             baseline, round(before / baseline, 1)])


if __name__ == "__main__":
    main()
