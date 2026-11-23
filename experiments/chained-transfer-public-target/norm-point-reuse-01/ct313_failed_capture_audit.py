#!/usr/bin/env python3
"""CT313 read-only audit of *failed* bounded child captures; NEVER admit ECDLP evidence.

A producer-supplied failure receipt is only a checkable record of partial bytes,
not trusted execution attestation, PCC or a complete native/solver result.
"""
import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "ct313-failed-native-capture/v1"
STATUSES = {"nonzero_exit", "timeout", "overflow", "spawn", "binary_changed",
            "host_changed", "collector_error", "invalid_exit"}
FIELDS = {"schema", "role", "source_commit_sha", "executable_sha256_before",
          "executable_sha256_after", "argv", "host_before", "host_after",
          "fixture_git_blob", "fixture_sha256", "status", "exit_code",
          "collector_error", "external_wall_ns", "stdout_sha256",
          "stdout_bytes", "stderr_sha256", "stderr_bytes", "admitted", "pcc"}


def refuse(reason):
    raise ValueError("CT313: " + reason)


def strict_json(raw):
    def object_pairs(pairs):
        seen = {}
        for k, v in pairs:
            if k in seen:
                refuse("duplicate JSON key")
            seen[k] = v
        return seen

    def forbidden_constant(_):
        refuse("nonfinite JSON constant")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=object_pairs,
                      parse_constant=forbidden_constant)


def hexdigest(raw):
    return hashlib.sha256(raw).hexdigest()


def gitblob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def derived_failure_status(d):
    """CT314: rederive CT310's exact failure precedence from serialized fields.

    This checks producer/internal consistency, NOT external execution proof.
    The original producer serializes a non-integer exit as JSON null.
    """
    if d["executable_sha256_before"] != d["executable_sha256_after"]:
        return "binary_changed"
    if d["host_before"] != d["host_after"]:
        return "host_changed"
    error = d["collector_error"]
    if error == "timeout":
        return "timeout"
    if error == "capture limit exceeded":
        return "overflow"
    if error == "spawn failed":
        return "spawn"
    if error is not None:
        return "collector_error"
    if d["exit_code"] is None:
        return "invalid_exit"
    if d["exit_code"] != 0:
        return "nonzero_exit"
    return None


def check(d, root, role, fixture):
    if type(d) is not dict or set(d) != FIELDS or d["schema"] != SCHEMA:
        refuse("failure receipt schema differs")
    if d["role"] != role or role not in ("original", "reuse"):
        refuse("wrong capture role")
    if d["admitted"] is not False or d["pcc"] != "unverified":
        refuse("failure receipt claims success")
    if type(d["status"]) is not str or d["status"] not in STATUSES:
        refuse("unrecognized failure status")
    if type(d["external_wall_ns"]) is not int or d["external_wall_ns"] <= 0:
        refuse("invalid external wall")
    for key, width in (("source_commit_sha", 40), ("executable_sha256_before", 64),
                       ("executable_sha256_after", 64), ("fixture_git_blob", 40),
                       ("fixture_sha256", 64)):
        val = d[key]
        if type(val) is not str or len(val) != width or any(c not in "0123456789abcdef" for c in val):
            refuse("malformed " + key)
    if type(d["argv"]) is not list or not d["argv"] or not all(
            type(arg) is str and arg for arg in d["argv"]):
        refuse("malformed argv")
    if type(d["exit_code"]) not in (int, type(None)):
        refuse("malformed exit code")
    if type(d["collector_error"]) not in (str, type(None)):
        refuse("malformed collector error")
    if type(d["host_before"]) is not dict or type(d["host_after"]) is not dict:
        refuse("malformed host bindings")
    if ((d["status"] == "binary_changed") !=
            (d["executable_sha256_before"] != d["executable_sha256_after"])):
        # Host drift can also occur with binary drift, but binary has precedence.
        if d["status"] == "binary_changed" or d["executable_sha256_before"] != d["executable_sha256_after"]:
            refuse("inconsistent binary change classification")
    if d["status"] == "host_changed" and d["host_before"] == d["host_after"]:
        refuse("missing claimed host drift")
    if d["status"] not in ("host_changed", "binary_changed") and d["host_before"] != d["host_after"]:
        refuse("unclassified host drift")
    if d["status"] != derived_failure_status(d):
        refuse("inconsistent failure classification: status/exit/error/host/binary")
    raw_fixture = Path(fixture).read_bytes()
    if d["fixture_sha256"] != hexdigest(raw_fixture) or d["fixture_git_blob"] != gitblob(raw_fixture):
        refuse("wrong fixture binding")
    for stream in ("stdout", "stderr"):
        raw = (Path(root) / (role + "." + stream)).read_bytes()
        ns = d[stream + "_bytes"]
        digest = d[stream + "_sha256"]
        if type(ns) is not int or ns != len(raw) or digest != hexdigest(raw):
            refuse("mismatched failed " + stream + " bytes")
    retained = Path(root) / (role + ".bin")
    if retained.exists() and hexdigest(retained.read_bytes()) != d["executable_sha256_after"]:
        refuse("retained binary SHA mismatch")
    return {"schema": "ct313-failure-receipt-audit/v1", "role": role,
            "status": d["status"], "raw_failure_bound": True,
            "execution_independently_verified": False, "pcc": "unverified"}


def verify(root, role, fixture):
    doc = strict_json((Path(root) / (role + ".failure.json")).read_bytes())
    return check(doc, root, role, fixture)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture-dir", type=Path, required=True)
    p.add_argument("--role", choices=("original", "reuse"), required=True)
    p.add_argument("--fixture", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(verify(args.capture_dir, args.role, args.fixture), sort_keys=True))


if __name__ == "__main__":
    main()
