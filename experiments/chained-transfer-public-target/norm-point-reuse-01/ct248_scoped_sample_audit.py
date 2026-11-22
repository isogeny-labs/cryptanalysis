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
LIFETIME = "CT244_PRIMITIVE_TIMING "
SLOTS = ("C13_0_to_1", "C13_1_to_0", "C13_1_to_2", "C13_2_to_1",
         "C169_0_to_2", "C169_2_to_0", "D_target_norm")
ROUTES = ("direct_composite", "literal_sequential_Jacobian_maps",
          "strongest_retained_lift_chain")
# Pinned selected-vectors Rust test (blob bcd27773a7b179c3beeb3d5782a5de97a7df19f2),
# not a trust assertion about an unauthenticated native transcript.
SOURCE_SCOPE = ("actual selected source entries only; all setup/primitive work "
                "unpriced and complete primitive census still open; no measured speed advantage")
SCALARS = (0, 1, 2, 17, 12345, 2773072)  # ELL=2773073 in pinned original source
PIC_KEY_WORDS = 19  # PicClass.key().0: [u32;19]
CALL_FIELDS = (
    "external_packet_parse", "external_norm_and_geometry", "external_full_order",
    "infinity_halves", "two_torsion_halves", "generic_halving_factorization",
    "generic_ordinate", "explicit_half_check", "quadratic_source_phi",
    "correction_difference", "correction_dictionary_lookup",
    "matching_corrections_checked", "source_lift_addition",
    "degree13_elliptic_evaluation", "degree169_elliptic_evaluation",
    "norm_point_doubling", "quadratic_target_phi", "target_correction_addition",
    "final_actual_norm", "final_full_order", "inverse_full_group_scalar")
COMMON_CALLS = ("external_packet_parse", "external_norm_and_geometry",
                "external_full_order", "final_actual_norm", "final_full_order")



def nat(x, field):
    if type(x) is not int or x < 0:
        raise ValueError(f"{field}: must be a nonnegative JSON integer")
    return x


def exact(obj, keys, field):
    if type(obj) is not dict or set(obj) != set(keys):
        raise ValueError(f"{field}: unexpected keys or type")


def pic_key(value, field):
    if type(value) is not list or len(value) != PIC_KEY_WORDS:
        raise ValueError(f"{field}: expected exact 19-word PicClass key")
    for j, word in enumerate(value):
        if nat(word, f"{field}[{j}]") >= 2**32:
            raise ValueError(f"{field}[{j}]: outside u32")


def decode(raw):
    samples, vector_rows, lifetime_rows = [], [], []
    for line in raw.splitlines():
        if line.startswith(SAMPLE):
            samples.append(json.loads(line[len(SAMPLE):]))
        elif line.startswith(VECTORS):
            vector_rows.append(json.loads(line[len(VECTORS):]))
        elif line.startswith(LIFETIME):
            lifetime_rows.append(json.loads(line[len(LIFETIME):]))
    if len(samples) != 144 or len(vector_rows) != 1 or len(lifetime_rows) != 1:
        raise ValueError(f"CT249 requires 144 samples, one 48-vector and one lifetime: "
                         f"{len(samples)}/{len(vector_rows)}/{len(lifetime_rows)}")
    return samples, vector_rows[0], lifetime_rows[0]


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
    samples, v, lifetime = decode(raw)
    if type(v) is not dict or set(v) != {"all48", "scope"}:
        raise ValueError("original selected-vector envelope changed")
    if v["scope"] != SOURCE_SCOPE:
        raise ValueError("original source vector scope changed")
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
        scalar = nat(row["scalar_OUTSIDE_runtime"], "scalar")
        if scalar != SCALARS[(row_idx % 24) // 4]:
            raise ValueError(f"selected vector {row_idx}: scalar schedule changed")
        pic_key(row["input"], "input")
        pic_key(row["whole_outputs_equal"], "whole_outputs_equal")
        expected = expected_slots(from_side, to_side, arm)
        if c != expected:
            raise ValueError(f"sample {i}: directed primitive call pattern differs")
        source = row[ROUTES[arm]]
        exact(source, CALL_FIELDS, "original native Calls")
        for field in CALL_FIELDS:
            nat(source[field], f"original Calls.{field}")
        for field in COMMON_CALLS:
            if source[field] != 1:
                raise ValueError(f"selected source {field}: common full route charge changed")
        for field in ("quadratic_source_phi", "quadratic_target_phi"):
            if source[field] != (2 if arm == 1 else 1):
                raise ValueError(f"selected route {arm}: {field} changed")
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
    # Reconcile the real native Runtime drop record, not a modeled C13/C169 price.
    # This is a necessary producer-internal consistency check, never an
    # independent timing replay or complete route cost.
    exact(lifetime, ("schema", "scope", "slots", "calls", "scoped_samples_emitted",
                     "elapsed_ns", "measured_complete_solve", "pcc"), "lifetime")
    if lifetime["schema"] != "ct244-primitives-v1":
        raise ValueError("CT249 native lifetime schema changed")
    if lifetime["scope"] != "runtime_lifetime_after_constructor; eval-only; uncalibrated":
        raise ValueError("CT249 lifetime clock scope changed")
    if type(lifetime["slots"]) is not list or tuple(lifetime["slots"]) != SLOTS:
        raise ValueError("CT249 directed lifetime slots changed")
    if lifetime["measured_complete_solve"] is not False or lifetime["pcc"] != "unverified":
        raise ValueError("CT249 lifetime record misrepresents standing")
    if nat(lifetime["scoped_samples_emitted"], "lifetime emitted") != 144:
        raise ValueError("CT249 lifetime record omitted or added epochs")
    total_calls, total_ns = lifetime["calls"], lifetime["elapsed_ns"]
    if type(total_calls) is not list or type(total_ns) is not list or (
            len(total_calls), len(total_ns)) != (7, 7):
        raise ValueError("CT249 lifetime must contain two seven-slot vectors")
    scoped_calls = [sum(x["calls"][j] for x in samples) for j in range(7)]
    scoped_ns = [sum(x["elapsed_ns"][j] for x in samples) for j in range(7)]
    extra_calls, extra_ns = [], []
    for j in range(7):
        n_calls = nat(total_calls[j], f"lifetime calls[{j}]")
        n_ns = nat(total_ns[j], f"lifetime elapsed_ns[{j}]")
        if n_calls == 0 and n_ns:
            raise ValueError(f"CT249 nonzero elapsed time in uncalled lifetime slot {j}")
        if n_calls < scoped_calls[j] or n_ns < scoped_ns[j]:
            raise ValueError(f"CT249 scoped epoch totals exceed lifetime in slot {j}")
        extra_calls.append(n_calls - scoped_calls[j])
        extra_ns.append(n_ns - scoped_ns[j])
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
        "lifetime_clock_reconciled": True,
        "unscoped_lifetime_calls": extra_calls,
        "unscoped_lifetime_elapsed_ns": extra_ns,
        "native_timing_reproduced_by_independent_runner": False,
        "complete_single_target_cost": None,
        "pcc": "unverified",
    }


def synthetic():
    rows, samples = [], []
    for i in range(48):
        f, t = ((0, 2) if i < 24 else (2, 0))
        row = {"from": f, "to": t, "scalar_OUTSIDE_runtime": SCALARS[(i%24)//4],
               "sector": i % 4, "input": [i] + [0]*18,
               "whole_outputs_equal": [i] + [0]*18}
        for arm, key in enumerate(ROUTES):
            c = expected_slots(f, t, arm)
            counters = {field: 0 for field in CALL_FIELDS}
            counters.update({"degree13_elliptic_evaluation": sum(c[:4]),
                             "degree169_elliptic_evaluation": sum(c[4:6]),
                             "norm_point_doubling": c[6],
                             "quadratic_source_phi": 2 if arm == 1 else 1,
                             "quadratic_target_phi": 2 if arm == 1 else 1})
            for field in COMMON_CALLS:
                counters[field] = 1
            row[key] = counters
            samples.append({"schema": "ct248-scoped-primitives-v1", "sequence": i*3+arm,
                "scope": "reset_calls_to_calls; eval_and_padd_only",
                "calls": c, "elapsed_ns": [x*1000 for x in c],
                "source_C13": sum(c[:4]), "source_C169": sum(c[4:6]),
                "source_D": c[6], "measured_complete_solve": False, "pcc": "unverified"})
        rows.append(row)
    return samples, {"all48": rows, "scope": SOURCE_SCOPE}  # data are synthetic in self-test only


def synthetic_lifetime(samples, extra_calls=None, extra_ns=None):
    if extra_calls is None:
        extra_calls = [1] * 7  # Explicit nonzero outside-epoch work.
    if extra_ns is None:
        extra_ns = [100] * 7
    return {"schema": "ct244-primitives-v1",
            "scope": "runtime_lifetime_after_constructor; eval-only; uncalibrated",
            "slots": list(SLOTS),
            "calls": [sum(x["calls"][j] for x in samples) + extra_calls[j]
                      for j in range(7)],
            "scoped_samples_emitted": len(samples),
            "elapsed_ns": [sum(x["elapsed_ns"][j] for x in samples) + extra_ns[j]
                           for j in range(7)],
            "measured_complete_solve": False, "pcc": "unverified"}


def encode(samples, vectors, lifetime):
    return "\n".join([SAMPLE + json.dumps(x, sort_keys=True) for x in samples] +
                     [VECTORS + json.dumps(vectors, sort_keys=True),
                      LIFETIME + json.dumps(lifetime, sort_keys=True)]) + "\n"


def self_test():
    samples, vec = synthetic()
    lifetime = synthetic_lifetime(samples)
    raw = encode(samples, vec, lifetime)
    normal = audit(raw)
    if (normal["scoped_samples"], normal["unscoped_lifetime_calls"],
            normal["unscoped_lifetime_elapsed_ns"]) != (144, [1]*7, [100]*7):
        raise AssertionError("CT249 synthetic positive with unscoped work failed")
    zero = audit(encode(samples, vec, synthetic_lifetime(samples, [0]*7, [0]*7)))
    if zero["unscoped_lifetime_calls"] != [0]*7 or zero["unscoped_lifetime_elapsed_ns"] != [0]*7:
        raise AssertionError("CT249 zero-unscoped control failed")
    tests = []
    def mutation(fn):
        a, b, c = copy.deepcopy(samples), copy.deepcopy(vec), copy.deepcopy(lifetime)
        fn(a, b, c)
        tests.append(encode(a, b, c))
    mutation(lambda a,b,c: a.pop())
    mutation(lambda a,b,c: a.append(copy.deepcopy(a[0])))
    mutation(lambda a,b,c: a[1].update(sequence=0))
    mutation(lambda a,b,c: a[0]["calls"].__setitem__(4, True))
    mutation(lambda a,b,c: a[0]["calls"].__setitem__(4, -1))
    mutation(lambda a,b,c: a[0]["calls"].pop())
    mutation(lambda a,b,c: a[0]["elapsed_ns"].__setitem__(0, 9))
    mutation(lambda a,b,c: a[0].update(source_C169=0))
    mutation(lambda a,b,c: a[1]["calls"].__setitem__(0, 3))
    mutation(lambda a,b,c: a[1].update(schema="ct248-unknown"))
    mutation(lambda a,b,c: a[1].update(measured_complete_solve=True))
    mutation(lambda a,b,c: b["all48"][0].update(to=1))
    mutation(lambda a,b,c: b["all48"][0]["direct_composite"].update(norm_point_doubling=2))
    mutation(lambda a,b,c: b["all48"][0].update(sector=True))
    mutation(lambda a,b,c: b["all48"].pop())
    mutation(lambda a,b,c: b.update(scope=False, all48=[]))
    tests.append(raw + VECTORS + json.dumps(vec) + "\n")
    tests.append("\n".join(line for line in raw.splitlines()
                           if not line.startswith(LIFETIME)) + "\n")
    tests.append(raw + LIFETIME + json.dumps(lifetime) + "\n")
    mutation(lambda a,b,c: c["calls"].__setitem__(4, 0))
    mutation(lambda a,b,c: c["elapsed_ns"].__setitem__(0, 0))
    mutation(lambda a,b,c: c["slots"].__setitem__(0, "C13_WRONG"))
    mutation(lambda a,b,c: c.update(scope="wrong"))
    mutation(lambda a,b,c: c.update(schema="ct249-unknown"))
    mutation(lambda a,b,c: c.update(scoped_samples_emitted=143))
    mutation(lambda a,b,c: c.update(measured_complete_solve=True))
    mutation(lambda a,b,c: c.update(pcc="verified"))
    mutation(lambda a,b,c: c["calls"].__setitem__(6, False))
    mutation(lambda a,b,c: c["elapsed_ns"].__setitem__(1, True))
    mutation(lambda a,b,c: c["elapsed_ns"].pop())
    mutation(lambda a,b,c: c.update(unexpected_key=1))
    # CT299: previously accepted transcript mutations, now rejected.
    mutation(lambda a,b,c: b["all48"][0].update(scalar_OUTSIDE_runtime=999))
    mutation(lambda a,b,c: b.update(scope="synthetic; not a native source record"))
    mutation(lambda a,b,c: b["all48"][0]["input"].pop())
    mutation(lambda a,b,c: b["all48"][0]["whole_outputs_equal"].__setitem__(0, True))
    mutation(lambda a,b,c: b["all48"][0]["input"].__setitem__(1, 2**32))
    mutation(lambda a,b,c: b["all48"][0][ROUTES[0]].update(external_packet_parse=0))
    mutation(lambda a,b,c: b["all48"][0][ROUTES[0]].update(quadratic_source_phi=0))
    mutation(lambda a,b,c: b["all48"][0][ROUTES[0]].update(external_full_order=False))
    mutation(lambda a,b,c: b["all48"][0][ROUTES[0]].update(unexpected_counter=1))
    for i, test in enumerate(tests):
        try:
            audit(test)
        except (ValueError, TypeError, KeyError):
            continue
        raise AssertionError(f"CT248 corruption {i} escaped fail-closed audit")
    print(f"CT299_AUDITOR_SELFTEST_PASS {len(tests)} mutations and two synthetic positive controls; no native run or cost")


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
