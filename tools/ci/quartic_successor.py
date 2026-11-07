#!/usr/bin/env python3
"""Run the two field-index producers in a new workspace, preserving old attempts."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from check_quartic_certificates import MANIFEST, REPOSITORY, verify_inputs
from quartic_portable_replay import copy_verified, new_output

STUDY = Path("experiments/hecke-432-j1728-field-index-gate-20261026")
MODES = {
    "field": ("run_sage.py", "protocol.json", ("attempt.json", "polynomial_result.json", "result.json")),
    "basis": ("basis_audit_sage.py", "basis_protocol.json", ("basis_attempt.json", "basis_result.json")),
}


def prepare(root, output, manifest, mode):
    root, output = Path(root).resolve(), Path(output).absolute()
    if output.resolve().is_relative_to(root):
        raise ValueError("a successor workspace must be outside the source checkout")
    if verify_inputs(root, manifest["inputs"]):
        raise ValueError("frozen source mismatch")
    output = new_output(output, root)
    copy_verified(root, output / "originals", manifest["inputs"])
    shutil.copytree(output / "originals", output / "worktree")
    script, protocol, generated = MODES[mode]
    study = output / "worktree" / STUDY
    for name in generated:
        (study / name).unlink(missing_ok=True)
    data = json.loads((study / protocol).read_text())
    return output, study / script, study / protocol, data["timeout_seconds"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=MODES)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args(argv)
    manifest = json.loads(MANIFEST.read_text())
    # Every executing job goes through this repository's checked launcher.
    launcher = REPOSITORY / "sage"
    if not args.prepare_only and not launcher.is_file():
        raise ValueError("the repository's checked Sage launcher is required")
    output, script, protocol, timeout = prepare(REPOSITORY, args.out, manifest, args.mode)
    command = [str(launcher), "-python", str(script)]
    metadata = {"mode": args.mode, "command": command, "timeout_seconds": timeout,
                "source_sha256": sha256(script.read_bytes()).hexdigest(),
                "protocol_sha256": sha256(protocol.read_bytes()).hexdigest(),
                "original_manifest_sha256": sha256(MANIFEST.read_bytes()).hexdigest(),
                "status": "PREPARED_ONLY" if args.prepare_only else "PREPARED"}
    (output / "launch.json").write_text(json.dumps(metadata, indent=2) + "\n")
    if args.prepare_only:
        return 0
    runtime = subprocess.run([str(launcher), "--runtime-info"], capture_output=True, text=True,
                             timeout=60)
    (output / "checked-runtime.stdout").write_text(runtime.stdout)
    (output / "checked-runtime.stderr").write_text(runtime.stderr)
    if runtime.returncode:
        metadata.update({"status": "CHECKED_RUNTIME_REFUSED", "returncode": runtime.returncode})
        (output / "attempt.json").write_text(json.dumps(metadata, indent=2) + "\n")
        raise ValueError("checked Sage runtime verification failed")
    start = time.monotonic()
    with (output / "stdout.txt").open("w") as stdout, (output / "stderr.txt").open("w") as stderr:
        try:
            run = subprocess.Popen(command, cwd=script.parent, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
            code = run.wait(timeout=timeout)
            status = "COMPLETED" if code == 0 else "SAGE_ERROR"
        except subprocess.TimeoutExpired:
            try:
                os.killpg(run.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            run.wait()
            code, status = 124, "TIME_LIMIT"
    metadata.update({"status": status, "returncode": code,
                     "elapsed_seconds": round(time.monotonic() - start, 3)})
    metadata["outputs"] = {name: sha256((script.parent / name).read_bytes()).hexdigest()
                           for name in MODES[args.mode][2] if (script.parent / name).is_file()}
    if verify_inputs(REPOSITORY, manifest["inputs"]):
        metadata["source_changed"] = True
        code = 1
    (output / "attempt.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
