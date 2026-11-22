#!/usr/bin/env python3
"""CT316: Linux GNU-time per-child peak RSS wrapper and read-only evidence audit.

Source-level/producer-bound only: does not independently prove child execution.
No original Jacobian models, S3, paid compute, or ECDLP benchmarks in --self-test.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tempfile

FORMAT = "CT316_V1 RSS_KIB=%M EXIT=%x"
SCHEMA = "ct316-gnu-time-peak-rss/v1"
LINE = re.compile(rb"CT316_V1 RSS_KIB=([1-9][0-9]*) EXIT=0\n\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


def refuse(msg):
    raise ValueError("CT316: " + msg)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sha_lock(x):
    if type(x) is not str or SHA.fullmatch(x) is None:
        refuse("invalid canonical time executable SHA256")
    return x


def check_meter_binary(path, expected_sha):
    if platform.system() != "Linux":
        refuse("GNU time peak RSS is only admitted on Linux")
    path = Path(path)
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        refuse("time executable must be an absolute executable file")
    observed = sha(path.read_bytes())
    if observed != sha_lock(expected_sha):
        refuse("time executable SHA256 differs from explicit pin")
    return observed


def invocation(meter_path, expected_sha, native_argv, output_path):
    """The unchanged CT176 subprocess collector receives this exact argv."""
    check_meter_binary(meter_path, expected_sha)
    if (type(native_argv) is not list or not native_argv or
            any(type(x) is not str or not x for x in native_argv)):
        refuse("invalid native argv")
    output_path = Path(output_path)
    if not output_path.is_absolute() or output_path.exists():
        refuse("meter output must name a new absolute path")
    return [str(meter_path), "-f", FORMAT, "-o", str(output_path)] + native_argv


def measured_peak(output_path):
    try:
        raw = Path(output_path).read_bytes()
    except OSError as exc:
        refuse("missing meter output: " + str(exc))
    # Refuse GNU time diagnostic text, missing line or a child failure.
    match = LINE.fullmatch(raw)
    if match is None:
        refuse("noncanonical/failed GNU time result")
    peak = int(match.group(1))
    if peak <= 0 or peak > 2**63 - 1:
        refuse("invalid peak RSS in KiB")
    return peak, sha(raw)


def produce_receipt(output_path, meter, meter_sha, native_argv, invoked_argv):
    peak, output_sha = measured_peak(output_path)
    if invocation_for_check(meter, meter_sha, native_argv, output_path) != invoked_argv:
        refuse("meter invocation does not bind the native argv")
    return {
        "schema": SCHEMA, "time_executable_sha256": meter_sha,
        "time_executable_path": str(meter), "native_argv": list(native_argv),
        "invoked_argv": list(invoked_argv),
        "meter_output_sha256": output_sha, "peak_rss_kib": peak,
        "meter_unit": "KiB", "claim": "child-ru_maxrss-not-process-tree",
        "pcc": "unverified",
    }


def invocation_for_check(meter_path, expected_sha, native_argv, output_path):
    """Read-only recomputation: unlike invocation, output must already exist."""
    check_meter_binary(meter_path, expected_sha)
    if (type(native_argv) is not list or not native_argv or
            any(type(x) is not str or not x for x in native_argv)):
        refuse("invalid native argv")
    if not Path(output_path).is_absolute():
        refuse("meter output path not absolute")
    return [str(meter_path), "-f", FORMAT, "-o", str(output_path)] + native_argv


def check_receipt(record, output_path, meter, expected_sha, native_argv):
    if type(record) is not dict or set(record) != {
        "schema", "time_executable_sha256", "time_executable_path",
        "native_argv", "invoked_argv", "meter_output_sha256", "peak_rss_kib",
        "meter_unit", "claim", "pcc",
    }:
        refuse("incorrect meter receipt schema")
    if (record["schema"] != SCHEMA or record["meter_unit"] != "KiB" or
        record["claim"] != "child-ru_maxrss-not-process-tree" or
        record["pcc"] != "unverified"):
        refuse("unsupported meter provenance/standing")
    if record["time_executable_sha256"] != sha_lock(expected_sha):
        refuse("meter SHA pin changed")
    if record["time_executable_path"] != str(meter) or record["native_argv"] != native_argv:
        refuse("time path or native argv differs from runner")
    if (record["invoked_argv"] !=
            invocation_for_check(meter, expected_sha, native_argv, output_path)):
        refuse("underlying invoked argv differs")
    actual, raw_sha = measured_peak(output_path)
    if (record["meter_output_sha256"] != raw_sha or
        type(record["peak_rss_kib"]) is not int or
        record["peak_rss_kib"] != actual):
        refuse("meter byte digest or RSS claim differs")
    return actual


def verify(receipt_path, output_path, meter, meter_sha, native_argv):
    def pairs_unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                refuse("duplicate JSON key")
            d[k] = v
        return d
    def invalid_constant(x):
        refuse("invalid JSON constant " + x)
    rec = json.loads(Path(receipt_path).read_bytes(),
                     object_pairs_hook=pairs_unique, parse_constant=invalid_constant)
    return check_receipt(rec, output_path, meter, meter_sha, native_argv)


def self_test():
    # Harmless Python child and synthetic mutations. No Jacobian/model input.
    meter = Path("/usr/bin/time")
    if not meter.is_file():
        refuse("GNU time missing on source-test host")
    meter_sha = sha(meter.read_bytes())
    passed, rejected = 0, 0
    with tempfile.TemporaryDirectory(prefix="ct316-benign-os-rss-") as d:
        root = Path(d)
        native_argv = ["/usr/bin/python3", "-c",
                       "import sys; a=bytearray(4*1024*1024); "
                       "print('CT316_BENIGN_CHILD'); sys.stdout.flush()"]
        out = root / "meter.out"
        command = invocation(meter, meter_sha, native_argv, out)
        run = subprocess.run(command, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, timeout=10, check=False)
        if run.returncode != 0 or run.stdout != b"CT316_BENIGN_CHILD\n":
            raise AssertionError("benign child failed")
        rec = produce_receipt(out, meter, meter_sha, native_argv, command)
        receipt = root / "meter.json"
        receipt.write_text(json.dumps(rec, sort_keys=True))
        if verify(receipt, out, meter, meter_sha, native_argv) < 1:
            raise AssertionError("actual OS RSS positive control missing")
        passed += 1
        mutations = [
            lambda r: r.update(peak_rss_kib=None),
            lambda r: r.update(peak_rss_kib=0),
            lambda r: r.update(peak_rss_kib=True),
            lambda r: r.update(peak_rss_kib=r["peak_rss_kib"]+1),
            lambda r: r.update(meter_output_sha256="0"*64),
            lambda r: r.update(time_executable_sha256="0"*64),
            lambda r: r.update(native_argv=["/bin/false"]),
            lambda r: r.update(invoked_argv=["/bin/false"]),
            lambda r: r.update(claim="independently-validated"),
            lambda r: r.update(pcc="verified"),
        ]
        for mutate in mutations:
            bad = copy.deepcopy(rec)
            mutate(bad)
            try:
                check_receipt(bad, out, meter, meter_sha, native_argv)
            except ValueError:
                rejected += 1
            else:
                raise AssertionError("forged meter receipt accepted")
        raw = out.read_bytes()
        bad_values = [b"", b"CT316_V1 RSS_KIB=0 EXIT=0\n",
                      b"CT316_V1 RSS_KIB=00 EXIT=0\n",
                      b"CT316_V1 RSS_KIB=2 EXIT=1\n",
                      b"CT316_V1 RSS_KIB=True EXIT=0\n",
                      raw + b"Command exited with nonzero status\n"]
        for corrupt in bad_values:
            out.write_bytes(corrupt)
            try:
                verify(receipt, out, meter, meter_sha, native_argv)
            except ValueError:
                rejected += 1
            else:
                raise AssertionError("malformed/altered GNU time output accepted")
        out.write_bytes(raw)
        if verify(receipt, out, meter, meter_sha, native_argv) != rec["peak_rss_kib"]:
            raise AssertionError("correct restored receipt did not validate")
        try:
            invocation(meter, "0"*64, native_argv, root/"unused")
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("unlocked meter binary accepted")
        try:
            invocation(meter, meter_sha, native_argv, out)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("overwriting meter output accepted")
    if passed != 1 or rejected != 18:
        raise AssertionError("unexpected CT316 mutation population")
    return {"schema": "ct316-benign-real-os-source-selftest/v1",
            "benign_os_child_rss_measured": passed, "mutations_refused": rejected,
            "native_jacobian_models_executed": 0, "pcc": "unverified"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        print(json.dumps({"schema": SCHEMA, "execute": False,
                          "native_jacobian_models_executed": 0,
                          "pcc": "unverified"}))
