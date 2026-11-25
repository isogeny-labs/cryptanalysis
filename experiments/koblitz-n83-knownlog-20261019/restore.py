#!/usr/bin/env python3
"""Restore and check every pinned source this experiment builds or runs.

* The IC producer is the n=83 baseline's, unchanged: the rank-probe
  producer of `koblitz-n83-rankprobe-20261019`. Its own `restore.py`
  restores crypto 770f6a69 into `../koblitz-n83-rankprobe-20261019/snapshots/r770`
  (the reconcile experiment's extraction, digest-checked), derives the
  producer and checks it against that experiment's frozen digest
  (`d4394df3...`). The tuned rho, the pinned oracle, B's K600 base and Q0 come
  from the same snapshot.
* That experiment's `protocol.json` and `arm.py` (the baseline and rho arms
  run through it) are checked against this protocol's pins.
* Every local source, manifest, lock file and input of this directory
  (including the known-log generator crate `knownlog/`) is checked against
  `protocol.json`.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RANKPROBE = HERE.parent / "koblitz-n83-rankprobe-20261019"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def local_files():
    return {
        "generator_manifest": HERE / "knownlog/Cargo.toml",
        "generator_lock": HERE / "knownlog/Cargo.lock",
        "generator_source": HERE / "knownlog/src/main.rs",
        "knownlog_checker": HERE / "check_knownlog.py",
        "arm_wrapper": HERE / "arm.py",
        "schedule_builder": HERE / "make_schedule.py",
        "schedule_runner": HERE / "run_schedule.py",
        "receipt_verifier": HERE / "verify_receipt.py",
        "targets_builder": HERE / "make_targets.py",
        "cold_targets": HERE / "inputs/cold_targets.json",
        "power_prior_builder": HERE / "make_power_prior.py",
        "power_prior": HERE / "inputs/power_prior.json",
        "cost_model": HERE / "cost_model.py",
        "cost_model_result": HERE / "analysis/cost_model.json",
        "power_check": HERE / "power_check.py",
        "power_result": HERE / "analysis/power.json",
        "smoke_identities": HERE / "smoke/smoke_local.json",
        "protocol_builder": HERE / "make_protocol.py",
    }


def upstream_files():
    return {"rankprobe_protocol": RANKPROBE / "protocol.json", "rankprobe_arm_wrapper": RANKPROBE / "arm.py",
            "rankprobe_restore": RANKPROBE / "restore.py"}


def restore(crypto_repo, check_pins=True):
    spec = importlib.util.spec_from_file_location("rankprobe_restore", RANKPROBE / "restore.py")
    rankprobe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rankprobe)  # koblitz-n83-rankprobe-20261019/restore.py, its own pins checked
    result = rankprobe.restore(crypto_repo, True)
    if check_pins:
        pins = json.loads((HERE / "protocol.json").read_text())["sources"]
        if result["online_source_sha256"] != pins["producer_source_sha256"]:
            raise ValueError("derived rank-probe producer differs from the pinned digest")
        wrong = [key for key, path in upstream_files().items() if sha256(path) != pins["upstream_sha256"][key]]
        wrong += [key for key, path in local_files().items() if sha256(path) != pins["local_sha256"][key]]
        if wrong:
            raise ValueError("source differs from protocol.json: " + ", ".join(wrong))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crypto-repo", type=Path)
    parser.add_argument("--no-pin-check", action="store_true",
                        help="development only: restore without checking this protocol's pins")
    args = parser.parse_args()
    print(json.dumps(restore(args.crypto_repo, not args.no_pin_check), sort_keys=True))


if __name__ == "__main__":
    main()
