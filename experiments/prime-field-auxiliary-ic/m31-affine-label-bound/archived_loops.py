"""Replay the loop-time decomposition on the committed 31-bit single-target records."""
import json
import re
import subprocess
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

DIRECTORY = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0"
HERE = Path(__file__).resolve().parent


def read(stem, extension):
    # Read Git objects so sparse checkouts use exactly the same archived inputs.
    return subprocess.check_output(
        ["git", "show", f"HEAD:{DIRECTORY}/{stem}.{extension}"], cwd=HERE
    )


def observations(arm, seed):
    stem = f"{arm}_seed{seed}"
    data = json.loads(read(stem, "audited.json"), parse_float=Decimal)
    rows = [json.loads(line) for line in read(stem, "relations.jsonl").splitlines()]
    assert len(rows) == data["relations"]
    return data, rows


def ns_per_query(record):
    return Fraction(record["loop_seconds"]) * 10**9 / record["queries"]


def main():
    print("seed,v1_ns,v2_ns,batch_ns,v1_v2_time,v2_batch_unit,v2_batch_count,"
          "v2_batch_time,batch_tail,rho_budget_ns")
    for seed in range(3):
        old, old_rows = observations("v1_chain", seed)
        new, new_rows = observations("v2_chain", seed)
        batch, batch_rows = observations("v2_batch", seed)
        assert old_rows == new_rows and old["queries"] == new["queries"]
        assert old["rank"] == new["rank"] and new_rows != batch_rows
        assert new["generated_targets"] == new["queries"]
        extra = batch["generated_targets"] - batch["queries"]
        assert 0 <= extra < batch["batch_width"]
        unit = ns_per_query(new) / ns_per_query(batch)
        count = Fraction(new["queries"], batch["queries"])
        elapsed = Fraction(new["loop_seconds"]) / Fraction(batch["loop_seconds"])
        assert unit * count == elapsed
        rho = json.loads(read(f"rho_seed{seed}", "audited.json"), parse_float=Decimal)
        budget = Fraction(rho["end_to_end_seconds"]) * 10**9 / batch["queries"]
        values = (ns_per_query(old), ns_per_query(new), ns_per_query(batch),
                  ns_per_query(old) / ns_per_query(new), unit, count, elapsed)
        print(seed, *(f"{float(v):.6f}" for v in values), extra, f"{float(budget):.6f}", sep=",")


def common_prefix():
    print("seed,queries,chain_seconds,batch_seconds,ratio,faster_intervals,total_intervals")
    for seed in range(3):
        elapsed = []
        for arm in ("v2_chain", "v2_batch"):
            log = read(f"{arm}_seed{seed}", "log").decode()
            checkpoints = re.findall(r"^queries (\d+), relations \d+, seconds ([\d.]+)", log, re.M)[:19]
            assert [int(q) for q, _ in checkpoints] == list(range(1_000_000, 19_000_001, 1_000_000))
            times = [Decimal(0)] + [Decimal(t) for _, t in checkpoints]
            elapsed.append([end-start for start, end in zip(times, times[1:])])
        chain, batch = elapsed
        # Allow 10 microseconds at each printed endpoint of an interval.
        tolerance = Decimal("0.000020")
        assert all(b > tolerance and a-tolerance > Decimal("1.22")*(b+tolerance)
                   for a, b in zip(chain, batch))
        ratio = sum(chain)/sum(batch)
        print(seed, 19_000_000, sum(chain), sum(batch), f"{ratio:.6f}",
              sum(a > b for a, b in zip(chain, batch)), len(chain), sep=",")


if __name__ == "__main__":
    main()
    print()
    common_prefix()
