#!/usr/bin/env python3
"""Restore and check every pinned source and input this replication builds.

This is `koblitz-n83-closure-indexlift-20261019`'s `restore.py` (PR #997,
merged as e55510070) with two changes: the local file list, and a check of
every parent digest. The derivation is the parent's and is not changed.

* crypto 770f6a69 goes into `snapshots/r770/`. It is extracted by the
  reconcile experiment's own code
  (`../koblitz-n83-reconcile-20261014/restore_sources.py`) and checked
  against the reconcile protocol's r770 digests. `make_online_source.py`
  (verbatim) then derives the closure + index-lift producer. Its chain is the
  rank-probe producer (`d4394df3...`), the index-lift producer
  (`7df72603...`), the closure producer (`8916e034...`) and the composition.
  The composition's digest must equal the PARENT protocol's frozen
  `online_source_sha256` (`1d328b2e...`) and this protocol's.
* the two Z[tau]-closure headers (`snapshots/closure/`) are regenerated
  from B's K600 header by `make_closure_base.py` (verbatim). Each SHA-256
  must equal the parent protocol's and this protocol's.
* every file copied verbatim from the parent (`VERBATIM`) must have the
  digest the parent protocol froze for it (`sources.local_sha256`). The
  parent protocol is read from `../koblitz-n83-closure-indexlift-20261019/
  protocol.json`, and its own SHA-256 is pinned here (`PARENT_PROTOCOL_SHA256`).
* every local file must have the digest in this `protocol.json`.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
RECONCILE = EXPERIMENTS / "koblitz-n83-reconcile-20261014"
SNAPSHOT = HERE / "snapshots" / "r770"
DERIVED = SNAPSHOT / "examples" / "koblitz_orbit_dlp_fast_online_closure_indexlift.rs"
CLOSURE = HERE / "snapshots" / "closure"
CLOSURE_BASES = {"M38": (16, 64), "M10": (60, 16)}  # name: (columns, norm cap)
PARENT = EXPERIMENTS / "koblitz-n83-closure-indexlift-20261019"
PARENT_PROTOCOL_SHA256 = "ff5b4cbfba8097cf1c1125f500f4f75ac82bd2d6518fae5da4976e5eec64a9c1"
# local_files() keys copied byte for byte from the parent; their digests are the parent protocol's.
VERBATIM = ("online_manifest", "online_lock", "online_derivation", "indexlift_derivation", "closure_derivation",
            "parent_closure_protocol", "rankprobe_derivation", "rankcut_derivation", "stacked_derivation",
            "tablefilter_derivation", "probepipe_derivation", "combined_derivation", "closure_base_builder",
            "closure_verifier", "closure_log_table_M38", "closure_log_table_M10", "closure_local_decisive_test",
            "local_layout_test", "lift2_lib", "lift2_tests", "lift2_manifest", "lift2_lock", "arm_wrapper",
            "archived_identities", "log_table_check")


def closure_path(name):
    return CLOSURE / ("base_n83_closure_%s.jsonl" % name)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def local_files():
    return {
        "online_manifest": HERE / "online/Cargo.toml",
        "online_lock": HERE / "online/Cargo.lock",
        "online_derivation": HERE / "make_online_source.py",
        "indexlift_derivation": HERE / "make_indexlift_source.py",
        "closure_derivation": HERE / "make_closure_source.py",
        "parent_closure_protocol": HERE / "inputs/parent_closure_protocol.json",
        "rankprobe_derivation": HERE / "make_rankprobe_source.py",
        "rankcut_derivation": HERE / "make_rankcut_source.py",
        "stacked_derivation": HERE / "make_stacked_source.py",
        "tablefilter_derivation": HERE / "make_tablefilter_source.py",
        "probepipe_derivation": HERE / "make_probepipe_source.py",
        "combined_derivation": HERE / "make_combined_source.py",
        "closure_base_builder": HERE / "make_closure_base.py",
        "closure_verifier": HERE / "verify_closure.py",
        "closure_log_table_M38": HERE / "inputs/factor_logs_n83_closure_M38.json",
        "closure_log_table_M10": HERE / "inputs/factor_logs_n83_closure_M10.json",
        "closure_local_decisive_test": HERE / "inputs/local_decisive_test.json",
        "local_layout_test": HERE / "inputs/local_layout_test.json",
        "lift2_lib": HERE / "lift2/src/lib.rs",
        "lift2_tests": HERE / "lift2/tests/exhaustive.rs",
        "lift2_manifest": HERE / "lift2/Cargo.toml",
        "lift2_lock": HERE / "lift2/Cargo.lock",
        "arm_wrapper": HERE / "arm.py",
        "archived_identities": HERE / "inputs/archived_identities.json",
        "log_table_check": HERE / "check_log_table.py",
        "schedule_builder": HERE / "make_schedule.py",
        "schedule_runner": HERE / "run_schedule.py",
        "receipt_verifier": HERE / "verify_receipt.py",
        "receipt_verifier_tests": HERE / "test_verify_receipt.py",
        "targets_builder": HERE / "make_targets.py",
        "cold_targets": HERE / "inputs/cold_targets.json",
        "panel_disjointness": HERE / "inputs/panel_disjointness.json",
        "panel_scanner": HERE / "check_panel_disjoint.py",
        "figures_builder": HERE / "make_figures.py",
        "power_check": HERE / "power_check.py",
        "power_prior_builder": HERE / "make_power_prior.py",
        "power_prior": HERE / "inputs/power_prior.json",
        "power_result": HERE / "analysis/power.json",
        "protocol_builder": HERE / "make_protocol.py",
        "host_cpu_record": HERE.parent.parent / "scripts/host_cpu_record.py",
    }


def parent_protocol():
    path = PARENT / "protocol.json"
    if sha256(path) != PARENT_PROTOCOL_SHA256:
        raise ValueError("the parent protocol differs from its pinned digest")
    return json.loads(path.read_text())


def check_parent_digests(result):
    """Every parent digest: derived producer, closure headers, verbatim files."""
    parent = parent_protocol()
    problems = []
    if result["online_source_sha256"] != parent["sources"]["online_source_sha256"]:
        problems.append("derived producer differs from the parent's frozen digest")
    for name in CLOSURE_BASES:
        if result["closure_headers_sha256"][name] != parent["online"]["bases"][name]["header_sha256"]:
            problems.append("closure header %s differs from the parent's frozen digest" % name)
    files = local_files()
    for key in VERBATIM:
        if sha256(files[key]) != parent["sources"]["local_sha256"][key]:
            problems.append("%s differs from the parent's frozen digest" % key)
    if problems:
        raise ValueError("; ".join(problems))
    return {"parent_protocol_sha256": PARENT_PROTOCOL_SHA256, "verbatim_files_checked": len(VERBATIM),
            "online_source_sha256_equals_parent": True, "closure_headers_equal_parent": True}


def restore(crypto_repo, check_pins=True):
    sys.path.insert(0, str(RECONCILE))
    import restore_sources as reconcile  # noqa: E402
    expected_r770 = json.loads((RECONCILE / "protocol.json").read_text())["sources"]["r770"]["sha256"]
    if SNAPSHOT.is_symlink():
        raise ValueError("snapshots/r770 must be a local directory")
    if not SNAPSHOT.exists():
        if crypto_repo is None:
            raise FileNotFoundError("pass --crypto-repo, a clone of https://github.com/aburan28/crypto")
        SNAPSHOT.parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="n83-clirep-restore-", dir=SNAPSHOT.parent) as folder:
            staged = Path(folder) / "r770"
            staged.mkdir()
            reconcile.extract("r770", crypto_repo, staged)
            reconcile.check("r770", staged, expected_r770)
            staged.rename(SNAPSHOT)
    if DERIVED.exists():
        DERIVED.unlink()
    reconcile.check("r770", SNAPSHOT, expected_r770)
    subprocess.run([sys.executable, str(HERE / "make_online_source.py")], check=True,
                   stdout=subprocess.DEVNULL)
    for name, (columns, cap) in CLOSURE_BASES.items():
        subprocess.run([sys.executable, str(HERE / "make_closure_base.py"), "--columns", str(columns),
                        "--norm", str(cap), "--out", str(closure_path(name))], check=True,
                       stdout=subprocess.DEVNULL)
    result = {"r770": str(SNAPSHOT), "online_source_sha256": sha256(DERIVED),
              "closure_headers_sha256": {name: sha256(closure_path(name)) for name in CLOSURE_BASES}}
    result["parent"] = check_parent_digests(result)
    if check_pins:
        protocol = json.loads((HERE / "protocol.json").read_text())
        pins = protocol["sources"]
        if sha256(DERIVED) != pins["online_source_sha256"]:
            raise ValueError("derived online producer differs from the frozen digest")
        for name in CLOSURE_BASES:
            if result["closure_headers_sha256"][name] != protocol["online"]["bases"][name]["header_sha256"]:
                raise ValueError("closure header %s differs from the frozen digest" % name)
        wrong = [key for key, path in local_files().items() if sha256(path) != pins["local_sha256"][key]]
        if wrong:
            raise ValueError("local source differs from protocol.json: " + ", ".join(wrong))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crypto-repo", type=Path)
    parser.add_argument("--print-local-digests", action="store_true",
                        help="print the local digests (used once, to freeze the protocol)")
    parser.add_argument("--no-pin-check", action="store_true",
                        help="development only: restore and derive without checking protocol pins")
    args = parser.parse_args()
    if args.print_local_digests:
        print(json.dumps({key: sha256(path) for key, path in local_files().items()},
                         indent=2, sort_keys=True))
        return
    print(json.dumps(restore(args.crypto_repo, not args.no_pin_check), sort_keys=True))


if __name__ == "__main__":
    main()
