#!/usr/bin/env python3
"""Restore and check every pinned source and input of the n=83 K'=4 / 400-orbit experiment.

The producer is the field-ops experiment's (`../koblitz-n83-fieldops-20261104`,
on main). This script does not re-derive it: it runs the field-ops
`restore.py` (with its pin check, so every pin of THAT protocol holds: crypto
770f6a69, the whole derivation chain, the rank-finder digest 301615b3..., the
field-ops source 8dc428ea..., the M10 and M38 headers), and then:

* checks the field-ops files this experiment builds and runs (`fieldops_files()`:
  the field-ops protocol, its crates, builder and verifier) against the SHA-256
  pinned in this `protocol.json`;
* regenerates the two closure headers this experiment runs into its own
  `snapshots/closure/`: M38 (`make_closure_base.py --columns 16 --norm 64`) and
  D4 (`--columns 4 --norm 165`), both with the field-ops builder unchanged, and
  requires each SHA-256 to equal the protocol's (M38's also equals the
  field-ops protocol's);
* checks that `inputs/factor_logs_n83_closure_D4.json` is the table
  `make_log_table.py` derives, and that the files copied byte for byte from the
  field-ops experiment (`VERBATIM_FROM_FIELDOPS`) still equal theirs;
* checks every local file against the digest in this `protocol.json`.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDOPS = HERE.parent / "koblitz-n83-fieldops-20261104"
FIELDOPS_PROTOCOL_SHA256 = "abe5bb74569b0cf4ec88f0ad0bf1c8fbd882260b7b2e6bd08860a22a7b526700"
CLOSURE = HERE / "snapshots" / "closure"
CLOSURE_BASES = {"M38": (16, 64), "D4": (4, 165)}  # name: (columns, norm cap)
# Files of this directory that are byte for byte the field-ops experiment's.
VERBATIM_FROM_FIELDOPS = {"run_schedule.py": "run_schedule.py",
                          "inputs/factor_logs_n83_closure_M38.json": "inputs/factor_logs_n83_closure_M38.json"}


def closure_path(name):
    return CLOSURE / ("base_n83_closure_%s.jsonl" % name)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fieldops_files():
    return {
        "fieldops_protocol": FIELDOPS / "protocol.json",
        "fieldops_restore": FIELDOPS / "restore.py",
        "fieldops_closure_base_builder": FIELDOPS / "make_closure_base.py",
        "fieldops_closure_verifier": FIELDOPS / "verify_closure.py",
        "fieldops_receipt_verifier": FIELDOPS / "verify_receipt.py",
        "fieldops_source_derivation": FIELDOPS / "make_fieldops_source.py",
        "online_b_manifest": FIELDOPS / "online-b/Cargo.toml",
        "online_b_lock": FIELDOPS / "online-b/Cargo.lock",
        "online_b_cargo_config": FIELDOPS / "online-b/.cargo/config.toml",
        "online_manifest": FIELDOPS / "online/Cargo.toml",
        "online_lock": FIELDOPS / "online/Cargo.lock",
        "lift2_lib": FIELDOPS / "lift2/src/lib.rs",
        "lift2_lock": FIELDOPS / "lift2/Cargo.lock",
    }


def local_files():
    names = ("arm.py", "run_schedule.py", "make_schedule.py", "make_protocol.py", "verify_receipt.py",
             "test_verify_receipt.py", "check_log_table.py", "make_log_table.py", "local_identity.py",
             "make_local_profile.py", "make_targets.py", "check_panel_disjoint.py", "check_seed_disjoint.py",
             "make_power_prior.py", "power_check.py", "band_model.py", "restore.py",
             "inputs/factor_logs_n83_closure_M38.json", "inputs/factor_logs_n83_closure_D4.json",
             "inputs/local_identity.json", "inputs/local_profile.json", "inputs/local_prototype_rows.jsonl",
             "inputs/local_verify_closure_D4.json", "inputs/cold_targets.json", "inputs/panel_disjointness.json",
             "inputs/seed_disjointness.json", "inputs/power_prior.json", "analysis/power.json",
             "profile/run_cold.sh", "profile/run_rank.sh", "profile/prototype_driver.py")
    files = {name.replace("/", "_").replace(".", "_"): HERE / name for name in names}
    files["host_cpu_record"] = HERE.parent.parent / "scripts/host_cpu_record.py"
    return files


def check_verbatim():
    wrong = [mine for mine, theirs in VERBATIM_FROM_FIELDOPS.items() if sha256(HERE / mine) != sha256(FIELDOPS / theirs)]
    if wrong:
        raise ValueError("not byte for byte the field-ops experiment's: " + ", ".join(wrong))
    return sorted(VERBATIM_FROM_FIELDOPS)


def restore(crypto_repo, check_pins=True):
    if sha256(FIELDOPS / "protocol.json") != FIELDOPS_PROTOCOL_SHA256:
        raise ValueError("the field-ops protocol differs from its pinned digest")
    argv = [sys.executable, str(FIELDOPS / "restore.py")]
    if crypto_repo is not None:
        argv += ["--crypto-repo", str(crypto_repo)]
    producer = json.loads(subprocess.run(argv, check=True, capture_output=True, text=True).stdout)
    fo = json.loads((FIELDOPS / "protocol.json").read_text())
    if producer["fieldops_source_sha256"] != fo["sources"]["fieldops_source_sha256"]:
        raise ValueError("the field-ops producer differs from the field-ops protocol's frozen digest")
    for name, (columns, cap) in CLOSURE_BASES.items():
        subprocess.run([sys.executable, str(FIELDOPS / "make_closure_base.py"), "--columns", str(columns),
                        "--norm", str(cap), "--out", str(closure_path(name))], check=True, stdout=subprocess.DEVNULL)
    result = {"fieldops_restore": producer, "fieldops_source_sha256": producer["fieldops_source_sha256"],
              "closure_headers_sha256": {name: sha256(closure_path(name)) for name in CLOSURE_BASES},
              "verbatim_from_fieldops": check_verbatim()}
    if result["closure_headers_sha256"]["M38"] != fo["online"]["bases"]["M38"]["header_sha256"]:
        raise ValueError("the M38 header differs from the field-ops protocol's frozen digest")
    subprocess.run([sys.executable, str(HERE / "make_log_table.py"), "--check"], check=True, stdout=subprocess.DEVNULL)
    result["d4_table_is_derived"] = True
    if check_pins:
        protocol = json.loads((HERE / "protocol.json").read_text())
        pins = protocol["sources"]
        for name in CLOSURE_BASES:
            if result["closure_headers_sha256"][name] != protocol["online"]["bases"][name]["header_sha256"]:
                raise ValueError("closure header %s differs from the frozen digest" % name)
        wrong = [key for key, path in fieldops_files().items()
                 if sha256(path) != pins["fieldops_files_pinned"][key]]
        wrong += [key for key, path in local_files().items() if sha256(path) != pins["local_sha256"][key]]
        if wrong:
            raise ValueError("source differs from protocol.json: " + ", ".join(wrong))
        result["pins_checked"] = len(fieldops_files()) + len(local_files())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crypto-repo", type=Path)
    parser.add_argument("--no-pin-check", action="store_true",
                        help="development only: restore and derive without checking this protocol's pins")
    args = parser.parse_args()
    print(json.dumps(restore(args.crypto_repo, not args.no_pin_check), sort_keys=True))


if __name__ == "__main__":
    main()
