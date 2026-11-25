"""Rebuild the four public reference tables, check their digests, and emit timings."""
import csv
import hashlib
import json
import random
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = "e18e2fc84821086c1609d28446b25f5ebbfa9784:experiments/prime-field-auxiliary-ic/snapshot/comparison/"
DIGESTS = {
    "auxiliary": {
        "full": "ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879",
        "compact": "2a3c6f7786994b29ae3fea65db93c07a4085cba8a79b8da608668df235a6b4d4",
    },
    "plain": {
        "full": "8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa",
        "compact": "62d0f1bddd578e7a6c96416b59ba16ba2d3945f68d4942a3c9e8a31cdfe7ccc9",
    },
}

def frozen(name):
    return subprocess.check_output(["git", "show", SOURCE + name], cwd=HERE)

def references(directory, basis):
    data = json.loads(frozen(f"field31/{basis}/public.json"))
    p = data["p"]
    points = data["factor_base_representatives"]
    if (p, data["a"], data["b"], len(points)) != (2**31-1, 2, 14, 500):
        raise ValueError("Unexpected public fixture")
    (directory / basis).write_text("".join(f"{x} {y}\n" for x, y in points))
    signed = [(x, sign_y) for x, y in points for sign_y in (y, -y % p)]
    entries = {}
    for i, (x, y) in enumerate(signed):
        for j in range(i, len(signed)):
            xx, yy = signed[j]
            if x == xx:
                if (y + yy) % p == 0:
                    continue
                slope = (3*x*x + 2) * pow(2*y, -1, p)
            else:
                slope = (yy-y) * pow(xx-x, -1, p)
            u = (slope*slope-x-xx) % p
            v = (slope*(x-u)-y) % p
            entries.setdefault(2*u + v%2, (i << 16) | j)
    ordered = sorted(entries.items())
    for layout, digest in DIGESTS[basis].items():
        records = ordered if layout == "full" else ((k//2, v) for k,v in ordered if k%2 == 0)
        blob = b"".join(struct.pack("<II", k, v) for k, v in records)
        if hashlib.sha256(blob).hexdigest() != digest:
            raise ValueError(f"Reference digest mismatch for {basis}/{layout}")
        (directory / f"{basis}-{layout}.bin").write_bytes(blob)

def replay(directory):
    if sys.byteorder != "little":
        raise ValueError("The native reference reader requires a little-endian host")
    (directory / "common.hpp").write_bytes(frozen("common.hpp"))
    for basis in DIGESTS:
        references(directory, basis)
    subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31", "-I", str(directory),
                    str(HERE / "build.cpp"), "-o", "build"], cwd=directory, check=True)
    blocks = [(basis, r) for basis in DIGESTS for r in range(24)]
    random.Random(112427).shuffle(blocks)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["basis", "round", "position", "layout", "build_ns"])
    for basis, r in blocks:
        order = ("full", "compact") if r%2 else ("compact", "full")
        for pos, layout in enumerate(order):
            ns = subprocess.check_output(["./build", basis, layout, f"{basis}-{layout}.bin"],
                                         cwd=directory, text=True)
            writer.writerow([basis, r, pos, layout, int(ns)])

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        replay(Path(tmp))
