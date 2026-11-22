#!/usr/bin/env python3
"""CT319: bind CT315 complete-cold wall/RSS claims to CT304 raw process receipts.

Still source-only. Neither these producer receipts nor fabricated self-test
measurements authenticate process execution or establish a cryptanalytic gain.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile

import ct304_execution_receipt_gate as receipt_gate
import ct315_complete_cold_panel as cold
import ct318_joint_cold_group_gate as joint

SCHEMA = "ct319-receipt-bound-cold-group/v1"


def refuse(why):
    raise ValueError("CT319: " + why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def argv_hash(argv):
    return sha(json.dumps(argv, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def audit(panel_raw, witness_raw, root, fixture):
    root = Path(root)
    fixture = Path(fixture)
    # Fail closed on unchanged CT315/CT317 source/group gates first.
    joined = joint.audit(panel_raw, witness_raw, root)
    panel = cold.strict_json(panel_raw)
    raw_fixture = fixture.read_bytes()
    fixture_sha = sha(raw_fixture)
    fixture_blob = receipt_gate.gitblob(raw_fixture)

    for row in panel["runs"]:
        rid = row["run_id"]
        arm = row["arm"]
        # CT317's run-id path sanitizer ran in joint.audit; CT304 additionally
        # requires its original producer's 32-hex run identity.
        binary = root / (arm + ".binary")
        stdout = root / (rid + ".stdout")
        stderr = root / (rid + ".stderr")
        recpath = root / (rid + ".receipt.json")
        rec = receipt_gate.check_capture(
            recpath, arm, stdout, stderr, binary, fixture_sha, fixture_blob)
        if rec["run_id"] != rid:
            refuse("CT304 run ID does not match CT315 row " + rid)
        required = (
            (rec["executable_sha256"], row["binary_sha256"], "binary"),
            (rec["stdout_sha256"], row["stdout_sha256"], "stdout"),
            (rec["external_wall_ns"], row["external_wall_ns"], "wall"),
            (rec["peak_rss_kib"], row["peak_rss_kib"], "peak RSS"),
            (rec["host"]["hostname"], row["host"], "host"),
            (rec["host"]["cpu_affinity"], row["cpu_affinity"], "affinity"),
            (argv_hash(rec["argv"]), row["argv_sha256"], "argv"),
        )
        for observed, claimed, label in required:
            if observed != claimed:
                refuse(rid + " disagrees with captured " + label)
        if type(rec["peak_rss_kib"]) is not int or rec["peak_rss_kib"] <= 0:
            refuse(rid + " missing physical peak-RSS receipt")
    return {
        **joined,
        "schema": SCHEMA,
        "source_gates": ["CT315", "CT317", "CT318", "CT304"],
        "fixture_sha256": fixture_sha,
        "fixture_git_blob": fixture_blob,
        "raw_receipts_bound_to_cold_wall_and_peak_rss": len(panel["runs"]),
        "raw_stderr_and_executable_hashes_checked": len(panel["runs"]),
        "producer_receipts_independently_authenticated": False,
        "source_commit_to_binary_build_provenance_verified": False,
        "actual_native_jacobian_executions_by_this_checker": 0,
        "qualifies_as_signed_speedup": False,
        "pcc": "unverified",
    }


def _fixture(root, candidate_ns):
    panel, witness = joint._fixture(root, candidate_ns)
    model = root / "fixture.original"
    model.write_bytes(b"CT319 synthetic original model bytes, NOT S3 custody\n")
    fbytes = model.read_bytes()
    for row in panel["runs"]:
        prior_id = row["run_id"]
        rid = sha(("CT319:" + prior_id).encode())[:32]
        arm = row["arm"]
        stdout = (root / (prior_id + ".stdout")).read_bytes()
        (root / (rid + ".stdout")).write_bytes(stdout)
        stderr = ("synthetic stderr for " + rid + "\n").encode()
        (root / (rid + ".stderr")).write_bytes(stderr)
        binary = root / (arm + ".binary")
        if not binary.exists():
            binary.write_bytes(("bin-" + arm).encode())
        argv = [str(binary), "--synthetic-toy", prior_id]
        rec = {
            "schema": receipt_gate.SCHEMA, "role": arm, "run_id": rid,
            "source_commit_sha": "c" * 40,
            "executable_sha256": sha(binary.read_bytes()),
            "argv": argv,
            "host": {
                "hostname": "synthetic-host", "machine": "x86_64",
                "system": "Linux", "kernel": "synthetic-kernel",
                "cpu_affinity": [0],
            },
            "fixture_sha256": sha(fbytes),
            "fixture_git_blob": receipt_gate.gitblob(fbytes),
            "exit_code": 0, "timed_out": False, "capture_complete": True,
            "stdout_sha256": sha(stdout), "stdout_bytes": len(stdout),
            "stderr_sha256": sha(stderr), "stderr_bytes": len(stderr),
            "external_wall_ns": row["external_wall_ns"],
            "peak_rss_kib": row["peak_rss_kib"],
        }
        recbytes = encoded(rec)
        (root / (rid + ".receipt.json")).write_bytes(recbytes)
        row["run_id"] = rid
        row["argv_sha256"] = argv_hash(argv)
        row["receipt_sha256"] = sha(recbytes)
    return panel, witness, model


def self_test():
    refusals = 0
    with tempfile.TemporaryDirectory(prefix="ct319-source-mock-") as d:
        root = Path(d)
        p, w, fixture = _fixture(root, 700)
        pos = audit(encoded(p), encoded(w), root, fixture)
        if pos["raw_receipts_bound_to_cold_wall_and_peak_rss"] != 28:
            raise AssertionError("CT319 synthetic positive population missing")
        if not (pos["provisional_best_baseline_over_candidate_exact"]["numerator"]
                > pos["provisional_best_baseline_over_candidate_exact"]["denominator"]):
            raise AssertionError("CT319 synthetic favorable ratio absent")
        q, v, _ = _fixture(root, 1700)
        neg = audit(encoded(q), encoded(v), root, fixture)
        if not (neg["provisional_best_baseline_over_candidate_exact"]["numerator"]
                < neg["provisional_best_baseline_over_candidate_exact"]["denominator"]):
            raise AssertionError("CT319 synthetic negative ratio not preserved")

        # The original CT318 accepts these legitimate-JSON fabricated
        # cost/argv mutations because it only hashes the receipt's bytes.
        for name, mutate in (
            ("wall", lambda panel: panel["runs"][0].update(
                external_wall_ns=panel["runs"][0]["external_wall_ns"] + 100)),
            ("rss", lambda panel: panel["runs"][0].update(peak_rss_kib=1001)),
            ("argv", lambda panel: panel["runs"][0].update(argv_sha256="0" * 64)),
        ):
            altered = copy.deepcopy(p)
            mutate(altered)
            joint.audit(encoded(altered), encoded(w), root)
            try:
                audit(encoded(altered), encoded(w), root, fixture)
            except (ValueError, OSError):
                refusals += 1
            else:
                raise AssertionError("CT319 admitted CT318 false-acceptance " + name)

        first = p["runs"][0]
        rid = first["run_id"]
        rp = root / (rid + ".receipt.json")
        stderr = root / (rid + ".stderr")
        binary = root / (first["arm"] + ".binary")
        for name, fn in (
            ("wrong-binary", lambda b: b + b"tamper"),
            ("absent-binary", lambda b: b""),
        ):
            raw = binary.read_bytes()
            binary.write_bytes(fn(raw))
            try:
                audit(encoded(p), encoded(w), root, fixture)
            except (ValueError, OSError):
                refusals += 1
            else:
                raise AssertionError("CT319 admitted " + name)
            finally:
                binary.write_bytes(raw)
        raw = stderr.read_bytes()
        stderr.write_bytes(raw + b"forged stderr\n")
        try:
            audit(encoded(p), encoded(w), root, fixture)
        except (ValueError, OSError):
            refusals += 1
        else:
            raise AssertionError("CT319 admitted changed stderr")
        finally:
            stderr.write_bytes(raw)

        original = rp.read_bytes()
        for label, change in (
            ("nonzero", lambda rec: rec.update(exit_code=1)),
            ("wall", lambda rec: rec.update(external_wall_ns=100000)),
            ("host", lambda rec: rec["host"].update(hostname="forged-host")),
            ("run", lambda rec: rec.update(run_id="e" * 32)),
            ("stdout", lambda rec: rec.update(stdout_sha256="0" * 64)),
            ("role", lambda rec: rec.update(role="forged-arm")),
        ):
            rec = receipt_gate.strict_json(original)
            change(rec)
            new_raw = encoded(rec)
            rp.write_bytes(new_raw)
            altered = copy.deepcopy(p)
            altered["runs"][0]["receipt_sha256"] = sha(new_raw)
            # CT318 accepts the altered receipt if its new raw hash is
            # updated; CT304 must independently reject its semantics.
            joint.audit(encoded(altered), encoded(w), root)
            try:
                audit(encoded(altered), encoded(w), root, fixture)
            except (ValueError, OSError):
                refusals += 1
            else:
                raise AssertionError("CT319 admitted forged receipt " + label)
            finally:
                rp.write_bytes(original)

        raw = fixture.read_bytes()
        fixture.write_bytes(b"wrong fixture\n")
        try:
            audit(encoded(p), encoded(w), root, fixture)
        except (ValueError, OSError):
            refusals += 1
        else:
            raise AssertionError("CT319 admitted changed fixture")
        finally:
            fixture.write_bytes(raw)

        stderr.unlink()
        try:
            audit(encoded(p), encoded(w), root, fixture)
        except (ValueError, OSError):
            refusals += 1
        else:
            raise AssertionError("CT319 admitted missing stderr")
    if refusals != 13:
        raise AssertionError("CT319 lost corruption controls: " + str(refusals))
    return {
        "schema": "ct319-source-only-selftest/v1",
        "synthetic_positive_negative_panels": 2,
        "synthetic_complete_cold_processes_per_panel": 28,
        "ct318_false_acceptances_closed": 3,
        "synthetic_corruptions_refused": refusals,
        "actual_native_jacobian_executions": 0,
        "pcc": "unverified",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--panel", type=Path)
    p.add_argument("--witness", type=Path)
    p.add_argument("--raw-root", type=Path)
    p.add_argument("--fixture", type=Path)
    args = p.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        if args.witness is None or args.raw_root is None or args.fixture is None:
            refuse("--witness, --raw-root, and --fixture are mandatory")
        print(json.dumps(audit(
            args.panel.read_bytes(), args.witness.read_bytes(),
            args.raw_root, args.fixture), sort_keys=True))


if __name__ == "__main__":
    main()
