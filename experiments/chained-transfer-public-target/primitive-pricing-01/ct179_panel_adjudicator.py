#!/usr/bin/env python3
"""CT179: strict OFFLINE adjudication of a complete CT176 cold transfer panel.

No native code is executed. This is producer-authored source checking, not PCC.
"""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

SCHEMA = "ct176-cold-public-process-panel/v1"
CHILD_SCHEMA = "ct175-single-public-packet-cold-route/v1"
FIXTURE_BLOB = "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3"
SEED = 20261117
BLOCKS = 8
ARMS = ("direct_composite", "strongest_retained_lift_chain",
        "strongest_retained_lift_chain", "direct_composite",
        "direct_composite", "direct_composite")
N = 48 * BLOCKS * len(ARMS)
MAX_LINE = 2_000_000


def refuse(condition, reason):
    if not condition:
        raise ValueError(reason)


def strict_pairs(pairs):
    d = {}
    for k, v in pairs:
        refuse(k not in d, "duplicate JSON object key: " + k)
        d[k] = v
    return d


def bad_constant(value):
    raise ValueError("nonfinite JSON token: " + value)


def decode_json(raw):
    return json.loads(raw, object_pairs_hook=strict_pairs,
                      parse_constant=bad_constant)


def decimal(value, name, positive=False):
    refuse(type(value) is str and value and value.isascii()
           and value.isdecimal(), name + ": not a decimal string")
    n = int(value)
    refuse(str(n) == value and (n > 0 if positive else n >= 0),
           name + ": noncanonical or out of range")
    return n


def integer(value, name, minimum=0):
    refuse(type(value) is int and value >= minimum, name + ": nonnegative integer required")
    return value


def word_array(value, name):
    refuse(type(value) is list and len(value) == 19, name + ": 19 words required")
    for word in value:
        refuse(type(word) is int and 0 <= word <= 0xFFFFFFFF,
               name + ": invalid unsigned word")


def hex_digest(value):
    return (type(value) is str and len(value) == 64
            and all(ch in "0123456789abcdef" for ch in value))


def frozen_fixture(path):
    raw = Path(path).read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    refuse(blob == FIXTURE_BLOB, "original 48-row fixture Git blob mismatch")
    data = decode_json(raw)
    refuse(type(data) is dict and set(data) == {"scope", "all48"},
           "fixture schema")
    rows = data["all48"]
    refuse(type(rows) is list and len(rows) == 48, "fixture population")
    seen = set()
    for i, row in enumerate(rows):
        refuse(type(row) is dict and set(row) == {
            "from", "to", "sector", "scalar_OUTSIDE_runtime", "input",
            "whole_outputs_equal", "direct_composite",
            "literal_sequential_Jacobian_maps", "strongest_retained_lift_chain"
        }, "fixture row field set")
        d = integer(row["from"], "from")
        t = integer(row["to"], "to")
        s = integer(row["sector"], "sector")
        k = integer(row["scalar_OUTSIDE_runtime"], "scalar label")
        refuse((d, t) in ((0, 2), (2, 0)) and s < 4 and
               k in (0, 1, 2, 17, 12345, 2771710), "fixture cohort")
        refuse((d, t, s, k) not in seen, "duplicate fixture cohort")
        seen.add((d, t, s, k))
        word_array(row["input"], "fixture source")
        word_array(row["whole_outputs_equal"], "fixture target")
        for arm in ("direct_composite", "strongest_retained_lift_chain",
                    "literal_sequential_Jacobian_maps"):
            calls = row[arm]
            refuse(type(calls) is dict and len(calls) == 21, "fixture calls")
            for val in calls.values():
                integer(val, "fixture counter")
    refuse(len(seen) == 48, "missing cohort")
    return rows, hashlib.sha256(raw).hexdigest()


def roster():
    for block in range(BLOCKS):
        packet_order = list(range(48))
        random.Random(SEED + block).shuffle(packet_order)
        for index in packet_order:
            for position, arm in enumerate(ARMS):
                yield block, index, position, arm


def raw_pipe(sample, prefix):
    encoded = sample.get(prefix + "_base64")
    refuse(type(encoded) is str, prefix + " missing base64")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError(prefix + " base64 malformed") from exc
    refuse(len(data) <= 131072, prefix + " exceeds bounded complete output")
    digest = sample.get(prefix + "_sha256")
    refuse(hex_digest(digest) and hashlib.sha256(data).hexdigest() == digest,
           prefix + " digest mismatch")
    try:
        text = data.decode("utf-8", "backslashreplace")
    except UnicodeError as exc:
        raise ValueError(prefix + " decode error") from exc
    refuse(sample.get(prefix) == text, prefix + " rendered text differs")
    return text


def valid_sample(sample, row, index, arm):
    refuse(type(sample) is dict, "sample not an object")
    refuse(sample.get("verified") is True and
           sample.get("capture_complete") is True and
           sample.get("error") is None, "failed or censored sample")
    refuse(type(sample.get("exit_code")) is int and
           sample["exit_code"] == 0, "child exit not zero")
    elapsed = decimal(sample.get("external_wall_ns_decimal"), "external wall", True)
    stdout = raw_pipe(sample, "stdout")
    raw_pipe(sample, "stderr")
    lines = stdout.strip().splitlines()
    refuse(len(lines) == 1, "child must have one JSON line")
    child = decode_json(lines[0])
    refuse(type(child) is dict and child.get("schema") == CHILD_SCHEMA,
           "native child schema")
    expected = {
        "packet_index": index, "from": row["from"], "to": row["to"],
        "sector": row["sector"],
        "scalar_label_outside_runtime": row["scalar_OUTSIDE_runtime"],
        "fixture_rows_checked": 48, "preflight_native_routes": 0,
        "preflight_native_inverses": 0,
    }
    for name, value in expected.items():
        refuse(type(child.get(name)) is int and child[name] == value,
               "child cohort: " + name)
    refuse(child.get("arm") == arm and
           child.get("rustc_child_process_spawned") is False and
           child.get("external_os_loader_wall_included") is False,
           "wrong arm/provenance")
    for name, expected_words in (("public_source_packet", row["input"]),
                                 ("verified_canonical_target", row["whole_outputs_equal"])):
        value = child.get(name)
        word_array(value, name)
        refuse(value == expected_words, name + " changed")
    counts = child.get("native_calls")
    expected_calls = row[arm]
    refuse(type(counts) is dict and set(counts) == set(expected_calls)
           and len(counts) == 21, "native counter schema")
    for name, v in expected_calls.items():
        refuse(type(counts[name]) is int and counts[name] == v,
               "native counter mismatch: " + name)
    native = child.get("native_sample")
    refuse(type(native) is dict and native.get("complete_counter_match") is True,
           "native sample failed verification")
    # CT180: the Rust monotonic clock starts before setup, and the route
    # timer starts only after setup. Both intervals are enclosed by total.
    # The Python external wall clock encloses the whole fresh child process.
    # A reversed ordering is impossible for a correctly measured sample and
    # must not be allowed to bias the paired transfer cost estimator.
    route_ns = decimal(native.get("elapsed_ns_decimal"), "native elapsed", True)
    setup_ns = decimal(child.get("same_process_setup_ns_decimal"), "native setup")
    total_ns = decimal(child.get("in_process_total_ns_decimal"), "native in-process", True)
    refuse(setup_ns + route_ns <= total_ns, "native setup/route exceeds internal total")
    refuse(total_ns <= elapsed, "internal total exceeds external process wall")
    rss = child.get("peak_rss_kib_linux")
    if rss is not None:
        integer(rss, "peak RSS")
    refuse(sample.get("peak_rss_kib_linux") == rss and
           (rss is None or type(sample.get("peak_rss_kib_linux")) is int),
           "peak RSS mismatch")
    return elapsed, rss


def percentile(values, p):
    refuse(len(values) > 0, "percentile has no observations")
    x = sorted(values)
    z = (len(x) - 1) * p
    lo = math.floor(z)
    hi = math.ceil(z)
    return x[lo] + (x[hi] - x[lo]) * (z - lo)


def paired_statistics(matrix, rows):
    # Matrix is keyed by (block,packet) and includes 6 strictly positive wall times.
    packet_logs = {}
    drift = {}
    for i in range(48):
        changes = []
        controls = []
        for b in range(BLOCKS):
            a, c, d, aa, a1, a2 = matrix[(b, i)]
            refuse(min(a, c, d, aa, a1, a2) > 0, "zero external wall time")
            changes.append(math.log((a + aa) / (c + d)))
            controls.append(abs(math.log(a1 / a2)))
        packet_logs[i] = statistics.median(changes)
        drift[i] = controls
    groups = {}
    for i, row in enumerate(rows):
        key = (row["from"], row["to"], row["sector"],
               "identity" if row["scalar_OUTSIDE_runtime"] == 0 else "generic")
        groups.setdefault(key, []).append(i)
    refuse(len(groups) == 16, "missing frozen strata")
    result = []
    for k, ids in sorted(groups.items()):
        effect = statistics.median(packet_logs[i] for i in ids)
        control = [v for i in ids for v in drift[i]]
        ci = None
        if len(ids) > 1:
            rng = random.Random(SEED + 7919 * (k[0] + 1) +
                                127 * k[2] + (1 if k[3] == "generic" else 0))
            samples = []
            for _ in range(2000):
                batch = [packet_logs[rng.choice(ids)] for _ in ids]
                samples.append(statistics.median(batch))
            ci = [math.exp(percentile(samples, p)) for p in (0.025, 0.975)]
        result.append({
            "direction": [k[0], k[1]], "sector": k[2], "class": k[3],
            "unique_packets": len(ids), "paired_blocks": len(ids) * BLOCKS,
            "direct_over_retained_transfer_wall_ratio": math.exp(effect),
            "cluster_bootstrap_ratio_ci95": ci,
            "aa_abs_log_ratio_p95": percentile(control, 0.95),
        })
    return result


def adjudicate(panel, fixture):
    rows, fixture_hash = frozen_fixture(fixture)
    dig = hashlib.sha256()
    with open(panel, "rb") as fh:
        def next_obj():
            line = fh.readline(MAX_LINE + 1)
            refuse(line and len(line) <= MAX_LINE, "missing/oversize panel line")
            dig.update(line)
            return decode_json(line)

        manifest = next_obj()
        refuse(type(manifest) is dict and manifest.get("type") == "manifest"
               and manifest.get("schema") == SCHEMA, "manifest schema")
        for name, val in (("fixture_git_blob", FIXTURE_BLOB),
                          ("fixture_sha256", fixture_hash),
                          ("blocks", BLOCKS), ("seed", SEED),
                          ("processes", N), ("packets", 48)):
            refuse(type(manifest.get(name)) is type(val)
                   and manifest[name] == val, "manifest mismatch: " + name)
        refuse(manifest.get("arms_in_each_block") == list(ARMS),
               "manifest arm roster mismatch")
        refuse(hex_digest(manifest.get("executable_sha256")) and
               type(manifest.get("host")) is dict,
               "missing executable/host identity")
        integer(manifest.get("panel_wall_seconds"), "panel budget", 1)
        integer(manifest.get("timeout_seconds"), "child timeout", 1)
        refuse(type(manifest.get("executable_path")) is str and
               manifest["executable_path"], "missing executable path")
        matrix = {}
        rss_vals = []
        missing_rss = 0
        for b, i, pos, arm in roster():
            s = next_obj()
            refuse(type(s) is dict and s.get("type") == "sample",
                   "non-sample within roster")
            for label, expected in (("block", b), ("packet_index", i),
                                    ("position", pos), ("arm", arm)):
                refuse(type(s.get(label)) is type(expected)
                       and s[label] == expected, "roster mismatch: " + label)
            refuse(s.get("argv") == [manifest["executable_path"],
                                    "--cold-route", str(i), arm],
                   "spawned command mismatch")
            t, rss = valid_sample(s, rows[i], i, arm)
            matrix.setdefault((b, i), []).append(t)
            if rss is None:
                missing_rss += 1
            else:
                rss_vals.append(rss)
        terminal = next_obj()
        refuse(type(terminal) is dict and terminal.get("type") == "terminal"
               and terminal.get("verified_complete") is True
               and terminal.get("refusal") is None
               and type(terminal.get("attempted")) is int
               and terminal["attempted"] == N
               and type(terminal.get("planned")) is int
               and terminal["planned"] == N, "terminal refused/incomplete")
        refuse(fh.read(1) == b"", "trailing records after terminal")
    return {
        "schema": "ct179-cold-transfer-only-adjudication/v1",
        "standing": "[pcc:unverified]",
        "input_panel_sha256": dig.hexdigest(),
        "frozen_fixture_sha256": fixture_hash,
        "frozen_fixture_git_blob": FIXTURE_BLOB,
        "executable_sha256_producer_reported": manifest["executable_sha256"],
        "host_identity_producer_reported": manifest["host"],
        "observed_complete_processes": N,
        "peak_rss_kib_linux_producer_reported_max": max(rss_vals, default=None),
        "processes_missing_peak_rss": missing_rss,
        "complete_memory_evidence": missing_rss == 0,
        "strata": paired_statistics(matrix, rows),
        "scope": "producer-only cold transfer wall, not a complete ECDLP",
        "complete_single_target_ecdlp_advantage_established": False,
        "original_full_695_701_custody_replayed": False,
        "signed_independent_pcc": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = adjudicate(args.panel, args.fixture)
    with args.output.open("x", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True, allow_nan=False)
        fh.write("\n")
    print("CT179 producer-only transfer adjudication complete, NO ECDLP speedup claim")


if __name__ == "__main__":
    main()
