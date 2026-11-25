"""Emit exact branch masks for the existing 32-fiber smoothness panel."""
import csv
from functools import cache
from pathlib import Path
import sys

from branch_diagram import coordinates


def best(masks):
    return sum((sum(m >> bit & 1 for m in masks) * 2 > len(masks)) << bit for bit in range(128))


def errors(mask, others):
    return sum((mask ^ m).bit_count() for m in others)


if __name__ == "__main__":
    scope = Path(__file__).resolve().parent
    with (scope / "torus7-smooth.csv").open() as source:
        rows = [r for r in csv.DictReader(source) if r["bound"] == "1024"]
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["odd_power", "terminal", "mask"])
    masks = []
    for row in rows:
        terminal, labels = coordinates(int(row["terminal"]))
        mask = sum(label << key for key, _, label, _ in labels)
        assert mask.bit_count() == int(row["base_smooth"])+int(row["base_other"])
        masks.append(mask)
        writer.writerow([row["odd_power"], terminal, mask])
    assert masks[0] == 0x5ec55aed5ec7a5051ebd2a65e6d923ee
    assert len(set(masks)) == len(masks) == 32
    pooled = errors(best(masks), masks)
    fitted = best(masks[:16])
    print("pooled lower bound", pooled, "archived on 31", errors(masks[0], masks[1:]),
          "first 16 on last 16", errors(fitted, masks[16:]),
          "constant zero on last 16", errors(0,masks[16:]),
          "constant one on last 16", errors((1<<128)-1,masks[16:]), file=sys.stderr)
    varying = sum(0 < sum(m >> i & 1 for m in masks) < len(masks) for i in range(128))
    print("keys with both labels", varying, file=sys.stderr)

    # Each pair uses the union of its two masks to keep every base point.
    weights = [[128-(a|b).bit_count() for b in masks[16:]] for a in masks[:16]]

    @cache
    def best_pair_score(used):
        i = used.bit_count()
        if i == 16:
            return 0
        return max(weight + best_pair_score(used | (1 << j))
                   for j, weight in enumerate(weights[i]) if not (used >> j & 1))

    print("maximum safe rejects with cross-half pairing", 2*best_pair_score(0),
          "identity pairing", 2*sum(row[j] for j, row in enumerate(weights)), file=sys.stderr)
