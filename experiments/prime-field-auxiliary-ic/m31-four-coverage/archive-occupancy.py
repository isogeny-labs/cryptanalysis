"""Fixed-query iid reference for the three archived signed-pair counts.

ArchivePairSupport.lean counts 578 finite endpoints on this basis. The signed
pair labels modulo overall sign consist of 17 doubles and 2*C(17,2) pairs.
Every label therefore occupies two distinct group elements. In the reference
model, each query independently samples one of the q group elements uniformly,
and every hit is observed. The archived walks need not obey this model.
"""
from decimal import Decimal
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import re
import subprocess

COMMIT = "9a1d8a6cf4158197c06b0782f833d4626931ebff"
Q = 2147505293
LABELS = 289
CHECKPOINT = 19_000_000
SCALE = 10**80


def git_blob(path):
    return subprocess.check_output(
        ["git", "-C", str(Path(__file__).resolve().parent), "show", f"{COMMIT}:{path}"]
    )


def archived_counts():
    counts = []
    for seed in range(3):
        record = f"benchmarks/records/20261115T0646Z-prime31-retro-v2-batch-seed{seed}.json"
        manifest = json.loads(git_blob(record))
        entry, = [e for e in manifest["raw"] if e["path"].endswith(".log")]
        log = git_blob(entry["path"])
        if len(log) != entry["bytes"] or sha256(log).hexdigest() != entry["sha256"]:
            raise ValueError("archive log differs from manifest")
        count, = re.findall(rf"^queries {CHECKPOINT}, relations (\d+), seconds ", log.decode(), re.M)
        counts.append(int(count))
    return counts


def multiply(a, b):
    """Outward rounding for two nonnegative fixed-point intervals."""
    return a[0]*b[0]//SCALE, (a[1]*b[1] + SCALE-1)//SCALE


def probability_power(numerator, denominator, exponent):
    lo, rem = divmod(numerator*SCALE, denominator)
    base = lo, lo + bool(rem)
    result = SCALE, SCALE
    while exponent:
        if exponent & 1:
            result = multiply(result, base)
        base = multiply(base, base)
        exponent >>= 1
    return result


def cdf(limit, draws):
    """Sum exact occupancy masses up to limit using inclusion-exclusion.

    For a specified set of k labels, exclude draws outside that set, then
    require all k to be present. A permitted subset of size j contributes
    (1 - 2*(LABELS-j)/Q)^draws. Choose the k labels in C(LABELS,k) ways.
    """
    powers = [probability_power(Q-2*(LABELS-j), Q, draws) for j in range(limit+1)]
    lo = hi = 0
    for k in range(limit+1):
        for j in range(k+1):
            factor = (-1)**(k-j) * comb(LABELS,k) * comb(k,j)
            lower, upper = powers[j]
            if factor < 0:
                lower, upper = upper, lower
            lo += factor * lower
            hi += factor * upper
    return lo, hi


def show(name, interval):
    lo, hi = interval
    if not 0 <= lo <= hi <= SCALE or hi-lo > SCALE//10**12:
        raise ArithmeticError("insufficient interval precision")
    print(f"{name}: {Decimal(lo + hi) / (2*SCALE):.10f} (absolute error < 1e-10)")


if __name__ == "__main__":
    counts = archived_counts()
    print("checkpoint distinct rows:", counts)
    # The progress message precedes extraction and duplicate rejection for this query.
    draws = CHECKPOINT - 1
    show("P(distinct <= observed minimum)", cdf(min(counts), draws))
    left, right = cdf(max(counts)-1, draws)
    show("P(distinct >= observed maximum)", (SCALE-right, SCALE-left))
