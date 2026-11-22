#!/usr/bin/env python3
"""CT300: source-only regression against the exact published 48 real vector rows.

The selected vector rows are genuine frozen *producer* evidence. The 144 timing
samples constructed here are synthetic zero-nanosecond controls: this script
makes no claim of native timing, full cold solve, independent arithmetic, or PCC.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import ct248_scoped_sample_audit as auditor

FROZEN_GIT_BLOB = "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3"
FIXED_CHAIN_ELL = 2_771_711
EXPECTED_SCALARS = (0, 1, 2, 17, 12345, FIXED_CHAIN_ELL - 1)
OLD_NORM = "transported_norm_doubling"
NEW_NORM = "norm_point_doubling"


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + bytes((0,)) + data).hexdigest()


def load_frozen(data):
    """Refuse any altered fixture byte, even if all JSON fields still parse."""
    observed = git_blob_sha(data)
    if observed != FROZEN_GIT_BLOB:
        raise ValueError("CT300 original 48-vector fixture Git blob mismatch: " + observed)
    doc = json.loads(data.decode("utf-8"),
                     parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    if type(doc) is not dict or set(doc) != {"all48", "scope"}:
        raise ValueError("original selected-vector envelope differs")
    if doc["scope"] != auditor.SOURCE_SCOPE:
        raise ValueError("original scope differs")
    if type(doc["all48"]) is not list or len(doc["all48"]) != 48:
        raise ValueError("original 48 vectors missing")
    return doc



def typed_equal(a, b):
    """No bool-as-int or float-as-int source-record aliasing."""
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(typed_equal(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(typed_equal(x, y) for x, y in zip(a, b))
    return a == b


def normalize_frozen_native_vectors(doc):
    """Map ONLY the archived counter name to CT125/CT244's native name."""
    work = copy.deepcopy(doc)
    for row in work["all48"]:
        for route in auditor.ROUTES:
            old = row[route]
            if type(old) is not dict or OLD_NORM not in old or NEW_NORM in old:
                raise ValueError("CT301 frozen Calls schema differs")
            old[NEW_NORM] = old.pop(OLD_NORM)
            if set(old) != set(auditor.CALL_FIELDS):
                raise ValueError("CT301 original Calls counters differ")
    return work


def bind_transcript_to_frozen(raw_log, frozen_bytes):
    """Require complete *value* parity with the exact original 48-row source.

    This source-only integrity check does not independently verify arithmetic,
    clocks, process provenance, or physical execution.
    """
    frozen = load_frozen(frozen_bytes)  # byte-level pinned Git-object check
    expected = normalize_frozen_native_vectors(frozen)
    _, native_vectors, _ = auditor.decode(raw_log)
    if not typed_equal(native_vectors, expected):
        raise ValueError("CT301 native selected vectors differ from pinned authentic 48-row source")
    return True


def build_mock_transcript(doc):
    """Preserve every frozen class key; adapt only the old/new norm counter name."""
    if auditor.SCALARS != EXPECTED_SCALARS:
        raise ValueError("CT300 auditor scalar schedule differs from pinned fixed-chain source")
    work = copy.deepcopy(doc)
    samples = []
    for i, row in enumerate(work["all48"]):
        if (type(row) is not dict or type(row.get("scalar_OUTSIDE_runtime")) is not int
                or row["scalar_OUTSIDE_runtime"] != EXPECTED_SCALARS[(i % 24) // 4]):
            raise ValueError("CT300 authentic selected scalar differs")
        if (row.get("from"), row.get("to")) != ((0, 2) if i < 24 else (2, 0)):
            raise ValueError("CT300 authentic direction differs")
        if type(row.get("sector")) is not int or row["sector"] != i % 4:
            raise ValueError("CT300 authentic cofactor sector differs")
        for arm, route in enumerate(auditor.ROUTES):
            original = row[route]
            if type(original) is not dict or OLD_NORM not in original or NEW_NORM in original:
                raise ValueError("CT300 genuine original counter schema differs")
            c = original.copy()
            c[NEW_NORM] = c.pop(OLD_NORM)
            if set(c) != set(auditor.CALL_FIELDS):
                raise ValueError("CT300 original counter dictionary is incomplete or changed")
            row[route] = c
            slots = auditor.expected_slots(row["from"], row["to"], arm)
            samples.append({
                "schema": "ct248-scoped-primitives-v1",
                "sequence": i * 3 + arm,
                "scope": "reset_calls_to_calls; eval_and_padd_only",
                "calls": slots,
                "elapsed_ns": [0] * 7,  # SYNTHETIC; never attribute to native timing.
                "source_C13": sum(slots[:4]),
                "source_C169": sum(slots[4:6]),
                "source_D": slots[6],
                "measured_complete_solve": False,
                "pcc": "unverified",
            })
    lifetime = auditor.synthetic_lifetime(samples, [0] * 7, [0] * 7)
    return auditor.encode(samples, work, lifetime)


def expect_reject(fn, label):
    try:
        fn()
    except (ValueError, TypeError, KeyError):
        return
    raise RuntimeError("CT300 negative control passed unexpectedly: " + label)


def run(raw):
    document = load_frozen(raw)
    transcript = build_mock_transcript(document)
    checked = auditor.audit(transcript)
    bind_transcript_to_frozen(transcript, raw)  # CT301 positive: genuine source, synthetic clocks
    if checked["selected_vectors"] != 48 or checked["scoped_samples"] != 144:
        raise RuntimeError("CT300 authentic selected program was not admitted")
    if checked["complete_single_target_cost"] is not None:
        raise RuntimeError("CT300 synthetic clock became a complete-solve claim")

    # The CT299 hardcoded wrong order MUST fail the actual fixture.
    original = auditor.SCALARS
    try:
        auditor.SCALARS = (0, 1, 2, 17, 12345, 2_773_072)
        expect_reject(lambda: build_mock_transcript(document), "wrong original-prime scalar")
    finally:
        auditor.SCALARS = original

    # Same-shaped real key mutation is not detected by the structural audit,
    # but an altered original fixture is rejected by the pinned Git blob.
    altered = copy.deepcopy(document)
    first = altered["all48"][0]["input"]
    first[3] = (first[3] + 1) % (2 ** 32)
    expect_reject(lambda: load_frozen(json.dumps(altered).encode("utf-8")),
                  "same-shape modified authentic class key")
    expect_reject(lambda: load_frozen(raw + b" "), "byte-level fixture alteration")
    expect_reject(lambda: load_frozen(raw[:-1]), "truncated fixture")

    # The already-extracted authentic program can still be checked for source
    # counter tampering after normalization (with no fake clock cost).
    bad_doc = copy.deepcopy(document)
    bad_doc["all48"][0]["direct_composite"]["external_full_order"] = 0
    expect_reject(lambda: auditor.audit(build_mock_transcript(bad_doc)),
                  "tampered full-route source counter")

    # CT301: the old structural auditor accepts altered 19-word values or
    # unpriced counters; source-bound native admission must reject all three.
    samples, original_vectors, lifetime = auditor.decode(transcript)
    def forged(mutator):
        vectors = copy.deepcopy(original_vectors)
        mutator(vectors)
        return auditor.encode(samples, vectors, lifetime)
    def flip_input(vectors):
        key = vectors["all48"][0]["input"]
        key[3] = (key[3] + 1) % (2 ** 32)
    def flip_output(vectors):
        key = vectors["all48"][7]["whole_outputs_equal"]
        key[4] = (key[4] + 1) % (2 ** 32)
    def flip_unpriced(vectors):
        route = vectors["all48"][0]["direct_composite"]
        route["infinity_halves"] += 1
    for name, mutator in (
        ("same-shape input class key", flip_input),
        ("same-shape output class key", flip_output),
        ("unpriced original call counter", flip_unpriced),
    ):
        forged_log = forged(mutator)
        # Demonstrate the gap without claiming it is a mathematical proof.
        auditor.audit(forged_log)
        expect_reject(lambda log=forged_log: bind_transcript_to_frozen(log, raw), name)
    expect_reject(lambda: bind_transcript_to_frozen(transcript, raw + b" "),
                  "native admission with altered immutable fixture bytes")

    return {
        "schema": "ct300-authentic-fixture-source-gate-v1",
        "frozen_git_blob": FROZEN_GIT_BLOB,
        "original_selected_vectors": 48,
        "real_scalar_schedule": list(EXPECTED_SCALARS),
        "synthetic_clock_samples": 144,
        "negative_controls_rejected": 5,
        "ct301_binding_negative_controls_rejected": 4,
        "ct301_source_values_bound": True,
        "scope": "producer-native frozen rows, source-only mock clock; no elapsed timing or full-solve result",
        "pcc": "unverified",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.fixture.read_bytes()), sort_keys=True))


if __name__ == "__main__":
    main()
