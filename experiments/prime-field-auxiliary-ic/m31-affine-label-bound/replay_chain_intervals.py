"""From a mathlib environment: lake env python3 /absolute/path/to/replay_chain_intervals.py."""
from decimal import Decimal
from pathlib import Path
import re
import subprocess

REVISION = "f70acb81dfc81f77b940220b95cd33558a615aaa"
DIRECTORY = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0"
HERE = Path(__file__).resolve().parent


def checkpoints(arm, seed):
    path = f"{DIRECTORY}/{arm}_seed{seed}.log"
    log = subprocess.check_output(["git", "show", f"{REVISION}:{path}"], cwd=HERE, text=True)
    counts = []
    micros = [0]
    for line in log.splitlines():
        if line.startswith("queries "):
            match = re.fullmatch(r"queries (\d+), relations (\d+), seconds ([\d.]+)", line)
            if match is None:
                raise ValueError(f"Unexpected checkpoint in {path}: {line}")
            query, relations, seconds = match.groups()
            elapsed = Decimal(seconds) * 1_000_000
            if elapsed != int(elapsed) or not 0 < elapsed < 100_000_000:
                raise ValueError(f"Unexpected timestamp in {path}: {seconds}")
            counts.append((int(query), int(relations)))
            micros.append(int(elapsed))
    return counts, micros


def main():
    datasets = []
    for seed, length in enumerate([36, 60, 41]):
        counts, first = checkpoints("v1_chain", seed)
        other_counts, second = checkpoints("v2_chain", seed)
        expected = range(1_000_000, (length + 1) * 1_000_000, 1_000_000)
        if counts != other_counts or [q for q, _ in counts] != list(expected):
            raise ValueError(f"Unmatched checkpoints for seed {seed}")
        datasets.append("[" + ",".join(f"({a},{b})" for a, b in zip(first, second)) + "]")
    source = "import Mathlib\ndef endpoints : List (List (Nat × Nat)) := [" + ",".join(datasets) + "]\n"
    source += """
-- Durations are in microseconds. Six significant digits below 100 s give
-- at most 50 us rounding error per endpoint, hence 100 us per interval.
def valid (p q : Nat × Nat) : Bool := decide
  (p.1 + 100 < q.1 ∧ p.2 + 100 < q.2 ∧
   1194 * (q.2 - p.2 + 100) < 1000 * (q.1 - p.1 - 100))
example : endpoints.map List.length = [37,61,42] := by decide
example : endpoints.all (fun xs => (xs.zipWith valid xs.tail).all id) = true := by native_decide
theorem intervalRatio (a b x y : ℝ) (lo : a-100 ≤ x) (hi : y ≤ b+100)
    (pos : 0 < y) (cert : 1194*(b+100) < 1000*(a-100)) :
    1.194 < x/y := by apply (lt_div_iff₀ pos).mpr; linarith
"""
    subprocess.run(["lean", "--stdin"], input=source, text=True, check=True)
    print("Lean verified all 137 archived v1/v2 chain interval inequalities.")


if __name__ == "__main__":
    main()
