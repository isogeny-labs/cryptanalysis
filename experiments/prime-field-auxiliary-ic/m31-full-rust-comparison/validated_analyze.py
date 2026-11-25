"""Check matched collector runs and report charged paired ratios."""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

here = Path(__file__).resolve().parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "validated-raw.csv"
rows = list(csv.DictReader(path.open()))
assert len(rows) == 96, len(rows)
paired = defaultdict(dict)
for row in rows:
    key = (row["basis"], row["seed"], row["repeat"])
    assert row["batch"] in {"checked", "assume_valid"}
    assert row["scalar"] == "123456789"
    assert row["batch"] not in paired[key]
    paired[key][row["batch"]] = row
assert len(paired) == 48, len(paired)
for pair in paired.values():
    assert set(pair) == {"checked", "assume_valid"}
    a, b = pair["checked"], pair["assume_valid"]
    for field in ("basis_sha256", "scalar", "trials", "relations", "entries"):
        assert a[field] == b[field], (field, a[field], b[field])

for basis in ("auxiliary", "plain"):
    group = [pair for (name, _, _), pair in paired.items() if name == basis]
    assert len(group) == 24
    for field in ("charged_wall_ns", "charged_cpu_ns", "rust_total_ns"):
        a = [int(pair["checked"][field]) / 1e6 for pair in group]
        b = [int(pair["assume_valid"][field]) / 1e6 for pair in group]
        ratios = [x / y for x, y in zip(a, b)]
        print(basis, field, "checked_median_ms", round(statistics.median(a), 3),
              "candidate_median_ms", round(statistics.median(b), 3),
              "paired_ratio", round(statistics.median(ratios), 4),
              "candidate_wins", sum(y < x for x, y in zip(a, b)), "/24")
