#!/usr/bin/env python3
"""Restore and check every pinned source and input of the n=83 field-ops-2 on D4 experiment.

Both producers are the field-ops-2 experiment's (`../koblitz-n83-fieldops2-20261107`,
on main): side A is its side A (the field-ops producer `ic_online_fieldops_r770`,
built from its `online/` crate) and side B its side B (the field-ops-2 producer
R1, `ic_online_fieldops2_r770`, built from its `online-b/` crate). This script
does not re-derive either: it runs the field-ops-2 `restore.py` (with its pin
check, so every pin of THAT protocol holds: crypto 770f6a69, the whole derivation
chain, the field-ops source 8dc428ea... and the field-ops-2 source), and then:

* checks the field-ops-2 files this experiment builds and runs
  (`fieldops2_files()`: the protocol, both crates, the derivations, the closure
  builder and verifier) against the SHA-256 pinned in this `protocol.json`;
* regenerates the D4 closure header (`make_closure_base.py --columns 4 --norm 165`,
  the field-ops builder unchanged) into this experiment's own `snapshots/closure/`
  and requires its SHA-256 to equal the one frozen by `koblitz-n83-k4c400-20261107`
  (`K4_D4_HEADER_SHA256`), the header of the run 42425640847 receipt;
* checks that `inputs/factor_logs_n83_closure_D4.json` is the table
  `make_log_table.py` derives from the field-ops-2 M38 table and is byte for byte the
  k4c400 experiment's, and that the files copied byte for byte
  (`VERBATIM`) still equal their sources;
* checks every local file against the digest in this `protocol.json`.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FO2 = HERE.parent / "koblitz-n83-fieldops2-20261107"
K4 = HERE.parent / "koblitz-n83-k4c400-20261107"
FO2_PROTOCOL_SHA256 = "86f690a1d25fdc739355165e62fc7ae6721362fcce3001ccebdcec1696b7f5ee"
K4_PROTOCOL_SHA256 = "b4a5b0c462a03ce79a3e51809e3b5b73425d144abef51cf8af5e64957c6f92b7"
K4_D4_HEADER_SHA256 = "fabaf09f47c28a744cfb8888198d411d4e033c2deb4caf657d2eda3da07361d4"
CLOSURE = HERE / "snapshots" / "closure"
D4_COLUMNS, D4_NORM = 4, 165
# Files of this directory that are byte for byte another experiment's: (mine, theirs).
VERBATIM = {"run_schedule.py": FO2 / "run_schedule.py",
            "arm.py": K4 / "arm.py",
            "inputs/factor_logs_n83_closure_D4.json": K4 / "inputs/factor_logs_n83_closure_D4.json",
            "inputs/local_verify_closure_D4.json": K4 / "inputs/local_verify_closure_D4.json"}


def closure_path():
    return CLOSURE / "base_n83_closure_D4.jsonl"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fieldops2_files():
    return {
        "fieldops2_protocol": FO2 / "protocol.json",
        "fieldops2_restore": FO2 / "restore.py",
        "closure_base_builder": FO2 / "make_closure_base.py",
        "closure_verifier": FO2 / "verify_closure.py",
        "fieldops_source_derivation": FO2 / "make_fieldops_source.py",
        "fieldops2_source_derivation": FO2 / "make_fieldops2_source.py",
        "online_manifest": FO2 / "online/Cargo.toml",
        "online_lock": FO2 / "online/Cargo.lock",
        "online_cargo_config": FO2 / "online/.cargo/config.toml",
        "online_b_manifest": FO2 / "online-b/Cargo.toml",
        "online_b_lock": FO2 / "online-b/Cargo.lock",
        "online_b_cargo_config": FO2 / "online-b/.cargo/config.toml",
        "lift2_lib": FO2 / "lift2/src/lib.rs",
        "lift2_lock": FO2 / "lift2/Cargo.lock",
        "m38_table": FO2 / "inputs/factor_logs_n83_closure_M38.json",
        "k4c400_protocol": K4 / "protocol.json",
    }


def local_files():
    names = ("arm.py", "run_schedule.py", "make_schedule.py", "make_protocol.py", "verify_receipt.py",
             "test_verify_receipt.py", "check_log_table.py", "make_log_table.py", "local_identity.py",
             "make_targets.py", "check_panel_disjoint.py", "check_seed_disjoint.py",
             "make_power_prior.py", "power_check.py", "band_model.py", "restore.py",
             "inputs/factor_logs_n83_closure_D4.json", "inputs/local_identity.json",
             "inputs/local_verify_closure_D4.json", "inputs/cold_targets.json", "inputs/panel_disjointness.json",
             "inputs/seed_disjointness.json", "inputs/power_prior.json", "analysis/power.json")
    files = {name.replace("/", "_").replace(".", "_"): HERE / name for name in names}
    files["host_cpu_record"] = HERE.parent.parent / "scripts/host_cpu_record.py"
    return files


def check_verbatim():
    wrong = [mine for mine, theirs in VERBATIM.items() if sha256(HERE / mine) != sha256(theirs)]
    if wrong:
        raise ValueError("not byte for byte the source experiment's: " + ", ".join(wrong))
    return sorted(VERBATIM)


def restore(crypto_repo, check_pins=True):
    if sha256(FO2 / "protocol.json") != FO2_PROTOCOL_SHA256:
        raise ValueError("the field-ops-2 protocol differs from its pinned digest")
    if sha256(K4 / "protocol.json") != K4_PROTOCOL_SHA256:
        raise ValueError("the k4c400 protocol differs from its pinned digest")
    argv = [sys.executable, str(FO2 / "restore.py")]
    if crypto_repo is not None:
        argv += ["--crypto-repo", str(crypto_repo)]
    producer = json.loads(subprocess.run(argv, check=True, capture_output=True, text=True).stdout)
    fo2 = json.loads((FO2 / "protocol.json").read_text())
    if producer["online_source_sha256"] != fo2["sources"]["online_source_sha256"]:
        raise ValueError("side A's producer differs from the field-ops-2 protocol's frozen digest")
    if producer["fieldops2_source_sha256"] != fo2["sources"]["fieldops2_source_sha256"]:
        raise ValueError("side B's producer differs from the field-ops-2 protocol's frozen digest")
    subprocess.run([sys.executable, str(FO2 / "make_closure_base.py"), "--columns", str(D4_COLUMNS),
                    "--norm", str(D4_NORM), "--out", str(closure_path())], check=True, stdout=subprocess.DEVNULL)
    result = {"fieldops2_restore": producer, "fieldops_source_sha256": producer["online_source_sha256"],
              "fieldops2_source_sha256": producer["fieldops2_source_sha256"],
              "d4_header_sha256": sha256(closure_path()), "verbatim": check_verbatim()}
    if result["d4_header_sha256"] != K4_D4_HEADER_SHA256:
        raise ValueError("the D4 header differs from the one the k4c400 experiment froze and ran")
    subprocess.run([sys.executable, str(HERE / "make_log_table.py"), "--check"], check=True, stdout=subprocess.DEVNULL)
    result["d4_table_is_derived"] = True
    if check_pins:
        protocol = json.loads((HERE / "protocol.json").read_text())
        pins = protocol["sources"]
        if result["d4_header_sha256"] != protocol["online"]["bases"]["D4"]["header_sha256"]:
            raise ValueError("the D4 header differs from the frozen digest")
        wrong = [key for key, path in fieldops2_files().items()
                 if sha256(path) != pins["fieldops2_files_pinned"][key]]
        wrong += [key for key, path in local_files().items() if sha256(path) != pins["local_sha256"][key]]
        if wrong:
            raise ValueError("source differs from protocol.json: " + ", ".join(wrong))
        result["pins_checked"] = len(fieldops2_files()) + len(local_files())
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
