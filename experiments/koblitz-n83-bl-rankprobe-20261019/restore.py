#!/usr/bin/env python3
"""Restore and check every pinned source this experiment builds or executes.

Nothing is derived here. The two frozen sibling experiments restore their own
sources, each checked against its own frozen protocol:

* `../koblitz-n83-rankprobe-20261019/restore.py`: crypto 770f6a69 into its
  `snapshots/r770/` and the rank-probe producer (the n=83 baseline's
  `ic_online_rankprobe_r770`) derived by its `make_online_source.py`, checked
  against its `protocol.json` (`online_source_sha256 d4394df3...` and every
  local digest);
* `../koblitz-n83-bl-arm-20261014/restore_sources.py`: crypto 770f6a69 into its
  `snapshot/` and the generated BL arm (`bl_generated/`), checked against its
  `protocol.json` `sources.sha256` and B's `tier1_protocol.json`.

Then every local file and every sibling file this run executes (wrappers,
table tools, manifests, locks, B's factor-log table) is checked against this
experiment's `protocol.json` (`sources.local_sha256`, `sources.sibling_sha256`).
`--print-digests` prints the local and sibling digests without checking.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
RP = EXP / "koblitz-n83-rankprobe-20261019"
BL = EXP / "koblitz-n83-bl-arm-20261014"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tables():
    sys.path.insert(0, str(HERE))
    import make_protocol  # noqa: E402  (the digest lists)
    return make_protocol.local_files(), make_protocol.sibling_files()


def restore(crypto_repo, check_pins=True):
    result = {}
    proc = subprocess.run([sys.executable, str(RP / "restore.py")] +
                          (["--crypto-repo", str(crypto_repo)] if crypto_repo else []),
                          check=True, capture_output=True, text=True)
    result["rankprobe_restore"] = json.loads(proc.stdout.strip().splitlines()[-1])
    proc = subprocess.run([sys.executable, str(BL / "restore_sources.py")] +
                          (["--crypto-repo", str(crypto_repo)] if crypto_repo else []),
                          check=True, capture_output=True, text=True)
    result["bl_restore"] = proc.stdout.strip().splitlines()[-1]
    if check_pins:
        pins = json.loads((HERE / "protocol.json").read_text())["sources"]
        local, sibling = tables()
        wrong = [k for k, p in local.items() if sha256(p) != pins["local_sha256"][k]]
        wrong += [k for k, p in sibling.items() if sha256(p) != pins["sibling_sha256"][k]]
        if wrong:
            raise ValueError("files differ from protocol.json: " + ", ".join(sorted(wrong)))
        if result["rankprobe_restore"]["online_source_sha256"] != \
                json.loads((HERE / "protocol.json").read_text())["baseline_at_freeze"]["online_source_sha256"]:
            raise ValueError("the restored IC producer is not the baseline row's")
        result["pins"] = "PASS"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crypto-repo", type=Path)
    parser.add_argument("--print-digests", action="store_true")
    parser.add_argument("--no-pin-check", action="store_true", help="development only")
    args = parser.parse_args()
    if args.print_digests:
        local, sibling = tables()
        print(json.dumps({"local": {k: sha256(p) for k, p in local.items()},
                          "sibling": {k: sha256(p) for k, p in sibling.items()}}, indent=1, sort_keys=True))
        return
    print(json.dumps(restore(args.crypto_repo, not args.no_pin_check), sort_keys=True))


if __name__ == "__main__":
    main()
