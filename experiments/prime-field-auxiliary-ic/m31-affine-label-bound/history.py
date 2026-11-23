"""Exact optimal accuracy for each suffix length of the archived M31 cyclic census."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
P = 2**31 - 1


def main():
    with (ROOT / "history12.csv").open() as f:
        data = list(csv.DictReader(f))
    assert len(data) == 8192
    full = []
    for i, row in enumerate(data):
        assert (int(row["history"]), int(row["destination"])) == divmod(i, 2)
        full.append(int(row["coordinates"]))
    assert min(full) > 0 and sum(full) == P
    # Every window has the same count whether reached from its left or right.
    for h in range(4096):
        assert full[h]+full[h+4096] == full[2*h]+full[2*h+1]
    print("history,best_correct,best_fraction,smallest_cell")
    for k in range(13):
        width = 2 << k
        counts = [sum(full[i::width]) for i in range(width)]
        if k == 1:
            with (ROOT / "translation.csv").open() as f:
                assert counts == [int(r["coordinates"]) for r in csv.DictReader(f)]
        correct = sum(max(a,b) for a,b in zip(counts[::2],counts[1::2]))
        print(f"{k},{correct},{correct/P:.10f},{min(counts)}")


if __name__ == "__main__":
    main()
