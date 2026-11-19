#!/usr/bin/env python3
"""CT248: fail-closed audit of 144 arm-local primitive samples and 48 vectors.

Only validates original unfiltered native stdout/stderr combined into one raw
log. Synthetic --self-test does not produce a performance measurement.
"""
import argparse
import copy
import hashlib
import json
import statistics
from pathlib import Path

SAMPLE = "CT248_PRIMITIVE_SAMPLE "
VECTORS = "N4_FIXED_CHAIN_SELECTED_CALL_VECTORS "
ROUTES = ("direct_composite", "literal_sequential_Jacobian_maps",
          "strongest_retained_lift_chain")


def nat(x, field):
    if type(x) is not int or x < 0:
        raise ValueError(f"{field}: must be a nonnegative JSON integer")
    return x


def exact(obj, keys, field):
    if type(obj) is not dict or set(obj) != set(keys):
        raise ValueError(f"{field}: unexpected keys or type")


def decode(raw):
    samples, vector_rows = [], []
    for line in raw.splitlines():
        if line.startswith(SAMPLE):
            samples.append(json.loads(line[len(SAMPLE):]))
        elif line.startswith(VECTORS):
            vector_rows.append(json.loads(line[len(VECTORS):]))
    if len(samples) != 144 or len(vector_rows) != 1:
        raise ValueError(f"CT248 requires 144 samples and one 48-vector source: "
                         f"{len(samples)}/{len(vector_rows)}")
    return samples, vector_rows[0]


def expected_slots(from_side, to_side, arm):
    if (from_side, to_side) == (0, 2):
        direction = [0, 2]
        direct = 4
    elif (from_side, to_side) == (2, 0):
        direction = [3, 1]
        direct = 5
    else:
        raise ValueError("CT248 selected source direction changed")
    counts = [0] * 7
    if arm == 0:
        counts[direct] = 1
        counts[6] = 1
    elif arm == 1:
        for slot in direction:
            counts[slot] = 2
        counts[6] = 2
    else:
        for slot in direction:
            counts[slot] = 1
        counts[6] = 1
    return counts


def audit(raw):
    samples, v = decode(raw)
    if type(v) is not dict or set(v) != {"all48", "scope"}:
        raise ValueError("original selected-vector envelope changed")
    rows = v["all48"]
    if type(rows) is not list or len(rows) != 48:
        raise ValueError("original selected-vector population is not 48")
    samples_by_row = []
    for i, sample in enumerate(samples):
        exact(sample, ("schema", "sequence", "scope", "calls",
                       "elapsed_ns", "source_C13", "source_C169",
                       "source_D", "measured_complete_solve", "pcc"),
              "sample")
        if sample["schema"] != "ct248-scoped-primitives-v1":
            raise ValueError("sample schema differs")
        if sample["scope"] != "reset_calls_to_calls; eval_and_padd_only":
            raise ValueError("sample epoch scope differs")
        if sample["measured_complete_solve"] is not False or sample["pcc"] != "unverified":
            raise ValueError("sample misrepresents standing")
        if nat(sample["sequence"], "sequence") != i:
            raise ValueError("sample missing, duplicated, or out of order")
        c, ns = sample["calls"], sample["elapsed_ns"]
        if type(c) is not list or type(ns) is not list or len(c) != 7 or len(ns) != 7:
            raise ValueError("seven original slots required")
        for j in range(7):
            nat(c[j], f"calls[{j}]")
            nat(ns[j], f"elapsed_ns[{j}]")
            if c[j] == 0 and ns[j] != 0:
                raise ValueError("nonzero time in uncalled slot")
        if sum(c[:4]) != nat(sample["source_C13"], "source C13"):
            raise ValueError("C13 source vs physical map count mismatch")
        if sum(c[4:6]) != nat(sample["source_C169"], "source C169"):
            raise ValueError("C169 source vs physical map count mismatch")
        if c[6] != nat(sample["source_D"], "source D"):
            raise ValueError("D source vs physical double count mismatch")

        row_idx, arm = divmod(i, 3)
        row = rows[row_idx]
        if type(row) is not dict or set(row) != {
            "from", "to", "scalar_OUTSIDE_runtime", "sector", "input",
            "direct_composite", "literal_sequential_Jacobian_maps",
            "strongest_retained_lift_chain", "whole_outputs_equal"}:
            raise ValueError("selected-vector row keys changed")
        from_side, to_side = row["from"], row["to"]
        if type(from_side) is not int or type(to_side) is not int:
            raise ValueError("selected direction not typed integers")
        if (from_side, to_side) != ((0, 2) if row_idx < 24 else (2, 0)):
            raise ValueError("selected direction/order changed")
        if nat(row["sector"], "sector") != row_idx % 4:
            raise ValueError("selected sector/order changed")
        nat(row["scalar_OUTSIDE_runtime"], "scalar")
        if type(row["input"]) is not list or type(row["whole_outputs_equal"]) is not list:
            raise ValueError("selected source/target class type changed")
        expected = expected_slots(from_side, to_side, arm)
        if c != expected:
            raise ValueError(f"sample {i}: directed primitive call pattern differs")
        source = row[ROUTES[arm]]
        if type(source) is not dict:
            raise ValueError("original route counters missing")
        for field, claimed in (
                ("degree13_elliptic_evaluation", sample["source_C13"]),
                ("degree169_elliptic_evaluation", sample["source_C169"]),
                ("norm_point_doubling", sample["source_D"])):
            if field not in source or nat(source[field], field) != claimed:
                raise ValueError(f"sample {i}: selected source {field} differs")
        if arm == 2:
            samples_by_row.append(samples[i-2:i+1])

    if len(samples_by_row) != 48:
        raise ValueError("48 complete selected arm triplets required")
    # These sums are measured expressions only: NOT elapsed whole routes/solver.
    paired_deltas = []
    for direct, literal, retained in samples_by_row:
        d, l, r = (sum(x["elapsed_ns"]) for x in (direct, literal, retained))
        paired_deltas.append(d - r)
    return {
        "schema": "ct248-route-local-audit-v1",
        "log_sha256": hashlib.sha256(raw.encode("utf8")).hexdigest(),
        "selected_vectors": len(rows),
        "scoped_samples": len(samples),
        "median_direct_minus_retained_eval_and_d_ns": statistics.median(paired_deltas),
        "strict_counter_parity": True,
        "native_timing_reproduced_by_independent_runner": False,
        "complete_single_target_cost": None,
        "pcc": "unverified",
    }


def synthetic():
    rows, samples = [], []
    for i in range(48):
        f, t = ((0, 2) if i < 24 else (2, 0))
        row = {"from": f, "to": t, "scalar_OUTSIDE_runtime": (0,1,2,17,12345,99999)[(i%24)//4],
               "sector": i % 4, "input": [i], "whole_outputs_equal": [i]}
        for arm, key in enumerate(ROUTES):
            c = expected_slots(f, t, arm)
            row[key] = {"degree13_elliptic_evaluation": sum(c[:4]),
                        "degree169_elliptic_evaluation": sum(c[4:6]),
                        "norm_point_doubling": c[6]}
            samples.append({"schema": "ct248-scoped-primitives-v1", "sequence": i*3+arm,
                "scope": "reset_calls_to_calls; eval_and_padd_only",
                "calls": c, "elapsed_ns": [x*1000 for x in c],
                "source_C13": sum(c[:4]), "source_C169": sum(c[4:6]),
                "source_D": c[6], "measured_complete_solve": False, "pcc": "unverified"})
        rows.append(row)
    return samples, {"all48": rows, "scope": "synthetic; not a measurement"}


def encode(samples, vectors):
    return "\n".join([SAMPLE + json.dumps(x, sort_keys=True) for x in samples] +
                     [VECTORS + json.dumps(vectors, sort_keys=True)]) + "\n"


def self_test():
    samples, vec = synthetic()
    raw = encode(samples, vec)
    assert audit(raw)["scoped_samples"] == 144
    tests = []
    def mutation(fn):
        a, b = copy.deepcopy(samples), copy.deepcopy(vec)
        fn(a, b)
        tests.append(encode(a, b))
    mutation(lambda a,b: a.pop())
    mutation(lambda a,b: a.append(copy.deepcopy(a[0])))
    mutation(lambda a,b: a[1].update(sequence=0))
    mutation(lambda a,b: a[0]["calls"].__setitem__(4, True))
    mutation(lambda a,b: a[0]["calls"].__setitem__(4, -1))
    mutation(lambda a,b: a[0]["calls"].pop())
    mutation(lambda a,b: a[0]["elapsed_ns"].__setitem__(0, 9))
    mutation(lambda a,b: a[0].update(source_C169=0))
    mutation(lambda a,b: a[1]["calls"].__setitem__(0, 3))
    mutation(lambda a,b: a[1].update(schema="ct248-unknown"))
    mutation(lambda a,b: a[1].update(measured_complete_solve=True))
    mutation(lambda a,b: b["all48"][0].update(to=1))
    mutation(lambda a,b: b["all48"][0]["direct_composite"].update(norm_point_doubling=2))
    mutation(lambda a,b: b["all48"][0].update(sector=True))
    mutation(lambda a,b: b["all48"].pop())
    mutation(lambda a,b: b.update(scope=False, all48=[]))
    tests.append(raw + VECTORS + json.dumps(vec) + "\n")
    for i, test in enumerate(tests):
        try:
            audit(test)
        except (ValueError, TypeError, KeyError):
            continue
        raise AssertionError(f"CT248 corruption {i} escaped fail-closed audit")
    print(f"CT248_AUDITOR_SELFTEST_PASS {len(tests)} mutations; no native run or cost")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test", action="store_true")
    g.add_argument("--log", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
    else:
        print(json.dumps(audit(args.log.read_text(encoding="utf8")), sort_keys=True))


if __name__ == "__main__":
    main()
