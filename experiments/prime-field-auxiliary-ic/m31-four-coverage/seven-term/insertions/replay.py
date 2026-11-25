"""Rebuild the frozen census and check every insertion in reverse basis order."""
import csv
import hashlib
import io
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
COMMIT = "2c32697f49c8bc4f05820929823865eb02ca4dc7"
PREFIX = "experiments/prime-field-auxiliary-ic/"


def archived(path):
    return subprocess.check_output(["git", "show", f"{COMMIT}:{PREFIX}{path}"], cwd=HERE)


def replay(binary):
    def census(xs, *args):
        data = "".join(f"{x}\n" for x in reversed(xs))
        return subprocess.check_output([binary, *args], input=data, text=True)

    def overlap(xs):
        rows = list(csv.DictReader(io.StringIO(census(xs))))
        three, four = rows[2:]
        return int(three["exact_finite"]) + int(four["exact_finite"]) - int(four["upto_finite"])

    raw = archived("m31-basis-mask/coordinates.txt")
    if hashlib.sha256(raw).hexdigest() != "e7ddb831369de7724ca977022707d844512ccfe0191cb2c5daf5a22ad84a6203":
        raise ValueError("Frozen basis digest mismatch")
    xs = list(map(int, raw.splitlines()))
    with (HERE / "counts.csv").open() as stream:
        records = list(csv.DictReader(stream))
    outside = {int(r["x"]) for r in records}
    core = [x for x in xs if x not in outside]
    if (len(xs), len(core), len(records), len(outside)) != (195, 74, 121, 121):
        raise ValueError("Basis partition mismatch")
    if [int(census(b, "simple-five")) for b in (core, xs)] != [20, 20]:
        raise ValueError("Five-label class count mismatch")
    initial = overlap(core)
    if initial != 61056:
        raise ValueError("Core overlap mismatch")
    for record in records:
        i, x = int(record["index"]), int(record["x"])
        if not 0 <= i < len(xs) or xs[i] != x:
            raise ValueError(f"Coordinate mismatch at {i}")
        observed = overlap(core + [x])
        excess = observed - initial - 2 * 10 * 2 * 20
        if (observed, excess) != (int(record["overlap"]), int(record["excess_after_800"])) or excess <= 0:
            raise ValueError(f"Insertion mismatch at {i}")
    print("Verified all 121 insertions in reverse order.")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "census.cpp"
        binary = Path(tmp) / "census"
        source.write_bytes(archived("m31-four-coverage/census.cpp"))
        subprocess.run(["c++", "-std=c++17", "-O3", str(source), "-o", str(binary)], check=True)
        replay(binary)
